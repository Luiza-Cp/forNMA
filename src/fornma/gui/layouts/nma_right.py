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
            # título centralizado com a mesma largura do palco (slider+gráfico)
            html.Div(
                html.H6("NMA — Step 1: Adjust threshold ellipse", style={"margin": 0, "textAlign": "center"}),
                style={"width": "calc(var(--bay) + var(--g))", "maxWidth": "90vw", "margin": "0 auto"},
            ),

            dcc.Store(id="store-nma-step1", data={}),
            dcc.Store(id="store-nma-wizard", data={"step": 1}),

            # ... dentro da lista children de build_nma_right_pane(), logo após o título:

            html.Pre(
                id="nma-step1-debug",
                style={
                    "width": "calc(var(--bay) + var(--g))",
                    "maxWidth": "90vw",
                    "margin": "4px auto 0",
                    "background": "#f8fafc",
                    "border": "1px solid #e5e7eb",
                    "borderRadius": "6px",
                    "padding": "6px 8px",
                    "fontSize": "12px",
                    "whiteSpace": "pre-wrap",

                },
            ),

            # ===== PALCO central =====
            html.Div(
                id="nma-stage1",
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "stretch",
                    "gap": "0",
                    "width": "calc(var(--bay) + var(--g))",
                    "maxWidth": "90vw",
                    "margin": "0 auto",
                },
                children=[


                    # Coluna estreita: rótulo À ESQUERDA do slider vertical (altura = G)
                    html.Div(
                        style={
                            "width": "var(--bay)",
                            "height": f"{G}px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                        children=[
                            # Linha com rótulo (esquerda) + slider (direita)
                            html.Div(
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "gap": "6px",
                                    "height": "100%",
                                },
                                children=[
                                    # RÓTULO — vertical, centralizado, do lado esquerdo
                                    html.Div(
                                        style={
                                            "height": "100%",
                                            "width": "28px",  # ajuste fino da largura do rótulo
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                        },
                                        children=html.Span(
                                            "Area SD",
                                            style={
                                                "writingMode": "vertical-rl",
                                                "transform": "rotate(180deg)",
                                                # texto de baixo para cima (como no print)
                                                "fontSize": "12px",
                                                "color": "#6b7280",
                                                "userSelect": "none",
                                            },
                                        ),
                                    ),
                                    # SLIDER vertical (altura EXATA = G)
                                    dcc.Slider(
                                        id="nma-area-sd",
                                        min=0.5, max=3.0, step=0.05, value=1.0,
                                        marks=None,
                                        updatemode="drag",
                                        tooltip={"placement": "bottom", "always_visible": False},
                                        vertical=True,
                                        verticalHeight=G,  # <- mesma altura do gráfico
                                    ),
                                ],
                            ),
                        ],
                    ),

                    # Coluna larga: gráfico quadrado (G x G)
                    html.Div(
                        style={"width": "var(--g)"},
                        children=dcc.Graph(
                            id="nma-fig-ellipse",
                            config={"editable": False},
                            style={"width": f"{G}px", "height": f"{G}px"},
                        ),
                    ),
                ],
            ),

            # Slider horizontal (NII) — mesma largura do gráfico (G)
            html.Div(
                id="nma-nii-slider-row",
                style={"width": f"{G}px", "maxWidth": "90vw", "margin": "0 auto"},
                children=[
                    dbc.Label("NII SD"),
                    dcc.Slider(
                        id="nma-nii-sd",
                        min=0.5, max=3.0, step=0.05, value=1.0,
                        marks=None,
                        updatemode="drag",
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ],
            ),


            # Botão Next alinhado à largura do palco
            html.Div(
                style={
                    "width": f"{BAY+G}px",
                    "maxWidth": "90vw",
                    "margin": "0 auto",
                    "display": "flex",
                    "justifyContent": "center",
                },
                children=[html.Button("Next", id="nma-step1-next")],
            ),


        ],
    )
