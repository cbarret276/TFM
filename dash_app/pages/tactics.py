from dash import html, dcc
import dash_bootstrap_components as dbc
from layouts.filters import get_filters


# Card 1.1
card1_1 = dbc.Card([
    dcc.Loading(
        id="loading-spinner11",
        children=dbc.CardBody([
                html.H5("Tácticas", className="card-kpi-title"),
                html.P(
                    "--",
                    id="tactics_kpi1-value",
                    className="card-kpi-value",
                ),
            ])
        ),
    dbc.Tooltip("Número de tácticas de ataque detectadas en las muestras.", target="tactics_kpi1-value", placement="top")
    ])

# Card 1.2
card1_2 = dbc.Card([
    dcc.Loading(
        id="loading-spinner12",
        children=dbc.CardBody([
                html.H5("Técnicas", className="card-kpi-title"),
                html.P(
                    "--",
                    id="tactics_kpi2-value",         
                    className="card-kpi-value",
                ),            
            ])
    ),
    dbc.Tooltip("Número de técnicas de ataque detectadas en las muestras.", target="tactics_kpi2-value", placement="top")
    ])

# Card 1.3
card1_3 = dbc.Card([
    dcc.Loading(
        id="loading-spinner13",
        children=dbc.CardBody([
                html.H5("Técnicas con impacto", className="card-kpi-title"),
                html.P(
                    "--",         
                    id="tactics_kpi3-value",
                    className="card-kpi-value",
                ),
            ])
    ),
    dbc.Tooltip("Número de técnicas de ataque detectadas con impacto en disponibilidad.", target="tactics_kpi3-value", placement="top")
    ])

# Card 1.4
card1_4 = dbc.Card([
    dcc.Loading(
        id="loading-spinner14",
        children=dbc.CardBody([
                html.H5("Plataformas objetivo", className="card-kpi-title"),
                html.P(
                    "--",         
                    id="tactics_kpi4-value",
                    className="card-kpi-value",
                ),
            ])
    ),
    dbc.Tooltip("Número de plataformas objetivo de las técnicas.", target="tactics_kpi4-value", placement="top")
    ])


# Card 2_1
card2_1 = dbc.Card(
    dbc.CardBody(
        [            
            dcc.Loading(
                id="loading-spinner21",
                children=dcc.Graph(
                    id="sankey-tactics-techniques", 
                    className="w-100 h-100"
                ),
            ),
        ],
        className="p-0"
    ),
    className="p-1"
)

# Card 2_2
card2_2 = dbc.Card(
    dbc.CardBody(
        [            
            dcc.Loading(
                id="loading-spinner22",
                children=dcc.Graph(
                    id="sankey-techniques-families", 
                    className="w-100 h-100"
                ),
            ),
        ],
        className="p-0"
    ),
    className="p-1"
)

# Card 3_1
card3_1 = dbc.Card(
    dbc.CardBody(
        [            
            dcc.Loading(
                id="loading-spinner31",
                children=dcc.Graph(
                    id="temporal-techniques-graph", 
                    className="w-100 h-100"
                ),
            ),
        ],
        className="p-0"
    ),
    className="p-1"
)

# Card 3_2
card3_2 = dbc.Card(
    dbc.CardBody(
        [            
            dcc.Loading(
                id="loading-spinner32",
                children=dcc.Graph(
                    id="heatmap-tactics-families", 
                    className="w-100 h-100"
                ),
            ),
            dbc.Tooltip("Haz clic para filtrar por la familia asociada.", target="heatmap-tactics-families", placement="top")
        ],
        className="p-0"
    ),
    className="p-1"
)


# Content
layout = dbc.Container(
    [

        dbc.Row([
            dbc.Col(html.H4("Tácticas y técnicas MITRE", className="mt-md-3 title_page"), xs=12),
            dbc.Col(get_filters(), xs=12),
        ], className="align-items-end gx-2"),

        dbc.Row([
            dbc.Col(card1_1),
            dbc.Col(card1_2),
            dbc.Col(card1_3),
            dbc.Col(card1_4)
        ]),

        dbc.Row([
            dbc.Col(card2_1, xs=12, lg=6),
            dbc.Col(card2_2, xs=12, lg=6)
        ]),

        dbc.Row([
            dbc.Col(card3_1, xs=12, lg=6),
            dbc.Col(card3_2, xs=12, lg=6)
            
        ]),

    ],
    fluid=True,
    className="dbc dbc-ag-grid",
)

