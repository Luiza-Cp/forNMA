from dash import html, dcc
import dash_bootstrap_components as dbc

def build_nma_right_pane():
    # ajuste só estes números:
    G   = 640  # lado do gráfico (px)
    BAY = 80   # “baia” fixa para o slider vertical (px)

    return html.Div(
        id="nma-right-pane",
        style={
            "--g":   f"{G}px",
            "--bay": f"{BAY}px",
            "padding": "8px",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column",
            "gap": "12px",
        },
        children=[
            dcc.Store(id="store-nma-step1", data={}),
            dcc.Store(id="store-nma-wizard", data={"step": 1}),
            dcc.Store(id="store-nma-settings", data={}),

            # ===================== STEP 1 =====================
            html.Div(
                id="nma-step1-pane",
                style={"display": "block", "width": f"{BAY + G}px", "maxWidth": "90vw", "margin": "0 auto"},
                children=[
                    html.Div(
                        html.H6("NMA — Step 1: Adjust threshold ellipse",
                                style={"margin": 0, "textAlign": "center"}),
                    ),

                    html.Pre(
                        id="nma-step1-debug",
                        style={
                            "width": "100%", "margin": "4px auto 0",
                            "background": "#f8fafc", "border": "1px solid #e5e7eb",
                            "borderRadius": "6px", "padding": "6px 8px",
                            "fontSize": "12px", "whiteSpace": "pre-wrap",
                        },
                    ),

                    # palco: rótulo + slider vertical + gráfico
                    html.Div(
                        id="nma-stage1",
                        style={
                            "display": "flex",
                            "justifyContent": "center",
                            "alignItems": "stretch",
                            "gap": "0",
                            "width": "100%",
                            "margin": "0 auto",
                        },
                        children=[
                            # Coluna estreita: rótulo + slider vertical (altura = G)
                            html.Div(
                                style={
                                    "width": "var(--bay)",
                                    "height": f"{G}px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                                children=[
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                            "gap": "6px",
                                            "height": "100%",
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    "height": "100%",
                                                    "width": "28px",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "justifyContent": "center",
                                                },
                                                children=html.Span(
                                                    "Standard Deviations from Area",
                                                    style={
                                                        "writingMode": "vertical-rl",
                                                        "transform": "rotate(180deg)",
                                                        "fontSize": "12px",
                                                        "color": "#6b7280",
                                                        "userSelect": "none",
                                                        "height": "100%",
                                                        "display": "flex",
                                                        "alignItems": "flex-end",
                                                        "justifyContent": "center",
                                                        "paddingBottom": "4px",
                                                    },
                                                ),
                                            ),
                                            html.Div(
                                                dcc.Slider(
                                                    id="nma-area-sd",
                                                    min=0.5, max=3.0, step=0.05, value=1.0,
                                                    marks={"0.5": "0.5", "3": "3"},
                                                    updatemode="drag",
                                                    tooltip={"placement": "bottom", "always_visible": False},
                                                    vertical=True,
                                                    verticalHeight=G,
                                                ),
                                                style={"overflow": "visible"},
                                            ),
                                        ],
                                    ),
                                ],
                            ),

                            # Coluna larga: gráfico (G x G)
                            html.Div(
                                style={"width": "var(--g)"},
                                children=dcc.Graph(
                                    id="nma-fig-ellipse",
                                    config={"editable": False, "displayModeBar": False},
                                    style={"width": f"{G}px", "height": f"{G}px"},
                                ),
                            ),
                        ],
                    ),

                    # Slider horizontal (NII)
                    html.Div(
                        id="nma-nii-slider-row",
                        style={"width": f"{G}px", "maxWidth": "90vw", "margin": "0 auto"},
                        children=[
                            html.Div(
                                "Standard Deviations from NII",
                                style={"fontSize": "12px", "color": "#6b7280", "marginBottom": "6px"},
                            ),
                            html.Div(
                                dcc.Slider(
                                    id="nma-nii-sd",
                                    min=0.5, max=3.0, step=0.05, value=1.0,
                                    marks={"0.5": "0.5", "3": "3"},
                                    updatemode="drag",
                                    tooltip={"placement": "bottom", "always_visible": False},
                                ),
                                style={"overflow": "visible", "marginBottom": "6px"},
                            ),
                        ],
                    ),

                    # Botão Next (só Step 1)
                    html.Div(
                        style={"width": "100%", "margin": "0 auto", "display": "flex", "justifyContent": "center"},
                        children=[html.Button("Next", id="nma-step1-next")],
                    ),
                ],
            ),

            # ===================== STEP 2 =====================
            html.Div(
                id="nma-step2-pane",
                style={"display": "none", "width": f"{BAY + G}px", "maxWidth": "90vw", "margin": "0 auto"},
                children=[
                    html.H6("NMA — Step 2: Set NII thresholds", style={"textAlign": "center", "marginTop": "8px"}),
                    dcc.Graph(
                        id="nma-fig-lines",
                        config={"editable": True, "edits": {"shapePosition": True}},
                        style={"width": f"{G}px", "height": f"{G}px", "margin": "0 auto"},
                    ),
                    html.Div(
                        className="d-flex justify-content-center gap-2 mt-2",
                        children=[
                            html.Button("Previous", id="nma-step2-prev"),
                            html.Button("Complete", id="nma-step2-complete", className="ms-2"),
                        ],
                    ),
                ],
            ),

            # ===================== RESULT (Step 3) =====================
            html.Div(
                id="nma-result-pane",
                style={"display": "none", "width": f"{BAY + G}px", "maxWidth": "90vw", "margin": "0 auto"},
                children=[
                    html.H6("NMA — Settings criadas", style={"textAlign": "center", "marginTop": "8px"}),
                    html.Div(
                        "As configurações foram criadas com sucesso.",
                        style={"textAlign": "center", "margin": "6px 0 12px", "color": "#065f46"},
                    ),
                    dcc.Graph(
                        id="nma-fig-preview",
                        config={"displayModeBar": False},
                        style={"width": f"{G}px", "height": f"{G}px", "margin": "0 auto"},
                    ),

                    # Botão inicial (mostra painel)
                    html.Div(
                        style={"display": "flex", "justifyContent": "center", "marginTop": "12px"},
                        children=[html.Button("Save settings", id="nma-save-open")],
                    ),

                    # Painel de SAVE (inicialmente oculto)
                    html.Div(
                        id="nma-save-panel",
                        style={"display": "none"},
                        children=[
                            html.Div(
                                style={
                                    "marginTop": "12px",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "alignItems": "center",
                                    "gap": "8px",
                                },
                                children=[
                                    html.Div(
                                        style={"display": "flex", "gap": "8px", "alignItems": "center"},
                                        children=[
                                            dcc.Input(
                                                id="nma-save-path",
                                                type="text",
                                                placeholder="Escolha a pasta (ou digite o caminho)…",
                                                style={"width": "420px"},
                                            ),
                                            html.Button("Browse…", id="nma-save-browse"),
                                        ],
                                    ),
                                    html.Button("Save now", id="nma-save-do"),
                                    html.Div(id="nma-save-status", style={"textAlign": "center", "marginTop": "6px"}),
                                ],
                            ),
                        ],
                    ),
                ],
            ),

        ],
    )

