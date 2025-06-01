from elasticsearch import Elasticsearch
import utils.commons as utils
import pandas as pd

class ElasticContext:
    def __init__(self, host="http://elasticsearch:9200"):
        self.es = Elasticsearch(
            hosts=[host],
            max_retries=5,
            retry_on_timeout=True,
            timeout=30,
        )

        self.BRONZE_INDEX = "bronze_mw_raw"
        self.GOLD_HRLY_INDEX = f"gold_mw_agr_hourly_*"

        # Load TTP dicts
        self.attack_mapping = utils.load_ttp_dict()

        # Load country dicts
        self.country_mapping = utils.load_country_dict()


    def close(self):
        if self.es:
            self.es.close()

    # Get aggregated data by time bins 
    def fetch_aggreg_by_bins(
        self,
        start_datetime=None,
        end_datetime=None,
        interval="1h",
        size="100"):

        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"created": {"gte": start_datetime, 
                                               "lte": end_datetime, 
                                               "format": "strict_date_optional_time"}}}
                    ]
                }
            },
            "aggs": {
                "by_time": {
                    "date_histogram": {
                        "field": "created",
                        "fixed_interval": interval
                    },
                    "aggs": {
                        "by_family": {
                            "terms": {
                                "field": "family",
                                "missing": "Unknown",
                                "size": size
                            },
                            "aggs": {
                                "avg_score": {
                                    "avg": {
                                        "field": "score"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "size": 0  # No devolvemos documentos, solo agregaciones
        }

        # Execute the query
        results = self.es.search(index=self.BRONZE_INDEX, body=query)

        # Procesamos los resultados de agregaciones
        data = []
        for bucket in results["aggregations"]["by_time"]["buckets"]:
            timestamp = bucket["key_as_string"]
            for family_bucket in bucket["by_family"]["buckets"]:
                avg_score = family_bucket.get("avg_score", {}).get("value", None)  # Obtén el valor promedio del score
                data.append({
                    "timestamp": timestamp,
                    "family": family_bucket["key"],
                    "count": family_bucket["doc_count"],
                    "avg_score": avg_score  # Incluye el promedio del score
                })

        return data

    # # Get aggregated data by time bins
    # def fetch_aggreg_by_bins(
    #     self,
    #     session_id,
    #     start_datetime=None,
    #     end_datetime=None,
    #     interval="1h",
    #     size="10"
    # ):
        
    #     query = {
    #         "query": {
    #             "bool": {
    #                 "filter": [
    #                     {
    #                         "term": {
    #                             "type": "family"
    #                         }
    #                     },
    #                     {
    #                         "range": {
    #                             "date": {
    #                                 "gte": start_datetime,
    #                                 "lte": end_datetime,
    #                                 "format": "strict_date_optional_time"
    #                             }
    #                         }
    #                     }
    #                 ]
    #             }
    #         },
    #         "aggs": {
    #             "by_time": {
    #                 "date_histogram": {
    #                     "field": "date",
    #                     "fixed_interval": interval
    #                 },
    #                 "aggs": {
    #                     "by_family": {
    #                         "terms": {
    #                             "field": "family",
    #                             "missing": "Unknown",
    #                             "size": size
    #                         },
    #                         "aggs": {
    #                             "count": {
    #                                 "sum": {
    #                                     "field": "count" 
    #                                 }
    #                             },
    #                             "avg_score": {
    #                                 "avg": {
    #                                     "field": "avg_score"
    #                                 }
    #                             }
    #                         }
    #                     }
    #                 }
    #             }
    #         },
    #         "size": 0  # No devolvemos documentos, solo agregaciones
    #     }

    #     # Ejecutar la consulta
    #     results = self.es.search(index=self.GOLD_HRLY_INDEX, body=query)

    #     # Procesar los resultados de las agregaciones
    #     data = []
    #     for bucket in results["aggregations"]["by_time"]["buckets"]:
    #         timestamp = bucket["key_as_string"]
    #         for family_bucket in bucket["by_family"]["buckets"]:
    #             avg_score = family_bucket.get("avg_score", {}).get("value", None)  # Obtén el valor promedio del score
    #             count = family_bucket.get("count", {}).get("value", 0)  # Obtén la suma del campo 'count'
    #             data.append({
    #                 "timestamp": timestamp,
    #                 "family": family_bucket["key"],
    #                 "count": count,
    #                 "avg_score": avg_score  # Incluye el promedio del score
    #             })

    #     return data


    # Get aggregated ioc data
    def fetch_aggregated_iocs(
            self,
            start_datetime=None,
            end_datetime=None,
            families=None, 
            limit=50
        ):

        """
        Aggregates IOCs (IPs, domains, TTPs) from the bronze index within a time range,
        optionally filtered by malware family.
        """

        query_filters = [
            {
                "range": {
                    "created": {
                        "gte": start_datetime,
                        "lte": end_datetime,
                        "format": "strict_date_optional_time"
                    }
                }
            }
        ]

        # Add optional family filter
        if families:
            query_filters.append({
                "terms": {
                    "family": families
                }
            })


        query = {
            "query": {
                "bool": {
                    "filter": query_filters
                }
            },
            "aggs": {
                "ips_count": {
                    "terms": {
                        "field": "ips",
                        "size": limit
                    }
                },
                "domains_count": {
                    "terms": {
                        "field": "domains",
                        "size": limit
                    }
                },
                "ttps_count": {
                    "terms": {
                        "field": "ttp",
                        "size": limit
                    }
                }
            },
            "size": 0
        }
        
        results = self.es.search(index=self.BRONZE_INDEX, body=query)

        ip_counts = [
            {"ip": bucket["key"], "count": bucket["doc_count"]}
            for bucket in results["aggregations"]["ips_count"]["buckets"]
        ]

        domain_counts = [
            {"domain": bucket["key"], "count": bucket["doc_count"]}
            for bucket in results["aggregations"]["domains_count"]["buckets"]
        ]

        ttp_counts = [
            {"ttp": bucket["key"], "count": bucket["doc_count"]}
            for bucket in results["aggregations"]["ttps_count"]["buckets"]
        ]

        return ip_counts, domain_counts, ttp_counts

    def fetch_ips_by_family_agg(self, start_dt, end_dt, families=None, size=200):
        """
        Devuelve IPs observadas agrupadas por familia usando agregaciones (más eficiente).
        """
        filters = [
            {"range": {
                "created": {
                    "gte": start_dt,
                    "lte": end_dt,
                    "format": "strict_date_optional_time"
                }
            }},
            {"exists": {"field": "ips"}}
        ]

        if families:
            filters.append({"terms": {"family": families}})

        query = {
            "size": 0,
            "query": {
                "bool": {"filter": filters}
            },
            "aggs": {
                "by_family": {
                    "terms": {"field": "family", "size": 30},
                    "aggs": {
                        "by_ip": {
                            "terms": {"field": "ips", "size": size}
                        }
                    }
                }
            }
        }

        response = self.es.search(index=self.BRONZE_INDEX, body=query)
        results = []

        for family_bucket in response["aggregations"]["by_family"]["buckets"]:
            family = family_bucket["key"]
            for ip_bucket in family_bucket["by_ip"]["buckets"]:
                results.append({
                    "ip": ip_bucket["key"],
                    "family": family,
                    "count": ip_bucket["doc_count"]
                })

        return pd.DataFrame(results)


    # Método para realizar la consulta de TTP y su conteo
    def fetch_ttp_count(
        self,
        start_datetime,
        end_datetime,
        families,
        group_by_family: bool = True
    ):
        """
        Query Elasticsearch to retrieve TTP counts grouped by family,
        then map each TTP to its tactic using local ATT&CK mapping.
        """

        query_filters = [
            {
                "range": {
                    "created": {
                        "gte": start_datetime,
                        "lte": end_datetime,
                        "format": "strict_date_optional_time"
                    }
                }
            }
        ]

        # Optional filter by selected families
        if families:
            query_filters.append({
                "terms": {
                    "family": families
                }
            })

        # Construct query dynamically based on grouping
        if group_by_family:
            agg_query = {
                "family_count": {
                    "terms": {"field": "family", "missing": "Desconocida", "size": 1000},
                    "aggs": {
                        "ttps": {
                            "terms": {"field": "ttp", "size": 1000}
                        }
                    }
                }
            }
        else:
            agg_query = {
                "ttp_count": {
                    "terms": {"field": "ttp", "missing": "Desconocida", "size": 1000},
                    "aggs": {
                        "families": {
                            "terms": {"field": "family", "size": 1000}
                        }
                    }
                }
            }

        query = {
            "query": {
                "bool": {
                    "filter": query_filters
                }
            },
            "aggs": agg_query,
            "size": 0
        }

        # Execute the query
        results = self.es.search(index=self.BRONZE_INDEX, body=query)
        
        ttp_counts = []

        if group_by_family:
            family_buckets = results["aggregations"]["family_count"]["buckets"]
            for family_bucket in family_buckets:
                family_name = family_bucket["key"]
                for ttp_bucket in family_bucket["ttps"]["buckets"]:
                    ttp_code = ttp_bucket["key"]
                    count = ttp_bucket["doc_count"]

                    attack_data = self.attack_mapping.get(ttp_code)
                    if attack_data:
                        ttp_counts.append({
                            "tactic": "-".join(attack_data["tactics"]),
                            "technique": attack_data["name"],
                            "platforms": attack_data["platforms"],
                            "defenses": attack_data["defenses"],
                            "impact": attack_data["impact"],
                            "families": family_name,
                            "count": count
                        })
        else:
            ttp_buckets = results["aggregations"]["ttp_count"]["buckets"]
            for ttp_bucket in ttp_buckets:
                ttp_code = ttp_bucket["key"]
                count = ttp_bucket["doc_count"]
                families_list = [b["key"] for b in ttp_bucket["families"]["buckets"]]

                attack_data = self.attack_mapping.get(ttp_code)
                if attack_data:
                    ttp_counts.append({
                        "tactic": "-".join(attack_data["tactics"]),
                        "technique": attack_data["name"],
                        "platforms": attack_data["platforms"],
                        "defenses": attack_data["defenses"],
                        "families": ", ".join(families_list),
                        "impact": attack_data["impact"],
                        "count": count
                    })
        
        return ttp_counts

    # Method to fetch number of elements within a date range
    def fetch_techniques_over_time(
        self,
        start_datetime,
        end_datetime,
        interval="1d",
        families=None
    ):
        """
        Devuelve el número de TTPs agrupado por táctica y fecha.
        """
        query_filters = [
            {
                "range": {
                    "created": {
                        "gte": start_datetime,
                        "lte": end_datetime,
                        "format": "strict_date_optional_time"
                    }
                }
            }
        ]

        if families:
            query_filters.append({
                "terms": {
                    "family": families
                }
            })

        query = {
            "query": {
                "bool": {
                    "filter": query_filters
                }
            },
            "aggs": {
                "by_time": {
                    "date_histogram": {
                        "field": "created",
                        "fixed_interval": interval
                    },
                    "aggs": {
                        "by_ttp": {
                            "terms": {
                                "field": "ttp",
                                "size": 1000,
                                "missing": "unknown"
                            }
                        }
                    }
                }
            },
            "size": 0
        }

        results = self.es.search(index=self.BRONZE_INDEX, body=query)

        data = []
        for time_bucket in results["aggregations"]["by_time"]["buckets"]:
            timestamp = time_bucket["key_as_string"]
            for ttp_bucket in time_bucket["by_ttp"]["buckets"]:
                ttp = ttp_bucket["key"]
                count = ttp_bucket["doc_count"]

                attack_data = self.attack_mapping.get(ttp)
                if attack_data:
                    for tactic in attack_data["tactics"]:
                        data.append({
                            "timestamp": timestamp,
                            "tactic": tactic,
                            "technique": attack_data["name"],
                            "count": count
                        })

        return pd.DataFrame(data)


    # Method to fetch number of elements within a date range
    def fetch_gold(
            self,
            start_datetime,
            end_datetime,
            index_template='gold_mw_agr',
            grain="hourly",
            families=None):
        """
        Fetches from the Gold index for the specified date range.
        :param start_datetime: Start datetime in ISO 8601 format.
        :param end_datetime: End datetime in ISO 8601 format.
        :param index_template: Gold index template with wildcard for date partitions.
        :return: Dictionary with aggregated KPI values.
        """
        index_template = f"{index_template}_{grain}_*"

        filters = [
            {"range": {
                "date": {
                    "gte": start_datetime,
                    "lte": end_datetime,
                    "format": "strict_date_optional_time"
                }
            }}
        ]
        if families:
            filters.append({"terms": {"family": families}})

        query = {
            "query": {
                "bool": {
                    "filter": filters
                }
            },
            "aggs": {
                "total_count": {"sum": {"field": "count"}},  # Total records
                "total_count_malware": {                    
                    "filter": {"bool": {"must": [{"term": {"type": "family"}}],
                                        "must_not": [{"term": {"family": "Unknown"}}]}},
                    "aggs": {"sum_count": {"sum": {"field": "count"}}}
                },
                "avg_score": {
                    "filter": {"term": {"type": "family"}},
                    "aggs": {"avg_value": {"avg": {"field": "avg_score"}}}
                },
                "unique_domains": {
                    "filter": {"term": {"type": "summary"}},
                    "aggs": {"domains": {"sum": {"field": "unique_domains"}}}
                },
                "unique_ips": {
                    "filter": {"term": {"type": "summary"}},
                    "aggs": {"ips": {"sum": {"field": "unique_ips"}}}
                },
                "family_count": {
                    "filter": {"term": {"type": "family"}},
                    "aggs": {"distinct_families": {"cardinality": {"field": "family"}}}
                }
            },
            "size": 0  # Return only aggregations
        }

        # Execute the query
        results = self.es.search(index=index_template, body=query)

        aggs = results.get("aggregations")
        if not aggs:
            return None

        # Process results
        total_records = results["aggregations"]["total_count"]["value"]
        total_records_malware = results["aggregations"]["total_count_malware"]["sum_count"]["value"]
        avg_score = results["aggregations"]["avg_score"]["avg_value"]["value"]
        unique_domains = results["aggregations"]["unique_domains"]["domains"]["value"]
        unique_ips = results["aggregations"]["unique_ips"]["ips"]["value"]
        family_num = results["aggregations"]["family_count"]["distinct_families"]["value"]
        return {
            "total_records": total_records,
            "total_records_malware": total_records_malware,
            "avg_score": avg_score,
            "unique_domains": unique_domains,
            "unique_ips": unique_ips,
            "family_num": family_num
        }

    # Method to fetch malware data grouped by country from Elasticsearch
    def fetch_malware_data_by_country(self,                                      
                                      start_datetime=None,
                                      end_datetime=None):
        """
        Queries Elasticsearch to retrieve the count of malware detections grouped by country and family, 
        filtered by a date range.
        
        :param session_id: Current session identifier
        :param start_datetime: Start of the date range (ISO 8601 format)
        :param end_datetime: End of the date range (ISO 8601 format)
        :param index_name: The name of the Elasticsearch index to query
        :return: List of dictionaries containing country, family, count, latitude, and longitude
        """
        query = {
            "size": 0,  # Do not return individual documents
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"created": {"gte": start_datetime, 
                                               "lte": end_datetime, 
                                               "format": "strict_date_optional_time"}}},
                        {"exists": {"field": "origin_country"}}
                    ]
                }
            },
            "aggs": {
                "by_country": {
                    "terms": {
                        "field": "origin_country",  # Group results by country codes
                        "size": 200,  # Maximum number of buckets
                        "missing": "Unknown",  # Assign "Unknown" to documents without a country code
                    },
                    "aggs": {
                        "by_family": {
                            "terms": {
                                "field": "family",  # Group by malware family
                                "size": 100,  # Limit the number of families per country
                            }
                        }
                    }
                }
            }
        }

        # Execute the query
        results = self.es.search(index=self.BRONZE_INDEX, body=query)

        # Prepare data for the map
        country_data = []
        for bucket in results["aggregations"]["by_country"]["buckets"]:
            country_code = bucket["key"]
            for family_bucket in bucket["by_family"]["buckets"]:
                family = family_bucket["key"]
                count = family_bucket["doc_count"]

                # Map country codes to latitude and longitude
                country_coord = self.country_mapping.get(country_code)

                country_data.append({
                    "country": country_code,
                    "family": family,
                    "count": count,
                    "latitude": country_coord["latitude"],
                    "longitude": country_coord["longitude"],
                })

        return country_data
    

    def fetch_sample_count_by_country(
        self, start_datetime=None, end_datetime=None, 
        families=None
    ):
        """
        Returns a DataFrame with the count of samples grouped by country
        """

        query_filters = [
            {
                "range": {
                    "created": {
                        "gte": start_datetime,
                        "lte": end_datetime,
                        "format": "strict_date_optional_time"
                    }
                }
            }
        ]

        # Optional filter by selected families
        if families:
            query_filters.append({"terms": {"family": families}})

        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": query_filters
                }
            },
            "aggs": {
                "by_country": {
                    "terms": {
                        "field": "origin_country",
                        "size": 200
                    }
                }
            }
        }

        results = self.es.search(index=self.BRONZE_INDEX, body=query)
        buckets = results["aggregations"]["by_country"]["buckets"]

        data = [{"country": b["key"], "sample_count": b["doc_count"]} for b in buckets]
        return pd.DataFrame(data)

    def build_ip_enrichment_dataframe(
        self, start_datetime, end_datetime, families=None, 
        limit=1000, enrich=True
    ):
        """
        Returns a DataFrame for Sankey diagram linking:
        IP → confidence_level → threat_type → malware → country
        Only includes IPs seen in the specified time range with enrichment data.
        """

        ip_counts, _, _ = self.fetch_aggregated_iocs(start_datetime, end_datetime, families, limit=limit)
        if not ip_counts:
            return pd.DataFrame()

        df = pd.DataFrame(ip_counts).nlargest(limit, "count")
        if df.empty:
            return pd.DataFrame()

        if enrich:
            try:
                response = self.es.mget(
                    index="silver_ioc_ip_enriched",
                    body={"ids": df["ip"].tolist()}
                )
            except Exception:
                return pd.DataFrame()

            enriched_data = []
            for doc in response["docs"]:
                if doc.get("found"):
                    src = doc["_source"]
                    tf = src.get("threatfox", {})
                    enriched_data.append({
                        "ip": doc["_id"],
                        "confidence_level": tf.get("confidence_level"),
                        "threat_type": tf.get("threat_type"),
                        "malware": tf.get("malware")
                    })

            df_enriched = pd.DataFrame(enriched_data)
            df = pd.merge(df, df_enriched, on="ip", how="inner")

        geo_data = utils.geolocate_ip_list(df["ip"].tolist())
        if not geo_data:
            return pd.DataFrame()
        
        df_geo = pd.DataFrame(geo_data)[["ip", "country", "country_code"]]
        df = df.merge(df_geo, on="ip", how="left")

        return df
        