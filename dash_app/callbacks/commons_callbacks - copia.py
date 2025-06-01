from dash import Input, Output, callback, State, clientside_callback
from dash import callback_context as ctx
from app_instance import esc
from datetime import datetime, timedelta
import pandas as pd

import importlib

PAGES = {
    "/": "pages.home",
    "/tactics": "pages.tactics",
    "/indicators": "pages.indicators",
    "/geolocation": "pages.geolocation",
    "/analysis": "pages.analysis"
}

def register_render_page_content():
    # updates the Bootstrap global light/dark color mode
    clientside_callback(
        """
        switchOn => {       
            document.documentElement.setAttribute('data-bs-theme', switchOn ? 'light' : 'dark');  
            return window.dash_clientside.no_update
        }
        """,
        Output("switch", "id"),
        Input("switch", "value"),
    )

    clientside_callback(
        """
        (data,switchOn) => {
        document.documentElement.setAttribute('data-mantine-color-scheme', switchOn ? 'light' : 'dark');
        return window.dash_clientside.no_update
        }
        """,
        Input('session-id', 'data'),
        Input('switch', 'value'),
    )

    clientside_callback(
        """
        function(_, prev) {
            return window.innerWidth;
        }
        """,
        Output("screen-width", "data"),
        Input("switch", "value"),
        prevent_initial_call=False
    )

    clientside_callback(
        """
        function(pathname) {
            try {
                return localStorage.getItem("userTimezone") || "UTC";
            } catch (e) {
                return "UTC";
            }
        }
        """,
        Output("user-timezone", "data"),
        Input("url", "pathname")
    )

    # Multi page pattern
    @callback(
        Output("page-content", "children"), 
        Input("url", "pathname")
    )
    def render_page_content(pathname):
        
        # If the pathname is not found, use the default page
        if pathname not in PAGES:
            pathname = "/"

        # Import the corresponding page module
        page_module = importlib.import_module(PAGES[pathname])
        
        return page_module.layout

    # Lateral menu for mobile devices
    @callback(
        Output("offcanvas-menu", "is_open"),
        Input("btn-toggle-menu", "n_clicks"),
        State("offcanvas-menu", "is_open"),
        prevent_initial_call=True
    )
    def toggle_offcanvas(n, is_open):
        return not is_open if n else is_open


def register_filters_callbacks():
#     # Callback to update the date range picker
#     @callback(
#         Output("datetime-picker-start", "value"),
#         Output("datetime-picker-end", "value"),
#         Input("datetime-picker-start", "value"),
#         Input("datetime-picker-end", "value"),
#         prevent_initial_call=True
#     )
#     def sync_dates(start_value, end_value):
#         start = pd.to_datetime(start_value)
#         end = pd.to_datetime(end_value)
#         triggered = ctx.triggered_id 

#         if triggered == "datetime-picker-start" and start >= end:
#                 new_end = (start + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
#                 return start.isoformat(), new_end.isoformat()

#         elif triggered == "datetime-picker-end" and end <= start: 
#                 new_start = (end - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
#                 return new_start.isoformat(), end.isoformat()

#         return start_value, end_value

    # Callback to store the global filters in session storage
    @callback(
        Output("global-filters", "data"),
        [
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("family-dropdown", "value")
        ],
        prevent_initial_call=True
    )
    def update_global_filters(start, end, families):
        return {
            "start": start,
            "end": end,
            "families": families
        }

    # Callback to update the family filter dropdown options
    @callback(
        Output("family-dropdown", "options"),
        Input("datetime-picker-start", "value"),
        Input("datetime-picker-end", "value"),
    )
    def update_family_filter(start, end):
        # Get the start and end values from the DateTimePicker components
        start = pd.to_datetime(start).isoformat()
        end = pd.to_datetime(end).isoformat()

        # Get the data from elasticsearch
        df = pd.DataFrame(esc.fetch_aggreg_by_bins(start, end, size=100))

        if df.empty:
            return []

        families = sorted(set(df["family"].dropna()) - {"Unknown"})
        options = [{"label": fam, "value": fam} for fam in families]

        return options
    
    # Callback to update filters from session
    @callback(
        Output("datetime-picker-start", "value"),
        Output("datetime-picker-end", "value"),
        Output("family-dropdown", "value"),
        Input("url", "pathname"),
        State("global-filters", "data"),
        prevent_initial_call=True
    )
    def restore_filters(path, data):
        if data:
            return data.get("start"), data.get("end"), data.get("families") 
        else: 
            initial_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            initial_end = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() 
            return initial_start, initial_end, None
    
    #  Callback to update the date range picker based on the selected time range
    @callback(
        Output("datetime-picker-start", "value"),
        Output("datetime-picker-end", "value"),
        Input("time-range-selector", "value"),
        prevent_initial_call=True
    )
    def update_dates_from_selector(range_selected):
        now = datetime.now()
        if range_selected == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = (start + timedelta(days=1))
        elif range_selected == "last24h":
            end = now
            start = end - timedelta(hours=24)
        elif range_selected == "last7d":
            end = now
            start = end - timedelta(days=7)
        elif range_selected == "last30d":
            end = now
            start = end - timedelta(days=30)
        elif range_selected == "last365d":
            end = now
            start = end - timedelta(days=365)
        else:
            return dash.no_update, dash.no_update

        return start.isoformat(), end.isoformat()

    # Limpia el selector si el usuario cambia manualmente las fechas
    @callback(
        Output("time-range-selector", "value"),
        Input("datetime-picker-start", "value"),
        Input("datetime-picker-end", "value"),
        prevent_initial_call=True
    )
    def clear_selector_on_manual_change(start, end):
        triggered = ctx.triggered_id
        if triggered in ["datetime-picker-start", "datetime-picker-end"]:
            return None
        return dash.no_update