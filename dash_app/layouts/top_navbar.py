from dash import html
import dash_bootstrap_components as dbc
from layouts.sidebar import sidebar_mobile

# Top navigation bar, visible only on extra small (xs) and small (sm) screens
top_navbar = dbc.Navbar(
    dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    html.I(className="fa fa-bars"),
                    id="btn-toggle-menu",
                    n_clicks=0,
                    className="ms-3"
                ),
                width="auto"
            ),
            dbc.Col(
                html.Img(src="/assets/logo.png", style={"height": "2rem"}),
                width="auto"
            ),
            dbc.Col(
                html.H4("MalwareBI", className="text-white mb-0 ms-2"),
                width="auto"
            )
        ],
        align="center",
        justify="start",
        className="gx-2",
        style={"width": "100%", "margin": 0}
    ),
    color="primary",
    dark=True,
    className="d-md-none"
)


# Offcanvas sidebar menu for mobile devices
mobile_sidebar = dbc.Offcanvas(
    id="offcanvas-menu",
    title="Menu",  # Title of the offcanvas menu
    is_open=False,  # Initially closed
    children=sidebar_mobile,  # resto del contenido de navegación móvil
    placement="start",  # Sidebar slides in from the left
    className="d-md-none",  # Visible only on extra small (xs) and small (sm) screens
    style={"width": "16rem"}  # Set the width of the offcanvas menu
)