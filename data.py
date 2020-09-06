import json
import pandas as pd
import requests

def _get_ny_data(url, token):
    r = requests.get(url, params={"app_token": token})
    r_json = r.json()
    df = pd.DataFrame(r_json["value"])
    if (next_url := r_json.get("@odata.nextLink")):
        df = pd.concat([df, _get_ny_data(next_url, token)])
    return df

def _get_covid_data(token):
    url = "https://health.data.ny.gov/api/odata/v4/xdss-u53e"
    df = _get_ny_data(url, token)
    df["test_date"] = pd.to_datetime(df["test_date"], format="%Y-%m-%dT%H:%M:%S")
    return df

def _get_population_data(token):
    url = "https://data.ny.gov/api/odata/v4/krt9-ym2k"
    df = _get_ny_data(url, token)
    df = df[df["geography"].str.contains("County")]
    df = df[df["year"] == df["year"].max()]
    df["county"] = df["geography"].str.rsplit(" ", 1).str[0]
    df["fips"] = df["fips_code"].astype("str").str.zfill(5)
    return df

def _get_metrics_data(df_cov, df_pop):
    df = pd.merge(df_cov, df_pop, on=["county"])
    df = df.set_index(["county", "test_date"])

    # 7 day moving average infection rate
    df_avg = pd.DataFrame(df.groupby("county").rolling(7)["new_positives"].mean()).reset_index()
    df_avg = df_avg.rename(columns={"new_positives": "new_positives_moving_avg_7d"})
    df_avg.index = pd.MultiIndex.from_tuples(df_avg.level_1, names=["county", "test_date"])
    df = pd.merge(df, df_avg, left_index=True, right_index=True)
    df["new_positives_moving_avg_7d"] = df["new_positives_moving_avg_7d"] / df["population"] * 100_000

    # cumulative infection rate
    df["cumulative_infection_rate"] = df["cumulative_number_of_positives"] / df["population"] * 100_000

    return df

def _get_county_geojson():
    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    r = requests.get(url)
    return r.json()

def get_data(token):
    df_cov = _get_covid_data(token)
    df_pop = _get_population_data(token)
    df_metrics = _get_metrics_data(df_cov, df_pop)
    county_geojson = _get_county_geojson()
    return df_metrics, county_geojson