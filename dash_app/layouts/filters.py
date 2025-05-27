from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from datetime import datetime, timedelta

def get_filters(initial_start=None, initial_end=None):

    # If not provided, set default start to today at 00:00 and end to tomorrow at 00:00
    if initial_start is None:
        initial_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    if initial_end is None:
        initial_end = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() 

    return html.Div(
        [
            # Primera fila: fechas
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Row([
                            dbc.Col(html.Label("Desde:", htmlFor="datetime-picker-start", className="text-nowrap me-1"), width="auto"),
                            dbc.Col(
                                dmc.DateTimePicker(
                                    id="datetime-picker-start",
                                    value=initial_start,
                                    highlightToday=True,
                                    className="w-60"
                                ),
                                className="m-0"
                            ),
                        ], className="align-items-center"),
                        xs=12, md=4, lg=3, xl=3, xxl=2, className="mb-2"
                    ),

                    dbc.Col(
                        dbc.Row([
                            dbc.Col(html.Label("Hasta:", htmlFor="datetime-picker-end", className="text-nowrap me-1"), width="auto"),
                            dbc.Col(
                                dmc.DateTimePicker(
                                    id="datetime-picker-end",
                                    value=initial_end,
                                    highlightToday=True,
                                    className="w-60"
                                ),
                                className="m-0"
                            ),
                        ], className="align-items-center"),
                        xs=12, md=4, lg=3, xl=3, xxl=2, className="mb-2"
                    ),

                ],
                className="gx-2 gy-1 header-controls"
            ),

            # Segunda fila: filtro por familia
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Row([
                            dbc.Col(html.Label("Familias:", className="text-nowrap me-1"), width="auto"),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="family-dropdown",
                                    placeholder="Todas",
                                    multi=True,
                                    className="w-60"
                                ),
                                className="m-0"
                            ),
                        ], className="align-items-center"),
                        xs=12, md=8, lg=6, xl=5, xxl=4, className="mb-2"
                    )
                ],
                className="gx-2 gy-1 header-controls mt-auto"
            )
        ]
    )