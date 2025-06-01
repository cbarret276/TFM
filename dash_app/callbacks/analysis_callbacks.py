from dash import Input, Output, State, callback
from dash_bootstrap_templates import template_from_url
from app_instance import esc
from layouts.sidebar import theme_changer_aio
from utils.commons import local_to_utc, iso2_to_country_name


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
            filters.append({"multi_match": {"query": search, "fields": [
                "id", "sha256", "delivery_method", 
                "ips", "domains", "tags", "ttp"
            ]}})
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
            {"headerName": "Id", "field": "id", "width": 170},
            {"headerName": "Fecha", "field": "created", "width": 200},
            {"headerName": "Score", "field": "score", "width": 60},
            {"headerName": "Tags", "field": "tags", "width": 170},
            {"headerName": "Técnicas", "field": "ttp", "width": 150},
            {"headerName": "Familia", "field": "family", "width": 120},
            {"headerName": "Propagación", "field": "delivery_method", "width": 130},
            {"headerName": "Tipo fichero", "field": "file_type", "width": 120},
            {"headerName": "Tamaño fichero", "field": "file_size", "width": 120},
            {"headerName": "Origen", "field": "origin_country", "width": 100},
            {"headerName": "IPs", "field": "ips", "width": 250},
            {"headerName": "Dominios", "field": "domains", "width": 250},
        ]

        return column_defs, rows or []
    
    @callback(
        Output("analysis-filetype-dropdown", "options"),
        Output("analysis-country-dropdown", "options"),
        Input("interval", "n_intervals"),  
        Input("datetime-picker-start", "value"),
        Input("datetime-picker-end", "value")
    )
    def load_dropdown_options(_, start_date, end_date):
        if not start_date or not end_date:
            return [], []

        start_dt = local_to_utc(start_date, "UTC") 
        end_dt = local_to_utc(end_date, "UTC")

        base_query = {
            "query": {
                "range": {
                    "created": {
                        "gte": start_dt,
                        "lte": end_dt,
                        "format": "strict_date_optional_time"
                    }
                }
            },
            "size": 0
        }

        # Consulta para file_type
        filetype_query = base_query.copy()
        filetype_query["aggs"] = {
            "filetypes": {
                "terms": {
                    "field": "file_type",
                    "size": 100
                }
            }
        }

        # Consulta para origin_country
        country_query = base_query.copy()
        country_query["aggs"] = {
            "countries": {
                "terms": {
                    "field": "origin_country",
                    "size": 200
                }
            }
        }

        try:
            filetype_resp = esc.es.search(index="bronze_mw_raw", body=filetype_query)
            country_resp = esc.es.search(index="bronze_mw_raw", body=country_query)

            filetype_options = [
                {"label": b["key"], "value": b["key"]}
                for b in filetype_resp["aggregations"]["filetypes"]["buckets"]
            ]

            country_options = sorted(
                [
                    {
                        "label": iso2_to_country_name(b["key"]) or b["key"],
                        "value": b["key"]
                    }
                    for b in country_resp["aggregations"]["countries"]["buckets"]
                ],
                key=lambda x: x["label"]
            )

            print(country_options)

        except Exception as e:
            print("Error al cargar valores únicos:", e)
            return [], []

        return filetype_options, country_options