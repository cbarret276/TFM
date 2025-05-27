from dash import html, dcc
import dash_bootstrap_components as dbc
from layouts.filters import get_filters
                 
# Card 1.1
card1_1 = dbc.Card([
    dcc.Loading(
        id="loading-spinner11",
        children=dbc.CardBody([
                html.H5("Muestras", className="card-kpi-title"),
                html.P(
                    "--",
                    id="kpi1-value",
                    className="card-kpi-value",
                ),
            ])
        )
    ])

# Card 1.2
card1_2 = dbc.Card([
    dcc.Loading(
        id="loading-spinner12",
        children=dbc.CardBody([
                html.H5("Malware", className="card-kpi-title"),
                html.P(
                    "--",
                    id="kpi2-value",         
                    className="card-kpi-value",
                ),            
            ])
        )
    ])

# Card 1.3
card1_3 = dbc.Card([
    dcc.Loading(
        id="loading-spinner13",
        children=dbc.CardBody([
                html.H5("Score", className="card-kpi-title"),
                html.P(
                    "--",         
                    id="kpi3-value",
                    className="card-kpi-value",
                ),
            ])
        )
    ])

# Card 1.4
card1_4 = dbc.Card([
    dcc.Loading(
        id="loading-spinner14",
        children=dbc.CardBody([
                html.H5("Familias", className="card-kpi-title"),
                html.P(
                    "--",         
                    id="kpi4-value",
                    className="card-kpi-value",
                ),
            ])
        )
    ])


# Card 1.5
card1_5 = dbc.Card([
    dcc.Loading(
        id="loading-spinner15",
        children=dbc.CardBody([
                html.H5("IOCs", className="card-kpi-title"),
                html.P(
                    "--",         
                    id="kpi5-value",
                    className="card-kpi-value",
                ),
            ])
        )
    ])


# Card 2_1
card2_1 = dbc.Card(
    dbc.CardBody(
        [            
            dcc.Loading(
                id="loading-spinner21",
                children=dcc.Graph(
                    id="histogram-graph", 
                    className="w-100 h-100"
                ),
            ),
        ],
        className="p-0"
    ),
    className="p-1"
)

# Card 2.2
card2_2 = dbc.Card(
    dbc.CardBody(
        [    
            dcc.Loading(
                id="loading-spinner22",
                children=dcc.Graph(
                    id="graph-bar",
                    className="w-100 h-100"
                ),
            ),
        ],
        className="p-0"
    ),
    className="p-1"
)


# Card 3.1

card3_1 = dbc.Card(
    dbc.CardBody(
        [
            dcc.Loading(
                id="loading-spinner31",
                children=dcc.Graph(
                    id="map",
                    className="w-100 h-100"
                ),
            )
        ],
        className="p-0"
    ),
    className="p-1"
)


# Card 3.2
card3_2 = dbc.Card(
    dbc.CardBody(
        [    
            dcc.Loading(
                id="loading-spinner32",
                children=dcc.Graph(
                    id="graph-treemap", 
                    className="w-100 h-100"
                )
            )
        ],
        className="p-0"
    ),
    className="p-1"
)



# Content
layout = dbc.Container(
    [

        dbc.Row([
            dbc.Col(html.H4("Panorámica", className="mt-md-3 title_page"), xs=12),
            dbc.Col(get_filters(), xs=12),
        ], className="align-items-end gx-2"),
        
        dbc.Row([
            dbc.Col(card1_1),
            dbc.Col(card1_2),
            dbc.Col(card1_3),
            dbc.Col(card1_4),
            dbc.Col(card1_5),
        ]),

        dbc.Row([
            dbc.Col(card2_1, xs=12, lg=8),
            dbc.Col(card2_2, xs=12, lg=4),
        ]),

        dbc.Row([
            dbc.Col(card3_1, xs=12, lg=6),                
            dbc.Col(card3_2, xs=12, lg=6),
        ]),

    ],
    fluid=True,
    className="dbc dbc-ag-grid",
)

