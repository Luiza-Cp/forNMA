# src/fornma/gui/app.py
import webbrowser
from copy import deepcopy
from pathlib import Path
from typing import Dict
import base64
from dash import Dash, html, dcc, Input, Output, State, ALL, no_update, ctx
import dash_bootstrap_components as dbc

from .layouts.segmentation import build_sidebar as build_segmentation_sidebar
from .callbacks.segmentation import register as register_segmentation_callbacks
from fornma.gui.utils.params_builder import build_interface_params
from fornma.Segmentation.run import run as run_pipeline

import json, threading, time, os
from datetime import datetime
PROGRESS_FILE = None  # definido quando o usuário inicia Preview/Run

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
try:
    with open(ASSETS_DIR / "fornma_logo.png", "rb") as _lf:
        DEFAULT_LOGO = "data:image/png;base64," + base64.b64encode(_lf.read()).decode("ascii")
except Exception:
    DEFAULT_LOGO = None  # se não achar o arquivo, a <img> fica sem src inicial


# --- util: native dialog to pick folders (100% local)
def pick_directory_dialog() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory()
        root.destroy()
        return path or ""
    except Exception:
        # fallback: no GUI available
        return ""


# --- initial table state (1 channel, 1 example row)
def initial_table_state() -> Dict:
    return {
        "channels": [{"id": "ch1", "name": "Channel 1"}],
        "channels": [{"id": "ch1", "name": "Channel 1"}],
        "rows": [
            {"condition": "Control", "ch1": ""}  # use channel ids as keys
        ]
    }

# --- helper to flatten the grid of ids/values (para padrões ALL, ALL)
def _flatten_id_value_grid(ids_grid, values_grid):
    """Retorna [(id_dict, value), ...] aceitando tanto lista plana quanto lista de listas."""
    flat = []

    # Nada para fazer
    if not isinstance(ids_grid, list) or not isinstance(values_grid, list):
        return flat

    # Caso A: lista PLANA de dicts
    if ids_grid and isinstance(ids_grid[0], dict):
        for pid, val in zip(ids_grid, values_grid or []):
            flat.append((pid, val))
        return flat

    # Caso B: GRADE (lista de listas)
    for row_ids, row_vals in zip(ids_grid or [], values_grid or []):
        if isinstance(row_ids, list):
            for pid, val in zip(row_ids or [], row_vals or []):
                flat.append((pid, val))
        else:
            # fallback defensivo: se por algum motivo vier misto
            if isinstance(row_ids, dict):
                flat.append((row_ids, row_vals))
    return flat



# --- helpers to build the dynamic HTML table
def render_table(data: Dict) -> html.Div:
    channels = data.get("channels", [])  # [{"id":"ch1","name":"Channel 1"}, ...]
    rows = data.get("rows", [])

    # header: Condition + inputs to rename channel columns
    header_cells = [html.Th("Condition")]
    for ch in channels:
        header_cells.append(
            html.Th(
                dcc.Input(
                    id={"type": "chan-name", "col": ch["id"]},
                    value=ch.get("name", ""),
                    placeholder="Channel name",
                    style={"width": "100%"},
                    persistence=True, persisted_props=["value"], persistence_type="session",
                )
            )
        )
    header = html.Thead(html.Tr(header_cells))

    # body
    body_rows = []
    for r_idx, row in enumerate(rows):
        cond_cell = html.Td(dcc.Input(
            id={"type": "cond-input", "row": r_idx},
            value=row.get("condition", ""),
            placeholder="Condition name",
            style={"width": "100%"},
            persistence=True, persisted_props=["value"], persistence_type="session",
        ))

        chan_cells = []
        for ch in channels:
            ch_id = ch["id"]
            path_val = row.get(ch_id, "")
            chan_cells.append(
                html.Td(
                    html.Div([
                        dcc.Input(
                            id={"type": "path-input", "row": r_idx, "col": ch_id},
                            value=path_val,
                            placeholder=f"Path to {ch.get('name','')}",
                            style={"width": "80%"},
                            persistence=True, persisted_props=["value"], persistence_type="session",
                        ),
                        html.Button(
                            "Browse",
                            id={"type": "browse-btn", "row": r_idx, "col": ch_id},
                            n_clicks=0,
                            style={"marginLeft": "6px"}
                        )
                    ], style={"display": "flex", "alignItems": "center"})
                )
            )
        body_rows.append(html.Tr([cond_cell] + chan_cells))

    table = dbc.Table([header, html.Tbody(body_rows)], bordered=True, responsive=True, style={"background": "white"})
    return table


def create_app():
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="forNMA GUI",
        suppress_callback_exceptions=True,
    )

    MODULES = [
        ("tab-home", "Home"),
        ("tab-registration", "Image Registration"),
        ("tab-segmentation", "Segmentation"),
        ("tab-foci-overlay", "Foci Overlay"),
        ("tab-NMA", "NMA"),
        ("tab-graphs", "Graphical Analysis"),
        ("tab-clustering", "Clustering"),
        ("tab-stats", "Statistics"),
        ("tab-tracking", "Tracking"),
    ]

    tabs = dcc.Tabs(
        id="tabs",
        value="tab-home",
        children=[dcc.Tab(label=label, value=tab) for tab, label in MODULES],
    )

    # left column with sidebars (only the active one is shown)
    sidebars = html.Div([
        # HOME sidebar
        html.Div(id={"type": "sidebar", "tab": "tab-home"}, children=[
            html.H3("Home"),
            html.P("Welcome! Instructions, links, etc."),
            html.Button("Open README", id="btn-open-readme"),
        ]),

        # SEGMENTATION sidebar (imported)
        build_segmentation_sidebar(),

        # add other module sidebars here as needed
    ], id="left-pane", style={
        "width": "25%", "padding": "12px", "borderRight": "3px solid #2d5bd1",
        "background": "#eef2ff", "height": "100vh", "overflowY": "auto",
        "position": "relative", "zIndex": 2,
    })

    # stores
    store = dcc.Store(id="store-images", data=initial_table_state())
    store_seg = dcc.Store(id="store-seg", data={})
    store_clicks = dcc.Store(id="store-browse-clicks", data={})

    # --- IMAGES MODAL
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Load images — conditions × channels")),
            dbc.ModalBody([
                dbc.Alert(id="alert-errors", is_open=False, color="danger"),
                html.Div(id="table-container")  # only the table is dynamic
            ], style={"background": "#f6f8ff"}),
            dbc.ModalFooter([
                html.Div(id="counter-box", style={"marginRight": "auto"}),
                html.Button("+ Add condition", id="btn-add-row", n_clicks=0),
                html.Button("+ Add channel", id="btn-add-col", n_clicks=0, style={"marginLeft": "10px"}),
                html.Button("Save", id="btn-save-table", n_clicks=0, style={"marginLeft": "18px"}),
                html.Button("Close", id="btn-close-modal", n_clicks=0, style={"marginLeft": "6px"})
            ])
        ],
        id="images-modal",
        is_open=False, size="xl", backdrop="static", scrollable=True
    )

    # --- MAIN LAYOUT (two columns)
    app.layout = html.Div([
        store,
        store_seg,
        store_clicks,

        html.Div([
            sidebars,  # left column (all sidebars)
            html.Div([tabs, html.Div(id="tab-content", style={"padding": "10px"})],
                     style={
                         "width": "75%",
                         "padding": "10px",
                         "height": "100vh",
                         "overflow": "hidden",
                         "position": "relative",
                         "zIndex": 1}),
        ], style={"display": "flex"}),
        modal
    ])

    # --- TAB CONTENT (placeholders)
    @app.callback(
        Output("tab-content", "children"),
        Input("tabs", "value")
    )
    def _render_tab(tab):
        if tab == "tab-home":
            return html.Div([
                html.H3("Preview / Results"),
                html.Div("forNMA logo or preview appears here.",
                         style={"textAlign": "center", "margin": "40px"}),
                html.Img(id="preview-img", style={"maxWidth": "100%", "maxHeight": "70vh"})
            ])
        elif tab == "tab-tracking":
            return html.Div([html.H4("Tracking module"), html.P("Coming soon...")])
        elif tab == "tab-registration":
            return html.Div([html.H4("Image Registration module"), html.P("Coming soon...")])
        elif tab == "tab-segmentation":
            return html.Div(
                [
                    html.H4("Segmentation — progress & logs"),

                    # Wrapper sempre visível
                    html.Div(
                        id="seg-run-ui",
                        children=[
                            # Container em GRID: imagem (70vh) + rodapé (12vh)
                            html.Div(
                                id="seg-grid",
                                children=[
                                    # ===== ÁREA DA IMAGEM (70vh máx) =====
                                    html.Div(
                                        id="seg-stage",
                                        children=html.Img(
                                            id="seg-live-img",
                                            src=DEFAULT_LOGO,  # logo até aparecer 1ª preview
                                            style={
                                                "minHeight": 0,
                                                "display": "flex",
                                                "alignItems": "center",
                                                "justifyContent": "center",
                                                # 👇 logo sempre presente como fundo
                                                "backgroundImage": f"url({DEFAULT_LOGO})",
                                                "backgroundRepeat": "no-repeat",
                                                "backgroundPosition": "center",
                                                "backgroundSize": "contain",
                                                "maxHeight": "70vh",
                                                "maxWidth": "100%",
                                            },
                                            title="Latest saved image",
                                        ),
                                        style={
                                            "minHeight": 0,
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                        },
                                    ),

                                    # ===== RODAPÉ (BARRA DE PROGRESSO) — 12vh =====
                                    html.Div(
                                        id="seg-footer",
                                        children=[
                                            dbc.Progress(
                                                id="seg-progress",
                                                value=0, max=100,
                                                striped=True, animated=True,
                                                style={"height": "22px"},
                                            ),
                                            html.Div(
                                                id="seg-progress-text",
                                                style={"marginTop": "6px", "fontFamily": "monospace"},
                                            ),
                                        ],
                                        style={
                                            "display": "none",  # começa escondido, callback mostra
                                            "flexDirection": "column",
                                            "justifyContent": "center",
                                            "gap": "6px",
                                        },
                                    ),
                                ],
                                style={
                                    "height": "82vh",  # total do painel
                                    "width": "100%",
                                    "boxSizing": "border-box",
                                    "overflow": "hidden",
                                    "display": "grid",
                                    "gridTemplateRows": "70vh 12vh",  # imagem + rodapé
                                    "rowGap": "8px",
                                },
                            ),
                        ],
                        style={
                            "display": "block",  # painel sempre visível
                            "width": "100%",
                            "maxWidth": "100%",
                            "overflow": "hidden",
                        },
                    ),

                    html.Hr(),
                    html.Pre(
                        id="seg-log",
                        style={"whiteSpace": "pre-wrap", "maxHeight": "55vh", "overflowY": "auto"},
                    ),

                    dcc.Interval(id="seg-poll", interval=800, disabled=True),
                ],
                style={"padding": "8px"},
            )

    # --- OPEN/CLOSE MODAL
    @app.callback(
        Output("images-modal", "is_open"),
        Output("table-container", "children"),
        Input("btn-open-modal", "n_clicks"),
        Input("btn-close-modal", "n_clicks"),
        State("images-modal", "is_open"),
        State("store-images", "data"),
        prevent_initial_call=True
    )
    def _toggle_modal(open_clicks, close_clicks, is_open, data):
        trig = ctx.triggered_id
        if trig == "btn-open-modal":
            return True, render_table(data)
        elif trig == "btn-close-modal":
            return False, no_update
        return is_open, no_update

    # --- SHOW ONLY THE ACTIVE SIDEBAR
    @app.callback(
        Output({"type": "sidebar", "tab": ALL}, "style"),
        Input("tabs", "value"),
        State({"type": "sidebar", "tab": ALL}, "id"),
    )
    def toggle_sidebars(active_tab, sidebar_ids):
        show, hide = {"display": "block"}, {"display": "none"}
        return [show if sid["tab"] == active_tab else hide for sid in sidebar_ids]

    # --- ADD CONDITION / CHANNEL
    @app.callback(
        Output("store-images", "data", allow_duplicate=True),
        Output("table-container", "children", allow_duplicate=True),
        Input("btn-add-row", "n_clicks"),
        Input("btn-add-col", "n_clicks"),
        State("store-images", "data"),
        prevent_initial_call=True
    )
    def _add_row_col(n_row, n_col, data):
        if not ctx.triggered_id:
            return no_update, no_update

        data = deepcopy(data)
        trig = ctx.triggered_id

        if trig == "btn-add-row":
            # nova linha com as chaves dos canais atuais, tudo vazio
            new_row = {"condition": ""}
            for ch in data.get("channels", []):
                new_row[ch["id"]] = ""
            data["rows"].append(new_row)

        elif trig == "btn-add-col":
            # novo canal com ID estável e inicializa vazio em TODAS as linhas
            max_idx = max([int(ch["id"][2:]) for ch in data.get("channels", [])] or [0])
            new_id = f"ch{max_idx + 1}"
            data["channels"].append({"id": new_id, "name": f"Channel {max_idx + 1}"})
            for row in data.get("rows", []):
                row[new_id] = ""

        return data, render_table(data)

    # --- edit condition names (inline)
    @app.callback(
        Output("store-images", "data", allow_duplicate=True),
        Input({"type": "cond-input", "row": ALL}, "value"),
        State("store-images", "data"),
        prevent_initial_call=True
    )
    def _edit_condition(values, data):
        data = deepcopy(data)
        for i, v in enumerate(values):
            if i < len(data["rows"]):
                data["rows"][i]["condition"] = v
        return data

    # --- browse button
    @app.callback(
        Output("store-images", "data", allow_duplicate=True),
        Output("table-container", "children", allow_duplicate=True),
        Output("store-browse-clicks", "data"),
        Input({"type": "browse-btn", "row": ALL, "col": ALL}, "n_clicks"),
        State({"type": "browse-btn", "row": ALL, "col": ALL}, "id"),
        State("store-browse-clicks", "data"),
        State("store-images", "data"),
        prevent_initial_call=True
    )
    def _browse(nclicks, btn_ids, prev_counts, data):
        def keystr(row, col):
            return f"{row}::{col}"

        current = {keystr(b["row"], b["col"]): int(n or 0) for b, n in zip(btn_ids, nclicks)}
        prev_counts = prev_counts or {}

        increased = [k for k, c in current.items() if c > prev_counts.get(k, 0)]
        if not increased:
            return no_update, no_update, current

        k = increased[-1]
        row_str, ch_id = k.split("::", 1)
        row = int(row_str)

        chosen = pick_directory_dialog()
        if chosen:
            data = deepcopy(data)
            data["rows"][row][ch_id] = chosen
            return data, render_table(data), current
        return no_update, no_update, current

    # --- save table (validate and summarize)
    @app.callback(
        Output("alert-errors", "children"),
        Output("alert-errors", "is_open"),
        Output("images-modal", "is_open", allow_duplicate=True),
        Output("summary-box", "children"),
        Input("btn-save-table", "n_clicks"),
        State("store-images", "data"),
        prevent_initial_call=True
    )
    def _save_table(_, data):
        channels = data.get("channels", [])
        rows = data.get("rows", [])

        errors = []
        # canais
        ch_names = [(ch.get("name") or "").strip() for ch in channels]
        if any(n == "" for n in ch_names):
            errors.append("There are channels without a name.")
        if len(set(ch_names)) != len(ch_names):
            errors.append("Channel names must be unique.")

        # condições
        conds = [(r.get("condition") or "").strip() for r in rows]
        if any(c == "" for c in conds):
            errors.append("There are conditions without a name.")
        if len(set(conds)) != len(conds):
            errors.append("Condition names must be unique.")

        # paths
        for i, r in enumerate(rows):
            for ch in channels:
                ch_id = ch["id"]
                ch_name = ch["name"]
                p = (r.get(ch_id, "") or "").strip()
                if p == "":
                    errors.append(f"Row {i + 1} — {ch_name}: empty path.")
                elif not Path(p).exists():
                    errors.append(f"Row {i + 1} — {ch_name}: path does not exist.")

        if errors:
            return html.Ul([html.Li(e) for e in errors]), True, no_update, no_update

        # summary
        lines = ["Image selection OK:\n", f"Conditions: {len(rows)} | Channels: {len(channels)}\n"]
        for r in rows:
            lines.append(f"- {r['condition']}:")
            for ch in channels:
                lines.append(f"    {ch['name']}: {r[ch['id']]}")
        summary = "\n".join(lines)

        return "", False, False, summary

    # --- rename channels live
    @app.callback(
        Output("store-images", "data", allow_duplicate=True),
        Input({"type": "chan-name", "col": ALL}, "value"),
        State({"type": "chan-name", "col": ALL}, "id"),
        State("store-images", "data"),
        prevent_initial_call=True
    )
    def _rename_channels(values, ids, data):
        data = deepcopy(data)
        rename_map = {comp_id["col"]: (val or "").strip() for comp_id, val in zip(ids, values)}
        for ch in data["channels"]:
            if ch["id"] in rename_map:
                ch["name"] = rename_map[ch["id"]]
        return data

    @app.callback(
        Output("store-images", "data", allow_duplicate=True),
        Input({"type": "path-input", "row": ALL, "col": ALL}, "value"),
        State({"type": "path-input", "row": ALL, "col": ALL}, "id"),
        State("store-images", "data"),
        prevent_initial_call=True
    )
    def _edit_paths(values_grid, ids_grid, data):
        data = deepcopy(data)
        for pid, val in _flatten_id_value_grid(ids_grid, values_grid):
            # segurança extra contra formatos inesperados
            if not isinstance(pid, dict):
                continue
            r = pid.get("row")
            ch_id = pid.get("col")
            if not isinstance(r, int) or not isinstance(ch_id, str):
                continue
            if r < 0 or r >= len(data.get("rows", [])):
                continue
            data["rows"][r][ch_id] = (val or "").strip()
        return data

    # em create_app(), depois dos outros callbacks (qualquer lugar apropriado)
    @app.callback(
        Output("save-path", "value"),
        Input("btn-browse-save", "n_clicks"),
        State("save-path", "value"),
        prevent_initial_call=True
    )
    def _choose_save_dir(n, current_value):
        chosen = pick_directory_dialog()
        return chosen or current_value or ""

    # --- register segmentation module callbacks (collapse/options/value)
    register_segmentation_callbacks(app)

    # --- update counter in modal footer
    @app.callback(
        Output("counter-box", "children"),
        Input("store-images", "data")
    )
    def _update_counter(data):
        return f"Channels: {len(data.get('channels', []))} | Conditions: {len(data.get('rows', []))}"

    from dash import no_update

    @app.callback(
        Output("seg-poll", "disabled", allow_duplicate=True),
        Output("seg-log", "children", allow_duplicate=True),
        Output("summary-box", "children", allow_duplicate=True),
        Output("btn-stop", "style", allow_duplicate=True),
        Input("btn-preview", "n_clicks"),
        Input("btn-run", "n_clicks"),
        State("store-images", "data"),
        State("store-seg", "data"),
        prevent_initial_call=True,
    )
    def _start_preview_or_run(n_prev, n_run, images_data, seg_data):
        from uuid import uuid4
        import tempfile
        global PROGRESS_FILE

        trig = ctx.triggered_id
        if trig not in ("btn-preview", "btn-run"):
            # ⚠️ este callback tem 4 outputs
            return no_update, no_update, no_update, no_update

        preview = (trig == "btn-preview")

        # 1) Monta parâmetros
        params, errs = build_interface_params(images_data, seg_data)
        if errs:
            hide_stop = {"marginLeft": "8px", "color": "#b00020", "display": "none"}
            return True, "", "Errors:\n- " + "\n- ".join(sorted(set(errs))), hide_stop

        # 2) Define arquivo único desta execução e zera o progresso
        PROGRESS_FILE = os.path.join(tempfile.gettempdir(), f"_fornma_progress_{uuid4().hex}.json")
        try:
            with open(PROGRESS_FILE, "w") as f:
                json.dump({
                    "status": "starting",
                    "total": 0,
                    "done": 0,
                    "percent": 0,
                    "cancel": False,
                    "started_at": datetime.now().isoformat(timespec="seconds")
                }, f)
        except Exception:
            pass

        # 3) Thread do trabalho pesado
        def _worker():
            global PROGRESS_FILE
            try:
                os.environ["FORNMA_PROGRESS_FILE"] = PROGRESS_FILE
                run_pipeline(params, preview=preview)

                # não sobrescreve erro/cancel
                try:
                    with open(PROGRESS_FILE, "r") as f:
                        d = json.load(f)
                except Exception:
                    d = {}
                if d.get("status") not in ("error", "canceled"):
                    d.update({"status": "done", "percent": 100})
                    with open(PROGRESS_FILE, "w") as f:
                        json.dump(d, f)
            except Exception as e:
                with open(PROGRESS_FILE, "w") as f:
                    json.dump({"status": "error", "message": str(e)}, f)
            finally:
                # dá tempo do polling ler o último estado e remove o arquivo
                try:
                    time.sleep(1.0)
                    if PROGRESS_FILE and os.path.exists(PROGRESS_FILE):
                        os.remove(PROGRESS_FILE)
                except Exception:
                    pass
                PROGRESS_FILE = None  # solta o caminho para a próxima execução

        threading.Thread(target=_worker, daemon=True).start()

        # 4) Liga polling + header + mostra Stop
        chans = [k.replace("Channel ", "") for k in params.keys() if k.startswith("Channel ")]
        action = "PREVIEW" if preview else "RUN"
        header = "\n".join([
            f"{action} started…",
            f"Channels: {', '.join(chans) if chans else '—'}",
            f"Nuclei channel: {params['global'].get('channel_with_nuclei') or '—'}",
            f"Output: {params['global'].get('output_folder', 'results')}",
        ])
        show_stop = {"marginLeft": "8px", "color": "#b00020", "display": "inline-block"}
        return False, "", header, show_stop

    # --- SYNC: escreve todas as opções de segmentação no store-seg
    @app.callback(
        Output("store-seg", "data"),
        # GENERAL
        Input({"type": "seg-field", "group": "general", "name": "magnification"}, "value"),
        Input({"type": "seg-field", "group": "general", "name": "pixel-size"}, "value"),
        Input({"type": "seg-field", "group": "general", "name": "channel_with_nuclei", "field": "channels"}, "value"),
        Input({"type": "seg-flag", "group": "general", "name": "overtime"}, "value"),
        # SEGMENTATION (globais)
        Input({"type": "seg-flag", "group": "segmentation", "name": "rescale-intensity"}, "value"),
        Input({"type": "seg-flag", "group": "segmentation", "name": "remove-bg"}, "value"),
        Input({"type": "seg-field", "group": "segmentation", "name": "rolling-radius"}, "value"),
        Input({"type": "seg-field", "group": "segmentation", "name": "seg_method"}, "value"),
        # FORNMA
        Input({"type": "seg-field", "group": "fornma", "name": "threshold"}, "value"),
        Input({"type": "seg-field", "group": "fornma", "name": "offset"}, "value"),
        Input({"type": "seg-field", "group": "fornma", "name": "smooth"}, "value"),
        Input({"type": "seg-field", "group": "fornma", "name": "adjust_size"}, "value"),
        Input({"type": "seg-field", "group": "fornma", "name": "cut_edges"}, "value"),
        Input({"type": "seg-flag", "group": "fornma", "name": "find_low_intensity_nucleus"}, "value"),
        Input({"type": "seg-flag", "group": "fornma", "name": "weakly_labeled"}, "value"),
        # CELLPOSE
        Input({"type": "seg-field", "group": "cellpose", "name": "diameter"}, "value"),
        Input({"type": "seg-field", "group": "cellpose", "name": "flow_threshold"}, "value"),
        Input({"type": "seg-field", "group": "cellpose", "name": "mask_threshold"}, "value"),
        Input({"type": "seg-field", "group": "cellpose", "name": "cellprob_threshold"}, "value"),
        Input({"type": "seg-flag", "group": "cellpose", "name": "use_gpu"}, "value"),
        Input({"type": "seg-flag", "group": "cellpose", "name": "invert"}, "value"),
        # FILTERS
        Input({"type": "seg-field", "group": "filters", "name": "shape"}, "value"),
        Input({"type": "seg-field", "group": "filters", "name": "eccentricity"}, "value"),
        Input({"type": "seg-field", "group": "filters", "name": "minimum_size"}, "value"),
        Input({"type": "seg-field", "group": "filters", "name": "maximum_size"}, "value"),
        Input({"type": "seg-field", "group": "filters", "name": "minimum_radius"}, "value"),
        Input({"type": "seg-field", "group": "filters", "name": "maximum_radius"}, "value"),
        # SAVE PATH (campo de texto/botão de browse)
        Input("save-path", "value"),
        # +++ ADICIONE ISSO AO DECORATOR +++
        Input({"type": "ch-field", "ch": ALL, "name": ALL}, "value"),
        State({"type": "ch-field", "ch": ALL, "name": ALL}, "id"),
        Input({"type": "ch-flag", "ch": ALL, "name": ALL}, "value"),
        State({"type": "ch-flag", "ch": ALL, "name": ALL}, "id"),

        prevent_initial_call=False,
    )
    def _sync_seg_store(
            magnification, pixel_size, ch_with_nuclei, overtime,
            rescale_intensity, remove_bg, rolling_radius, seg_method,
            f_th, f_off, f_blur, f_adj, f_cut, f_findlow, f_weak,
            c_diam, c_flow, c_mask, c_cellprob, c_gpu, c_invert,
            fl_shape, fl_ecc, fl_min_sz, fl_max_sz, fl_min_r, fl_max_r,
            save_path, perch_field_vals, perch_field_ids, perch_flag_vals, perch_flag_ids
    ):
        seg_data = {
            "general": {
                "path_to_save": save_path or "results",
                # Atenção: aqui guardamos o *ID* do canal (ex.: "ch1"); o builder converte para NOME depois
                # (ele mapeia id->nome usando a lista de canais da tabela) :contentReference[oaicite:3]{index=3}
                "channel_with_nuclei": ch_with_nuclei,
                "overtime": bool(overtime),
            },
            "segmentation": {
                "magnification": magnification,
                "pixel-size": pixel_size,
                "rescale-intensity": bool(rescale_intensity),
                "remove-bg": bool(remove_bg),
                "rolling-radius": rolling_radius,
                "seg_method": seg_method,
                # usado para setar cellpose.use_cellpose :contentReference[oaicite:4]{index=4}
            },
            "fornma": {
                "threshold": f_th,
                "offset": f_off,
                "smooth": f_blur,
                "adjust_size": f_adj,
                "cut_edges": f_cut,
                "find_low_intensity_nucleus": bool(f_findlow),
                "weakly_labeled": bool(f_weak),
            },
            "cellpose": {
                "diameter": c_diam,
                "flow_threshold": c_flow,
                "mask_threshold": c_mask,
                "cellprob_threshold": c_cellprob,
                "use_gpu": bool(c_gpu),
                "invert": bool(c_invert),
            },
            "filters": {
                "shape": fl_shape,
                "eccentricity": fl_ecc,
                "minimum_size": fl_min_sz,
                "maximum_size": fl_max_sz,
                "minimum_radius": fl_min_r,
                "maximum_radius": fl_max_r,
            },
        }
        # --- mapear valores POR CANAL vindos dos componentes dinâmicos
        channels_map = {}

        def _put(ch, name, val):
            if ch is None or name is None:
                return
            channels_map.setdefault(ch, {})[name] = val

        # Campos numéricos/inputs (rolling_ball_radius, ring_size, foci_* etc.)
        for comp_id, val in zip(perch_field_ids or [], perch_field_vals or []):
            if isinstance(comp_id, dict):
                _put(comp_id.get("ch"), comp_id.get("name"), val)

        # Toggles/switches (remove_background, rescale_intensity, match_histograms, use_ellipse, etc.)
        for comp_id, val in zip(perch_flag_ids or [], perch_flag_vals or []):
            if isinstance(comp_id, dict):
                _put(comp_id.get("ch"), comp_id.get("name"), bool(val))

        # Salva no store-seg (sem perder o que já existe)
        seg_data = dict(seg_data or {})
        seg_data["channels"] = channels_map

        return seg_data

    # --- POLLING: lê o arquivo de progresso e atualiza a UI
    from dash import no_update
    import os, json, base64

    @app.callback(
        Output("seg-live-img", "src", allow_duplicate=True),  # <-- add allow_duplicate
        Output("seg-progress", "value"),
        Output("seg-progress-text", "children"),
        Output("seg-log", "children"),
        Output("seg-poll", "disabled"),
        Output("btn-stop", "style", allow_duplicate=True),
        Input("seg-poll", "n_intervals"),
        prevent_initial_call=True
    )

    def _poll_progress(_n):
        img_src = no_update
        hide_stop = {"display": "none"}
        show_stop = {"display": "inline-block"}

        # Se o arquivo ainda não existe, esconda stop e desabilite polling
        if not PROGRESS_FILE or not os.path.exists(PROGRESS_FILE):
            return img_src, no_update, no_update, no_update, True, hide_stop

        # Carrega o JSON de progresso
        try:
            with open(PROGRESS_FILE, "r") as f:
                d = json.load(f)
        except Exception:
            # Não conseguiu ler -> trate como “sem progresso”
            return img_src, no_update, no_update, no_update, True, hide_stop

        # Se chegou aqui, 'd' existe
        preview_path = d.get("preview_path")
        if preview_path and os.path.exists(preview_path):
            try:
                with open(preview_path, "rb") as pf:
                    b64 = base64.b64encode(pf.read()).decode("ascii")
                img_src = f"data:image/png;base64,{b64}"
            except Exception:
                pass  # não quebra a UI se a imagem falhar

        status = d.get("status", "running")
        percent = int(d.get("percent", 0))
        log = d.get("log", "") or ""
        text = f"{percent}%"

        if status == "error":
            return img_src, percent, "Error", (log or "Unknown error."), True, hide_stop
        if status == "canceled":
            return img_src, percent, "Canceled", (log or "Canceled by user."), True, hide_stop
        if status == "done":
            return img_src, 100, "100% (done)", (log or "Finished."), True, hide_stop

        # running / starting
        return img_src, percent, text, log, False, show_stop

    @app.callback(
        Output("seg-log", "children", allow_duplicate=True),
        Output("seg-poll", "disabled", allow_duplicate=True),
        Output("btn-stop", "style", allow_duplicate=True),
        Input("btn-stop", "n_clicks"),
        prevent_initial_call=True
    )
    def _on_stop(n):
        hide_stop = {"marginLeft": "8px", "color": "#b00020", "display": "none"}
        if not n:
            return no_update, no_update, hide_stop

        try:
            d = {}
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, "r") as f:
                    try:
                        d = json.load(f)
                    except Exception:
                        d = {}
            # marca cancel
            d.update({"cancel": True, "status": d.get("status", "running")})
            with open(PROGRESS_FILE, "w") as f:
                json.dump(d, f)

            return "Stopping… requested. Waiting current image to finish.", False, hide_stop
        except Exception as e:
            return f"Stop failed: {e}", False, hide_stop

    from dash import no_update

    @app.callback(
        Output("seg-run-ui", "style"),
        Output("seg-footer", "style"),
        Output("seg-live-img", "src", allow_duplicate=True),
        Input("seg-poll", "disabled"),
        prevent_initial_call=True,  # <-- obrigatório com allow_duplicate
    )
    def _toggle_seg_run_ui(disabled):
        base = {"display": "block", "width": "100%", "maxWidth": "100%", "overflow": "hidden"}

        if disabled:
            # Não está rodando: esconde rodapé e força o logo no src
            footer_hide = {"display": "none"}
            return base, footer_hide, DEFAULT_LOGO
        else:
            # Rodando: mostra rodapé; não mexe no src (polling vai atualizar)
            footer_show = {
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "gap": "6px",
            }
            return base, footer_show, no_update

    return app


def main():
    app = create_app()
    url = "http://127.0.0.1:8050/"
    try:
        webbrowser.open(url)
    except Exception:
        pass
    app.run(debug=True, host="127.0.0.1", port=8050)