# Import packages
from app_instance import app
from dash import dcc, html
from dash_mantine_components import MantineProvider 
import uuid
from layouts.sidebar import sidebar
from layouts.top_navbar import top_navbar, mobile_sidebar
from layouts.dummy_components import get_dummy_components
from callbacks.commons_callbacks import register_filters_callbacks
from callbacks.commons_callbacks import register_render_page_content
from callbacks.home_callbacks import register_home_callbacks
from callbacks.tactics_callbacks import register_tactics_callbacks
from callbacks.indicators_callbacks import register_indicators_callbacks
from callbacks.analysis_callbacks import register_analysis_callbacks
from callbacks.geolocation_callbacks import register_geolocation_callbacks

# App layout with sidebar, header, and main content
def serve_layout():
    session_id = str(uuid.uuid4())

    return MantineProvider(  # Wrapping the layout with MantineProvider
        children=html.Div([
            dcc.Store(data=session_id, id='session-id'),
            dcc.Store(id="screen-width", data=768),
            dcc.Store(id="global-filters", storage_type="session"),
            dcc.Store(id="user-timezone", storage_type="local"),
            dcc.Interval(id='interval', interval=60000, n_intervals=0),
            dcc.Location(id="url"),
            top_navbar,
            mobile_sidebar,
            sidebar,
            html.Div(id="page-content", className="content"),
            get_dummy_components()
        ])
    )

app.layout = serve_layout()

# Register callbacks
register_render_page_content()
register_filters_callbacks()
register_home_callbacks()
register_indicators_callbacks()
register_tactics_callbacks()
register_geolocation_callbacks()
register_analysis_callbacks()


# Run the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5173)
    

