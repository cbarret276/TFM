from dash import html, dcc
import dash_mantine_components as dmc
from pages.analysis import analysis_table_component
from layouts.filters import get_filters

def get_dummy_components():
    return html.Div([
        analysis_table_component,
        dcc.Input(id="analysis-search"),
        dcc.Dropdown(id="analysis-filetype-dropdown"),
        dcc.Dropdown(id="analysis-country-dropdown"),
        dcc.RangeSlider(
            id="analysis-score-slider",
            min=0,
            max=10,
            step=1,
            value=[0, 10],
            marks={i: str(i) for i in range(0, 11)}
        ),
        get_filters()
    ], style={"display": "none"})