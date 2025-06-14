from dash import Input, Output, State, callback, Patch, no_update
from dash_bootstrap_templates import template_from_url
from app_instance import esc
from utils.commons import format_number, utc_to_local, local_to_utc
from utils.commons import geolocate_ip_list, shorten
from utils.graphs import empty_figure, adjust_palette
from utils.graphs import calculate_interval_and_range
from utils.graphs import custom_dark_template, build_safe_template
from layouts.sidebar import theme_changer_aio
import plotly.express as px
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

        # KPIs
        total_records = results["total_records"]
        total_records_malware = results["total_records_malware"]
        score_mean = results["avg_score"] if results["avg_score"] else 0
        family_num = results["family_num"]
        
        df = esc.fetch_iocs_counts_by_family(
            start_dt, 
            end_dt, 
            families,
            size=100
        )
        # Check if the DataFrame is empty or has no data
        if df.empty:
            unique_domains = unique_ips = 0
        else:
            unique_domains = df["ip_count"].sum()
            unique_ips = df["domain_count"].sum()
        ioc_num = unique_domains + unique_ips

        return (
            format_number("%.1f", total_records),
            format_number("%.1f", total_records_malware),
            format_number("%.2f", score_mean),
            format_number("%d", family_num),
            format_number("%d", ioc_num)
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
            title="Evolución temporal de familias",
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
            legend=dict(
               title="Familias",
            ),
            bargap=0.1,
            margin=dict(l=40, r=20, t=60, b=60),
            showlegend=(screen_width >= 576)
        )

        return fig

    # Clic and filter by family
    @callback(
        Output("family-dropdown", "value", allow_duplicate=True),
        Input("histogram-graph", "clickData"),
        State("histogram-graph", "figure"),
        prevent_initial_call=True
    )
    def update_family_dropdown_from_histogram(clickData, figure):
        if not clickData or "points" not in clickData:
            return no_update

        curve_number = clickData["points"][0].get("curveNumber")
        if curve_number is None:
            return no_update

        try:
            family = figure["data"][curve_number]["name"]
            return [family]
        except (IndexError, KeyError, TypeError):
            return no_update

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
            size=10
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
            hovertemplate="Familia: %{y}<br>" +
                  "Nº de muestras: %{x}<br>" +
                  "<extra></extra>" 
        )

        return fig


    # Click in family grahpbar and update filter by selected family
    @callback(
        Output("family-dropdown", "value", allow_duplicate=True),
        Input("graph-bar", "clickData"),
        State("family-dropdown", "value"),
        prevent_initial_call=True
    )
    def update_family_dropdown_from_bar(clickData, current_value):
        if not clickData or "points" not in clickData:
            return no_update

        selected_family = clickData["points"][0]["y"]
        return [selected_family]

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
        if not color_mode_switch_on:
            template_map = custom_dark_template(build_safe_template(template_name))
        else:
            template_map = build_safe_template(template_name)

        # Convert date range to UTC
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()

        df = esc.fetch_ips_by_family_agg(
            start_dt, end_dt, 
            selected_families, 
            size_family=20,
            size_ips=70
        )
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
            lat="latitude_jittered",  
            lon="longitude_jittered", 
            size="size_scaled",  # Size of circles corresponds to malware count
            color="family",  # Color differentiation based on malware families
            color_discrete_sequence=adjust_palette(df["family"].nunique()),
            hover_name="country",  
            hover_data={"count": True, "family": True},  
            text="ip",
            zoom=0.5,  # Initial zoom level
            center={"lat":20.92, "lon":17.28},  # Center the map
            template=template_map,  
            custom_data=["ip", "count", "country", "family"]
        )

        fig.update_layout(
            title="Top IOCs (IPs) por países",
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
               font=dict(size=11),
               bgcolor="rgba(255,255,255,0.7)",
               bordercolor="rgba(0,0,0,0.1)",
               borderwidth=1
            ),
            showlegend=(screen_width >= 576),
            margin=dict(l=20, r=20, t=60, b=20),
        )

        fig.update_traces(
            hovertemplate=(
                "Familia: %{customdata[3]}<br>" +
                "IP: %{customdata[0]}<br>" +
                "País: %{customdata[2]}<br>" +
                "Nº de muestras: %{customdata[1]}<br>" +
                "<extra></extra>"
            )
        )

        return fig

    # Click in map update family filter 
    @callback(
        Output("family-dropdown", "value", allow_duplicate=True),
        Input("map", "clickData"),
        prevent_initial_call=True
    )
    def update_family_dropdown_from_map(clickData):
        if not clickData or "points" not in clickData:
            return no_update

        family = clickData["points"][0].get("customdata", [None, None, None, None])[3]
        if family:
            return [family]

        return no_update

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
            lambda x: f"Familias: {shorten(x, max_len=80)}" if x else ""
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
            custom_data=["label_short", "familias_label", "families"],
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
            hovertemplate="Técnica: %{label}<br>" +
                          "Nº de muestras: %{value}<br>" +
                          "Táctica: %{parent}<br>" +
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
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"

        template_general = build_safe_template(template_name)
        template_map = custom_dark_template(build_safe_template(template_name))

        patched_figure = Patch()
        patched_figure["layout"]["template"] = template_general
        patched_figure_map = Patch()
        patched_figure_map["layout"]["template"] = template_map
        return patched_figure, patched_figure_map, patched_figure, patched_figure

