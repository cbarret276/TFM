from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from layouts.filters import get_filters

# Main card for the geographical map
card_geo_map = dbc.Card(
    dbc.CardBody(
        [
            dcc.Loading(
                id="loading-spinner-geolocation-map",
                children=[
                    dbc.Row([
                        dbc.Col([
                            html.Label("Información a mostrar:", htmlFor="geo-view", className="form-label"),
                        ], className="col-12 col-md-3 col-comp-graph"),
                        dbc.Col([
                            dcc.Dropdown(
                                id="geo-view",
                                options=[
                                    {"label": "Distribución de malware por países", "value": "samples"},
                                    {"label": "Diversidad de técnicas de ataque", "value": "ttps"},
                                    {"label": "Distribución de IoCs (IPs) por países", "value": "ips"}
                                ],
                                value="samples",
                                placeholder="Selecciona un tipo de análisis",
                                className="mb-2 xl-9"
                            )
                        ], className="col-12 col-md-9 col-comp-graph"),
                    ], className="align-items-center gx-2"),
                    dcc.Graph(id="geo-map", style={"height": "70vh"})
                ]
            )
        ],
        className="p-0"
    ),
    className="p-1"
)

# Layout for the geographical analysis page
layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col(html.H4("Análisis geográfico", className="mt-md-3 title_page"), xs=12),
            dbc.Col(get_filters(), xs=12),
        ], className="align-items-end gx-2"),

        dbc.Row([
            dbc.Col(card_geo_map, xs=12)
        ],),
    ],
    fluid=True,
    className="dbc"
)
