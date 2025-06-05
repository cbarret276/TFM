from dash import Input, Output, State, callback, html, Patch
from dash_bootstrap_templates import template_from_url
from app_instance import esc
from layouts.sidebar import theme_changer_aio
from utils.graphs import empty_figure, adjust_palette
from utils.graphs import generate_wordcloud, custom_dark_template, build_safe_template
from utils.commons import geolocate_ip_list, normalize_series
from utils.commons import format_number
import plotly.graph_objects as go
import pandas as pd
import plotly.io as pio
import plotly.express as px
import copy


def register_indicators_callbacks():
    # Callback to update the IOCs KPI
    @callback(
        [
            Output("ioc_kpi1-value", "children"),  # Total de IOCs
            Output("ioc_kpi2-value", "children"),  # IPs únicas
            Output("ioc_kpi3-value", "children"),  # Dominios únicos
            Output("ioc_kpi4-value", "children")   # Score medio
        ],
        [
            Input("interval", "n_intervals"),
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("family-dropdown", "value")
        ],
        [
            State("user-timezone", "data")
        ]
    )
    def update_kpis_ioc(_, start_date, end_date, selected_families, tz_data):
        # Convert date range to UTC
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        
        # Normalize family filter
        families = None if not selected_families else [f.lower() for f in selected_families]

        # Fetch IOC data for KPI calculation
        results = esc.fetch_gold(start_dt, end_dt, families=families)

        if results is None:
            return ["--", "--", "--", "--"]

        # KPIs        
        score_mean = results["avg_score"] if results["avg_score"] else 0
        unique_domains = results["unique_domains"]
        unique_ips = results["unique_ips"]
        ioc_num = unique_domains + unique_ips

        return (
            format_number("%.1f", ioc_num),
            format_number("%.1f", unique_ips),
            format_number("%.1f", unique_domains),
            format_number("%.2f", score_mean),
        )


    # Callback to update the domain wordcloud (IOCs)
    @callback(
        Output("wordcloud-container", "children"),
        [
            Input("interval", "n_intervals"),
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("screen-width", "data"),
            Input("family-dropdown", "value"),
            Input("switch", "value"),
        ],
        [
            State("user-timezone", "data")
        ]
    )
    def update_domain_wordcloud(
        _, start_date, end_date, screen_width,
        selected_families, switch_on, tz_data
    ):
        # Resolve the current visual theme (light or dark)
        theme_mode = "light" if switch_on else "dark"

        # Normalize timezone to UTC for backend filtering
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()

        # Normalize family filter (not strictly required for domain wordcloud but kept for consistency)
        families = None if not selected_families else [f.lower() for f in selected_families]

        # Fetch aggregated domain frequencies from Elasticsearch
        _, domain_counts, _ = esc.fetch_aggregated_iocs(
            start_dt, end_dt, families, size=50
        )

        # Handle empty result
        if not domain_counts:
            return html.Div(
                "Sin datos",
                className="text-muted text-center",
                style={
                    "minHeight": "400px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                }
            )

        # Format data as frequency dict
        frequencies = {item["domain"]: item["count"] for item in domain_counts}
        
        # Generate base64 image for wordcloud
        img_base64 = generate_wordcloud(frequencies, screen_width, theme=theme_mode)
        return html.Div([
            html.H5("Dominios más frecuentes", className="card-kpi-title"),
            html.Img(
                src=f"data:image/png;base64,{img_base64}",
                className="img-fluid",
                style={"maxHeight": "360px", "objectFit": "contain"}
            )
        ], style={"minHeight": "400px","width": "100%", "display": "flex", "flexDirection": "column"})
    

    @callback(
        Output("top10-direcciones-ip", "figure"),
        [
            Input("interval", "n_intervals"),
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("family-dropdown", "value")
        ],
        [
            State(theme_changer_aio.ids.radio("theme"), "value"),
            State("switch", "value"),
            State("user-timezone", "data")
        ]
    )
    def update_top_ips(_, start_date, end_date, selected_families,
                    theme, switch_on, tz_data):
        # Resolve theme
        theme_name = template_from_url(theme)
        template_name = theme_name if switch_on else theme_name + "_dark"

        # Time range to UTC
        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()

        families = None if not selected_families else [f.lower() for f in selected_families]

        # Fetch IP counts from Elasticsearch
        ip_counts, _, _ = esc.fetch_aggregated_iocs(start_dt, end_dt, families)

        # Convert to DataFrame
        df = pd.DataFrame(ip_counts)

        if df.empty or df["count"].sum() == 0:
            return empty_figure()

        # Keep top 10 and sort
        df = df.nlargest(10, 'count').sort_values("count", ascending=False)

        # Build color map
        palette = adjust_palette(len(df))
        color_map = {ip: palette[i] for i, ip in enumerate(df["ip"])}

        # Create bar chart
        fig = px.bar(
            df,
            x="count",
            y="ip",
            orientation="h",
            color="ip",
            color_discrete_map=color_map,
            text="count",
            template=template_name
        )

        fig.update_layout(
            title="Top 10 direcciones IP",
            xaxis_title="Nº de apariciones",
            yaxis_title="Dirección IP",
            showlegend=False,
            margin=dict(l=40, r=20, t=60, b=60)
        )

        fig.update_traces(
            hovertemplate="IP: %{y}<br>Frecuencia: %{x}<extra></extra>"
        )

        return fig
    

    # Callback to update the Sankey diagram (IOC - ThreatFox)
    @callback(
        Output("sankey-ioc-threatfox", "figure"),
        [
            Input("interval", "n_intervals"),
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("family-dropdown", "value")
        ],
        [
            State(theme_changer_aio.ids.radio("theme"), "value"),
            State("switch", "value"),
            State("user-timezone", "data")
        ]
    )
    def update_sankey_ioc_threatfox(_, start_date, end_date, selected_families, theme, switch_on, tz_data):
        theme_name = template_from_url(theme)
        template_name = theme_name if switch_on else theme_name + "_dark"

        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC")
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC")
        families = None if not selected_families else [f.lower() for f in selected_families]

        df = esc.build_ip_enrichment_dataframe(start_dt, end_dt, families=families)

        if df.empty or df["count"].sum() == 0:
            return empty_figure()

        df = df.dropna(subset=["confidence_level", "threat_type", "malware", "country"])
        df["confidence_level"] = df["confidence_level"].astype(str)

        all_labels = pd.unique(df[["ip", "confidence_level", "threat_type", "malware", "country"]].values.ravel())
        idx_map = {label: i for i, label in enumerate(all_labels)}
        palette = adjust_palette(len(all_labels))

        sources, targets, values = [], [], []
        for col1, col2 in zip(["ip", "confidence_level", "threat_type", "malware"],
                            ["confidence_level", "threat_type", "malware", "country"]):
            grouped = df.groupby([col1, col2])["count"].sum().reset_index()
            for _, row in grouped.iterrows():
                src, tgt = row[col1], row[col2]
                if src in idx_map and tgt in idx_map:
                    sources.append(idx_map[src])
                    targets.append(idx_map[tgt])
                    values.append(row["count"])

        fig = go.Figure(go.Sankey(
            node=dict(
                label=all_labels.tolist(),
                color=palette,
                pad=25,
                thickness=20,
                line=dict(color="black", width=0.5)
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            )
        ))

        fig.update_layout(
            title="Análisis contextual de las IPs maliciosas",
            template=template_name,
            margin=dict(l=10, r=10, t=40, b=20)
        )

        return fig

    # Callback to update the IP map (top 50)
    @callback(
        Output("map-top50-ips", "figure"),
        [
            Input("interval", "n_intervals"),
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("screen-width", "data"),
            Input("family-dropdown", "value")
        ],
        [
            State(theme_changer_aio.ids.radio("theme"), "value"),
            State("switch", "value"),
            State("user-timezone", "data")
        ]
    )
    def update_ip_map(_, 
                    start_date, end_date, screen_width,
                    selected_families, theme, color_mode_switch_on, tz_data):
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"
       
        if not color_mode_switch_on:
            template_map = custom_dark_template(build_safe_template(template_name))
        else:
            template_map = build_safe_template(template_name)

        start_dt = pd.to_datetime(start_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        end_dt = pd.to_datetime(end_date).tz_localize(tz_data).tz_convert("UTC").isoformat()
        families = None if not selected_families else [f.lower() for f in selected_families]

        # Get top IPs
        ip_counts, _, _ = esc.fetch_aggregated_iocs(start_dt, end_dt, families)

        if ip_counts is None or not ip_counts:
            return empty_figure()

        df = pd.DataFrame(ip_counts).nlargest(100, "count")

        # Geolocate
        enriched = geolocate_ip_list(df["ip"].tolist())
        geo_df = pd.DataFrame(enriched).merge(df, on="ip")

         # Aggregate by country
        df_country = geo_df.groupby("country", as_index=False).agg({
            "count": "sum",
            "latitude": "first",  # One point per country
            "longitude": "first"
        })


        df_country["size_normalized"] = normalize_series(df_country["count"], 20, 40)
        df_country["label"] = df_country["country"] + "<br>(" + df_country["count"].astype(str) +")" 

        df_country = df_country.rename(columns={
            "country": "País",
            "count": "Nº muestras"
        })

        # Generate interactive map
        fig = px.scatter_map(
            data_frame=df_country,
            lat="latitude",
            lon="longitude",
            size="size_normalized",
            text="label",
            color="País",
            color_discrete_sequence=adjust_palette(df_country["País"].nunique()),
            zoom=0.5,  # Initial zoom level
            center={"lat":20.92, "lon":17.28},  # Center the map
            hover_data={
                "Nº muestras": True,
                "País": True,
                "latitude": False,         # Oculta
                "longitude": False,        # Oculta
                "size_normalized": False,  # Oculta
                "label": False             # Oculta si ya está en 'text'
            },
            template=template_map
        )

        # Update layout
        fig.update_layout(
            title="Distribución geográfica Top Países IoC",
            mapbox={                        
                "style": "open-street-map",  # style of the map
                "uirevision": "constant"
            },
            legend=dict(
               title="Países",
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
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig


    # Callback to update themes
    @callback(
        Output("map-top50-ips", "figure", allow_duplicate=True),
        Output("top10-direcciones-ip", "figure", allow_duplicate=True),
        Output("sankey-ioc-threatfox", "figure", allow_duplicate=True),
        Input(theme_changer_aio.ids.radio("theme"), "value"),
        Input("switch", "value"),
        prevent_initial_call=True
    )
    def update_themes(theme, color_mode_switch_on):
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"

        template_general = build_safe_template(template_name)
        template_map = custom_dark_template(build_safe_template(template_name))

        patched_figure = Patch()
        patched_figure["layout"]["template"] = template_general
        patched_figure_map = Patch()
        patched_figure_map["layout"]["template"] = template_map
        return patched_figure_map, patched_figure, patched_figure

