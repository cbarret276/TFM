from dash_ag_grid import AgGrid
from dash import html, dcc
import dash_bootstrap_components as dbc
from layouts.filters import get_filters

analysis_table_component = AgGrid(
    id="analysis-table",
    columnDefs=[],
    rowData=[],
    dashGridOptions={
        "pagination": True,
        "paginationPageSize": 20,
        "rowSelection": "single",
        "domLayout": "autoHeight",
    },
    defaultColDef={
        "resizable": True,
        "sortable": True,
        "filter": True
    }
)


# Card 1: Tabla de análisis con dash_ag_grid
card_analysis_table = dbc.Card(
    dbc.CardBody(
        dcc.Loading(
            id="loading-spinner-analysis-table",
            children=analysis_table_component
        ),
        className="p-0",
    ),
    className="p-1"
)

# Modal for Sample Details
sample_details_modal = dbc.Modal(
    id="sample-details-modal",
    is_open=False,
    size="lg",
    scrollable=True,
    centered=True,
    children=[
        dbc.ModalHeader(dbc.ModalTitle("Detalle de la muestra seleccionada")),
        dbc.ModalBody(id="sample-details-body"),
        dbc.ModalFooter(
            dbc.Button("Cerrar", id="close-sample-details", className="ms-auto", n_clicks=0)
        ),
    ]
)

# Content Layout
layout = dbc.Container(
    [
        # Title and global filters
        dbc.Row([
            dbc.Col(html.H4("Análisis de muestras", className="mt-md-3 title_page"), xs=12),
            dbc.Col(get_filters(), xs=12),  
        ], className="align-items-end gx-2"),

        # Filtros de búsqueda
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                    id="analysis-filetype-dropdown", placeholder="Tipo de fichero", multi=True
                ), md=4, className="mt-2"
            ),

            dbc.Col(
                dcc.Dropdown(
                    id="analysis-country-dropdown", placeholder="País origen", multi=True
                ), md=4, className="mt-2"
            ),

            dbc.Col(
                dbc.Row([
                    dbc.Col(
                        html.Label("Score:", className="text-end w-100"),
                        width="auto", className="align-items-center pe-0"
                    ),
                    dbc.Col(
                        dcc.RangeSlider(
                            id="analysis-score-slider", min=0, max=10, step=1, value=[0, 10],
                            marks={i: str(i) for i in range(0, 11)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ), className="range-slider-div"
                    )
                ]),
                md=4, className="mt-2"
            )
        ]),

        # Tabla principal
        dbc.Row([
            dbc.Col(card_analysis_table, xs=12)
        ]),

        sample_details_modal

    ],
    fluid=True,
    className="dbc dbc-ag-grid"
)