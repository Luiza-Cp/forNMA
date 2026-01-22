# src/fornma/gui/callbacks/nma.py
# src/fornma/gui/callbacks/nma.py
import os, json, time, threading, traceback, base64, io


# progress file helpers (GUI)
try:
    from fornma.gui.utils.progress import update_progress, cancel_requested
except Exception:
    from progress import update_progress, cancel_requested

# IMPORTAÇÃO CORRETA DO NMA (sem NEVER usar o pacote raiz fornma.NMA)
# pegamos diretamente a função plot_NMA, a classe NMA e CONFIG_PATH
from fornma.NMA.plot_NMA import (
    plot_NMA as run_nma_cli,
    NMA as NMAClass,
    CONFIG_PATH as NMA_CONFIG_PATH,
)

# reconstrução do control_parameters.pickle
try:
    from .nma_step2 import build_pkl_payload
except Exception:
    build_pkl_payload = None


from dash import Input, Output, State, ALL, html, dcc, no_update, ctx
import dash_bootstrap_components as dbc
from copy import deepcopy
from pathlib import Path
import pandas as pd


NMA_PROGRESS_FILE = None

# ---------- helpers ----------
def _read_columns(csv_path: str) -> list[str]:
    try:
        df = pd.read_csv(csv_path, nrows=0)
        return [str(c) for c in df.columns.tolist()]
    except Exception:
        return []


def _auto_pick(cols: list[str], targets: list[str]) -> str | None:
    """primeiro match exato (casefold), depois 'contains' (casefold)"""
    if not cols:
        return None
    lower = {c.casefold(): c for c in cols}
    for t in targets:
        if t.casefold() in lower:
            return lower[t.casefold()]
    for c in cols:
        ccf = c.casefold()
        if any(t.casefold() in ccf for t in targets):
            return c
    return None


def _empty_row(idx: int) -> dict:
    return {
        "idx": idx,
        "name": f"Dataset {idx+1}",
        "path": "",
        "columns": [],
        "area_col": None,
        "nii_col": None,
        "is_control": False,  # checkbox "Control"
    }


def _render_row(d: dict) -> dbc.Card:
    i = int(d.get("idx", 0))
    cols = d.get("columns", []) or []
    area_val = d.get("area_col")
    nii_val = d.get("nii_col")
    is_ctrl = bool(d.get("is_control", False))

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Input(
                                id={"type": "nma-name", "idx": i},
                                value=d.get("name", ""),
                                placeholder="Dataset name",
                                style={"width": "100%"},
                                persistence=True,
                                persisted_props=["value"],
                                persistence_type="session",
                            ),
                            md=7,
                        ),
                        dbc.Col(
                            dbc.Checkbox(
                                id={"type": "nma-control", "idx": i},
                                value=is_ctrl,
                                label="Control",
                                className="ms-2",
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            html.Button(
                                "Remove",
                                id={"type": "nma-remove", "idx": i},
                                n_clicks=0,
                                title="Remove this dataset",
                                style={"float": "right"},
                            ),
                            md=2,
                        ),
                    ],
                    className="g-2 align-items-center",
                )
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(dbc.Label("CSV path", id={"type": "nma-label-path", "idx": i}), md=2),
                            dbc.Col(
                                dcc.Input(
                                    id={"type": "nma-path", "idx": i},
                                    value=d.get("path", ""),
                                    placeholder="Select the CSV file…",
                                    style={"width": "100%"},
                                    persistence=True,
                                    persisted_props=["value"],
                                    persistence_type="session",
                                ),
                                md=8,
                            ),
                            dbc.Col(
                                html.Button(
                                    "Browse",
                                    id={"type": "nma-browse", "idx": i},
                                    n_clicks=0,
                                ),
                                md=2,
                            ),
                        ],
                        className="mb-2 g-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(dbc.Label("Area column", id={"type": "nma-label-area", "idx": i}), md=4),
                            dbc.Col(
                                dcc.Dropdown(
                                    id={"type": "nma-area", "idx": i},
                                    options=[{"label": c, "value": c} for c in cols],
                                    value=area_val if area_val in cols else None,
                                    placeholder="Select area column…",
                                    clearable=True,
                                ),
                                md=4,
                            ),
                        ],
                        className="mb-1 g-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(dbc.Label("NII column", id={"type": "nma-label-nii", "idx": i}), md=4),
                            dbc.Col(
                                dcc.Dropdown(
                                    id={"type": "nma-nii", "idx": i},
                                    options=[{"label": c, "value": c} for c in cols],
                                    value=nii_val if nii_val in cols else None,
                                    placeholder="Select NII column…",
                                    clearable=True,
                                ),
                                md=4,
                            ),
                        ],
                        className="mb-1 g-2",
                    ),
                ]
            ),
        ],
        className="mb-0",
        style={"borderRadius": "10px"},
    )


def _render_all(data: dict) -> list:
    """
    Renderiza UM Accordion com todos os datasets como itens colapsáveis.
    """
    rows = data.get("rows", []) or []
    if not rows:
        return []

    items = []
    for r in rows:
        i = int(r.get("idx", 0))
        title = r.get("name") or f"Dataset {i+1}"
        if r.get("is_control"):
            title = f"{title}  •  (Control)"
        items.append(
            dbc.AccordionItem(
                _render_row(r),
                title=title,
                item_id=f"ds-{i}",
            )
        )

    return [
        dbc.Accordion(
            items,
            id="nma-accordion",
            start_collapsed=True,
            always_open=False,
            flush=True,
        )
    ]


def _ensure_structure(d: dict) -> dict:
    d = dict(d or {})
    rows = d.get("rows")
    if not isinstance(rows, list):
        d["rows"] = []
    return d


# ---------- register ----------
def register(app, pick_file_dialog):
    """
    Registra os callbacks da aba NMA.
    Stores usados:
      - store-nma     (dados da sidebar e params finais)
      - store-nma-ui  (estado de UI: item aberto do Accordion)
    """

    # 1) renderização: sempre que store-nma mudar (mantém item aberto via store-nma-ui)
    @app.callback(
        Output("nma-datasets-container", "children"),
        Input("store-nma", "data"),
        State("store-nma-ui", "data"),
        prevent_initial_call=False,
    )
    def _render(d, ui):
        d = _ensure_structure(d)
        rows = d.get("rows", []) or []
        if not rows:
            return []

        # monta os itens
        items = []
        for r in rows:
            i = int(r.get("idx", 0))
            title = r.get("name") or f"Dataset {i + 1}"
            if r.get("is_control"):
                title = f"{title}  •  (Control)"
            items.append(
                dbc.AccordionItem(
                    _render_row(r),
                    title=title,
                    item_id=f"ds-{i}",
                )
            )

        # pega qual item estava aberto
        active = (ui or {}).get("active_item")

        return [
            dbc.Accordion(
                items,
                id="nma-accordion",
                start_collapsed=False if active else True,
                active_item=active,  # mantém quem fica aberto
                always_open=False,
                flush=True,
            )
        ]

    # 2) adicionar linha
    @app.callback(
        Output("store-nma", "data", allow_duplicate=True),
        Input("nma-add-row", "n_clicks"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _add_row(n, data):
        data = _ensure_structure(deepcopy(data))
        next_idx = len(data["rows"])
        data["rows"].append(_empty_row(next_idx))
        return data

    # 3) remover linha
    @app.callback(
        Output("store-nma", "data", allow_duplicate=True),
        Input({"type": "nma-remove", "idx": ALL}, "n_clicks"),
        State({"type": "nma-remove", "idx": ALL}, "id"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _remove_row(nclicks, ids, data):
        data = _ensure_structure(deepcopy(data))
        if not nclicks or not ids:
            return no_update
        # pega o último botão clicado
        latest = None
        for btn_id, n in zip(ids, nclicks):
            if int(n or 0) > 0:
                latest = btn_id
        if latest is None:
            return no_update
        rm_idx = int(latest["idx"])
        data["rows"] = [r for r in data["rows"] if int(r.get("idx", -1)) != rm_idx]
        # reindexa para manter idx sequencial
        for i, r in enumerate(data["rows"]):
            r["idx"] = i
        return data

    # 4) editar nome
    @app.callback(
        Output("store-nma", "data", allow_duplicate=True),
        Input({"type": "nma-name", "idx": ALL}, "value"),
        State({"type": "nma-name", "idx": ALL}, "id"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _edit_name(values, ids, data):
        data = _ensure_structure(deepcopy(data))
        for comp_id, val in zip(ids or [], values or []):
            i = int(comp_id["idx"])
            if i < len(data["rows"]):
                data["rows"][i]["name"] = (val or "").strip()
        return data

    # 5) editar path manual
    @app.callback(
        Output("store-nma", "data", allow_duplicate=True),
        Input({"type": "nma-path", "idx": ALL}, "value"),
        State({"type": "nma-path", "idx": ALL}, "id"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _edit_path(values, ids, data):
        data = _ensure_structure(deepcopy(data))
        for comp_id, val in zip(ids or [], values or []):
            i = int(comp_id["idx"])
            if i < len(data["rows"]):
                data["rows"][i]["path"] = (val or "").strip()
        return data

    # 6) browse (selecionar CSV) + autodetect
    @app.callback(
        Output("store-nma", "data", allow_duplicate=True),
        Input({"type": "nma-browse", "idx": ALL}, "n_clicks"),
        State({"type": "nma-browse", "idx": ALL}, "id"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _browse(nclicks, ids, data):
        data = _ensure_structure(deepcopy(data))
        if not nclicks or not ids:
            return no_update

        # encontra o último botão clicado
        changed = [btn for btn, n in zip(ids, nclicks) if int(n or 0) > 0]
        if not changed:
            return no_update
        comp_id = changed[-1]
        i = int(comp_id["idx"])

        chosen = pick_file_dialog()
        if not chosen:
            return no_update

        data["rows"][i]["path"] = chosen

        # ler colunas e autodetectar
        cols = _read_columns(chosen)
        data["rows"][i]["columns"] = cols

        # heurísticas de nomes
        area_guess = _auto_pick(cols, ["area", "nuclear_area", "nuc_area"])
        nii_guess = _auto_pick(
            cols,
            ["nii", "nuclear_irregularity", "irregularity", "regularity_index", "nuclear_regularit", "nuclear_index"],
        )
        data["rows"][i]["area_col"] = area_guess
        data["rows"][i]["nii_col"] = nii_guess

        return data

    # 7) seletores de coluna (override manual)
    @app.callback(
        Output("store-nma", "data", allow_duplicate=True),
        Input({"type": "nma-area", "idx": ALL}, "value"),
        Input({"type": "nma-nii", "idx": ALL}, "value"),
        State({"type": "nma-area", "idx": ALL}, "id"),
        State({"type": "nma-nii", "idx": ALL}, "id"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _select_cols(area_vals, nii_vals, area_ids, nii_ids, data):
        data = _ensure_structure(deepcopy(data))
        # area
        for comp_id, val in zip(area_ids or [], area_vals or []):
            i = int(comp_id["idx"])
            if i < len(data["rows"]):
                data["rows"][i]["area_col"] = val or None
        # nii
        for comp_id, val in zip(nii_ids or [], nii_vals or []):
            i = int(comp_id["idx"])
            if i < len(data["rows"]):
                data["rows"][i]["nii_col"] = val or None
        return data

    # 8) build settings (validação + JSON bonito) — múltiplos controles permitidos
    @app.callback(
        Output("nma-params", "children"),
        Output("nma-alert", "children"),
        Output("nma-alert", "is_open"),
        Output("store-nma", "data", allow_duplicate=True),
        Input("btn-nma-build", "n_clicks"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _build_settings(_n, data):
        from pathlib import Path
        import json

        data = _ensure_structure(deepcopy(data))
        rows = data.get("rows", [])

        errors = []
        payload = {"datasets": [], "controls": []}  # lista de nomes marcados como controle

        if not rows:
            errors.append("Add at least one dataset (+ Add dataset).")

        for r in rows:
            name = (r.get("name") or "").strip()
            path = (r.get("path") or "").strip()
            area = r.get("area_col")
            nii = r.get("nii_col")
            is_c = bool(r.get("is_control", False))

            if not name:
                errors.append("Dataset without a name.")
            if not path:
                errors.append(f"{name or 'Dataset'}: CSV path is empty.")
            elif not Path(path).exists():
                errors.append(f"{name or 'Dataset'}: CSV path does not exist.")
            if not area:
                errors.append(f"{name or 'Dataset'}: select the Area column.")
            if not nii:
                errors.append(f"{name or 'Dataset'}: select the NII column.")

            if is_c:
                payload["controls"].append(name or f"Dataset {int(r.get('idx', 0)) + 1}")

            payload["datasets"].append(
                {"name": name, "path": path, "area_col": area, "nii_col": nii, "is_control": is_c}
            )

        if errors:
            return "", html.Ul([html.Li(e) for e in errors]), True, data

        data["params"] = payload
        pretty = json.dumps(payload, indent=2, ensure_ascii=False)
        return pretty, "", False, data


    # 9) salvar valor do checkbox "Control" (sem exclusividade)
    @app.callback(
        Output("store-nma", "data", allow_duplicate=True),
        Input({"type": "nma-control", "idx": ALL}, "value"),
        State({"type": "nma-control", "idx": ALL}, "id"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _save_control(values, ids, data):
        data = _ensure_structure(deepcopy(data))
        if not ids:
            return data
        for comp_id, val in zip(ids, values):
            i = int(comp_id["idx"])
            if i < len(data["rows"]):
                data["rows"][i]["is_control"] = bool(val)
        return data

    # 10) persistir item aberto do Accordion
    @app.callback(
        Output("store-nma-ui", "data", allow_duplicate=True),
        Input("nma-accordion", "active_item"),
        State("store-nma-ui", "data"),
        prevent_initial_call=True,
    )
    def _persist_open_item(active_item, ui):
        ui = dict(ui or {})
        ui["active_item"] = active_item
        return ui

    # 11) painel de ANÁLISE NMA (dot / heatmap) — só aparece após settings prontas
    @app.callback(
        Output("nma-plot-config-container", "children"),
        Input("store-nma-settings", "data"),  # já existe no step2
        State("store-nma", "data"),
        prevent_initial_call=False,
    )
    def _render_nma_plot_panel(settings, store_nma):
        # precisa ter settings criadas/carregadas
        if not settings:
            return []

        data = store_nma or {}
        rows = data.get("rows", []) or []

        # precisa ter datasets carregados
        if not rows:
            return []

        # pelo menos um dataset com path válido
        if not any(r.get("path") for r in rows):
            return []

        # junta todas as colunas detectadas
        all_cols = set()
        for r in rows:
            for c in r.get("columns") or []:
                all_cols.add(str(c))
        col_options = [{"label": c, "value": c} for c in sorted(all_cols)] if all_cols else []

        palette_options = [
            {"label": "viridis", "value": "viridis"},
            {"label": "plasma", "value": "plasma"},
            {"label": "magma", "value": "magma"},
            {"label": "inferno", "value": "inferno"},
            {"label": "cividis", "value": "cividis"},
            {"label": "coolwarm", "value": "coolwarm"},
            {"label": "Spectral", "value": "Spectral"},
            {"label": "RdBu", "value": "RdBu"},
        ]

        return [
            html.H5("NMA analysis", className="mt-2"),
            html.Small("Choose how you want to plot NMA (dot plot or heatmap)."),

            # Tooltip para tipo de plot
            html.Div(
                [
                    dbc.RadioItems(
                        id="nma-plot-kind",
                        options=[
                            {"label": "Dot plot", "value": "dot"},
                            {"label": "Heatmap", "value": "heatmap"},
                        ],
                        value="dot",
                        inline=True,
                        className="mt-2",
                    ),
                    dbc.Tooltip(
                        "Dot plot: Individual nuclei as points. Heatmap: Density visualization for large datasets.",
                        target="nma-plot-kind",
                        placement="top",
                    ),
                ],
            ),

            # --- DOT PLOT ---
            html.Div(id="nma-plot-options-dot", className="mt-3", children=[
                html.B("Dot plot options", className="d-block mb-1"),

                # colunas vindas dos datasets
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Color by (column1)"),
                        dbc.Tooltip(
                            "Select column for color encoding. Nuclei will be colored based on values in this column.",
                            target="nma-dot-column1-wrapper",
                            placement="top",
                        ),
                    ], width=6, id="nma-dot-column1-wrapper"),
                    dbc.Col([
                        dbc.Label("Size by (column2)"),
                        dbc.Tooltip(
                            "Select column for size encoding. Nuclei size will scale with values in this column.",
                            target="nma-dot-column2-wrapper",
                            placement="top",
                        ),
                    ], width=6, id="nma-dot-column2-wrapper"),
                ], className="mb-1"),
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(
                            id="nma-dot-column1",
                            options=col_options,
                            placeholder="Column for colors",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="nma-dot-column2",
                            options=col_options,
                            placeholder="Column for sizes",
                        ),
                        width=6,
                    ),
                ], className="mb-2"),

                # Hue / Size norm
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Hue norm (min / max)"),
                        dbc.Tooltip(
                            "Manually set color scale limits. Leave empty for automatic scaling based on data range.",
                            target="nma-dot-hue-norm-wrapper",
                            placement="top",
                        ),
                        html.Div(id="nma-dot-hue-norm-wrapper"),
                        dbc.InputGroup([
                            dbc.Input(id="nma-dot-hue-min", type="number", placeholder="min"),
                            dbc.Input(id="nma-dot-hue-max", type="number", placeholder="max"),
                        ]),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Size norm (min / max)"),
                        dbc.Tooltip(
                            "Manually set size scaling limits. Leave empty for automatic scaling.",
                            target="nma-dot-size-norm-wrapper",
                            placement="top",
                        ),
                        html.Div(id="nma-dot-size-norm-wrapper"),
                        dbc.InputGroup([
                            dbc.Input(id="nma-dot-size-min", type="number", placeholder="min"),
                            dbc.Input(id="nma-dot-size-max", type="number", placeholder="max"),
                        ]),
                    ], width=6),
                ], className="mb-2"),

                # Sample size (depois dos norms)
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Sample size"),
                        dbc.Tooltip(
                            "Random subsample for faster plotting. Leave empty to use all nuclei.",
                            target="nma-dot-sample-size-wrapper",
                            placement="top",
                        ),
                        html.Div(id="nma-dot-sample-size-wrapper"),
                        dbc.Input(
                            id="nma-dot-sample-size",
                            type="number",
                            min=1,
                            placeholder="Random subsample size (optional)",
                        ),
                    ], width=6),
                ], className="mb-2"),

                # Palette (depois dos norms, com selector)
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Palette"),
                        dbc.Tooltip(
                            "Color palette for visualization. Different palettes highlight different data patterns.",
                            target="nma-dot-palette-wrapper",
                            placement="top",
                        ),
                        html.Div(id="nma-dot-palette-wrapper"),
                        dcc.Dropdown(
                            id="nma-dot-palette",
                            options=palette_options,
                            placeholder="Choose a palette (optional)",
                            clearable=True,
                        ),
                    ], width=6),
                ], className="mb-2"),

                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="nma-dot-flags",
                            options=[
                                {"label": "Single plot (grouped data)", "value": "single"},
                                {"label": "Overtime (time sequence)", "value": "overtime"},
                            ],
                            value=[],
                            inline=False,
                        ),
                        dbc.Tooltip(
                            "Single plot: Combine all datasets in one plot. Overtime: Visualize temporal changes if time data exists.",
                            target="nma-dot-flags",
                            placement="top",
                        ),
                    ], width=12),
                ]),
            ]),

            # --- HEATMAP ---
            html.Div(id="nma-plot-options-heatmap", className="mt-3", children=[
                html.B("Heatmap options", className="d-block mb-1"),
                dbc.Checklist(
                    id="nma-heatmap-flags",
                    options=[
                        {"label": "Single plot (grouped data)", "value": "single"},
                        {"label": "Overtime (time sequence)", "value": "overtime"},
                        {"label": "Jointplot (with histograms)", "value": "jointplot"},
                    ],
                    value=[],
                    inline=False,
                ),
                dbc.Tooltip(
                    "Single plot: Combined view. Overtime: Time series visualization. Jointplot: Include marginal histograms.",
                    target="nma-heatmap-flags",
                    placement="top",
                ),
            ]),

            # ALERTA de coluna ausente em alguns datasets
            dbc.Alert(
                id="nma-plot-warning",
                color="warning",
                is_open=False,
                className="mt-2",
            ),

            # --- Saving path + RUN ---
            html.Hr(className="mt-3"),

            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Saving path"),
                            dbc.Tooltip(
                                "Directory where NMA results and plots will be saved.",
                                target="nma-run-save-path-wrapper",
                                placement="top",
                            ),
                            html.Div(id="nma-run-save-path-wrapper"),
                            dbc.Input(
                                id="nma-run-save-path",
                                type="text",
                                placeholder="Folder to save NMA results",
                                style={"width": "100%"},
                            ),
                        ],
                        width=9,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Browse",
                                id="nma-run-browse",
                                size="sm",
                                className="mt-4",
                                title="Choose folder to save NMA output",
                            ),
                            dbc.Tooltip(
                                "Select output directory for NMA analysis results",
                                target="nma-run-browse",
                                placement="top",
                            ),
                        ],
                        width=3,
                    ),
                ],
                className="mt-2 mb-2",
            ),

            html.Div(
                [
                    html.Button(
                        "Run NMA",
                        id="btn-nma-run",
                        className="btn btn-primary",
                        title="Run NMA analysis with the selected options",
                    ),
                    dbc.Tooltip(
                        "Start NMA analysis with current settings. This may take several minutes depending on dataset size.",
                        target="btn-nma-run",
                        placement="top",
                    ),
                    html.Small(
                        id="nma-run-summary",
                        className="text-muted d-block mt-1",
                    ),
                ],
                className="mb-2",
            ),
        ]


    # 12) mostrar apenas o bloco correspondente ao tipo de plot
    @app.callback(
        Output("nma-plot-options-dot", "style"),
        Output("nma-plot-options-heatmap", "style"),
        Input("nma-plot-kind", "value"),
        prevent_initial_call=False,
    )
    def _toggle_dot_vs_heatmap(kind):
        if kind == "heatmap":
            return ({"display": "none"}, {"display": "block"})
        # default = dot
        return ({"display": "block"}, {"display": "none"})

    # 13) consolidar opções de plot e salvar em store-nma-plot
    @app.callback(
        Output("store-nma-plot", "data"),
        Input("nma-plot-kind", "value"),
        Input("nma-dot-column1", "value"),
        Input("nma-dot-column2", "value"),
        Input("nma-dot-hue-min", "value"),
        Input("nma-dot-hue-max", "value"),
        Input("nma-dot-size-min", "value"),
        Input("nma-dot-size-max", "value"),
        Input("nma-dot-sample-size", "value"),
        Input("nma-dot-palette", "value"),
        Input("nma-dot-flags", "value"),
        Input("nma-heatmap-flags", "value"),
        prevent_initial_call=False,
    )
    def _update_nma_plot_store(
            kind,
            c1, c2,
            hue_min, hue_max,
            size_min, size_max,
            sample_size,
            palette,
            dot_flags,
            heat_flags,
    ):
        dot_flags = dot_flags or []
        heat_flags = heat_flags or []

        dot_cfg = {
            "column1": c1,
            "column2": c2,
            "sample_size": int(sample_size) if sample_size is not None else None,
            "palette": palette or None,
            "hue_norm": (
                [float(hue_min), float(hue_max)]
                if hue_min is not None and hue_max is not None
                else None
            ),
            "size_norm": (
                [float(size_min), float(size_max)]
                if size_min is not None and size_max is not None
                else None
            ),
            "single": "single" in dot_flags,
            "overtime": "overtime" in dot_flags,
        }

        heat_cfg = {
            "single": "single" in heat_flags,
            "overtime": "overtime" in heat_flags,
            "jointplot": "jointplot" in heat_flags,
        }

        return {
            "kind": kind or "dot",
            "dot": dot_cfg,
            "heatmap": heat_cfg,
        }

    @app.callback(
        Output("nma-plot-warning", "children"),
        Output("nma-plot-warning", "is_open"),
        Input("nma-dot-column1", "value"),
        State("store-nma", "data"),
        prevent_initial_call=False,
    )
    def _warn_missing_color_column(col, data):
        from copy import deepcopy

        if not col:
            return "", False

        data = deepcopy(data or {})
        rows = data.get("rows", []) or []

        missing = []
        for r in rows:
            cols = set(r.get("columns") or [])
            if col not in cols:
                # usa o nome do dataset se tiver
                name = r.get("name") or f"Dataset {int(r.get('idx', 0)) + 1}"
                missing.append(name)

        if not missing:
            return "", False

        msg = [
            html.P(
                f"A coluna '{col}' não está presente em todos os datasets "
                f"selecionados para o NMA."
            ),
            html.Ul([html.Li(m) for m in missing]),
        ]
        return msg, True

    # --- Browse do diretório para salvar o NMA (resultados) ---
    @app.callback(
        Output("nma-run-save-path", "value"),
        Input("nma-run-browse", "n_clicks"),
        State("nma-run-save-path", "value"),
        prevent_initial_call=True,
    )
    def _browse_nma_run_folder(n, current):
        if not n:
            return current  # ou no_update

        try:
            import tkinter as tk
            from tkinter import filedialog as tkfd

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = tkfd.askdirectory(title="Choose folder to save NMA results")
            root.destroy()

            if not path:
                # se cancelar, mantém o valor atual
                return current

            return path
        except Exception:
            # em ambiente headless, não mexe no campo
            return current

    @app.callback(
        Output("nma-run-summary", "children"),
        Input("btn-nma-run", "n_clicks"),
        State("store-nma", "data"),
        State("store-nma-plot", "data"),
        State("nma-run-save-path", "value"),
        prevent_initial_call=True,
    )
    def _update_run_summary(n_clicks, store_nma, plot_cfg, save_path):
        from dash.exceptions import PreventUpdate
        from pathlib import Path

        if not n_clicks:
            raise PreventUpdate

        store_nma = store_nma or {}

        # 1) tenta pegar dos params (quando veio de "Create NMA settings")
        params = (store_nma.get("params") or {})
        datasets = list(params.get("datasets") or [])

        # 2) fallback: reconstruir a partir de rows (quando veio de "Load settings")
        if not datasets:
            rows = store_nma.get("rows") or []
            for r in rows:
                path = (r.get("path") or "").strip()
                if not path:
                    continue
                datasets.append(
                    {
                        "name": (r.get("name") or "").strip(),
                        "path": path,
                        "area_col": r.get("area_col"),
                        "nii_col": r.get("nii_col"),
                        "is_control": bool(r.get("is_control", False)),
                    }
                )

        n = len(datasets)

        # 3) tipo de plot
        kind = (plot_cfg or {}).get("kind", "dot")

        # 4) se não tiver saving path, usa a pasta do primeiro CSV válido
        if not save_path and datasets:
            first_path = next((d.get("path") for d in datasets if d.get("path")), None)
            if first_path:
                save_path = str(Path(first_path).parent)

        # 5) string final
        txt = f"{n} dataset(s), plot={kind}"
        if save_path:
            txt += f" → {save_path}"

        return txt

    # --- START RUN: cria progress_file, valida e dispara worker ---

    @app.callback(
        Output("nma-poll", "disabled", allow_duplicate=True),
        Output("nma-log", "children", allow_duplicate=True),
        Output("btn-nma-stop", "style", allow_duplicate=True),
        Input("btn-nma-run", "n_clicks"),
        State("store-nma", "data"),
        State("store-nma-settings", "data"),
        State("store-nma-step1", "data"),
        State("store-nma-plot", "data"),
        State("nma-run-save-path", "value"),
        prevent_initial_call=True,
    )
    def _start_nma_run(n_clicks, store_nma, settings, step1, plot_cfg, save_path):
        from dash import no_update
        hide_stop = {"display": "none"}
        show_stop = {"display": "inline-block"}

        try:
            print("\n[DEBUG NMA] _start_nma_run() called")
            print("  n_clicks:", n_clicks)

            if not n_clicks:
                print("[DEBUG NMA] n_clicks falsy, returning no_update")
                return no_update, no_update, hide_stop

            store_nma = store_nma or {}
            rows = store_nma.get("rows") or []
            print("  len(rows):", len(rows))

            # ------------------ pega paths direto da tabela ------------------
            paths = []
            missing = []
            for r in rows:
                name = (r.get("name") or "").strip() or "Unnamed dataset"
                path = (r.get("path") or "").strip()
                if not path:
                    missing.append(f"{name}: CSV path is empty.")
                    continue
                if not os.path.exists(path):
                    missing.append(f"{name}: CSV path does not exist: {path}")
                    continue
                paths.append(path)

            if not paths:
                msg = "No valid CSV paths found.\n" + ("\n".join(missing) if missing else "")
                print("[DEBUG NMA] ABORT, no paths.\n", msg)
                return True, msg, hide_stop

            if missing:
                # avisa mas segue com os que existem
                warn = "Some datasets were ignored:\n" + "\n".join(missing)
                print("[DEBUG NMA] Warning:", warn)
            else:
                warn = ""

            print("  paths used:", paths)

            # ------------------ saving path ------------------
            from pathlib import Path
            if not save_path:
                save_path = str(Path(paths[0]).parent)

            try:
                p = Path(str(save_path)).expanduser().resolve()
                p.mkdir(parents=True, exist_ok=True)
                save_path = str(p)
            except Exception as e:
                msg = f"Invalid saving path: {e}"
                print("[DEBUG NMA] ABORT:", msg)
                return True, msg, hide_stop

            print("  final save_path:", save_path)

            # ------------------ configurações de plot ------------------
            plot_cfg = plot_cfg or {}
            kind = plot_cfg.get("kind", "dot")
            dot_cfg = plot_cfg.get("dot") or {}
            heat_cfg = plot_cfg.get("heatmap") or {}

            print("  kind:", kind)
            print("  dot_cfg:", dot_cfg)
            print("  heat_cfg:", heat_cfg)

            if kind == "heatmap":
                graph_type = "heatmap" if not heat_cfg.get("jointplot") else "jointplot"
            else:
                graph_type = "dot"

            col1 = dot_cfg.get("column1")
            col2 = dot_cfg.get("column2")
            sample_size = dot_cfg.get("sample_size")
            single = bool(dot_cfg.get("single") or heat_cfg.get("single"))
            overtime = bool(dot_cfg.get("overtime") or heat_cfg.get("overtime"))
            palette = dot_cfg.get("palette") or "rainbow"
            hue_norm = dot_cfg.get("hue_norm")
            size_norm = dot_cfg.get("size_norm")

            print("  graph_type:", graph_type)
            print("  col1:", col1, " col2:", col2)
            print("  single:", single, " overtime:", overtime)
            print("  palette:", palette)
            print("  hue_norm:", hue_norm, " size_norm:", size_norm)

            # ------------------ progress file ------------------
            import tempfile, pathlib, time as _time
            ts = int(_time.time())
            progress_dir = os.path.join(tempfile.gettempdir(), "fornma_progress")
            pathlib.Path(progress_dir).mkdir(parents=True, exist_ok=True)
            progress_file = os.path.join(progress_dir, f"nma_progress_{ts}.json")
            print("  progress_file:", progress_file)

            try:
                update_progress(
                    progress_file,
                    status="running",
                    percent=0,
                    log="Starting NMA…\n" + warn if warn else "Starting NMA…",
                )
            except Exception as e:
                print("[DEBUG NMA] update_progress init failed:", repr(e))

            globals()["NMA_PROGRESS_FILE"] = progress_file

            # ------------------ control_parameters.pickle ------------------
            if build_pkl_payload is not None and settings and step1 and store_nma:
                import pickle
                try:
                    print("  writing NMA_CONFIG_PATH:", NMA_CONFIG_PATH)
                    print("  settings keys:", list((settings or {}).keys()))
                    print("  step1 keys:", list((step1 or {}).keys()))
                    thr_dbg = (settings or {}).get("thresholds") or {}
                    print("  thresholds em settings:", thr_dbg)

                    payload_pkl = build_pkl_payload(settings or {}, step1 or {}, store_nma or {})

                    # DEBUG: inspeção rápida do payload antes de salvar
                    try:
                        print("\n[NMA DEBUG] ==== _start_nma_run: payload_pkl (antes de salvar) ====")
                        print("[NMA DEBUG] keys:", sorted(payload_pkl.keys()))
                        print("[NMA DEBUG] x_left/x_mid/x_right:",
                              payload_pkl.get("x_left"),
                              payload_pkl.get("x_mid"),
                              payload_pkl.get("x_right"))
                        print("[NMA DEBUG] v_downx/v_midx/v_upx/v_downx2:",
                              payload_pkl.get("v_downx"),
                              payload_pkl.get("v_midx"),
                              payload_pkl.get("v_upx"),
                              payload_pkl.get("v_downx2"))
                        print("[NMA DEBUG] h_y_down/h_y_up:",
                              payload_pkl.get("h_y_down"),
                              payload_pkl.get("h_y_up"))
                        print("[NMA DEBUG] =============================================\n")
                    except Exception as e_dbg:
                        print("[NMA DEBUG] erro ao imprimir payload_pkl:", repr(e_dbg))

                    # salva o pickle
                    with open(NMA_CONFIG_PATH, "wb") as f:
                        pickle.dump(payload_pkl, f, protocol=pickle.HIGHEST_PROTOCOL)

                    # DEBUG: reler do disco e conferir se está igual
                    try:
                        with open(NMA_CONFIG_PATH, "rb") as f:
                            cp = pickle.load(f)
                        print("\n[NMA DEBUG] ==== _start_nma_run: control_parameters reloaded ====")
                        print("[NMA DEBUG] keys:", sorted(cp.keys()))
                        print("[NMA DEBUG] x_left/x_mid/x_right:",
                              cp.get("x_left"),
                              cp.get("x_mid"),
                              cp.get("x_right"))
                        print("[NMA DEBUG] v_downx/v_midx/v_upx/v_downx2:",
                              cp.get("v_downx"),
                              cp.get("v_midx"),
                              cp.get("v_upx"),
                              cp.get("v_downx2"))
                        print("[NMA DEBUG] h_y_down/h_y_up:",
                              cp.get("h_y_down"),
                              cp.get("h_y_up"))
                        print("[NMA DEBUG] =============================================\n")
                    except Exception as e2:
                        print("[NMA DEBUG] ERRO ao reler control_parameters.pickle:", repr(e2))

                except Exception as e:
                    print("[DEBUG NMA] build_pkl_payload failed:", repr(e))

            # ------------------ worker thread ------------------
            def _worker():
                import traceback  # <- pra evitar NameError dentro do except
                print("[DEBUG NMA] worker started")
                try:
                    orig_save = NMAClass.save_figs
                    done = 0

                    def _save_with_progress(self, fig, title):
                        nonlocal done
                        done += 1
                        pct = min(95, done * 5)
                        print(f"[DEBUG NMA] save_figs called, title={title}, pct={pct}")

                        img_src = None
                        try:
                            buf = io.BytesIO()
                            fig.savefig(buf, format="png", bbox_inches="tight")
                            buf.seek(0)
                            img_src = (
                                    "data:image/png;base64,"
                                    + base64.b64encode(buf.read()).decode("ascii")
                            )
                        except Exception as e:
                            print("[DEBUG NMA] fig to PNG failed:", repr(e))

                        payload_pg = {
                            "status": "running",
                            "percent": pct,
                            "log": f"Saved: {title}",
                        }
                        if img_src is not None:
                            payload_pg["image"] = img_src
                            payload_pg["title"] = title

                        try:
                            update_progress(progress_file, **payload_pg)
                        except Exception as e:
                            print("[DEBUG NMA] update_progress in save_figs failed:", repr(e))

                        return orig_save(self, fig, title)

                    NMAClass.save_figs = _save_with_progress

                    print("[DEBUG NMA] calling run_nma_cli(...)")
                    run_nma_cli(
                        path_list=paths,
                        saving_path=save_path,
                        graph_type=graph_type,
                        col1=col1,
                        col2=col2,
                        sample_size=sample_size,
                        single=single,
                        overtime=overtime,
                        palette=palette,
                        hue_norm=hue_norm,
                        size_norm=size_norm,
                    )
                    print("[DEBUG NMA] run_nma_cli finished OK")

                    NMAClass.save_figs = orig_save

                    update_progress(
                        progress_file,
                        status="done",
                        percent=100,
                        log="NMA finished.",
                    )
                    print("[DEBUG NMA] worker finished OK")
                except Exception as e:
                    print("[DEBUG NMA] worker exception:", repr(e))
                    try:
                        update_progress(
                            progress_file,
                            status="error",
                            percent=0,
                            log="".join(traceback.format_exception_only(type(e), e)),
                        )
                    except Exception as e2:
                        print("[DEBUG NMA] update_progress on error failed:", repr(e2))

            threading.Thread(target=_worker, daemon=True).start()

            # habilita o poll, escreve log e mostra STOP
            return False, "Running NMA…", show_stop

        except Exception as e:
            import traceback
            tb = "".join(traceback.format_exception_only(type(e), e))
            print("[DEBUG NMA] EXCEPTION in _start_nma_run:", tb)
            return True, f"Callback error in NMA: {tb}", hide_stop

    # --- POLL: lê o progress_file e atualiza barra/log/imagem ---
    @app.callback(
        Output("nma-progress", "value"),
        Output("nma-progress", "label"),
        Output("nma-log", "children", allow_duplicate=True),
        Output("nma-poll", "disabled", allow_duplicate=True),
        Output("btn-nma-stop", "style", allow_duplicate=True),
        # REMOVE ESTA LINHA: Output("nma-results-container", "children", allow_duplicate=True),
        Input("nma-poll", "n_intervals"),
        prevent_initial_call=True,
    )
    def _poll_nma(_n):
        from dash import no_update
        hide_stop = {"display": "none"}
        show_stop = {"display": "inline-block"}

        pf = globals().get("NMA_PROGRESS_FILE")
        if not (pf and os.path.exists(pf)):
            return no_update, no_update, no_update, True, hide_stop  # 5 valores

        try:
            with open(pf, "r") as f:
                d = json.load(f)
        except Exception:
            return no_update, no_update, no_update, True, hide_stop  # 5 valores

        status = d.get("status", "running")
        percent = int(d.get("percent", 0))
        log = d.get("log", "") or ""

        # REMOVE a parte do img_comp, não é mais necessário
        # pois não temos nma-results-container

        if status == "error":
            return percent, "Error", (log or "Unknown error."), True, hide_stop  # 5 valores
        if status == "canceled":
            return percent, "Canceled", (log or "Canceled by user."), True, hide_stop  # 5 valores
        if status == "done":
            try:
                os.remove(pf)
            except Exception:
                pass
            globals()["NMA_PROGRESS_FILE"] = None
            return 100, "100% (done)", (log or "Finished."), True, hide_stop  # 5 valores

        # running / starting
        return percent, f"{percent}%", log, False, show_stop  # 5 valores


    # --- STOP: sinaliza cancelamento no progress_file ---
    @app.callback(
        Output("nma-log", "children", allow_duplicate=True),
        Output("nma-poll", "disabled", allow_duplicate=True),
        Output("btn-nma-stop", "style", allow_duplicate=True),
        Input("btn-nma-stop", "n_clicks"),
        prevent_initial_call=True,
    )
    def _stop_nma(n):
        from dash import no_update
        hide_stop = {"display": "none"}

        if not n:
            return no_update, no_update, hide_stop

        pf = globals().get("NMA_PROGRESS_FILE")
        if pf and os.path.exists(pf):
            try:
                update_progress(pf, cancel=True, status="canceled", log="Cancel requested by user.")
            except Exception:
                pass

        return "Cancel requested…", True, hide_stop

    # ========== IMAGE VIEWER CALLBACKS ==========

    def _list_image_files(folder_path):
        """Lista arquivos PNG e SVG de uma pasta"""
        import glob
        import os

        if not folder_path or not os.path.exists(folder_path):
            return []

        image_files = []

        # Listar PNGs
        png_files = glob.glob(os.path.join(folder_path, "*.png"))
        # Listar SVGs
        svg_files = glob.glob(os.path.join(folder_path, "*.svg"))

        # Combinar e ordenar
        all_files = sorted(png_files + svg_files)

        # Filtrar duplicados (mesmo nome, extensões diferentes)
        seen_names = set()
        for file_path in all_files:
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            if base_name not in seen_names:
                seen_names.add(base_name)
                image_files.append({
                    "path": file_path,
                    "name": file_name,
                    "type": "png" if file_path.lower().endswith('.png') else "svg"
                })

        return image_files

    # Callback para listar imagens e esconder barra de progresso
    @app.callback(
        Output("nma-image-store", "data"),
        Output("nma-image-viewer", "style"),
        Output("nma-progress-container", "style"),
        Input("nma-poll", "n_intervals"),
        Input("nma-progress", "value"),
        Input("nma-log", "children"),
        State("nma-run-save-path", "value"),
        prevent_initial_call=True,
    )
    def _update_image_list_and_hide_progress(n_intervals, progress_value, log_text, save_path):
        # Verificar se o NMA terminou
        nma_done = False

        if progress_value == 100:
            nma_done = True

        if log_text and ("Finished" in log_text or "100%" in log_text):
            nma_done = True

        # Se não está feito, manter progresso visível
        if not nma_done:
            return no_update, {"display": "none"}, {"display": "block"}

        # Se está feito e temos save_path, listar imagens
        if nma_done and save_path:
            image_files = _list_image_files(save_path)

            if image_files:
                new_data = {
                    "image_files": image_files,
                    "current_index": 0,
                    "current_folder": save_path
                }
                return new_data, {"display": "block"}, {"display": "none"}
            else:
                # NMA terminou, mas não há imagens
                return no_update, {"display": "none"}, {"display": "none"}

        return no_update, {"display": "none"}, {"display": "none"}

    @app.callback(
        Output("nma-current-image", "src"),
        Output("nma-image-counter", "children"),
        Output("nma-image-name", "children"),
        Input("nma-image-store", "data"),
        Input("nma-prev-image", "n_clicks"),
        Input("nma-next-image", "n_clicks"),
        State("nma-image-store", "data"),
        prevent_initial_call=True,
    )
    def _update_displayed_image(data, prev_clicks, next_clicks, current_store):
        # Verificar qual input disparou o callback
        trigger = ctx.triggered_id

        # Se for uma mudança no store (primeira carga) ou clique nas setas
        if trigger == "nma-image-store" or trigger in ["nma-prev-image", "nma-next-image"]:

            # Usar current_store se disponível, senão usar data
            store_data = current_store if current_store else data

            if not store_data or not store_data.get("image_files"):
                return "", "0/0", "Nenhuma imagem disponível"

            image_files = store_data["image_files"]
            current_index = store_data["current_index"]

            # Se for clique nas setas, calcular novo índice
            if trigger == "nma-prev-image" and current_index > 0:
                current_index -= 1
            elif trigger == "nma-next-image" and current_index < len(image_files) - 1:
                current_index += 1

            # Atualizar o store com o novo índice (se mudou)
            if trigger in ["nma-prev-image", "nma-next-image"]:
                new_store_data = dict(store_data)
                new_store_data["current_index"] = current_index
                # Aqui você precisaria atualizar o store, mas isso criaria loop
                # Em vez disso, vamos apenas usar o índice calculado

            # Carregar a imagem atual
            current_image = image_files[current_index]

            try:
                with open(current_image["path"], "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()

                if current_image["type"] == "png":
                    img_src = f"data:image/png;base64,{image_data}"
                else:  # SVG
                    img_src = f"data:image/svg+xml;base64,{image_data}"
            except Exception:
                img_src = ""

            counter = f"{current_index + 1}/{len(image_files)}"
            name = current_image["name"]

            return img_src, counter, name

        return no_update, no_update, no_update


    # Callback para mostrar visualizador quando há imagens no store
    @app.callback(
        Output("nma-image-viewer", "style", allow_duplicate=True),
        Input("nma-image-store", "data"),
        prevent_initial_call=True,
    )
    def _show_viewer_when_images_exist(data):
        if data and data.get("image_files"):
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        Output("nma-image-store", "data", allow_duplicate=True),
        Input("nma-prev-image", "n_clicks"),
        Input("nma-next-image", "n_clicks"),
        State("nma-image-store", "data"),
        prevent_initial_call=True,
    )
    def _update_store_on_navigation(prev_clicks, next_clicks, data):
        if not ctx.triggered_id or not data or not data.get("image_files"):
            return no_update

        button_id = ctx.triggered_id
        image_files = data["image_files"]
        current_index = data["current_index"]

        # Determinar nova posição
        if button_id == "nma-prev-image" and current_index > 0:
            new_index = current_index - 1
        elif button_id == "nma-next-image" and current_index < len(image_files) - 1:
            new_index = current_index + 1
        else:
            new_index = current_index

        # Atualizar dados apenas se o índice mudou
        if new_index != current_index:
            new_data = dict(data)
            new_data["current_index"] = new_index
            return new_data

        return no_update









