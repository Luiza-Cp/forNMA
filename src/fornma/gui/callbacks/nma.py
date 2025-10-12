# src/fornma/gui/callbacks/nma.py
from dash import Input, Output, State, ALL, html, dcc, no_update, ctx
import dash_bootstrap_components as dbc
from copy import deepcopy
from pathlib import Path
import pandas as pd


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
                            dbc.Col(dbc.Label("Area column", id={"type": "nma-label-area", "idx": i}), md=2),
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
                            dbc.Col(dbc.Label("NII column", id={"type": "nma-label-nii", "idx": i}), md=2),
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
                    html.Small(
                        f"Detected columns: {', '.join(cols) if cols else '—'}",
                        className="text-muted",
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
