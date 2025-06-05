from dash import Input, Output, State, html
from dash import callback, callback_context, no_update, exceptions
from dash_bootstrap_templates import template_from_url
import dash_bootstrap_components as dbc
from app_instance import esc
from layouts.sidebar import theme_changer_aio
from utils.commons import local_to_utc, iso2_to_country_name, utc_to_local
import pandas as pd

# This module contains the callbacks for the analysis page of the dashboard.
def register_analysis_callbacks():

    # Callback for update aggrid
    @callback(
        Output("analysis-table", "columnDefs"),
        Output("analysis-table", "rowData"),
        [
            Input("interval", "n_intervals"),
            Input('datetime-picker-start', 'value'),
            Input('datetime-picker-end', 'value'),
            Input("screen-width", "data"),
            Input("family-dropdown", "value"),
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
        filetypes, countries, score_range,
        theme, dark_mode, tz_data
    ):
        # UTC date conversion
        start_dt = local_to_utc(start_date, tz_data)
        end_dt = local_to_utc(end_date, tz_data)

        # Construcción de filtros
        filters = []        
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
            "sort": [{"created": {"order": "desc"}}],  
            "size": 10000,
        }

        # Query to Elasticsearch
        try:
            response = esc.es.search(index="bronze_mw_raw", body=query_body)
            hits = response["hits"]["hits"]
        except Exception as e:
            return [], []

        # Format results
        rows = [hit["_source"] for hit in hits]

        # Convert timestamps to local time if necessary
        df = pd.DataFrame(rows)
        if "created" in df.columns:
            df = utc_to_local(df, "created", tz_data)
        rows = df.to_dict(orient="records")

        column_defs = [
            {"headerName": "Id", "field": "id", "width": 170},
            {"headerName": "Fecha", "field": "created", "width": 200},
            {"headerName": "Score", "field": "score", "width": 60},
            {"headerName": "Tags", "field": "tags", "width": 170},
            {"headerName": "Técnicas", "field": "ttp", "width": 150},
            {"headerName": "Familia", "field": "family", "width": 120},
            {"headerName": "IPs", "field": "ips", "width": 250},
            {"headerName": "Dominios", "field": "domains", "width": 250},
            {"headerName": "Tamaño fichero", "field": "file_size", "width": 120},
            {"headerName": "Propagación", "field": "delivery_method", "width": 130},
            {"headerName": "Tipo fichero", "field": "file_type", "width": 120},
            {"headerName": "Origen", "field": "origin_country", "width": 100},
            
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

        filetype_query = base_query.copy()
        filetype_query["aggs"] = {
            "filetypes": {
                "terms": {
                    "field": "file_type",
                    "size": 100
                }
            }
        }

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

        except Exception as e:            
            return [], []

        return filetype_options, country_options
    
    # Callback for toggling the sample details modal
    @callback(
        Output("sample-details-modal", "is_open"),
        Output("sample-details-body", "children"),
        Input("analysis-table", "selectedRows"),
        Input("close-sample-details", "n_clicks"),
        State("sample-details-modal", "is_open"),
        prevent_initial_call=True
    )
    def toggle_sample_modal(selected_rows, close_clicks, is_open):
        ctx = callback_context
        if not ctx.triggered:
            raise exceptions.PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "close-sample-details":
            return False, no_update

        if selected_rows and isinstance(selected_rows[0], dict):
            data = selected_rows[0]

            def get_val(x):
                return x[0] if isinstance(x, list) else x

            def badge_list(items, color="primary", href_func=None):
                badges = []
                for item in items:
                    if not item:
                        continue
                    try:
                        badge_kwargs = {
                            "children": str(item),
                            "color": color,
                            "className": "me-1 mb-1",
                            "pill": True
                        }
                        if href_func:
                            href = href_func(item)
                            if href: 
                                badge_kwargs["href"] = href
                                badge_kwargs["target"] = "_blank"
                        badges.append(dbc.Badge(**badge_kwargs))
                    except Exception:
                        continue
                if not badges:
                    return html.Div("No disponible", className="text-muted")
                return html.Div(badges)
        
            def external_link(label, url):
                return html.Div(
                    dbc.Button(label, href=url, target="_blank", color="link", className="px-0")
                )

            return True, html.Div([
                html.H5(f"ID de muestra: {get_val(data.get('id'))}", className="mb-2"),
                external_link("Ver detalle de muestra en Tria.ge", f"https://tria.ge/{get_val(data.get('id'))}"),
                html.P(f"Fecha de análisis: {get_val(data.get('created'))}"),
                html.P(f"Score: {get_val(data.get('score'))} / 10"),
                html.P(f"SHA256: {get_val(data.get('sha256'))}"),
                html.P(f"Tamaño de fichero: {get_val(data.get('file_size'))} bytes"),
                html.P(f"Tipo de fichero: {get_val(data.get('file_type')) or 'No disponible'}"),
                html.Hr(),
                html.H6("Familia"),
                badge_list(data.get("family", []), color="danger"),
                html.H6("Tags"),
                badge_list(data.get("tags", []), color="info"),
                html.H6("Técnicas MITRE ATT&CK"),
                badge_list(
                    data.get("ttp", []),
                    color="warning",
                    href_func=lambda ttp: f'https://attack.mitre.org/techniques/{ttp.replace(".","/")}/'
                ),
                html.H6("Dominios"),
                html.Ul([html.Li(dom) for dom in data.get("domains", [])]),
                html.H6("IPs"),
                badge_list(
                    data.get("ips", []),
                    color="secondary",
                    href_func=lambda ip: f'https://www.abuseipdb.com/check/{ip}'
                ),
            ])
        
        return is_open, no_update