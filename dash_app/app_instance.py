from dash import Dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from utils.elastic_wrapper import ElasticContext

# Initialize the app with Bootstrap theme
DBC_CSS = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

app = Dash(__name__, 
           external_stylesheets=[
               dbc.themes.BOOTSTRAP, 
               dbc.icons.FONT_AWESOME, 
               DBC_CSS, 
               dmc.styles.DATES,
               dmc.styles.ALL,
            ],
            suppress_callback_exceptions=True)

app.title = "Malware BI"

esc = ElasticContext()