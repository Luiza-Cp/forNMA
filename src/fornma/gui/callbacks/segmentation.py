# src/fornma/gui/callbacks/segmentation.py
from dash import Input, Output, State, ALL, html, dcc
import dash_bootstrap_components as dbc
from copy import deepcopy

def register(app):
    # --- Toggles: abre/fecha collapses de Foci e Cyto-ring
    @app.callback(
        Output({"type": "collapse", "group": "general", "name": "foci"}, "is_open"),
        Input({"type": "seg-flag", "group": "general", "name": "foci"}, "value"),
    )
    def _toggle_foci(v):
        return bool(v)

    @app.callback(
        Output({"type": "collapse", "group": "general", "name": "cyto-ring"}, "is_open"),
        Input({"type": "seg-flag", "group": "general", "name": "cyto-ring"}, "value"),
    )
    def _toggle_cyto(v):
        return bool(v)

    # --- Options: preenche TODOS os dropdowns com field="channels"
    @app.callback(
        Output({"type": "seg-field", "group": ALL, "name": ALL, "field": "channels"}, "options"),
        Input("store-images", "data"),
        State({"type": "seg-field", "group": ALL, "name": ALL, "field": "channels"}, "id"),
        prevent_initial_call=False
    )
    def _fill_channel_options(data, targets):
        chans = (data or {}).get("channels", [])
        opts = [{"label": ch.get("name", ch.get("id", "")), "value": ch.get("id")} for ch in chans]
        return [opts] * len(targets)

    # --- Value: mantém os 'value' válidos (single vs multi)
    @app.callback(
        Output({"type": "seg-field", "group": ALL, "name": ALL, "field": "channels"}, "value"),
        Input({"type": "seg-field", "group": ALL, "name": ALL, "field": "channels"}, "value"),
        Input("store-images", "data"),
        State({"type": "seg-field", "group": ALL, "name": ALL, "field": "channels"}, "id"),
        prevent_initial_call=True
    )
    def _normalize_channel_values(values_list, data, ids):
        valid = {ch["id"] for ch in (data or {}).get("channels", [])}
        out = []
        for v, comp_id in zip(values_list, ids):
            # seu single-select é o 'channel_with_nuclei'
            is_single = (comp_id.get("name") == "channel_with_nuclei")
            if is_single:
                if isinstance(v, list):
                    v = next((x for x in v if x in valid), None)
                v = v if (v in valid or v is None) else None
                out.append(v)
            else:
                if not isinstance(v, list):
                    v = [] if v is None else [v]
                out.append([x for x in v if x in valid])
        return out

    @app.callback(
        Output("collapse-rolling-radius", "is_open"),
        Input({"type": "seg-flag", "group": "segmentation", "name": "remove-bg"}, "value"),
    )

    def toggle_radius_box(remove_bg_checked):
        return bool(remove_bg_checked)

    @app.callback(
        Output("collapse-shape", "is_open"),
        Output("collapse-eccentricity", "is_open"),
        Output("collapse-min-size", "is_open"),
        Output("collapse-max-size", "is_open"),
        Output("collapse-min-radius", "is_open"),
        Output("collapse-max-radius", "is_open"),

        Output({"type": "seg-field", "group": "filters", "name": "shape"}, "disabled"),
        Output({"type": "seg-field", "group": "filters", "name": "eccentricity"}, "disabled"),
        Output({"type": "seg-field", "group": "filters", "name": "minimum_size"}, "disabled"),
        Output({"type": "seg-field", "group": "filters", "name": "maximum_size"}, "disabled"),
        Output({"type": "seg-field", "group": "filters", "name": "minimum_radius"}, "disabled"),
        Output({"type": "seg-field", "group": "filters", "name": "maximum_radius"}, "disabled"),

        Input({"type": "seg-flag", "group": "filters", "name": "shape-enable"}, "value"),
        Input({"type": "seg-flag", "group": "filters", "name": "eccentricity-enable"}, "value"),
        Input({"type": "seg-flag", "group": "filters", "name": "min-size-enable"}, "value"),
        Input({"type": "seg-flag", "group": "filters", "name": "max-size-enable"}, "value"),
        Input({"type": "seg-flag", "group": "filters", "name": "min-radius-enable"}, "value"),
        Input({"type": "seg-flag", "group": "filters", "name": "max-radius-enable"}, "value"),
    )
    def _toggle_filter_boxes(en_shape, en_ecc, en_min_sz, en_max_sz, en_min_r, en_max_r):
        opens = [bool(en_shape), bool(en_ecc), bool(en_min_sz), bool(en_max_sz), bool(en_min_r), bool(en_max_r)]
        disableds = [not x for x in opens]
        return (*opens, *disableds)

    @app.callback(
        Output("collapse-fornma-params", "is_open"),
        Input({"type": "seg-field", "group": "segmentation", "name": "seg_method"}, "value"),
    )
    def _toggle_fornma_block(seg_method):
        return seg_method == "fornma"

    @app.callback(
        Output("collapse-cellpose-params", "is_open"),
        Input({"type": "seg-field", "group": "segmentation", "name": "seg_method"}, "value"),
    )
    def _toggle_cellpose_block(method):
        return method == "cellpose"

    @app.callback(
        Output("collapse-offset", "is_open"),
        Input({"type": "seg-field", "group": "fornma", "name": "threshold"}, "value"),
    )
    def _toggle_offset(thresh):
        return thresh in {"local_mean", "local_gaussian"}

    @app.callback(
        Output({"type": "seg-field", "group": "fornma", "name": "offset"}, "disabled"),
        Input({"type": "seg-field", "group": "fornma", "name": "threshold"}, "value"),
    )
    def _disable_offset(thresh):
        return thresh not in {"local_mean", "local_gaussian"}

    @app.callback(
        Output("accordion-channels", "children"),
        Input("store-images", "data"),  # canais
        Input({"type": "seg-flag", "group": "general", "name": "foci"}, "value"),
        Input({"type": "seg-field", "group": "general", "name": "foci", "field": "channels"}, "value"),
        Input({"type": "seg-flag", "group": "general", "name": "cyto-ring"}, "value"),
        Input({"type": "seg-field", "group": "general", "name": "cyto-ring", "field": "channels"}, "value"),
        prevent_initial_call=False
    )
    def _build_channel_params(data, foci_on, foci_channels, ring_on, ring_channels):
        channels = (data or {}).get("channels", [])
        foci_set = set(foci_channels or [])
        ring_set = set(ring_channels or [])

        def base_block(ch_id):
            return dbc.Stack([
                # rescale_intensity
                dbc.Row([
                    dbc.Col(dbc.Label("Rescale intensity", id={"type":"ch-label","ch":ch_id,"name":"rescale"}), width=5),
                    dbc.Col(dbc.Switch(
                        id={"type":"ch-flag","ch":ch_id,"name":"rescale_intensity"},
                        value=True, label="On", className="mb-2"
                    ), width=7),
                ], className="mb-2"),
                dbc.Tooltip(
                    "Re-distributes image intensity to maximize contrast (recommended for high background).",
                    target={"type":"ch-label","ch":ch_id,"name":"rescale"}, placement="right",
                ),

                # remove_background + rolling_ball_radius
                dbc.Row([
                    dbc.Col(dbc.Label("Remove background", id={"type":"ch-label","ch":ch_id,"name":"rm-bg"}), width=5),
                    dbc.Col(dbc.Switch(
                        id={"type":"ch-flag","ch":ch_id,"name":"remove_background"},
                        value=True, label="On", className="mb-2"
                    ), width=7),
                ], className="mb-1"),
                dbc.Collapse(
                    dbc.Row([
                        dbc.Col(dbc.Label("Rolling-ball radius (px)", id={"type":"ch-label","ch":ch_id,"name":"rb"}), width=5),
                        dbc.Col(dcc.Input(
                            id={"type":"ch-field","ch":ch_id,"name":"rolling_ball_radius"},
                            type="number", min=1, step=1, value=40, placeholder="≥ maior objeto do fundo"
                        ), width=7),
                    ], className="mb-2"),
                    id={"type":"ch-collapse","ch":ch_id,"name":"rb"},
                    is_open=True  # abre quando remove_background estiver ON (ajustado por callback abaixo)
                ),
                dbc.Tooltip(
                    "Applies rolling-ball background subtraction. Radius ≥ maior objeto que NÃO é background.",
                    target={"type":"ch-label","ch":ch_id,"name":"rb"}, placement="right",
                ),

                # match_histograms
                dbc.Row([
                    dbc.Col(dbc.Label("Match histograms", id={"type":"ch-label","ch":ch_id,"name":"match"}), width=5),
                    dbc.Col(dbc.Switch(
                        id={"type":"ch-flag","ch":ch_id,"name":"match_histograms"},
                        value=False, label="On", className="mb-2"
                    ), width=7),
                ], className="mb-2"),
                dbc.Tooltip(
                    "Harmonize intensity distribution across images/conditions (quando aplicável).",
                    target={"type":"ch-label","ch":ch_id,"name":"match"}, placement="right",
                ),
            ], gap=1)

        def ring_block(ch_id):
            # aparece só se ring_on e canal selecionado
            return dbc.Stack([
                html.Hr(className="my-2"),
                html.Small("Translocation (Cytoplasmatic Ring)", className="text-muted"),
                # ring_size
                dbc.Row([
                    dbc.Col(dbc.Label("Ring size (px)", id={"type":"ch-label","ch":ch_id,"name":"ring_size"}), width=12),
                    dbc.Col(dcc.Slider(
                        id={"type":"ch-field","ch":ch_id,"name":"ring_size"},
                        min=1, max=20, step=1, value=3, marks={1:"1",20:"20"},
                        tooltip={"placement":"bottom","always_visible":False}
                    ), width=12),
                ], className="mb-2"),
                dbc.Tooltip(
                    "Width of the cytoplasmatic ring used for nucleus-cytoplasm intensity ratio.",
                    target={"type":"ch-label","ch":ch_id,"name":"ring_size"}, placement="right",
                ),
                # use_ellipse
                dbc.Row([
                    dbc.Col(dbc.Label("Use ellipse", id={"type":"ch-label","ch":ch_id,"name":"ellipse"}), width=5),
                    dbc.Col(dbc.Switch(
                        id={"type":"ch-flag","ch":ch_id,"name":"use_ellipse"},
                        value=True, label="On", className="mb-2"
                    ), width=7),
                ], className="mb-2"),
                dbc.Tooltip(
                    "Use elliptical approximation of nucleus contour to compute cytoplasmatic ring.",
                    target={"type":"ch-label","ch":ch_id,"name":"ellipse"}, placement="right",
                ),
            ], gap=1)

        def foci_block(ch_id):
            # aparece só se foci_on e canal selecionado
            return dbc.Stack([
                html.Hr(className="my-2"),
                html.Small("Foci (spots) detection", className="text-muted"),

                # foci_min_size (obrigatório)
                dbc.Row([
                    dbc.Col(dbc.Label("Min foci size (px²)", id={"type":"ch-label","ch":ch_id,"name":"foci_min_size"}), width=5),
                    dbc.Col(dcc.Input(
                        id={"type":"ch-field","ch":ch_id,"name":"foci_min_size"},
                        type="number", min=1, step=1, value=7,
                        style={"maxWidth": "120px"},
                    ), width=7),
                ], className="mb-2"),

                # foci_max_size (opcional: toggle + input)
                dbc.Row([
                    dbc.Col(
                        dbc.Label("Max foci size (px²)", id={"type": "ch-label", "ch": ch_id, "name": "foci_max_size"}),
                        xs=12, md=6),
                    dbc.Col(dbc.Switch(
                        id={"type": "ch-flag", "ch": ch_id, "name": "foci_max_size-enable"},
                        value=False, label="", className="mb-2"
                    ), xs="auto", md=2),
                    dbc.Col(dcc.Input(
                        id={"type": "ch-field", "ch": ch_id, "name": "foci_max_size"},
                        type="number", min=1, step=1, value=20,
                        style={"maxWidth": "120px"},
                        disabled=True  # controlado no callback
                    ),  xs="auto", md=4),
                ],className="g-2 align-items-center", style={"flexWrap": "wrap"}),

                # foci min int
                dbc.Row([
                    dbc.Col(
                        dbc.Label("Min foci intensity", id={"type": "ch-label", "ch": ch_id, "name": "foci_min_int"}),
                        xs=12, md=6),
                    dbc.Col(dbc.Switch(
                        id={"type": "ch-flag", "ch": ch_id, "name": "foci_min_int-enable"},
                        value=False, label="", className="mb-2"
                    ), xs="auto", md=2),
                    dbc.Col(dcc.Input(
                        id={"type": "ch-field", "ch": ch_id, "name": "foci_min_int"},
                        type="number", step=0.1, value=0.0,
                        disabled=True,
                        style={"maxWidth": "120px"},
                    ), xs="auto", md=4),
                ],className="g-2 align-items-center", style={"flexWrap": "wrap"}),

                # foci max int
                dbc.Row([
                    dbc.Col(
                        dbc.Label("Max foci intensity", id={"type": "ch-label", "ch": ch_id, "name": "foci_max_int"}),
                        xs=12, md=6
                    ),
                    dbc.Col(
                        dbc.Switch(
                            id={"type": "ch-flag", "ch": ch_id, "name": "foci_max_int-enable"},
                            value=False, label="", className="mb-2"
                        ),
                        xs="auto", md=2
                    ),
                    dbc.Col(
                        dcc.Input(
                            id={"type": "ch-field", "ch": ch_id, "name": "foci_max_int"},
                            type="number", step=0.1, value=1.0,
                            className="form-control form-control-sm",
                            style={"maxWidth": "120px"},  # evita “vazar”
                            disabled=True
                        ),
                        xs="auto", md=4
                    ),
                ], className="g-2 align-items-center", style={"flexWrap": "wrap"}),

                # foci_prominence
                dbc.Row([
                    dbc.Col(dbc.Label("Foci prominence", id={"type":"ch-label","ch":ch_id,"name":"foci_prominence"}), width=12),
                    dbc.Col(dcc.Slider(
                        id={"type":"ch-field","ch":ch_id,"name":"foci_prominence"},
                        min=0, max=5, step=0.1, value=1.2, marks={0:"0",5:"5"},
                        tooltip={"placement":"bottom","always_visible":False}
                    ), width=12),
                ], className="mb-2"),
                dbc.Tooltip(
                    "How much a spot stands out from its neighborhood (higher = stricter).",
                    target={"type":"ch-label","ch":ch_id,"name":"foci_prominence"}, placement="right",
                ),
            ], gap=1)

        # monta os itens
        items = []
        for i, ch in enumerate(channels):
            ch_id = ch.get("id", f"ch{i+1}")
            ch_name = ch.get("name") or f"Channel {i+1}"

            blocks = [base_block(ch_id)]
            if ring_on and ch_id in ring_set:
                blocks.append(ring_block(ch_id))
            if foci_on and ch_id in foci_set:
                blocks.append(foci_block(ch_id))

            items.append(
                dbc.AccordionItem(
                    title=ch_name,
                    item_id=str(ch_id),
                    children=dbc.Stack(blocks, gap=2)
                )
            )
        return items

    # Abre/fecha Rolling Ball por canal conforme toggle remove_background
    # abre/fecha o bloco do rolling-ball por canal (NÃO mudar)
    @app.callback(
        Output({"type": "ch-collapse", "ch": ALL, "name": "rb"}, "is_open"),
        Input({"type": "ch-flag", "ch": ALL, "name": "remove_background"}, "value"),
        prevent_initial_call=False
    )
    def _toggle_rb(per_channel_remove_bg):
        return [bool(v) for v in (per_channel_remove_bg or [])]

    # Abre/fecha collapses dos foci opcionais por canal
    @app.callback(
        Output({"type":"ch-collapse","ch": ALL, "name":"foci_max_size"}, "is_open"),
        Output({"type":"ch-collapse","ch": ALL, "name":"foci_min_int"}, "is_open"),
        Output({"type":"ch-collapse","ch": ALL, "name":"foci_max_int"}, "is_open"),
        Input({"type":"ch-flag","ch": ALL, "name":"foci_max_size-enable"}, "value"),
        Input({"type":"ch-flag","ch": ALL, "name":"foci_min_int-enable"}, "value"),
        Input({"type":"ch-flag","ch": ALL, "name":"foci_max_int-enable"}, "value"),
        prevent_initial_call=False
    )
    def _toggle_foci_optionals(en_max_size, en_min_int, en_max_int):
        def as_bools(lst): return [bool(v) for v in (lst or [])]
        return as_bools(en_max_size), as_bools(en_min_int), as_bools(en_max_int)

    @app.callback(
        Output({"type": "ch-field", "ch": ALL, "name": "foci_max_size"}, "disabled"),
        Output({"type": "ch-field", "ch": ALL, "name": "foci_min_int"}, "disabled"),
        Output({"type": "ch-field", "ch": ALL, "name": "foci_max_int"}, "disabled"),
        Input({"type": "ch-flag", "ch": ALL, "name": "foci_max_size-enable"}, "value"),
        Input({"type": "ch-flag", "ch": ALL, "name": "foci_min_int-enable"}, "value"),
        Input({"type": "ch-flag", "ch": ALL, "name": "foci_max_int-enable"}, "value"),
        prevent_initial_call=False
    )
    def _enable_foci_optionals(en_max_size, en_min_int, en_max_int):
        to_bools = lambda lst: [bool(x) for x in (lst or [])]
        max_size_on = to_bools(en_max_size)
        min_int_on = to_bools(en_min_int)
        max_int_on = to_bools(en_max_int)
        # disabled é o inverso do switch
        return ([not x for x in max_size_on],
                [not x for x in min_int_on],
                [not x for x in max_int_on])