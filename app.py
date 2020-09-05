# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import json
import plotly.express as px
import pandas as pd
import os
import requests

from urllib.request import urlopen

app = dash.Dash(__name__)

# get covid and population data
def get_ny_data(url, token):
    if "?" not in url:
        url += "?app_token=" + token
    else:
        url += "&app_token=" + token
    resp = requests.get(url)
    resp_json = resp.json()
    dfs = [pd.DataFrame(resp_json["value"])]
    if (next_url := resp_json.get("@odata.nextLink")):
        dfs.append(get_ny_data(next_url, token))
    return pd.concat(dfs)

NY_DATA_TOKEN = os.environ["NY_DATA_TOKEN"]
ny_covid_data = get_ny_data("https://health.data.ny.gov/api/odata/v4/xdss-u53e", NY_DATA_TOKEN)
ny_pop_data = get_ny_data("https://data.ny.gov/api/odata/v4/krt9-ym2k", NY_DATA_TOKEN)

# we only care about the most recent population for each county and we need a join key
df_ny_counties = ny_pop_data[ny_pop_data["geography"].str.contains("County")]
df_ny_counties = df_ny_counties[df_ny_counties["year"] == df_ny_counties["year"].max()]
df_ny_counties["county"] = df_ny_counties["geography"].str.rsplit(" ", 1).str[0]
df_ny_counties["fips"] = df_ny_counties["fips_code"].astype("str").str.zfill(5)

# join with covid data
df_ny_covid_rates = pd.merge(ny_covid_data, df_ny_counties, on=["county"])

# two metrics of interest
# 1. 7 day moving average of daily positive cases
# 2. cumulative positive cases relative to pop
df_ny_covid_rates["test_date"] = pd.to_datetime(df_ny_covid_rates["test_date"], format="%Y-%m-%dT%H:%M:%S")
df_ny_covid_rates = df_ny_covid_rates.set_index(["county", "test_date"])

df_moving_average = pd.DataFrame(df_ny_covid_rates.groupby("county").rolling(7)["new_positives"].mean()).reset_index()
df_moving_average = df_moving_average.rename(columns={"new_positives": "new_positives_7d_avg"})
df_moving_average.index = pd.MultiIndex.from_tuples(df_moving_average.level_1, names=["county", "test_date"])
df_ny_covid_rates = pd.merge(df_ny_covid_rates, df_moving_average, left_index=True, right_index=True)

df_ny_covid_rates["cumulative_infection_rate"] = df_ny_covid_rates["cumulative_number_of_positives"] / df_ny_covid_rates["population"]

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
    
df_recent_7d_avg = df_ny_covid_rates[["fips", "new_positives_7d_avg"]].reset_index()
df_recent_7d_avg = df_recent_7d_avg[df_recent_7d_avg["test_date"] == df_recent_7d_avg["test_date"].max()]

fig = px.choropleth(df_recent_7d_avg,
                    geojson=counties,
                    locations="fips",
                    color="new_positives_7d_avg",
                    color_continuous_scale="Bluered",
                    range_color=(df_recent_7d_avg["new_positives_7d_avg"].min(),
                                 df_recent_7d_avg["new_positives_7d_avg"].max()),
                    scope="usa",
                    labels={"new_positives_7d_avg": "Daily Average New Cases (7 Days)"},
                    hover_name="county",
                    hover_data=["new_positives_7d_avg"])
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

df = df_ny_covid_rates[["cumulative_infection_rate"]].reset_index()
fig2 = px.line(df, x="test_date", y="cumulative_infection_rate", color="county")
fig2.update_layout(yaxis=dict(tickformat=".2%"))

app.layout = html.Div(children=[
    html.H1(children='NY Covid Tracking'),

    html.Div(children='''
        Built on top of data.ny.gov using python, plot.ly, and dash.
    '''),

    dcc.Graph(
        id='recent-map',
        figure=fig
    ),
    
    dcc.Graph(
        id='line-graph',
        figure=fig2
    ),
])

if __name__ == "__main__":
    app.run_server(port=int(os.environ["PORT"]))