# src/fornma/gui/layouts/nma.py
from dash import html, dcc
import dash_bootstrap_components as dbc


def _header():
    return html.Div(
        id="nma-header",
        style={
            "flex": "0 0 auto",
            "position": "sticky",
            "top": 0,
            "zIndex": 2,
            "background": "#eef2ff",
            "paddingBottom": "8px",
        },
        children=[
            html.H3("NMEA — Inputs", style={"marginTop": 0}),
            dbc.Alert(
                id="nma-alert",
                color="danger",
                is_open=False,
                style={"marginBottom": "8px"},
            ),
            html.Div(
                [
                    html.Button(
                        "+ Add dataset",
                        id="nma-add-row",
                        n_clicks=0,
                        title="Add a new CSV dataset row",
                    ),
                ],
                style={"display": "flex", "gap": "8px"},
            ),
            html.Hr(style={"margin": "8px 0"}),
        ],
    )


def _scroll():
    return html.Div(
        id="nma-scroll",
        style={
            "flex": "1 1 auto",
            "overflowY": "auto",
            "paddingRight": "3px",
        },
        children=[
            html.H6("Datasets", id="nma-subtitle", className="text-muted mb-2"),
            dbc.Tooltip(
                "Add one or more CSV files. Mark any as Control if applicable.",
                target="nma-subtitle",
                placement="right",
            ),
            # container onde os itens (Accordion) são renderizados via callback
            html.Div(id="nma-datasets-container", children=[]),
        ],
    )


def _footer():
    return html.Div(
        id="nma-footer",
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

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "Create NMA settings",
                            id="btn-nma-build",
                            color="primary",
                            className="w-100",
                            n_clicks=0,
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Load settings",
                            id="btn-nma-load",
                            color="secondary",
                            className="w-100",
                            n_clicks=0,
                        ),
                        width=6,
                    ),
                ],
                className="g-2",
            ),
            html.Div(
                id="nma-load-status",
                style={"marginTop": "8px", "fontFamily": "monospace"}
            ),
        ],
    )


def build_sidebar():
    """
    Sidebar para a aba NMA (tab-NMA).
    """
    return html.Div(
        id={"type": "sidebar", "tab": "tab-NMA"},
        style={"display": "flex", "flexDirection": "column", "height": "100%"},
        children=[
            _header(),
            _scroll(),
            _footer(),
            html.Div(
                [
                    dbc.Label("Debug — NMA params (temporário)"),
                    html.Pre(
                        id="nma-params",
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
                id="nma-params-wrapper",
            ),
        ],
    )
