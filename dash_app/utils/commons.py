import csv
import locale
import pytz
import pandas as pd
import geoip2.database
import pycountry
import os

# Load ttp attacks dict
def load_ttp_dict():
    file_path = os.path.join(os.path.dirname(__file__), 
                                     "assets",
                                     "enterprise-attack-techniques.csv")
    attack_mapping = {}
    with open(file_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            attack_id = row["ID"]
            attack_mapping[attack_id] = {
                "stix_id": row["STIX ID"],
                "name": row["name"],
                "description": row["description"],
                "url": row["url"],
                "tactics": row["tactics"].split(", "),  # Divide táctics in list
                "detection": row["detection"],
                "platforms": row["platforms"],
                "defenses": row["defenses bypassed"],
                "impact": row["impact type"],
                # Add other fields as necessary
            }
    return attack_mapping


# Map country codes from ISO 2 to ISO 3
def iso2_to_iso3(code):
    try:
        return pycountry.countries.get(alpha_2=code).alpha_3
    except:
        return None

# Normalize country code to ISO 3 format
def normalize_country_code(country):
    if not isinstance(country, str):
        return None
    if len(country) == 3:
        return country.upper()
    elif len(country) == 2:
        return iso2_to_iso3(country.upper())
    return None

# Convert ISO 2 code to country name in Spanish
def iso2_to_country_name(iso2_code):
    try:
        country = pycountry.countries.get(alpha_2=iso2_code.upper())
        if not country:
            return None
        return country.name
    except Exception:
        return None

# Load country lat-long dict
def load_country_dict():
    country_mapping = {}
    file_path = os.path.join(os.path.dirname(__file__), 
                                 "assets",
                                 "country-coords.csv")
    with open(file_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=",")  # Correct delimiter
        for row in reader:
            country_code = row["country"]
            country_mapping[country_code] = {
                "latitude": float(row["latitude"]),  # Convert to float
                "longitude": float(row["longitude"]),  # Convert to float
            }
    return country_mapping

# Load IPS and country  dict
def geolocate_ip_list(ip_list):
    file_path = os.path.join(os.path.dirname(__file__), 
                                 "assets",
                                 "GeoLite2-City.mmdb")
    reader = geoip2.database.Reader(file_path)
    results = []

    for ip in ip_list:
        try:
            r = reader.city(ip)
            results.append({
                "ip": ip,
                "city": r.city.name or "",
                "country": r.country.name or "",
                "country_code": iso2_to_iso3(r.country.iso_code) or "",
                "latitude": r.location.latitude,
                "longitude": r.location.longitude
            })
        except Exception:
            continue  # ignore private or unmapped IPs

    reader.close()
    return results
    
# Format a number with abbreviations
def format_number(fstr, value):
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

    if value >= 1_000_000_000:  # Billions
        short_value = f"{value / 1_000_000_000:.2f}"
        suffix = "B"
    elif value >= 1_000_000:  # Millions
        short_value = f"{value / 1_000_000:.2f}"
        suffix = "M"
    elif value >= 1_000:  # Thousands
        short_value = f"{value / 1_000:.2f}"
        suffix = "K"
    else:  # Less than 1,000
        short_value = f"{value:.2f}"
        suffix = ""
    
    formatted_value = locale.format_string(fstr, float(short_value), grouping=True)
    
    return f"{formatted_value}{suffix}"

# Shorten technique names for display
def shorten(text, max_len=30):
    if "-" not in text or len(text) <= max_len:
        return text if len(text) <= max_len else text[:max_len - 3] + "..."
    
    parts = text.split("-")
    n = len(parts)
    
    reserved = n - 1
    available = max_len - reserved
    
    per_part = available // n
    shortened_parts = []

    for part in parts:
        if len(part) <= per_part:
            shortened_parts.append(part)
        else:
            shortened_parts.append(part[:per_part - 3] + "...")

    return "-".join(shortened_parts)


# Convert UTC timestamp to local timezone
def utc_to_local(df, column, tz_name):
    tz = pytz.timezone(tz_name or "UTC")
    df[column] = pd.to_datetime(df[column]).dt.tz_convert(tz)
    return df


# Convert local datetime to UTC
def local_to_utc(dt, tz_name):
    tz = pytz.timezone(tz_name or "UTC")
    return tz.localize(pd.to_datetime(dt)).astimezone(pytz.utc)


# Nomalize a pandas Series
def normalize_series(series, min_val=10, max_val=40):
    min_count = series.min()
    max_count = series.max()
    if max_count == min_count:
        return pd.Series([ (min_val + max_val) / 2 ] * len(series), index=series.index)
    return ((series - min_count) / (max_count - min_count)) * (max_val - min_val) + min_val