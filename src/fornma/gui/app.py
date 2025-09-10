# src/fornma/gui/app.py
import os
import webbrowser
from copy import deepcopy
from pathlib import Path
from typing import Dict

from dash import Dash, html, dcc, Input, Output, State, ALL, no_update, ctx
import dash_bootstrap_components as dbc

from .layouts.segmentation import build_sidebar as build_segmentation_sidebar
from .callbacks.segmentation import register as register_segmentation_callbacks


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
        "background": "#eef2ff", "height": "100vh", "overflowY": "auto"
    })

    # stores
    store = dcc.Store(id="store-images", data=initial_table_state())
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
        store_clicks,

        html.Div([
            sidebars,  # left column (all sidebars)
            html.Div([tabs, html.Div(id="tab-content", style={"padding": "10px"})],
                     style={"width": "75%", "padding": "10px", "height": "100vh", "overflow": "hidden"}),
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
            return html.Div([html.H4("Segmentation module"), html.P("Coming soon...")])
        elif tab == "tab-stats":
            return html.Div([html.H4("Statistics module"), html.P("Coming soon...")])
        return html.Div()

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

    # --- register segmentation module callbacks (collapse/options/value)
    register_segmentation_callbacks(app)

    # --- update counter in modal footer
    @app.callback(
        Output("counter-box", "children"),
        Input("store-images", "data")
    )
    def _update_counter(data):
        return f"Channels: {len(data.get('channels', []))} | Conditions: {len(data.get('rows', []))}"

    return app


def main():
    app = create_app()
    url = "http://127.0.0.1:8050/"
    try:
        webbrowser.open(url)
    except Exception:
        pass
    app.run(debug=True, host="127.0.0.1", port=8050)
