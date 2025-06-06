import dash_bootstrap_components as dbc
import subprocess

footer = dbc.Row(
    dbc.Col(
        dbc.NavLink(
            f"Versión 0.1.0 · Ver en GitHub",
            href="https://github.com/cbarret276/TFM",
            target="_blank",
            className="text-end",
            style={"marginRight": "4rem"}
        ),
        width=12,
        className="mt-1 mb-3"
    ),
    className="justify-content-center"
)