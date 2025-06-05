from dash import Input, Output, State, callback, Patch
from dash_bootstrap_templates import template_from_url
from app_instance import esc
from layouts.sidebar import theme_changer_aio
from utils.graphs import empty_figure, adjust_palette
from utils.commons import shorten, local_to_utc
import plotly.graph_objects as go
import pandas as pd
import plotly.io as pio
import plotly.express as px

def register_tactics_callbacks():

    # Callback to update KPI
    @callback(
        [ 
            Output("tactics_kpi1-value", "children"),
            Output("tactics_kpi2-value", "children"),
            Output("tactics_kpi3-value", "children"),
            Output("tactics_kpi4-value", "children")
        ],
        [
            Input("interval", "n_intervals"),
            Input("datetime-picker-start", "value"),
            Input("datetime-picker-end", "value"),
            Input("family-dropdown", "value")
        ],
        State("user-timezone", "data"),
    )
    def update_tactics_kpis(
        _, start_datetime, end_datetime, selected_families, tz_name
    ):
        # Convert datetime values to ISO format and localize to UTC
        start_dt = local_to_utc(
            pd.to_datetime(start_datetime).isoformat(), tz_name
        )
        end_dt =  local_to_utc(
            pd.to_datetime(end_datetime).isoformat(), tz_name
        )    

        # Normalize family filter
        if selected_families:
            selected_families = [f.lower() for f in selected_families]

        # Fetch TTP data
        df = pd.DataFrame(
            esc.fetch_ttp_count(
                start_dt,
                end_dt,
                selected_families,
                group_by_family=True
            )
        )

        # Filter out empty
        if df.empty:
            return "--", "--", "--", "--"

        # KPI 1: Unique tactics
        num_tactics = df["tactic"].nunique()

        # KPI 2: Unique techniques
        num_techniques = df["technique"].nunique()

        # KPI 3: Techniques with "Impact" among their defenses
        num_impact = df[df["impact"].notna() & (df["impact"] != "")]["technique"].nunique()

        # KPI 4: Distinct platforms
        all_platforms = df["platforms"].dropna().str.split(",")
        flat_platforms = set(p.strip() for sublist in all_platforms for p in sublist)
        num_platforms = len(flat_platforms)

        return str(num_tactics), str(num_techniques), str(num_impact), str(num_platforms)


    # Callback to update the Sankey diagrams
    @callback(
        [
            Output("sankey-tactics-techniques", "figure"),
            Output("sankey-techniques-families", "figure")
        ],
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
    def update_dual_sankey(
        _, start_datetime, end_datetime, selected_families, theme, 
        switch_on, tz_name
    ):
        # Resolve theme
        theme_name = template_from_url(theme)
        template_name = theme_name if switch_on else theme_name + "_dark"

         # Convert datetime values to ISO format and localize to UTC
        start_dt = local_to_utc(
            pd.to_datetime(start_datetime).isoformat(), tz_name
        )
        end_dt =  local_to_utc(
            pd.to_datetime(end_datetime).isoformat(), tz_name
        )    

        # Normalize selected families
        if selected_families:
            selected_families = [f.lower() for f in selected_families]

        # Fetch data
        df = pd.DataFrame(
            esc.fetch_ttp_count(
                start_dt, end_dt,
                selected_families, 
                group_by_family=True
            )
        )

        if df.empty or df["count"].sum() == 0:
            return empty_figure(), empty_figure()

        df = df[df["families"].notna() & (df["families"].str.strip() != "")]

        # Optional: reinforce filtering
        if selected_families:
            df = df[df["families"].str.lower().isin(selected_families)]

        # Aggregate and limit techniques
        df = df.groupby(["tactic", "technique", "families"])["count"].sum().reset_index()
        top_techniques = df.groupby("technique")["count"].sum().nlargest(20).index
        df = df[df["technique"].isin(top_techniques)]

        # Build node sets
        tactic_nodes = df["tactic"].unique().tolist()
        technique_nodes = df["technique"].unique().tolist()
        family_nodes = sorted(df["families"].dropna().str.strip().str.lower().unique())
        short_techniques = [shorten(t) for t in technique_nodes]

        # Sankey 1: Tácticas → Técnicas
        labels_tt = tactic_nodes + short_techniques
        palette_tt = adjust_palette(len(labels_tt))
        idx_tt = {name: i for i, name in enumerate(tactic_nodes)}
        idx_tt.update({tech: i + len(tactic_nodes) for i, tech in enumerate(technique_nodes)})

        sources_tt, targets_tt, values_tt = [], [], []
        for _, row in df.iterrows():
            tac = row["tactic"]
            tech = row["technique"]
            if tac in idx_tt and tech in idx_tt:
                sources_tt.append(idx_tt[tac])
                targets_tt.append(idx_tt[tech])
                values_tt.append(row["count"])

        fig_tt = go.Figure(go.Sankey(
            node=dict(label=labels_tt, color=palette_tt, pad=30, thickness=20),
            link=dict(source=sources_tt, target=targets_tt, value=values_tt)
        ))
        fig_tt.update_layout(
            title="Objetivos del ataque y técnicas",
            template=template_name,
            margin=dict(l=10, r=10, t=40, b=20)
        )

        # Sankey 2: Técnicas → Familias
        labels_tf = short_techniques + family_nodes
        palette_tf = adjust_palette(len(labels_tf))
        idx_tf = {tech: i for i, tech in enumerate(technique_nodes)}
        idx_tf.update({fam: i + len(technique_nodes) for i, fam in enumerate(family_nodes)})

        sources_tf, targets_tf, values_tf = [], [], []
        for _, row in df.iterrows():
            tech = row["technique"]
            fam_clean = row["families"].strip().lower()
            if tech in idx_tf and fam_clean in idx_tf:
                sources_tf.append(idx_tf[tech])
                targets_tf.append(idx_tf[fam_clean])
                values_tf.append(row["count"])

        fig_tf = go.Figure(go.Sankey(
            node=dict(label=labels_tf, color=palette_tf, pad=30, thickness=20),
            link=dict(source=sources_tf, target=targets_tf, value=values_tf)
        ))
        fig_tf.update_layout(
            title="Técnicas utilizadas y familias de malware",
            template=template_name,
            margin=dict(l=10, r=10, t=40, b=20)
        )

        return fig_tt, fig_tf

    # Callback to update temporal techniques graph
    @callback(
        Output("temporal-techniques-graph", "figure"),
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
    def update_temporal_techniques(
        _, start_datetime, end_datetime, screen_width,
        selected_families, theme, switch_on, tz_name
    ):
        template_name = template_from_url(theme)
        template_name = template_name if switch_on else template_name + "_dark"

        # Convert datetime values to ISO format and localize to UTC
        start_dt = local_to_utc(
            pd.to_datetime(start_datetime).isoformat(), tz_name
        )
        end_dt =  local_to_utc(
            pd.to_datetime(end_datetime).isoformat(), tz_name
        )

        # Normalize family filter
        if selected_families:
            selected_families = [f.lower() for f in selected_families]

        # Get data
        df = esc.fetch_techniques_over_time(
            start_dt, end_dt,
            interval="1h",
            families=selected_families
        )

        if df.empty:
            return empty_figure()

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Order tactics by frequency 
        tactic_order = df.groupby("tactic")["count"].sum().sort_values(ascending=False).index.tolist()
        df["tactic"] = pd.Categorical(df["tactic"], categories=tactic_order, ordered=True)
        color_map = adjust_palette(len(tactic_order))

        fig = px.histogram(
            df,
            x="timestamp",
            y="count",
            color="tactic",
            color_discrete_sequence=color_map,
            barmode="stack",
            template=template_name,
            title="Evolución temporal de técnicas observadas"
        )

        fig.update_layout(
            margin=dict(l=40, r=20, t=50, b=40),
            xaxis_title="Tiempo",
            yaxis_title="Nº de muestras",
            showlegend=(screen_width >= 576),
            legend_title="Táctica"
        )

        fig.update_traces(
            hovertemplate="Táctica: %{fullData.name}<br>" +
                        "Fecha: %{x}<br>" +
                        "Nº de muestras: %{y}<extra></extra>"
        )

        return fig


    # Callback to update heatmap técnicas-families  
    @callback(
        Output("heatmap-tactics-families", "figure"),
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
    def update_heatmap(
        _, start_datetime, end_datetime, screen_width,
        selected_families, theme, switch_on, tz_name
    ):
        theme_name = template_from_url(theme)
        template_name = theme_name if switch_on else theme_name + "_dark"

        # Convert datetime values to ISO format and localize to UTC
        start_dt = local_to_utc(
            pd.to_datetime(start_datetime).isoformat(), tz_name
        )
        end_dt =  local_to_utc(
            pd.to_datetime(end_datetime).isoformat(), tz_name
        )    

        # Normalize family filter
        if selected_families:
            selected_families = [f.lower() for f in selected_families]

        df = pd.DataFrame(
            esc.fetch_ttp_count(
                start_dt,
                end_dt,
                selected_families,
                group_by_family=True
            )
        )

        if df.empty:
            return empty_figure()

        df=df[df["families"] != "Desconocida"]

        # Optional: filter out empty families
        if selected_families:
            df = df[df["families"].str.lower().isin(selected_families)]

        # Pivot para construir el heatmap
        df_pivot = df.pivot_table(
            index="tactic",
            columns="families",
            values="count",
            aggfunc="sum",
            fill_value=0
        )

        short_y = [shorten(y, max_len=30) for y in df_pivot.index]

        fig = px.imshow(
            df_pivot,
            labels=dict(x="Familia", y="Táctica", color="Nº muestras"),
            x=df_pivot.columns,
            y=short_y,
            text_auto=True,
            color_continuous_scale=['#f2f6fa','#1f77b4'],
        )

        fig.update_layout(
            title="Tácticas y familias",
            autosize=True,
            template=template_name,
            margin=dict(l=20, r=0, t=50, b=20)
        )

        if screen_width < 576:
            fig.update_layout(
                coloraxis_colorbar=dict(
                    orientation="h",
                    x=0.25,
                    xanchor="center",
                    y=-0.2
                )
            )

        return fig

    # Callback to update themes
    @callback(
        Output("sankey-tactics-techniques", "figure", allow_duplicate=True),
        Output("sankey-techniques-families", "figure", allow_duplicate=True),
        Input(theme_changer_aio.ids.radio("theme"), "value"),
        Input("switch", "value"),
        prevent_initial_call=True
    )
    def update_themes(theme, color_mode_switch_on):
        theme_name = template_from_url(theme)
        template_name = theme_name if color_mode_switch_on else theme_name + "_dark"
        patched_figure = Patch()
        patched_figure["layout"]["template"] = pio.templates[template_name]
        return patched_figure, patched_figure
