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
                style={
                    "display": "block",
                    "width": f"{BAY + G}px",
                    "maxWidth": "90vw",
                    "margin": "0 auto",
                },
                children=[
                    html.Div(
                        html.H6(
                            "NMA — Step 1: Adjust threshold ellipse",
                            style={"margin": 0, "textAlign": "center"},
                        ),
                    ),

                    html.Pre(
                        id="nma-step1-debug",
                        style={
                            "width": "100%",
                            "margin": "4px auto 0",
                            "background": "#f8fafc",
                            "border": "1px solid #e5e7eb",
                            "borderRadius": "6px",
                            "padding": "6px 8px",
                            "fontSize": "12px",
                            "whiteSpace": "pre-wrap",
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
                                                    min=0.5,
                                                    max=3.0,
                                                    step=0.05,
                                                    value=1.0,
                                                    marks={"0.5": "0.5", "3": "3"},
                                                    updatemode="drag",
                                                    tooltip={
                                                        "placement": "bottom",
                                                        "always_visible": False,
                                                    },
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
                                    style={
                                        "width": f"{G}px",
                                        "height": f"{G}px",
                                    },
                                ),
                            ),
                        ],
                    ),

                    # Slider horizontal (NII)
                    html.Div(
                        id="nma-nii-slider-row",
                        style={
                            "width": f"{G}px",
                            "maxWidth": "90vw",
                            "margin": "0 auto",
                        },
                        children=[
                            html.Div(
                                "Standard Deviations from NII",
                                style={
                                    "fontSize": "12px",
                                    "color": "#6b7280",
                                    "marginBottom": "6px",
                                },
                            ),
                            html.Div(
                                dcc.Slider(
                                    id="nma-nii-sd",
                                    min=0.5,
                                    max=3.0,
                                    step=0.05,
                                    value=1.0,
                                    marks={"0.5": "0.5", "3": "3"},
                                    updatemode="drag",
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": False,
                                    },
                                ),
                                style={
                                    "overflow": "visible",
                                    "marginBottom": "6px",
                                },
                            ),
                        ],
                    ),

                    # Botão AUTO (DBSCAN)
                    html.Div(
                        style={
                            "width": f"{G}px",
                            "maxWidth": "90vw",
                            "margin": "0 auto",
                            "display": "flex",
                            "justifyContent": "center",
                            "gap": "8px",
                        },
                        children=[
                            html.Button(
                                "Auto (DBSCAN)",
                                id="nma-find-settings",
                                title="Detect core cluster and set ellipse/sliders",
                            ),
                        ],
                    ),

                    # Botão Next
                    html.Div(
                        style={
                            "width": "100%",
                            "margin": "0 auto",
                            "display": "flex",
                            "justifyContent": "center",
                        },
                        children=[html.Button("Next", id="nma-step1-next")],
                    ),
                ],
            ),

            # ===================== STEP 2 =====================
            html.Div(
                id="nma-step2-pane",
                style={
                    "display": "none",
                    "width": f"{BAY + G}px",
                    "maxWidth": "90vw",
                    "margin": "0 auto",
                },
                children=[
                    html.H6(
                        "NMA — Step 2: Set NII thresholds",
                        style={"textAlign": "center", "marginTop": "8px"},
                    ),
                    dcc.Graph(
                        id="nma-fig-lines",
                        config={"editable": True, "edits": {"shapePosition": True}},
                        style={
                            "width": f"{G}px",
                            "height": f"{G}px",
                            "margin": "0 auto",
                        },
                    ),
                    html.Div(
                        className="d-flex justify-content-center gap-2 mt-2",
                        children=[
                            html.Button("Previous", id="nma-step2-prev"),
                            html.Button(
                                "Complete",
                                id="nma-step2-complete",
                                className="ms-2",
                            ),
                        ],
                    ),
                ],
            ),

            # ===================== RESULT (Step 3) =====================
            html.Div(
                id="nma-result-pane",
                style={
                    "display": "none",
                    "width": "100%",          # agora usamos a largura toda
                    "maxWidth": "100%",
                    "margin": "0 auto",
                },
                children=[
                    html.H6(
                        "NMA — Settings criadas",
                        style={"textAlign": "center", "marginTop": "8px"},
                    ),

                    # ====== AQUI ENTRA A DIVISÃO EM DUAS COLUNAS ======
                    html.Div(
                        style={
                            "display": "flex",
                            "flexDirection": "row",
                            "gap": "16px",
                            "alignItems": "flex-start",
                            "justifyContent": "center",
                        },
                        children=[
                            # COLUNA ESQUERDA: preview + salvar settings
                            html.Div(
                                style={
                                    "flex": "0 0 auto",
                                    "width": f"{G}px",
                                },
                                children=[
                                    dcc.Graph(
                                        id="nma-fig-preview",
                                        config={"displayModeBar": False},
                                        style={
                                            "width": f"{G}px",
                                            "height": f"{G}px",
                                            "margin": "0 auto",
                                        },
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "alignItems": "center",
                                            "marginTop": "12px",
                                        },
                                        children=[
                                            html.Button(
                                                "Save settings",
                                                id="nma-save-open",
                                            ),
                                            html.Div(
                                                id="nma-save-status",
                                                style={
                                                    "textAlign": "center",
                                                    "marginTop": "8px",
                                                    "fontFamily": "monospace",
                                                },
                                            ),
                                        ],
                                    ),
                                ],
                            ),

                            # COLUNA DIREITA: progresso, log, imagens do NMA
                            html.Div(
                                style={
                                    "flex": "1 1 auto",
                                    "maxWidth": "100%",
                                },
                                children=[
                                    # poll
                                    dcc.Interval(
                                        id="nma-poll",
                                        interval=1000,
                                        disabled=True,
                                    ),

                                    # Barra de progresso
                                    dbc.Progress(
                                        id="nma-progress",
                                        value=0,
                                        label="0%",
                                        striped=True,
                                        animated=True,
                                        style={
                                            "height": "18px",
                                            "marginTop": "0px",
                                        },
                                    ),

                                    # Log + botão STOP
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "flex-start",
                                            "gap": "8px",
                                            "marginTop": "8px",
                                        },
                                        children=[
                                            html.Pre(
                                                id="nma-log",
                                                style={
                                                    "flex": "1",
                                                    "margin": 0,
                                                    "padding": "6px 8px",
                                                    "backgroundColor": "#f9fafb",
                                                    "borderRadius": "6px",
                                                    "maxHeight": "140px",
                                                    "overflowY": "auto",
                                                    "fontSize": "11px",
                                                    "whiteSpace": "pre-wrap",
                                                },
                                            ),
                                            dbc.Button(
                                                "Stop",
                                                id="btn-nma-stop",
                                                size="sm",
                                                color="danger",
                                                outline=True,
                                                style={"display": "none"},
                                            ),
                                        ],
                                    ),

                                    # Container para resultados / imagens geradas
                                    html.Div(
                                        id="nma-results-container",
                                        style={
                                            "marginTop": "10px",
                                            "maxHeight": "calc(100vh - 260px)",
                                            "overflowY": "auto",
                                            "border": "1px solid #e5e7eb",
                                            "borderRadius": "6px",
                                            "padding": "6px",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
