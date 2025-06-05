from elasticsearch import Elasticsearch
from utils.commons import geolocate_ip_list
from utils.commons import load_ttp_dict, load_country_dict
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
        self.attack_mapping = load_ttp_dict()

        # Load country dicts
        self.country_mapping = load_country_dict()


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

    # Get aggregated ioc data
    def fetch_aggregated_iocs(
            self,
            start_datetime=None,
            end_datetime=None,
            families=None, 
            size=100
        ):

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
                        "size": size
                    }
                },
                "domains_count": {
                    "terms": {
                        "field": "domains",
                        "size": size
                    }
                },
                "ttps_count": {
                    "terms": {
                        "field": "ttp",
                        "size": size
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

    # Method to fetch IPs by family using aggregations
    def fetch_ips_by_family_agg(self, start_dt, end_dt, families=None, size=200):
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
                    "terms": {"field": "family", "size": size*0.25},
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


    # Method to fetch TTP counts grouped by family or technique
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

        results = self.es.search(index=index_template, body=query)

        aggs = results.get("aggregations")
        if not aggs:
            return None

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

    # Method to fetch malware aggregated by country
    def fetch_malware_by_country(
        self,
        start_datetime=None,
        end_datetime=None,
        families=None,
        aggregate_by_family=False,
        with_coords=False,
        size=200,
        infer_miss_count=False
    ):
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
            query_filters.append({"terms": {"family": families}})

        aggs = {
            "by_country": {
                "terms": {
                    "field": "origin_country",
                    "size": size,
                    "missing": "Unknown"
                }
            }
        }

        if aggregate_by_family:
            aggs["by_country"]["aggs"] = {
                "by_family": {
                    "terms": {
                        "field": "family",
                        "size": size
                    }
                }
            }

        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": query_filters
                }
            },
            "aggs": aggs
        }

        results = self.es.search(index=self.BRONZE_INDEX, body=query)
        buckets = results["aggregations"]["by_country"]["buckets"]

        data = []
        for b in buckets:
            country_code = b["key"]
            entry = {"country": country_code}
            if with_coords:
                coords = self.country_mapping.get(country_code, {})
                entry["latitude"] = coords.get("latitude")
                entry["longitude"] = coords.get("longitude")
            if aggregate_by_family:
                for fb in b.get("by_family", {}).get("buckets", []):
                    entry["family"] = fb["key"]
                    entry["count"] = fb["doc_count"]
            else:
                entry["sample_count"]=b["doc_count"]
            data.append(entry)
        
        # If infer_missing_countries is True, we can add missing countries
        if infer_miss_count:
            missing_query = {
                "_source": ["ips", "family"],
                "query": {
                    "bool": {
                        "filter": query_filters + [{"exists": {"field": "ips"}}],
                        "must_not": [{"exists": {"field": "origin_country"}}]
                    }
                }
            }

            response = self.es.search(
                index=self.BRONZE_INDEX,
                body=missing_query,
                size=size
            )

            sample_modif = []

            for hit in response["hits"]["hits"]:
                ips = hit["_source"].get("ips", [])
            
                df_geo = pd.DataFrame(geolocate_ip_list(ips))

                if df_geo.empty:
                    continue

                inferred_country = df_geo["country_code"].value_counts().idxmax()

                entry = {"country": inferred_country}
                entry["count"] = 1
                if aggregate_by_family:
                    entry["family"] = hit["_source"].get("family", "Unknown")

                sample_modif.append(entry)
            
            df_samples = pd.DataFrame(sample_modif)

            if aggregate_by_family:
                df_grouped = df_samples.groupby(["country", "family"], as_index=False)["count"].sum()
            else:
                df_grouped = df_samples.groupby("country", as_index=False)["count"].sum()
                df_grouped.rename(columns={"count": "sample_count"}, inplace=True)
            
            if with_coords:
                df_grouped["latitude"] = df_grouped["country"].map(
                    lambda c: self.country_mapping.get(c, {}).get("latitude"))
                df_grouped["longitude"] = df_grouped["country"].map(
                    lambda c: self.country_mapping.get(c, {}).get("longitude"))
            data.extend(df_grouped.to_dict(orient="records"))


        return pd.DataFrame(data)
    
    # Method to fetch techniques by country
    def fetch_techniques_by_country(
        self,
        start_datetime=None,
        end_datetime=None,
        families=None,
        size=200,
        infer_miss_count=False
    ):
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
            query_filters.append({"terms": {"family": families}})

        query = {
            "_source": ["origin_country", "ttp"],
            "query": {
                "bool": {
                    "filter": query_filters + [{"exists": {"field": "origin_country"}}]
                }
            }
        }

        response = self.es.search(index=self.BRONZE_INDEX, body=query, size=size)

        records = []
        for hit in response["hits"]["hits"]:
            src = hit["_source"]
            country = src.get("origin_country")
            ttps = src.get("ttp", [])
            for t in set(ttps):  # evitar duplicados internos
                records.append({"country": country, "ttp": t})

        print(f"-- Técnicas con país conocido: {len(records)}")

        # Parte 2: muestras sin país, geolocalizar por IP
        if infer_miss_count:
            missing_query = {
                "_source": ["ips", "ttp"],
                "query": {
                    "bool": {
                        "filter": query_filters + [{"exists": {"field": "ips"}}],
                        "must_not": [{"exists": {"field": "origin_country"}}]
                    }
                }
            }

            response = self.es.search(index=self.BRONZE_INDEX, body=missing_query, size=size)

            for hit in response["hits"]["hits"]:
                src = hit["_source"]
                ips = src.get("ips", [])
                if not ips:
                    continue

                df_geo = pd.DataFrame(geolocate_ip_list(ips))
                if df_geo.empty:
                    continue

                inferred_country = df_geo["country_code"].value_counts().idxmax()
                ttps = src.get("ttp", [])
                for t in set(ttps):
                    records.append({"country": inferred_country, "ttp": t})

            print(f"-- Técnicas con país inferido: {len(records)}")

        # Agrupar por país y contar TTPs únicas
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame(columns=["country", "ttp_count"])

        df_unique = df.drop_duplicates()
        df_grouped = df_unique.groupby("country").size().reset_index(name="ttp_count")

        return df_grouped

    # Method to build a DataFrame for IP enrichment (optional)
    def build_ip_enrichment_dataframe(
        self, start_datetime, end_datetime, 
        families=None, 
        size=1000, enrich=True
    ):
        ip_counts, _, _ = self.fetch_aggregated_iocs(start_datetime, end_datetime, families, size=size)
        if not ip_counts:
            return pd.DataFrame()

        df = pd.DataFrame(ip_counts).nlargest(size, "count")
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

        geo_data = geolocate_ip_list(df["ip"].tolist())
        if not geo_data:
            return pd.DataFrame()
        
        df_geo = pd.DataFrame(geo_data)[["ip", "country", "country_code"]]
        df = df.merge(df_geo, on="ip", how="left")

        return df
        