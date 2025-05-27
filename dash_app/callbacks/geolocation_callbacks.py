from dash import Input, Output, State, callback, Patch
from plotly import io as pio
import plotly.graph_objects as go
import pandas as pd
from dash_bootstrap_templates import template_from_url
from layouts.sidebar import theme_changer_aio
from utils.commons import local_to_utc, iso2_to_iso3
from utils.graphs import empty_figure
from app_instance import esc

def register_geolocation_callbacks():

    @callback(
        Output("geo-map", "figure"),
        [
            Input("interval", "n_intervals"),
            Input('datetime-picker-start', 'value'),
            Input('datetime-picker-end', 'value'),
            Input("screen-width", "data"),
            Input("family-dropdown", "value"),
            Input("geo-view", "value"),
        ],
          [
            State(theme_changer_aio.ids.radio("theme"), "value"),
            State("switch", "value"),
            State("user-timezone", "data")
        ],
    )
    def update_geo_map(
        _, start_date, end_date, screen_width, selected_families, view_type,
        theme, dark_mode, tz_data
    ):
        # Set theme and template
        theme_name = template_from_url(theme)
        template_name = theme_name if dark_mode else theme_name + "_dark"

        # Convert datetime values to ISO format and localize to UTC
        start_dt = local_to_utc(
            pd.to_datetime(start_date).isoformat(), tz_data
        )
        end_dt =  local_to_utc(
            pd.to_datetime(end_date).isoformat(), tz_data
        )    

        # Datos simulados
        df = pd.DataFrame({
            "country_code": ["USA", "FRA", "CHN", "RUS", "BRA"],
            "country": ["Estados Unidos", "Francia", "China", "Rusia", "Brasil"],
            "samples": [120, 85, 300, 230, 150],
            "ips": [50, 22, 180, 140, 75],
            "ttps": ["T1059", "T1027", "T1059", "T1203", "T1082"]
        })

        # Selector del tipo de visualización
        if view_type == "samples":            
            # Get sample count by country
            df = esc.fetch_sample_count_by_country(start_dt, end_dt, selected_families)
            if df.empty:
                return empty_figure()
            # Convert from ISO-2 to ISO-3
            df["country_code"] = df["country"].apply(iso2_to_iso3)
            df = df[df["country_code"].notna()]            
            z_field = "sample_count"
            values = df[z_field]
            title = "Muestras de malware por país"
            color_title = "Muestras"
            colorscale = [[0, "#ffe6cc"], [1, "#ff7f0e"]]
                    

        elif view_type == "ips":
            df = esc.build_ip_enrichment_dataframe(
                start_dt, end_dt, selected_families, enrich=False
            )
            if df.empty:
                return empty_figure()
            df = df[df["country"].notna()]
            country_agg = df.groupby(["country","country_code"], as_index=False).agg({"ip": "count"})
            country_agg.rename(columns={"ip": "ip_count"}, inplace=True)
            df = country_agg
            z_field = "ip_count"
            values = country_agg[z_field]
            title = "IPs maliciosas por país"
            color_title = "IPs"
            colorscale = [
                [0.0, "#fde0dc"],  # rojo muy claro
                [0.25, "#f9bdbb"],
                [0.5, "#ef5350"],
                [0.75, "#e53935"],
                [1.0, "#b71c1c"]   # rojo intenso
            ]

        else:
            df["ttp_freq"] = df["ttps"].map({
                "T1059": 5, "T1027": 3, "T1203": 4, "T1082": 2
            }).fillna(1)
            z_field = "ttp_freq"
            color_title = "TTP"
            title = "Frecuencia de TTP dominante"
            values = df[z_field]
            colorscale=[[0, "#dceeff"], [1, "#1f77b4"]]


        # Crear figura con go.Choropleth
        fig = go.Figure(data=go.Choropleth(
            locations=df["country_code"],
            z=values,
            text=df["country"],
            colorscale=colorscale,
            zmin=0,
            zmax=values.max(),
            autocolorscale=False,
            reversescale=False,
            marker_line_color='gray',
            marker_line_width=0.5,
            colorbar=dict(
                title=color_title,
                thickness=8,
                len=0.25,
                x=0.97,
                y=0.55,
                xanchor="right",
                yanchor="middle",
                tickfont=dict(size=10)
            )
        ))

        fig.update_layout(
            autosize=True,
            template=template_name,            
            margin=dict(l=10, r=10, t=10, b=20),
            geo=dict(
                showframe=False,
                showcoastlines=False,
                showcountries=True,
                countrycolor="lightgray", 
                projection_type='equirectangular'
            ),
        )

        return fig
    
    # Callback to update themes
    @callback(
        Output("geo-map", "figure", allow_duplicate=True),
        Input(theme_changer_aio.ids.radio("theme"), "value"),
        Input("switch", "value"),
        prevent_initial_call=True
    )
    def update_themes(theme, color_mode_switch_on):
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"
        patched_figure = Patch()
        patched_figure["layout"]["template"] = pio.templates[template_name]
        return patched_figure
