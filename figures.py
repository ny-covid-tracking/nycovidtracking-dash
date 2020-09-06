import plotly.express as px

def _get_infection_map(df, geojs):
    df_map = df[["fips", "new_positives_moving_avg_7d"]].reset_index()
    df_map = df_map[df_map["test_date"] == df_map["test_date"].max()]
    df_map["text"] = df_map["new_positives_moving_avg_7d"].round(0)

    fig = px.choropleth(df_map,
                        locations="fips",
                        geojson=geojs,
                        color="new_positives_moving_avg_7d",
                        hover_name="county",
                        hover_data=["text"],
                        labels={
                            "new_positives_moving_avg_7d": "Daily Positive Case Rate per 100k (7 Day Moving Average)",
                            "text": "Daily Positive Case Rate per 100k (7 Day Moving Average)",
                        },
                        color_continuous_scale="thermal",
                        range_color=(
                            df_map["new_positives_moving_avg_7d"].min(),
                            df_map["new_positives_moving_avg_7d"].max()
                        ),
                        scope="usa",
                        title="Daily Positive Case Rate per 100k (7 Day Moving Average)")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(coloraxis_colorbar=dict(
        title="",
        ticksuffix=" new cases"),
        template="plotly_dark")

    return fig

def _get_infection_ts(df):
    df_ts = df[["cumulative_infection_rate"]].reset_index()

    fig = px.line(df_ts,
                  x="test_date",
                  y="cumulative_infection_rate",
                  line_group="county",
                  color="county",
                  hover_name="county",
                  hover_data=["cumulative_infection_rate"],
                  labels={
                      "county": "County",
                      "cumulative_infection_rate": "Cumulative Infections per 100k",
                      "test_date": "Date",
                  },
                  title="Cumulative Infections per 100k by County")
    fig.update_layout(template="plotly_dark")

    return fig

def get_figures(df_metrics, county_geojson):
    infection_map = _get_infection_map(df_metrics, county_geojson)
    infection_ts = _get_infection_ts(df_metrics)
    return infection_map, infection_ts