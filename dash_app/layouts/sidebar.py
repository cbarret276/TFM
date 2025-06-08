from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO

theme_changer_aio =  ThemeChangerAIO(
            aio_id="theme",
            button_props={
                "children": [
                                html.I(className="fas fa-palette"),
                                html.Span("Cambiar tema", id="span-theme-switch", className="ms-1")
                             ],
                "className": "btn-theme-changer" 
            }
        )

color_mode_switch =  html.Span(
    [
        dbc.Label(className="fa fa-moon fa-switch", html_for="switch"),
        dbc.Switch(id="switch", value=True, className="d-inline-block ms-1"),
        dbc.Label(className="fa fa-sun fa-switch", html_for="switch"),
    ],
    className="span-config"
)

theme_changer =  html.Span(
    [
       theme_changer_aio
    ],
    className="span-config"
)

sidebar = html.Div(
    [
        html.Div(
            [
                html.Img(src="/assets/logo.png", style={"width": "3rem"}),
                html.H4("MalwareBI", className="ms-2"),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.I(className="fas fa-chart-pie me-2"), 
                        html.Span("Panorámica")
                    ],
                    href="/",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-chess-knight me-2"),
                        html.Span("Tácticas"),
                    ],
                    href="/tactics",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Span("Indicadores"),
                    ],
                    href="/indicators",
                    active="exact",
                ),  
                dbc.NavLink(
                    [
                        html.I(className="fas fa-globe me-2"),
                        html.Span("Geografía"),
                    ],
                    href="/geolocation",
                    active="exact",
                ),  
                dbc.NavLink(
                    [
                        html.I(className="fas fa-search me-2"),
                        html.Span("Análisis"),
                    ],
                    href="/analysis",
                    active="exact",
                ), 
            ],
            vertical=True,
            pills=True,
        ),
        html.Hr(),
        color_mode_switch,        
        theme_changer,
    ],
    className="sidebar",
)

sidebar_mobile = html.Div(
    [
        dbc.Nav(
            [
                dbc.NavLink([html.I(className="fas fa-chart-pie me-2"), html.Span("Panorámica")], href="/", active="exact"),
                dbc.NavLink([html.I(className="fas fa-chess-knight me-2"), html.Span("Tácticas")], href="/tactics", active="exact"),
                dbc.NavLink([html.I(className="fas fa-exclamation-triangle me-2"), html.Span("Indicadores")], href="/indicators", active="exact"),
                dbc.NavLink([html.I(className="fas fa-globe me-2"), html.Span("Geografía")], href="/geolocation", active="exact"),
                dbc.NavLink([html.I(className="fas fa-clock me-2"), html.Span("Análisis")], href="/analysis", active="exact"),
            ],
            vertical=True,
            pills=True
        ),
        
    ]
)