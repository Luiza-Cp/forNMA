
# src/fornma/gui/layouts/registration.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import dcc



def build_registration_sidebar():

    return html.Div(
        id={"type": "sidebar", "tab": "tab-registration"},
        style={"display": "flex", "flexDirection": "column", "height": "100%"},
        children=[
            html.Div(
                id="reg-header",
                style={"flex": "0 0 auto", "position": "sticky", "top": 0, "zIndex": 2,
                       "background": "#eef2ff", "paddingBottom": "8px"},
                children=[
                    html.H3("Registration Inputs", style={"marginTop": 0}),

                    # << NOVO: abre o MESMO modal conditions × channels já usado no Segmentation
                    html.Button("Load images", id="btn-open-modal-reg", n_clicks=0),
                    dbc.Tooltip(
                        "Abra o seletor em grade para definir as pastas de cada canal (e condições). "
                        "Você pode escolher uma pasta diferente por canal.",
                        target="btn-open-modal-reg", placement="right",
                    ),

                    # --- (mantém) Pasta para SALVAR resultados
                    dbc.Row([
                        dbc.Col(dbc.Label("Saving path", id="label-reg-save-path"), width=5),
                        dbc.Col(
                            html.Div([
                                dcc.Input(
                                    id="reg-save-path",
                                    value="",
                                    placeholder="Folder to save results…",
                                    style={"width": "80%"},
                                    persistence=True, persisted_props=["value"], persistence_type="session",
                                ),
                                html.Button("Browse", id="btn-browse-save-reg", n_clicks=0, style={"marginLeft": "6px"}),
                            ], style={"display": "flex", "alignItems": "center"}),
                            width=7
                        ),
                        dbc.Tooltip(
                            "Onde os arquivos de saída (imagens registradas, logs, etc.) serão salvos.",
                            target="label-reg-save-path", placement="right",
                        ),
                    ], className="mb-2"),

                    html.Hr(style={"margin": "8px 0"}),
                ],
            ),

            # --- (mantém) Mapeamento de canais
            dbc.Accordion(
                id="reg-accordion",
                start_collapsed=True,
                children=[
                    dbc.AccordionItem(
                        title="Channel mapping",
                        item_id="channels",
                        children=[
                            dbc.Row([
                                dbc.Col(dbc.Label("Reference channel", id="label-reg-ref-ch"), width=5),
                                dbc.Col(dcc.Dropdown(
                                    id={"type":"reg-field","group":"channels","name":"ref","field":"channels"},
                                    options=[], value=None, clearable=False, placeholder="Select reference…"
                                ), width=7),
                                dbc.Tooltip(
                                    "Canal âncora: os demais serão corrigidos/alinhados em relação a este.",
                                    target="label-reg-ref-ch", placement="right",
                                ),
                            ], className="mb-2"),
                            dbc.Row([
                                dbc.Col(dbc.Label("Other channels to correct", id="label-reg-mov-ch"), width=5),
                                dbc.Col(dcc.Dropdown(
                                    id={"type":"reg-field","group":"channels","name":"moving","field":"channels"},
                                    options=[], value=[], multi=True, placeholder="Select channels…"
                                ), width=7),
                                dbc.Tooltip(
                                    "Canais a corrigir/alinhaar para coincidir com o canal de referência.",
                                    target="label-reg-mov-ch", placement="right",
                                ),
                            ], className="mb-2"),
                        ]
                    )
                ]
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Options"),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(dbc.Label("Crop output (keep common FOV)"), width="auto"),
                                    dbc.Col(
                                        dbc.Switch(
                                            id="reg-crop-flag",
                                            value=True,  # default ligado
                                            className="ms-2",
                                        ),
                                        width="auto",
                                    ),
                                ],
                                className="g-2 align-items-center",
                            ),
                        ]
                    ),
                ],
                className="mt-3",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Warnings"),
                    dbc.CardBody(
                        html.Div(id="reg-warn")  # <- alvo para mensagens de aviso
                    ),
                ],
                className="mt-3",
            ),
            # --- DEBUG (apenas UI; sem callbacks ainda) ---
            dbc.Card(
                [
                    dbc.CardHeader("Debug"),
                    dbc.CardBody(
                        [
                            dbc.Button(
                                "Debug: Show Parameters",
                                id="btn-debug-reg",
                                color="secondary",
                                size="sm",
                                className="mb-2"
                            ),
                            html.Pre(
                                id="reg-debug",
                                style={
                                    "whiteSpace": "pre-wrap",
                                    "fontFamily": "monospace",
                                    "background": "#0b1320",
                                    "color": "#c7d5ff",
                                    "padding": "8px",
                                    "borderRadius": "8px",
                                    "maxHeight": "35vh",
                                    "overflow": "auto",
                                },
                            ),
                        ]
                    ),
                ],
                className="mt-3",
            ),

            dbc.Card(
            [
                dbc.CardHeader("Debug do botão Run"),
                dbc.CardBody(
                    html.Pre(
                        id="reg-run-debug",
                        style={
                            "whiteSpace": "pre-wrap",
                            "fontFamily": "monospace",
                            "background": "#0b1320",
                            "color": "#c7d5ff",
                            "padding": "8px",
                            "borderRadius": "8px",
                            "maxHeight": "20vh",
                            "overflow": "auto",
                        },
                    )
                ),
            ],
            className="mt-2",
        ),



            # --- FOOTER (fixo no rodapé)
            html.Div(
                id="reg-footer-buttons",
                style={
                    "flex": "0 0 auto",
                    "position": "sticky",
                    "bottom": 0,
                    "zIndex": 2,
                    "background": "#eef2ff",
                    "padding": "8px 0",
                    "borderTop": "1px solid #cfd8ff",
                    "marginTop": "8px",
                },
                children=[
                    html.Hr(style={"margin": "8px 0"}),
                    html.Button("Run Registration", id="btn-run-reg"),
                    html.Button(
                        "Stop",
                        id="btn-stop-reg",
                        style={"marginLeft": "8px", "color": "#b00020", "display": "none"},
                    ),
                ],
            ),


        ],
    )
