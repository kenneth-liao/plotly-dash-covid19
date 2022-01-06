# core component library (dcc)
from dash import dcc
# bootstrap components for custom layouts
import dash_bootstrap_components as dbc
# html component library (html)
from dash import html
# Input and Output objects for callback decorator
from dash.dependencies import Input, Output
# connect app.py file
from app import app
import pandas as pd
from plotly import graph_objects as go
import plotly.io as pio

# ------------------------------------------------------------------------------
# User defined styling


# set the default theme for plotly
pio.templates.default = "plotly_white"

# set app width (out of 12 total columns)
app_width = 8
margin = (12-app_width)/2  # don't change this


# ------------------------------------------------------------------------------
# Data Processing


# define metrics
metric_options = [
    {'label': 'Confirmed Cases', 'value': 'cases'},
    {'label': 'Confirmed Deaths', 'value': 'deaths'},
    {'label': 'Tests', 'value': 'tests'},
    {'label': 'Vaccinations', 'value': 'vaccinations'}
]

# define intervals
interval_options = [
    {'label': 'Cumulative', 'value': 'total'},
    {'label': 'New per day', 'value': 'new'},
    {'label': 'Weekly', 'value': 'weekly'}
]

# load the latest data
data = pd.read_csv('data/owid-covid-data.csv')
# filter data down to only columns we need
data = data[['location', 'date', 'total_cases', 'new_cases', 'total_cases_per_million', 'new_cases_per_million',
             'total_deaths', 'new_deaths', 'total_deaths_per_million', 'new_deaths_per_million',
             'total_tests', 'new_tests', 'total_tests_per_thousand', 'new_tests_per_thousand',
             'total_vaccinations', 'new_vaccinations', 'total_vaccinations_per_hundred',
             'new_vaccinations_smoothed_per_million']]


# ------------------------------------------------------------------------------
# Define main DCC components


# location check list component
def location_checklist():
    return dcc.Checklist(
        id='location', value=['United States', 'United Kingdom', 'Germany', 'Canada', 'Italy'],
        options=[{'label': c, 'value': c} for c in data.location.unique()],
        inputStyle={'margin-right': '5px'}  # adds space between checkbox & label
    )


# metric dropdown component
def metric_dropdown():
    return dcc.Dropdown(
        id='metric',
        options=metric_options,
        value='cases',
        clearable=False
    )


# interval dropdown component
def interval_dropdown():
    return dcc.Dropdown(
        id='interval',
        options=interval_options,
        value='new',
        clearable=False
    )


# relative to population option
def relative_checklist():
    return dcc.Checklist(
        id='relative',
        options=[
            {'label': ' Relative to population', 'value': 'relative'}
        ]
    )


# visualization component
def visualization():
    return dcc.Graph(
        id='visualization',
        figure={},
        className='h-100',
        config={'displayModeBar': False}
    )


# ------------------------------------------------------------------------------
# App Layout


app.layout = html.Div([
    # the Location component stores the url in the address bar
    dcc.Location(id='url', refresh=False),

    dbc.Row(  # title
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.H1('COVID-19 Global Data Dashboard')
                ), className='mb-4'
            ), width={'size': app_width, 'offset': margin}
        )
    ),

    dbc.Row([  # logo & plotting options
        dbc.Col(  # logo
            dbc.Card(
                dbc.CardBody(
                    html.H1('Logo')
                ), className='mb-4', style={'height': '10vh'}
            ), width={'size': 2, 'offset': margin}
        ),
        dbc.Col([  # plotting options
            dbc.Card([
                dbc.Row([
                    dbc.Col([
                        html.H6('Metric'),
                        metric_dropdown()
                    ], style={'margin-left': '10px'}, align='center'),
                    dbc.Col([
                        html.H6('Interval'),
                        interval_dropdown()
                    ], style={'margin-left': '10px'}, align='center'),
                    dbc.Col([
                        relative_checklist(),
                    ], style={'margin-left': '10px'}, align='center')
                ], style={'height': '10vh'})
            ], className='mb-4')
        ], width={'size': 10-2*margin})
    ]),

    dbc.Row([  # country check list & visualization
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    # dcc checklist is rendered inside a div so it can be styled
                    location_checklist(), style={'height': '60vh', 'overflow': 'auto'}
                )
            ), width={'size': 2, 'offset': margin}
        ),
        dbc.Col([
            dbc.CardHeader(
                dbc.Tabs([
                    dbc.Tab(
                        label='Chart'
                    ),
                    dbc.Tab(
                        label='Map'
                    ),
                    dbc.Tab(
                        label='Table'
                    )
                ]), style={'height': '3vh', 'background-color': 'rgb(245, 245, 245)'}
            ),
            dbc.Card(
                dbc.CardBody(
                    visualization(), style={'height': '57vh'}
                )
            )
        ], width={'size': 10-2*margin}
        )
    ]),
    dbc.Row([
        dbc.Col(
            html.Div(
                html.P('Dashboard design by Kenneth Liao, 2022', className='mt-2')
            ), width={'size': 10-2*margin, 'offset': margin + 2}, style={'text-align': 'right'}
        )
    ])

])


# ------------------------------------------------------------------------------
# Calllbacks to connect DCC components


# enable/disable relative to population option
@app.callback(Output('relative', 'options'),
              Output('relative', 'style'),
              Input('metric', 'value'))
def disable_relative(metric):
    if metric == 'vaccinations':
        options = {'disabled': True}
        style = {'color': 'rgb(245, 15, 15)'}
    else:
        options = {'disabled': False}
        style = {'color': 'rgb(245, 245, 245)'}
    return options, style


# connect visualization
@app.callback(Output('visualization', 'figure'),
              [Input('location', 'value'),
               Input('metric', 'value'),
               Input('interval', 'value'),
               Input('relative', 'value')])
def update_figure(location, metric, interval, relative):
    # resample data to weekly
    if interval == 'weekly':
        # relative logic
        if (relative == 'relative') & (metric != 'vaccinations'):
            if metric == 'tests':
                col_name = 'new_' + metric + '_per_thousand'
            else:
                col_name = 'new_' + metric + '_per_million'
        else:
            col_name = 'new_' + metric

        resampled = data[['location', 'date', col_name]].groupby('location').rolling(7, on='date').sum()

        traces = []
        for country in location:
            traces.append(
                go.Scatter(name=country, mode='markers+lines',
                           x=resampled.loc[country, :]['date'],
                           y=resampled.loc[country, :][col_name])
            )

    else:
        # relative logic
        if (relative == 'relative') & (metric != 'vaccinations'):
            if metric == 'tests':
                col_name = interval + '_' + metric + '_per_thousand'
            else:
                col_name = interval + '_' + metric + '_per_million'
        else:
            col_name = interval + '_' + metric

        traces = []
        for country in location:
            traces.append(
                go.Scatter(name=country, mode='markers+lines',
                           x=data[data['location'] == country]['date'],
                           y=data[data['location'] == country][col_name])
            )

    fig = go.Figure(data=traces)
    fig.update_traces(marker={'size': 3}, line={'width': 1})
    fig.update_layout(hovermode='x', showlegend=True,
                      legend={'orientation': 'h'},
                      margin={'t': 50})

    return fig


if __name__ == '__main__':
    app.run_server(debug=False)
