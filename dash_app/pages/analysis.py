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

# Content Layout
layout = dbc.Container(
    [
        # Title and global filters
        dbc.Row([
            dbc.Col(html.H4("Análisis de muestras", className="mt-md-3 title_page"), xs=12),
            dbc.Col(get_filters(), xs=12),  # Este contenedor se puede cargar con filtros dinámicos
        ], className="align-items-end gx-2"),

        # Filtros de búsqueda
        dbc.Row([
            dbc.Col(dbc.Input(id="analysis-search", placeholder="Buscar hash, IP, dominio...", debounce=True)),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dcc.Dropdown(id="analysis-filetype-dropdown", placeholder="Tipo de fichero", multi=True), md=4),
            dbc.Col(dcc.Dropdown(id="analysis-country-dropdown", placeholder="País origen", multi=True), md=4),
            dbc.Col(dcc.RangeSlider(
                id="analysis-score-slider", min=0, max=10, step=1, value=[0, 10],
                marks={i: str(i) for i in range(0, 11)},
                tooltip={"placement": "bottom", "always_visible": True}
            ), md=4)
        ]),

        # Tabla principal
        dbc.Row([
            dbc.Col(card_analysis_table, xs=12)
        ]),

    ],
    fluid=True,
    className="dbc dbc-ag-grid"
)