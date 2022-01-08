from dash import dcc, html
from dash.dependencies import Input, Output
from plotly import graph_objects as go
# bootstrap components for custom layouts
import dash_bootstrap_components as dbc

# connect app files
from app import app
from apps import data


# ------------------------------------------------------------------------------
# Graph Object


graph = [
    html.Div(
        dcc.Graph(
            id='visualization',
            figure={},
            className='h-100',
            config={'displayModeBar': False}
        ), style={'height': '52vh'}
    ),

    html.Div(
        dbc.Row([
            dbc.Col(
                html.Div(
                    html.P(
                        id='slider-label-1',
                        children={}
                    )
                ), width=2, style={'text-align': 'center'}
            ),
            dbc.Col(
                dcc.RangeSlider(
                    id='date-slider',
                    min=0,
                    max=10,
                    value=[0, 10],
                    dots=True,
                    allowCross=False), width=8
            ),
            dbc.Col(
                html.Div(
                    html.P(
                        id='slider-label-2',
                        children={}
                    )
                ), width=2, style={'text-align': 'center'}
            )
        ]), style={'height': '3vh'}
    )
]


# ------------------------------------------------------------------------------
# Callbacks


@app.callback(Output('slider-label-1', 'children'),
              Output('slider-label-2', 'children'),
              Input('date-slider', 'value'))
def update_slider_labels(slider_range):
    label1, label2 = slider_range
    return label1, label2
    

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

        resampled = data.data[['location', 'date', col_name]].groupby('location').rolling(7, on='date').sum()

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
                           x=data.data[data.data['location'] == country]['date'],
                           y=data.data[data.data['location'] == country][col_name])
            )

    fig = go.Figure(data=traces)
    fig.update_traces(marker={'size': 3}, line={'width': 1})
    fig.update_layout(hovermode='x', showlegend=True,
                      legend={'orientation': 'h'},
                      margin={'t': 50})

    return fig
