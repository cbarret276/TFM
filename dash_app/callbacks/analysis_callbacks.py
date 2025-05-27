from dash import Input, Output, State, callback
from dash_bootstrap_templates import template_from_url
from app_instance import esc
from layouts.sidebar import theme_changer_aio
from utils.commons import local_to_utc


def register_analysis_callbacks():

    # Callback para actualizar la tabla de muestras
    @callback(
        Output("analysis-table", "columnDefs"),
        Output("analysis-table", "rowData"),
        [
            Input("interval", "n_intervals"),
            Input('datetime-picker-start', 'value'),
            Input('datetime-picker-end', 'value'),
            Input("screen-width", "data"),
            Input("family-dropdown", "value"),
            Input("analysis-search", "value"),
            Input("analysis-filetype-dropdown", "value"),
            Input("analysis-country-dropdown", "value"),
            Input("analysis-score-slider", "value")
        ],
        [
            State(theme_changer_aio.ids.radio("theme"), "value"),
            State("switch", "value"),
            State("user-timezone", "data")
        ],
        prevent_initial_call=True
    )
    def update_analysis_table(
        _, start_date, end_date, screen_width, selected_families, 
        search, filetypes, countries, score_range,
        theme, dark_mode, tz_data
    ):
        # Theme handling
        theme_name = template_from_url(theme)
        template_name = theme_name if dark_mode else theme_name + "_dark"

        # UTC date conversion
        start_dt = local_to_utc(start_date, tz_data)
        end_dt = local_to_utc(end_date, tz_data)

        # Construcción de filtros
        filters = []
        if search:
            filters.append({"multi_match": {"query": search, "fields": ["sha256", "ips", "domains", "urls"]}})
        if start_dt and end_dt:
            filters.append({"range": {"created": {"gte": start_dt, "lte": end_dt}}})
        if selected_families:
            filters.append({"terms": {"family": selected_families}})
        if filetypes:
            filters.append({"terms": {"file_type": filetypes}})
        if countries:
            filters.append({"terms": {"origin_country": countries}})
        if score_range:
            filters.append({"range": {"score": {"gte": score_range[0], "lte": score_range[1]}}})

        query_body = {
            "query": {"bool": {"must": filters}} if filters else {"match_all": {}},
            "size": 10000,
        }

        # Consulta a Elasticsearch
        try:
            response = esc.es.search(index="bronze_mw_raw", body=query_body)
            hits = response["hits"]["hits"]
        except Exception as e:
            print("Error al consultar Elasticsearch:", e)
            return [], []

        # Formatear resultados
        rows = [hit["_source"] for hit in hits]

        column_defs = [
            {"headerName": "SHA256", "field": "sha256"},
            {"headerName": "Fecha", "field": "created"},
            {"headerName": "Score", "field": "score"},
            {"headerName": "Familia", "field": "family"},
            {"headerName": "Tipo", "field": "file_type"},
            {"headerName": "País", "field": "origin_country"},
            {"headerName": "IPs", "field": "ips"},
            {"headerName": "Dominios", "field": "domains"},
        ]

        return column_defs, rows or []
    
