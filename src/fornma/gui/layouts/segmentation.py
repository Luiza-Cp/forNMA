from dash import html, dcc
import dash_bootstrap_components as dbc

GENERAL_SETTINGS = dbc.AccordionItem(
                    title="General Settings",
                    item_id="general",
                    children=[
                        # Nuclear Detection (single-select)
                        dbc.Row([
                            dbc.Col(
                                dbc.Label("Nuclear Detection", id="label-nuclear-detection"),
                                width=5
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id={
                                        "type": "seg-field",
                                        "group": "general",
                                        "name": "channel_with_nuclei",
                                        "field": "channels"
                                    },
                                    options=[],
                                    value=None,
                                    multi=False,
                                    placeholder="Select one channel..."
                                ),
                                width=7
                            ),
                            dbc.Tooltip(
                                "Pick the channel(s) that contain nuclei for detection.",
                                target="label-nuclear-detection",
                                placement="right",
                            )
                        ], className="mb-2"),

                        # Overtime
                        html.Div(
                            id="tip-overtime-flag",
                            children=dbc.Checkbox(
                                id={"type": "seg-flag", "group": "general", "name": "overtime"},
                                value=False, className="mb-2",
                                label="Overtime"
                            )
                        ),
                        dbc.Tooltip(
                            "Check this box if your images are a time sequence. Make sure you have only a field of images per folder",
                            target="tip-overtime-flag",
                            placement="right",
                        ),

                        # Foci
                        html.Div(
                            id="tip-foci-flag",
                            children=dbc.Checkbox(
                                id={"type": "seg-flag", "group": "general", "name": "foci"},
                                value=False, className="mb-2",
                                label="Foci"
                            )
                        ),
                        dbc.Tooltip(
                            "Enable spot (foci) detection in the selected channel(s).",
                            target="tip-foci-flag",
                            placement="right",
                        ),
                        dbc.Collapse(
                            id={"type": "collapse", "group": "general", "name": "foci"},
                            is_open=False,
                            children=dbc.Row([
                                dbc.Col(dbc.Label("Channels for Foci", id="label-foci-channels"), width=5),
                                dbc.Col(
                                    html.Div(
                                        id="tip-foci-channels",
                                        children=dcc.Dropdown(
                                            id={"type": "seg-field", "group": "general", "name": "foci", "field": "channels"},
                                            options=[], value=[], multi=True,
                                            placeholder="Select channels..."
                                        )
                                    ),
                                    width=7
                                )
                            ], className="mb-2"),
                        ),
                        dbc.Tooltip(
                            "Choose the channel(s) where foci will be detected (e.g., 53BP1, γH2AX).",
                            target="label-foci-channels",
                            placement="right",
                        ),
                        dbc.Tooltip(
                            "You can pick more than one channel (multi-select).",
                            target="tip-foci-channels",
                            placement="right",
                        ),

                        # Cytoplasmatic Ring
                        html.Div(
                            id="tip-cyto-ring-flag",
                            children=dbc.Checkbox(
                                id={"type": "seg-flag", "group": "general", "name": "cyto-ring"},
                                value=False, className="mb-2",
                                label="Cytoplasmatic Ring"
                            )
                        ),
                        dbc.Tooltip(
                            "Enable cytoplasmatic ring detection in the selected channel(s).",
                            target="tip-cyto-ring-flag",
                            placement="right",
                        ),
                        dbc.Collapse(
                            id={"type": "collapse", "group": "general", "name": "cyto-ring"},
                            is_open=False,
                            children=dbc.Row([
                                dbc.Col(dbc.Label("Channels for Cytoplasmatic Ring", id="label-cyto-ring-channels"), width=5),
                                dbc.Col(
                                    html.Div(
                                        id="tip-cyto-ring-channels",
                                        children=dcc.Dropdown(
                                            id={"type": "seg-field", "group": "general", "name": "cyto-ring", "field": "channels"},
                                            options=[], value=[], multi=True,
                                            placeholder="Select channels..."
                                        )
                                    ),
                                    width=7
                                )
                            ], className="mb-2"),
                        ),
                        dbc.Tooltip(
                            "Choose the channel(s) where a cytoplasmatic ring will be detected",
                            target="label-cyto-ring-channels",
                            placement="right",
                        ),
                        dbc.Tooltip(
                            "You can pick more than one channel (multi-select).",
                            target="tip-cyto-ring-channels",
                            placement="right",
                        ),
                    ]
                )

SEGMENTATION_SETTINGS = dbc.AccordionItem(
                    title="Segmentation Settings",
                    item_id="segmentation",
                    children=[
                        dbc.Row([
                            dbc.Col(
                                dbc.Label("Magnification", id="label-magnification"),
                                width=5
                            ),
                            dbc.Col(
                                dcc.Input(
                                    id={
                                        "type": "seg-field",
                                        "group": "general",
                                        "name": "magnification",
                                    },
                                    type="number",
                                    value= 20,
                                    placeholder="Enter a number...",
                                    min=0,  # limite inferior (opcional)
                                    step=5  # incremento (opcional)
                                ),
                                width=7
                            ),
                            dbc.Tooltip(
                                "Add the numeric vale for yout images magnification",
                                target="label-magnification",
                                placement="right",
                            )
                        ], className="mb-2"),

                        dbc.Row([
                            dbc.Col(
                                dbc.Label("Pixel Size", id="label-pixel-size"),
                                width=5
                            ),
                            dbc.Col(
                                dcc.Input(
                                    id={
                                        "type": "seg-field",
                                        "group": "general",
                                        "name": "pixel-size",
                                    },
                                    type="number",
                                    value=0.6,
                                    placeholder="Enter a number...",
                                    min=0,  # limite inferior (opcional)
                                    step=5  # incremento (opcional)
                                ),
                                width=7
                            ),
                            dbc.Tooltip(
                                "Pixel size is the real sample distance each pixel represents. It depends on the sensor pixel size divided by the objective magnification and adapter factor.",
                                target="label-pixel-size",
                                placement="right",
                            )
                        ], className="mb-2"),

                        dbc.Checkbox(
                            id={"type": "seg-flag", "group": "segmentation", "name": "rescale-intensity"},
                            value=False, className="mb-2",
                            label="Rescale Intensity"
                        ),

                        dbc.Tooltip(
                            "Normalize pixel intensities to the full range (0–255). This configuration is only \
                             valid for nuclei detection step.  You can configure intensity normalization during analysis\
                             at Advanced Settings menu.",
                            target={"type": "seg-flag", "group": "segmentation", "name": "rescale-intensity"},
                            placement="right",
                        ),

                        dbc.Checkbox(
                            id={"type": "seg-flag", "group": "segmentation", "name": "remove-bg"},
                            value=False, className="mb-2",
                            label="Remove Background"
                        ),
                        dbc.Tooltip(
                            "Subtract smooth background before segmentation. This configuration is only valid \
                            for nuclei detection step. You can configure background removal during analysis at Advanced \
                             Settings menu.",
                            target={"type": "seg-flag", "group": "segmentation", "name": "remove-bg"},
                            placement="right",
                        ),

                        # Caixa extra escondida por padrão
                        dbc.Collapse(
                            dbc.Row([
                                dbc.Col(
                                    dbc.Label("Rolling Ball Radius", id="label-rolling-radius"),
                                    width=5
                                ),
                                dbc.Col(
                                    dcc.Input(
                                        id={"type": "seg-field", "group": "segmentation", "name": "rolling-radius"},
                                        type="number",
                                        value=50,  # valor padrão
                                        min=1,
                                        step=1,
                                        placeholder="Enter radius..."
                                    ),
                                    width=7
                                ),
                            ]),
                            id="collapse-rolling-radius",
                            is_open=False,  # começa fechado
                        ),
                        dbc.Tooltip(
                            "Radius of the rolling ball (in pixels) used for background subtraction.",
                            target="label-rolling-radius",
                            placement="right",
                        ),
                        # --- Layout
                        dbc.Col([
                            dbc.Label("Segmentation Method", id="label-seg-method"),
                            dbc.RadioItems(
                                id={"type": "seg-field", "group": "segmentation", "name": "seg_method"},
                                options=[
                                    {"label": "forNMA", "value": "fornma"},
                                    {"label": "Cellpose", "value": "cellpose"},
                                ],
                                value="fornma",  # torna obrigatório (já começa selecionado)
                                inline=True,  # fica lado a lado
                                inputClassName="me-2"  # pequeno espaçamento entre bolinha e label
                            ),
                            dbc.Tooltip(
                                "Choose the segmentation pipeline: forNMA (faster) or Cellpose (more accurate).",
                                target="label-seg-method",
                                placement="right",
                            ),
                        ], width=12)

                    ]
                )

ADVANCED_SETTINGS = dbc.AccordionItem(
                    title="Advanced Settings",
                    item_id="advanced",
                    children=[
                        # === Shape
                        dbc.Row([
                            dbc.Col(dbc.Label("Shape", id="label-shape"), width=3),
                            dbc.Col(
                                dbc.Switch(
                                    id={"type": "seg-flag", "group": "filters", "name": "shape-enable"},
                                    value=True, className="mb-2", label="On"
                                ), width=3
                            ),
                            dbc.Col(
                                dbc.Collapse(
                                    dcc.Input(
                                        id={"type": "seg-field", "group": "filters", "name": "shape"},
                                        type="number", value=0.88, min=0, max=1, step=0.01,
                                        placeholder="Irregularity"
                                    ),
                                    id="collapse-shape", is_open=False
                                ),
                                width=4
                            ),
                            dbc.Tooltip(
                                "Filters nucleus by irregularity. If disabled, this filter is not applied.",
                                target="label-shape", placement="right",
                            ),
                        ], className="mb-2"),

                        # === Eccentricity
                        dbc.Row([
                            dbc.Col(dbc.Label("Eccentricity", id="label-eccentricity"), width=3),
                            dbc.Col(
                                dbc.Switch(
                                    id={"type": "seg-flag", "group": "filters", "name": "eccentricity-enable"},
                                    value=False, className="mb-2", label="On"
                                ), width=3
                            ),
                            dbc.Col(
                                dbc.Collapse(
                                    dcc.Input(
                                        id={"type": "seg-field", "group": "filters", "name": "eccentricity"},
                                        type="number", min=0, max=1, step=0.01,
                                        placeholder="0–1"
                                    ),
                                    id="collapse-eccentricity", is_open=False
                                ),
                                width=4
                            ),
                            dbc.Tooltip(
                                "Filter nuclei by eccentricity: 0 = circle; values closer to 1 are more elongated.",
                                target="label-eccentricity", placement="right",
                            ),
                        ], className="mb-2"),

                        # === Minimum Size (px)
                        dbc.Row([
                            dbc.Col(dbc.Label("Min Size", id="label-min-size"), width=3),
                            dbc.Col(
                                dbc.Switch(
                                    id={"type": "seg-flag", "group": "filters", "name": "min-size-enable"},
                                    value=False, className="mb-2", label="On"
                                ), width=3
                            ),
                            dbc.Col(
                                dbc.Collapse(
                                    dcc.Input(
                                        id={"type": "seg-field", "group": "filters", "name": "minimum_size"},
                                        type="number", min=1, step=1, placeholder="Min area (px²)"
                                    ),
                                    id="collapse-min-size", is_open=False
                                ),
                                width=4
                            ),
                            dbc.Tooltip(
                                "Minimum nucleus area in pixels. If disabled, not applied.",
                                target="label-min-size", placement="right",
                            ),
                        ], className="mb-2"),

                        # === Maximum Size (px)
                        dbc.Row([
                            dbc.Col(dbc.Label("Max Size", id="label-max-size"), width=3),
                            dbc.Col(
                                dbc.Switch(
                                    id={"type": "seg-flag", "group": "filters", "name": "max-size-enable"},
                                    value=False, className="mb-2", label="On"
                                ), width=3
                            ),
                            dbc.Col(
                                dbc.Collapse(
                                    dcc.Input(
                                        id={"type": "seg-field", "group": "filters", "name": "maximum_size"},
                                        type="number", min=1, step=1, placeholder="Max area (px²)"
                                    ),
                                    id="collapse-max-size", is_open=False
                                ),
                                width=4
                            ),
                            dbc.Tooltip(
                                "Maximum nucleus area in pixels. If disabled, not applied.",
                                target="label-max-size", placement="right",
                            ),
                        ], className="mb-2"),

                        # === Minimum Radius (px)
                        dbc.Row([
                            dbc.Col(dbc.Label("Min Radius", id="label-min-radius"), width=3),
                            dbc.Col(
                                dbc.Switch(
                                    id={"type": "seg-flag", "group": "filters", "name": "min-radius-enable"},
                                    value=False, className="mb-2", label="On"
                                ), width=3
                            ),
                            dbc.Col(
                                dbc.Collapse(
                                    dcc.Input(
                                        id={"type": "seg-field", "group": "filters", "name": "minimum_radius"},
                                        type="number", min=1, step=1, placeholder="Min radius (px)"
                                    ),
                                    id="collapse-min-radius", is_open=False
                                ),
                                width=4
                            ),
                            dbc.Tooltip(
                                "Minimum nucleus radius in pixels. If disabled, not applied.",
                                target="label-min-radius", placement="right",
                            ),
                        ], className="mb-2"),

                        # === Maximum Radius (px)
                        dbc.Row([
                            dbc.Col(dbc.Label("Max Radius", id="label-max-radius"), width=3),
                            dbc.Col(
                                dbc.Switch(
                                    id={"type": "seg-flag", "group": "filters", "name": "max-radius-enable"},
                                    value=False, className="mb-2", label="On"
                                ), width=3
                            ),
                            dbc.Col(
                                dbc.Collapse(
                                    dcc.Input(
                                        id={"type": "seg-field", "group": "filters", "name": "maximum_radius"},
                                        type="number", min=1, step=1, placeholder="Max radius (px)"
                                    ),
                                    id="collapse-max-radius", is_open=False
                                ),
                                width=4
                            ),
                            dbc.Tooltip(
                                "Maximum nucleus radius in pixels. If disabled, not applied.",
                                target="label-max-radius", placement="right",
                            ),
                        ], className="mb-2"),

                        # --- ForNMA Parameters (visível só quando seg_method == "fornma")
                        dbc.Collapse([
                            html.H5("forNMA Parameters", id="title-fornma-params", className="mt-3 mb-3"),

                            # Threshold + Offset (offset aparece só para thresholds locais)
                            dbc.Row([
                                dbc.Col(dbc.Label("Threshold", id="label-threshold"), width=5),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id={"type": "seg-field", "group": "fornma", "name": "threshold"},
                                        options=[
                                            {"label": "Isodata", "value": "isodata"},
                                            {"label": "Li", "value": "li"},
                                            {"label": "Mean", "value": "mean"},
                                            {"label": "Minimum", "value": "minimum"},
                                            {"label": "Median", "value": "median"},
                                            {"label": "Multi-Otsu", "value": "multi_otsu"},
                                            {"label": "Otsu", "value": "otsu"},
                                            {"label": "Triangle", "value": "triangle"},
                                            {"label": "Yen", "value": "yen"},
                                            {"label": "Local Mean", "value": "local_mean"},
                                            {"label": "Local Gaussian", "value": "local_gaussian"},
                                        ],
                                        value="triangle",
                                        clearable=False,
                                        placeholder="Select a threshold..."
                                    ),
                                    width=7
                                ),
                                dbc.Tooltip(
                                    "The threshold type to separate nuclei from background. Local thresholds "
                                    "require an offset (constant subtracted from the neighborhood's weighted mean).",
                                    target="label-threshold", placement="right",
                                ),
                            ], className="mb-2"),
                            # Offset (label + input dentro do mesmo Collapse)
                            dbc.Collapse(
                                dbc.Row([
                                    dbc.Col(dbc.Label("Offset", id="label-offset"), width=5),
                                    dbc.Col(
                                        dcc.Input(
                                            id={"type": "seg-field", "group": "fornma", "name": "offset"},
                                            type="number", value=5, step=1, placeholder="Offset",
                                        ),
                                        width=7
                                    ),
                                    dbc.Tooltip(
                                        "Constant subtracted from the local (weighted) mean when using Local thresholds.",
                                        target="label-offset", placement="right",
                                    ),
                                ], className="mb-2"),
                                id="collapse-offset",
                                is_open=False
                            ),

                            # --- Blur
                            dbc.Row([
                                dbc.Col(dbc.Label("Smooth (iterations)", id="label-smooth"), width=12),
                                dbc.Col(
                                    dcc.Slider(
                                        id={"type": "seg-field", "group": "fornma", "name": "smooth"},
                                        min=0, max=30, step=1, value=12,
                                        marks={0: "0", 30: "30"},
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                    width=12
                                ),
                                dbc.Tooltip(
                                    "Number of times to blur the nuclear mask. Higher = smoother contours.",
                                    target="label-smooth",
                                    placement="right",
                                ),
                            ], className="mb-3"),

                            # --- Adjust size
                            dbc.Row([
                                dbc.Col(dbc.Label("Adjust size", id="label-adjust-size"), width=12),
                                dbc.Col(
                                    dcc.Slider(
                                        id={"type": "seg-field", "group": "fornma", "name": "adjust_size"},
                                        min=-30, max=30, step=1, value=0,
                                        marks={-30: "-30", 30: "+30"},
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                    width=12
                                ),
                                dbc.Tooltip(
                                    "Adjust contours to the nucleus edge. Positive enlarges; negative shrinks (in pixels).",
                                    target="label-adjust-size",
                                    placement="right",
                                ),
                            ], className="mb-3"),

                            # --- Cut edges
                            dbc.Row([
                                dbc.Col(dbc.Label("Cut edges", id="label-cut-edges"), width=12),
                                dbc.Col(
                                    dcc.Slider(
                                        id={"type": "seg-field", "group": "fornma", "name": "cut_edges"},
                                        min=0, max=1, step=0.05, value=0.7,
                                        marks={0: "0", 1: "1"},
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                    width=12
                                ),
                                dbc.Tooltip(
                                    "Force cuts between close nuclei when watershed fails. Higher = more restrictive.",
                                    target="label-cut-edges",
                                    placement="right",
                                ),
                            ], className="mb-3"),

                            # Find low intensity nucleus
                            dbc.Row([
                                dbc.Col(dbc.Label("Find low-intensity nuclei", id="label-find-low"), width=8),
                                dbc.Col(
                                    dbc.Switch(
                                        id={"type": "seg-flag", "group": "fornma",
                                            "name": "find_low_intensity_nucleus"},
                                        value=False, label="On", className="mb-2"
                                    ),
                                    width=3
                                ),
                                dbc.Tooltip(
                                    "Run an extra pass to look for missed nuclei in covered/low-intensity regions.",
                                    target="label-find-low", placement="right",
                                ),
                            ], className="mb-2"),

                            # Weakly labeled
                            dbc.Row([
                                dbc.Col(dbc.Label("Weakly labeled images", id="label-weakly"), width=8),
                                dbc.Col(
                                    dbc.Switch(
                                        id={"type": "seg-flag", "group": "fornma", "name": "weakly_labeled"},
                                        value=False, label="On", className="mb-2"
                                    ),
                                    width=3
                                ),
                                dbc.Tooltip(
                                    "Activates extra routines for weak nuclear staining / unclear edges.",
                                    target="label-weakly", placement="right",
                                ),
                            ], className="mb-2"),

                        ], id="collapse-fornma-params", is_open=False),

                        dbc.Collapse([
                            html.H5("Cellpose Parameters", className="mt-3 mb-3"),

                            # Diameter
                            dbc.Row([
                                dbc.Col(dbc.Label("Diameter (px)", id="label-diameter"), width=12),
                                dbc.Col(
                                    dcc.Slider(
                                        id={"type": "seg-field", "group": "cellpose", "name": "diameter"},
                                        min=0, max=120, step=1, value=25,
                                        marks={0: "0", 120: "120"},
                                        tooltip={"placement": "bottom", "always_visible": False}
                                    ), width=12
                                ),
                                dbc.Tooltip(
                                    "Typical cell diameter in pixels; Cellpose rescales image around ~30 px diameter.",
                                    target="label-diameter", placement="right",
                                ),
                            ], className="mb-3"),

                            # Flow threshold
                            dbc.Row([
                                dbc.Col(dbc.Label("Flow Threshold", id="label-flow-thresh"), width=12),
                                dbc.Col(
                                    dcc.Slider(
                                        id={"type": "seg-field", "group": "cellpose", "name": "flow_threshold"},
                                        min=0, max=1, step=0.05, value=0.4,
                                        marks={0: "0", 1: "1"},
                                        tooltip={"placement": "bottom", "always_visible": False}
                                    ), width=12
                                ),
                                dbc.Tooltip(
                                    "Maximum flow error allowed per mask. Lower values = fewer but more accurate masks.",
                                    target="label-flow-thresh", placement="right",
                                ),
                            ], className="mb-3"),

                            # Mask threshold
                            dbc.Row([
                                dbc.Col(dbc.Label("Mask Threshold", id="label-mask-thresh"), width=12),
                                dbc.Col(
                                    dcc.Slider(
                                        id={"type": "seg-field", "group": "cellpose", "name": "mask_threshold"},
                                        min=-6, max=6, step=0.5, value=0.0,
                                        marks={-6: "-6", 6: "6"},
                                        tooltip={"placement": "bottom", "always_visible": False}
                                    ), width=12
                                ),
                                dbc.Tooltip(
                                    "Threshold for cell probability map. Lower = larger masks; higher = stricter inclusion.",
                                    target="label-mask-thresh", placement="right",
                                ),
                            ], className="mb-3"),

                            # Cellprob threshold
                            dbc.Row([
                                dbc.Col(dbc.Label("Cellprob Threshold", id="label-cellprob"), width=12),
                                dbc.Col(
                                    dcc.Slider(
                                        id={"type": "seg-field", "group": "cellpose", "name": "cellprob_threshold"},
                                        min=-6, max=6, step=0.5, value=-3,
                                        marks={-6: "-6", 6: "6"},
                                        tooltip={"placement": "bottom", "always_visible": False}
                                    ), width=12
                                ),
                                dbc.Tooltip(
                                    "Threshold for cell probability output; lower values = more cells, less confident.",
                                    target="label-cellprob", placement="right",
                                ),
                            ], className="mb-3"),

                            # Use GPU
                            dbc.Row([
                                dbc.Col(dbc.Label("Use GPU", id="label-use-gpu"), width=5),
                                dbc.Col(
                                    dbc.Switch(
                                        id={"type": "seg-flag", "group": "cellpose", "name": "use_gpu"},
                                        value=True, label="On", className="mb-2"
                                    ), width=7
                                ),
                                dbc.Tooltip(
                                    "Run Cellpose on GPU for faster execution (if available).",
                                    target="label-use-gpu", placement="right",
                                ),
                            ], className="mb-2"),

                            # Invert
                            dbc.Row([
                                dbc.Col(dbc.Label("Invert Intensities", id="label-invert"), width=5),
                                dbc.Col(
                                    dbc.Switch(
                                        id={"type": "seg-flag", "group": "cellpose", "name": "invert"},
                                        value=True, label="On", className="mb-2"
                                    ), width=7
                                ),
                                dbc.Tooltip(
                                    "Invert image intensities before segmentation (útil para fundos claros ou escuros).",
                                    target="label-invert", placement="right",
                                ),
                            ], className="mb-2"),

                        ], id="collapse-cellpose-params", is_open=False)

                    ]
                )

def build_sidebar():
    return html.Div(
        id={"type": "sidebar", "tab": "tab-segmentation"},
        # faz o container preencher a altura e virar coluna
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100%",         # o pai (left-pane) já tem 100vh
        },
        children=[
            # ---------- HEADER (fixo no topo) ----------
            html.Div(
                id="seg-header",
                style={
                    "flex": "0 0 auto",
                    "position": "sticky",
                    "top": 0,
                    "zIndex": 2,
                    "background": "#eef2ff",       # mesmo fundo do left-pane
                    "paddingBottom": "8px",
                },
                children=[
                    html.H3("Segmentation — Inputs", style={"marginTop": 0}),
                    html.Button("Load images", id="btn-open-modal"),
                    html.Div(
                        [
                            dbc.Label("Saving path", id="label-save-path", style={"marginTop": "8px"}),
                            html.Div(
                                [
                                    dcc.Input(
                                        id="save-path",
                                        value="",
                                        placeholder="Folder to save results…",
                                        style={"width": "80%"},
                                        persistence=True,
                                        persisted_props=["value"],
                                        persistence_type="session",
                                    ),
                                    html.Button(
                                        "Browse",
                                        id="btn-browse-save",
                                        n_clicks=0,
                                        style={"marginLeft": "6px"},
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                        ]
                    ),
                    dbc.Tooltip(
                        "Where outputs (tables, images, logs) will be written.",
                        target="label-save-path",
                        placement="right",
                    ),
                    html.Div(id="summary-box", style={"whiteSpace": "pre-wrap", "marginTop": "8px"}),
                    html.Hr(style={"margin": "8px 0"}),
                ],
            ),

            # ---------- SCROLL ÁREA (apenas o miolo rola) ----------
            html.Div(
                id="seg-scroll",
                style={
                    "flex": "1 1 auto",
                    "overflowY": "auto",
                    "paddingRight": "3px",  # espaço pro scrollbar não colar no conteúdo
                },
                children=[
                    # 👉 Os itens precisam estar dentro de um Accordion
                    dbc.Accordion(
                        id="seg-accordion",
                        start_collapsed=True,
                        always_open=True,
                        children=[
                            GENERAL_SETTINGS,
                            SEGMENTATION_SETTINGS,
                            ADVANCED_SETTINGS,
                        ],
                    ),

                    # --- Channel Settings (subtítulo + acordeão dinâmico)
                    html.Hr(className="my-3"),
                    html.H6("Channel Settings", id="subtitle-channel-settings", className="text-muted mb-2"),
                    dbc.Tooltip(
                        "Configure per-channel measurements and options here.",
                        target="subtitle-channel-settings",
                        placement="right",
                    ),
                    dbc.Accordion(
                        id="accordion-channels",
                        start_collapsed=True,  # todos iniciam fechados
                        always_open=False,  # apenas um aberto por vez
                        flush=True,  # visual mais clean
                    ),
                ],
            ),
            # ---------- FOOTER (fixo no rodapé) ----------
        html.Div(
                id="seg-footer",
                style={
                    "flex": "0 0 auto",
                    "position": "sticky",
                    "bottom": 0,
                    "zIndex": 2,
                    "background": "#eef2ff",
                    "padding": "8px 0",
                    "borderTop": "1px solid #cfd8ff",
                },
                children=[
                    html.Hr(style={"margin": "8px 0"}),
                    html.Button("Preview", id="btn-preview"),
                    html.Button("Run", id="btn-run", style={"marginLeft": "8px"}),
                ],
            ),

            html.Div(
                [
                    dbc.Label("Debug — parâmetros (temporário)"),
                    html.Pre(
                        id="run-params",
                        style={
                            "whiteSpace": "pre-wrap",
                            "overflowY": "auto",
                            "maxHeight": "30vh",
                            "border": "1px solid #ddd",
                            "padding": "8px",
                            "borderRadius": "6px",
                            "fontSize": "12px",
                            "background": "#fafafa",
                        },
                    ),
                ],
                id="run-params-wrapper",
            )
        ],
    )