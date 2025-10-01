# src/fornma/gui/layouts/foci_overlay.py
from dash import html, dcc
import dash_bootstrap_components as dbc

def build_sidebar():
    return html.Div(
        id={"type": "sidebar", "tab": "tab-foci-overlay"},
        style={"display": "none", "flexDirection": "column", "height": "100%"},
        children=[
            # HEADER (sticky)
            html.Div(
                id="foci-header",
                style={
                    "flex": "0 0 auto", "position": "sticky", "top": 0, "zIndex": 2,
                    "background": "#eef2ff", "paddingBottom": "8px",
                },
                children=[
                    html.H3("Foci Overlay — Inputs", style={"marginTop": 0}),
                    # Pickle folder
                    dbc.Label("Pickle (.pkl) folder", id="label-foci-pkl"),
                    html.Div(
                        [
                            dcc.Input(
                                id="foci-pkl-path", value="", placeholder="Folder with .pkl result files…",
                                style={"width": "80%"}, persistence=True, persisted_props=["value"], persistence_type="session",
                            ),
                            html.Button("Browse", id="btn-foci-browse-pkl", n_clicks=0, style={"marginLeft": "6px"}),
                        ],
                        style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
                    ),
                    dbc.Tooltip("Selecione a pasta que contém os .pkl gerados pelo forNMA.", target="label-foci-pkl", placement="right"),

                    # Saving path
                    dbc.Label("Saving path", id="label-foci-save"),
                    html.Div(
                        [
                            dcc.Input(
                                id="foci-save-path", value="", placeholder="Folder to save overlay outputs…",
                                style={"width": "80%"}, persistence=True, persisted_props=["value"], persistence_type="session",
                            ),
                            html.Button("Browse", id="btn-foci-browse-save", n_clicks=0, style={"marginLeft": "6px"}),
                        ],
                        style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
                    ),
                    dbc.Tooltip("Onde serão salvos CSVs e imagens de overlay.", target="label-foci-save", placement="right"),

                    # Channels selector (auto-filled from .pkl)
                    dbc.Label("Channels", id="label-foci-channels"),
                    dcc.Dropdown(
                        id="foci-channels",
                        options=[], value=[],
                        multi=True, placeholder="Select channels…",
                        persistence=True, persisted_props=["value"], persistence_type="session",
                        style={"marginBottom": "8px"},
                    ),
                    dbc.Tooltip("Preenchido automaticamente ao apontar uma pasta .pkl (colunas com sufixo “_channel”).", target="label-foci-channels", placement="right"),

                    dbc.Label("Actions"),
                    dcc.Checklist(
                        id="foci-actions",
                        options=[
                            {"label": "Overlay", "value": "overlay"},
                            {"label": "Plot profiles", "value": "profiles"},
                        ],
                        value=["overlay"],  # padrão
                        inputStyle={"marginRight": "6px"},
                        labelStyle={"display": "block", "marginBottom": "4px"},
                        style={"marginBottom": "8px"},
                    ),

                    # Options resumidas
                    html.Hr(style={"margin": "8px 0"}),
                    dbc.Checkbox(
                        id="foci-save-images",
                        value=True, className="mb-2",
                        label="Save overlay images"
                    ),

                    # Summary
                    dbc.Accordion(
                        [
                            dbc.AccordionItem(
                                html.Pre(
                                    id="foci-summary",
                                    style={
                                        "whiteSpace": "pre-wrap", "margin": 0,
                                        "maxHeight": "25vh", "overflowY": "auto", "fontFamily": "monospace",
                                    },
                                ),
                                title="Selection summary",
                                item_id="summary",
                            ),
                        ],
                        id="foci-summary-accordion",
                        start_collapsed=True, always_open=True, style={"marginTop": "8px"},
                    ),
                    html.Hr(style={"margin": "8px 0"}),
                ],
            ),

            # SCROLL (miolo)
            html.Div(
                id="foci-scroll",
                style={"flex": "1 1 auto", "overflowY": "auto", "paddingRight": "3px"},
                children=[
                    html.Small("Base pronta. Campos avançados (ex.: filtros) podem ser adicionados depois."),
                ],
            ),

            # FOOTER (sticky)
            html.Div(
                id="foci-footer",
                style={
                    "flex": "0 0 auto", "position": "sticky", "bottom": 0, "zIndex": 2,
                    "background": "#eef2ff", "padding": "8px 0", "borderTop": "1px solid #cfd8ff",
                },
                children=[
                    html.Hr(style={"margin": "8px 0"}),
                    html.Button("Run Overlay", id="btn-foci-run"),
                    html.Button("Stop", id="btn-foci-stop", style={"marginLeft": "8px", "color": "#b00020", "display": "none"}),
                ],
            ),
        ],
    )
