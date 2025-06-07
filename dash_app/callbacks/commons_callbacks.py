from dash import Input, Output, callback, State, clientside_callback, no_update, exceptions
from dash import callback_context as ctx
from app_instance import esc
from datetime import datetime, timedelta, timezone
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
    # Callback to update the global filters based on user input
    @callback(
        Output("global-filters", "data"),
        [
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("family-dropdown", "value"),
            Input("time-range-selector", "value")
        ],
        prevent_initial_call=True
    )
    def update_global_filters(start, end, families, range_selected):
        return {
            "start": start,
            "end": end,
            "families": families,
            "range": range_selected
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
    
 
    @callback(
        Output("datetime-picker-start", "value"),
        Output("datetime-picker-end", "value"),
        Output("family-dropdown", "value"),
        Output("time-range-selector", "value"),
        Input("url", "pathname"),
        State("global-filters", "data"),
        prevent_initial_call=True
    )
    def restore_filters(pathname, stored_data): 
        if stored_data:
            return (
                stored_data.get("start"),
                stored_data.get("end"),
                stored_data.get("families"),
                stored_data.get("range")
            )
        else: 
            start = datetime.now().replace(hour=0, minute=0, second=0)
            end = start + timedelta(days=1)
            start = start.astimezone().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
            end = end.astimezone().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
            time_range = "last24h"
            return (
                start, end, None, time_range
            )

 
    @callback(
        Output("datetime-picker-start", "value", allow_duplicate=True),
        Output("datetime-picker-end", "value", allow_duplicate=True),
        Output("family-dropdown", "value", allow_duplicate=True),
        Output("time-range-selector", "value", allow_duplicate=True),
        Input("time-range-selector", "value"),
        Input("datetime-picker-start", "value"),
        Input("datetime-picker-end", "value"),
        State("global-filters", "data"),
        prevent_initial_call=True
    )
    def update_manual_or_range(
        range_selected, manual_start, manual_end,
        stored_data
    ):
        
        if not stored_data:
            return no_update, no_update, no_update, no_update

        triggered = ctx.triggered_id
        now = datetime.now(timezone.utc).replace(microsecond=0)

        prev_start=stored_data.get("start")
        prev_end=stored_data.get("end")        
        prev_range=stored_data.get("range")
        
        if triggered == "time-range-selector":
            if (prev_range==range_selected):
                return no_update, no_update, no_update, no_update
            
            if range_selected == "today":
                start = now.replace(hour=0, minute=0, second=0)
                end = start + timedelta(days=1)
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
                return no_update, no_update, no_update, no_update

            start = start.astimezone().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
            end = end.astimezone().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
            
            return start, end, no_update, no_update


        elif triggered in ["datetime-picker-start", "datetime-picker-end"]:
            if (manual_start==prev_start and manual_end==prev_end):
                return no_update, no_update, no_update, no_update
            return manual_start, manual_end, no_update, ""


   