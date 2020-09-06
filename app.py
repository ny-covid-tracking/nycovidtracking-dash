import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import data
import figures
import os

from dash.dependencies import Input, Output

def make_app(infection_map, infection_ts):
    app = dash.Dash(external_stylesheets=[dbc.themes.CYBORG])

    @app.callback(
        Output(component_id="figure", component_property="figure"),
        [Input(component_id="map", component_property="n_clicks_timestamp"),
         Input(component_id="line", component_property="n_clicks_timestamp")])
    def update_figure(map_ts, line_ts):
        if map_ts >= line_ts:
            return infection_map
        return infection_ts

    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Daily New Infections", href="#", n_clicks_timestamp=0, id="map")),
            dbc.NavItem(dbc.NavLink("Infections over Time", href="#", n_clicks_timestamp=0, id="line"))
        ],
        brand="NY Covid Tracking",
        brand_href="#",
        dark=True,
        fixed=True,
        color="dark")

    app.layout = html.Div(children=[
        navbar,
        dcc.Graph(
            id="figure",
            figure=infection_map
        ),
    ])
    
    return app

if __name__ == "__main__":
    if not (NY_DATA_TOKEN := os.environ.get("NY_DATA_TOKEN")):
        os.exit(1)

    if not (PORT := os.environ.get("PORT")):
        os.exit(1)

    df_metrics, county_geojson = data.get_data(NY_DATA_TOKEN)

    infection_map, infection_ts = figures.get_figures(df_metrics, county_geojson)

    app = make_app(infection_map, infection_ts)
    app.run_server(host="0.0.0.0", port=int(PORT))