from dash import Input, Output, State, callback, Patch
from dash_bootstrap_templates import template_from_url
from app_instance import esc
from utils.commons import format_number, utc_to_local, local_to_utc
from utils.commons import geolocate_ip_list, iso2_to_iso3
from utils.graphs import empty_figure, adjust_palette
from utils.graphs import calculate_interval_and_range
from layouts.sidebar import theme_changer_aio
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def register_home_callbacks():   
    
    # Callback to update KPIs
    @callback(
        [
            Output("kpi1-value", "children"),
            Output("kpi2-value", "children"),
            Output("kpi3-value", "children"),
            Output("kpi4-value", "children"),
            Output("kpi5-value", "children"),
        ],
        [            
            Input("interval", "n_intervals"),
            Input('datetime-picker-start', 'value'),
            Input('datetime-picker-end', 'value'),
            Input("family-dropdown", "value")
        ],
        State("user-timezone", "data")
    )
    def update_kpis(_, start_date, end_date, selected_families, tz_data):
        # Convert date range to UTC
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()       

        families = None if not selected_families else [f.lower() for f in selected_families]

        # Fetch KPIs from the Gold index
        results = esc.fetch_gold(
                start_dt, 
                end_dt,
                grain="hourly",
                families=families
        )

        if results is None:
            return "--", "--", "--", "--", "--"

        # KPIs
        total_records = results["total_records"]
        total_records_malware = results["total_records_malware"]
        score_mean = results["avg_score"] if results["avg_score"] else 0
        family_num = results["family_num"]
        unique_domains = results["unique_domains"]
        unique_ips = results["unique_ips"]
        ioc_num = unique_domains + unique_ips

        return (
            format_number("%.1f", total_records),
            format_number("%.1f", total_records_malware),
            format_number("%.2f", score_mean),
            format_number("%d", family_num),
            format_number("%.1f", ioc_num)
        )

    # Update temporal histogram
    @callback(
        Output("histogram-graph", "figure"),
    [
        Input("interval", "n_intervals"),
        Input('datetime-picker-start', 'value'),
        Input('datetime-picker-end', 'value'),
        Input("screen-width", "data"),
        Input("family-dropdown", "value")
    ],
    [
        State(theme_changer_aio.ids.radio("theme"), "value"),
        State("switch", "value"),
        State("user-timezone", "data")
    ]
    )
    def update(_, start_date, end_date, screen_width,
               selected_families, theme, color_mode_switch_on, tz_data):
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"

        # Convert datetime values to ISO format and localize to UTC
        start_dt = local_to_utc(
            pd.to_datetime(start_date).isoformat(), tz_data
        )
        end_dt =  local_to_utc(
            pd.to_datetime(end_date).isoformat(), tz_data
        )     

        # Determine interval and normalize dates
        interval, start_dt, end_dt = calculate_interval_and_range(start_dt, end_dt)

        # Fetch data using dynamic interval
        df=pd.DataFrame(esc.fetch_aggreg_by_bins(
            start_dt,
            end_dt,
            interval=interval,
            size=10
        ))
        
        # Filter by selected families
        if selected_families not in (None, []):
            df = df[df["family"].isin(selected_families)]

        # Check if the DataFrame is empty or has no data
        if df.empty or df["count"].sum() == 0:
            return empty_figure()

        # Clean and normalize
        df = df[df["family"] != "Unknown"].sort_values(by="count", ascending=False)

         # Convert timestamps to local timezone        
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("UTC")

        # Assign colors
        family_order = (
            df.groupby("family")["count"]
            .sum()
            .sort_values(ascending=False)
            .index
            .tolist()
        )

        family_order.append("sin datos")
        df["family"] = pd.Categorical(df["family"], categories=family_order, ordered=True)
        palette = adjust_palette(len(family_order))
        color_map = {fam: palette[i] for i, fam in enumerate(family_order)}

        # Rebuild full time range
        date_range = pd.date_range(start=start_dt, end=end_dt, freq=interval)
        df_full = pd.DataFrame({"timestamp": date_range})        
        df = df_full.merge(df, on="timestamp", how="left")
        df["count"] = df["count"].fillna(0)
        df["avg_score"] = df["avg_score"].fillna(0)
        df["family"] = df["family"].fillna("sin datos")

        df = utc_to_local(df, "timestamp", tz_data)

        # Histrogram creation
        fig = px.histogram(
            df,
            x="timestamp",
            y="count",
            color="family",
            color_discrete_map=color_map,
            barmode="stack",                  
            title="Evolución temporal del malware",
            labels={
                "family": "Familia",
                "timestamp": "Período",
                "count": "Nº de muestras",
            },
            nbins=len(date_range),
            template=template_name
        )

        fig.update_layout(
            xaxis=dict(
                title="Tiempo",
                tickangle=0
            ),
            yaxis_title="Nº de Muestras",
            legend_title="Familia",
            bargap=0.1,
            margin=dict(l=40, r=20, t=60, b=60),
            showlegend=(screen_width >= 576)
        )

        return fig

    # Update graph-bar with families
    @callback(
        Output("graph-bar", "figure"),
        [             
            Input("interval", "n_intervals"),
            Input('datetime-picker-start', 'value'),
            Input('datetime-picker-end', 'value'),
            Input("family-dropdown", "value")
        ],
        [
            State(theme_changer_aio.ids.radio("theme"), "value"),
            State("switch", "value"),
            State("user-timezone", "data")
        ]
    )
    def update(_, start_date, end_date, selected_families, 
               theme, color_mode_switch_on, tz_data):
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"

         # Convert date range to UTC
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()

        df=pd.DataFrame(esc.fetch_aggreg_by_bins(
            start_dt,
            end_dt,
            size=20
        ))

        # Filter by selected families
        if selected_families not in (None, []):
            df = df[df["family"].isin(selected_families)]

        if df.empty or df["count"].sum() == 0:
            return empty_figure()

        filtered_df = df[df["family"] != "Unknown"]

        grouped_df = filtered_df.groupby("family", as_index=False)["count"].sum().nlargest(10, 'count')
        sorted_df = grouped_df.sort_values(by="count", ascending=False).reset_index(drop=True)

        # Generate color_map
        palette = adjust_palette(10)
        color_map = {family: palette[i] for i, family in enumerate(sorted_df["family"])}

        fig = px.bar(sorted_df, 
                     x="count",
                     y="family",
                     text="count",
                     color="family",
                     color_discrete_map=color_map,
                     template=template_name)

        fig.update_layout(
            title="Top 10 familias de malware", 
            xaxis_title="Nº de muestras",
            yaxis_title="Familias",
            showlegend=False,
            margin=dict(l=40, r=20, t=60, b=60),
        )

        # Modifica el texto del hover
        fig.update_traces(
            hovertemplate="<b>Familia:</b> %{y}<br>" +
                  "<b>Nº de muestras:</b> %{x}<br>" +
                  "<extra></extra>" 
        )

        return fig

    # Callback to update the map figure based on the selected time interval and theme
    @callback(
        Output("map", "figure"),
        [
            Input("interval", "n_intervals"),
            Input('datetime-picker-start', 'value'),
            Input('datetime-picker-end', 'value'),
            Input("screen-width", "data"),
            Input("family-dropdown", "value")
        ],
        State(theme_changer_aio.ids.radio("theme"), "value"),
        State("switch", "value"),
        State("user-timezone", "data")
    )
    def update_map(_, start_date, end_date, screen_width, selected_families, 
                   theme, color_mode_switch_on, tz_data):
        # Define template name based on the theme and color mode
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"

        # Convert date range to UTC
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()


        df = esc.fetch_ips_by_family_agg(start_dt, end_dt, selected_families)
        # Check if the DataFrame is empty or has no data
        if df.empty:
            return empty_figure()
    
        # Filter by selected families
        if selected_families not in (None, []):
            df = df[df["family"].isin(selected_families)]

        
        # Geolocate IPs
        geo_data = geolocate_ip_list(df["ip"].tolist())
        df_geo = pd.DataFrame(geo_data)
        df = df.merge(df_geo, on="ip", how="left")
        df = df.dropna(subset=["latitude", "longitude"])
        df["size_scaled"] = np.sqrt(df["count"]) * 5

        # Add jitter to latitude and longitude for better visibility
        df["latitude_jittered"] = df["latitude"] + np.random.uniform(-0.3, 0.3, size=len(df))
        df["longitude_jittered"] = df["longitude"] + np.random.uniform(-0.3, 0.3, size=len(df))

        # Create a scatter map using Plotly Express
        fig = px.scatter_map(
            data_frame=df,
            lat="latitude_jittered",  # Latitude for countries
            lon="longitude_jittered",  # Longitude for countries
            size="size_scaled",  # Size of circles corresponds to malware count
            color="family",  # Color differentiation based on malware families
            color_discrete_sequence=adjust_palette(df["family"].nunique()),
            hover_name="country",  # Country names in hover tooltip
            hover_data={"count": True, "family": True},  # Display malware count and family
            zoom=0.5,  # Initial zoom level
            center={"lat":20.92, "lon":17.28},  # Center the map
            template=template_name,  # Apply the selected template
            custom_data=["ip", "count", "country", "family"]
        )

        fig.update_layout(
            title="Orígenes de las amenazas",
            mapbox={
                "style": "open-street-map",
                "uirevision": "constant"
            },
            legend=dict(
               title="Familias",
               orientation="v",
               yanchor="top",
               y=1,
               xanchor="right",
               x=1,
               font=dict(size=10),
               bgcolor="rgba(255,255,255,0.7)",
               bordercolor="rgba(0,0,0,0.1)",
               borderwidth=1
            ),
            margin=dict(l=20, r=20, t=60, b=20),
        )

        fig.update_traces(
            hovertemplate=(
                "<b>Familia:</b> %{customdata[3]}<br>" +
                "<b>IP:</b> %{customdata[0]}<br>" +
                "<b>País:</b> %{customdata[2]}<br>" +
                "<b>Nº de muestras:</b> %{customdata[1]}<br>" +
                "<extra></extra>"
            )
        )

        return fig

    # Update graph-treemap with tactics
    @callback(
        Output("graph-treemap", "figure"),
        [ 
            Input("interval", "n_intervals"),        
            Input('datetime-picker-start', 'value'),
            Input('datetime-picker-end', 'value'),
            Input("family-dropdown", "value")
        ],
        [
            State(theme_changer_aio.ids.radio("theme"), "value"),
            State("switch", "value"),
            State("user-timezone", "data")
        ])
    def update(_, start_date, end_date, selected_families, 
               theme, color_mode_switch_on, tz_data
    ):
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"

        # Convert date range to UTC
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat() 

        families=None if selected_families in (None, []) else selected_families

        # Fetch data using the provided method
        df = pd.DataFrame(
            esc.fetch_ttp_count(
                start_dt, 
                end_dt,
                families,
                group_by_family=False
            )
        )

        # Check if the DataFrame is empty or has no data
        if df.empty or df["count"].sum() == 0:
            return empty_figure()
        
        df = df.groupby(by=['tactic','technique','platforms','families'])['count'].sum().reset_index()

        # Sort and extract the top 10 TTP
        df_sorted = df.sort_values(by='count', ascending=False)
        top_10 = df_sorted.head(10).reset_index(drop=True)        
        top_10["label_short"] = top_10["technique"].apply(
           lambda x: x[:25] + "..." if len(x) > 25 else x
        )

        top_10["familias_label"] = top_10["families"].apply(
            lambda x: f"<b>Familias:</b> {x}" if x else ""
        )

        # Generate color_map
        palette = adjust_palette(10)
        color_map = {tactic: palette[i] for i, tactic in enumerate(top_10["technique"])}        

        # Generate the treemap
        fig = px.treemap(
            top_10,
            path=[px.Constant("TTPs"), "tactic", "technique"],  # Hierarchical grouping
            values="count",
            title="Top 10 tácticas MITRE ATT&CK®",
            color="technique",
            color_discrete_map={'(?)':'white'} | color_map,
            custom_data=["label_short", "familias_label"],
            template=template_name
        )

        # Update layout and add details
        fig.update_traces(
            textfont=dict(size=12),            
            marker=dict(
                cornerradius=5,
                line=dict(
                    color="lightgrey",
                    width=0.5
                )
            ),
            texttemplate="%{customdata[0]}<br>%{value:,} (%{percentParent:.1%})",
            hovertemplate="<b>Técnica:</b> %{label}<br>" +
                          "<b>Nº de muestras:</b> %{value}<br>" +
                          "<b>Táctica:</b> %{parent}<br>" +
                          "%{customdata[1]}<br>" +  
                          "<extra></extra>"
        )
       
        fig.update_layout(
            margin=dict(l=20, r=20, t=60, b=20)
        )

        return fig


    # Update figures with the new theme much faster
    @callback(
        [
            Output("histogram-graph", "figure", allow_duplicate=True),
            Output("map", "figure", allow_duplicate=True),            
            Output("graph-bar", "figure", allow_duplicate=True),
            Output("graph-treemap", "figure", allow_duplicate=True),
        ],
        Input(theme_changer_aio.ids.radio("theme"), "value"),
        Input("switch", "value"),
        prevent_initial_call=True
    )
    def update_templates(theme, color_mode_switch_on):
        # Determinar el tema basado en el modo de color
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"

        # Crear el template común
        patched_figure = Patch()
        patched_figure["layout"]["template"] = pio.templates[template_name]

        # Retornar el mismo template para todas las salidas
        return patched_figure, patched_figure, patched_figure, patched_figure

