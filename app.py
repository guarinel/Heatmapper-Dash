import dash
import plotly.figure_factory as ff
import plotly
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH, ALL
import dash_core_components as dcc
import plotly.graph_objects as go
import dash_html_components as html
from dash.exceptions import PreventUpdate
import pandas as pd
import json

hm = at.HeatMapper(workstation=True)
global dict_of_df 
dict_of_df = {}
for item in hm.lib.list_symbols():
    hm.load_data(item)
    dict_of_df[item] = hm.df_data.copy() 
    
##################################LOAD DATA ######################################################    
names_and_values = []
names_and_values_to_plot = []
all_columns = []
disabled = []

def _is_cat(df):
    top_n = 100
    likely_cat = {}
    for var in df.columns:
        likely_cat[var] = 1.*df[var].value_counts(normalize=True).head(top_n).sum() > 0.8 #or some other threshold
    if 'daily_returns_std' in likely_cat.keys():
        likely_cat['daily_returns_std'] = False
    return [i for i in likely_cat.keys() if likely_cat[i]], [i for i in likely_cat.keys() if not likely_cat[i]]  


def description_card():
    return html.Div(
        id="description-card",
        children=[
            html.H5("Heatmapper Asimov"),
            html.H3("Welcome to the Heatmapper Dashboard"),
            html.Div(
                id="intro",
                children="Explore many different variables and strategies and their relationship with eachother. Select the simulation, and the parameters for the heatmap.",
            ),
        ],
    )

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] 

external_stylesheets = [dbc.themes.SANDSTONE] #SKETCHY

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    html.Div([
    html.Div(
            id="left-column",
            className="four columns",
            children=[description_card()] ),
            
    html.Div([
            dcc.Dropdown(
                id='simulation',
                options=[{'label': i, 'value': i} for i in hm.lib.list_symbols()],
                placeholder="Select a simulation",
                style = {'width': '49%'}),

            ],
        ),
    
    html.Div([
            html.Div(
                id='both_axis',
                children = [],
            )] , style={'width': '49%', 'display': 'inline-block', 'position':'relative'}),
        
    html.Div([
                html.Div([html.B("Update Database")]),
        
                html.Div([html.Button('update',id='update_button', n_clicks=0)]),] ,style={'width': '49%', 'top': '160px', 'right' : '220px', 'display': 'inline-block', 'position':'fixed'} ),    
        
    html.Div([html.B("For each different graph press reset")]),
    html.Div([html.Button('Reset',id='reset_button', n_clicks=0)]),
        
    ],  style ={'background': '#f9f9f9',  'position': 'relative',  'top': '0',  'height': '360px'} ),
    
    html.Div([
    html.Div(id = 'features', children = [], style = {'width': '46%', 'position': 'fixed',  'top': '360px', 'height': '400px', 'overflow': 'auto ', 'background': '#f9f9f9'}),
    html.Div(id = 'features_dummy', children = [], style = {'width': '54%', 'position': 'fixed', 'right' : '0px', 'top': '360px', 'height': '400px',  'background': '#f9f9f9'})]),
    
    html.Div(id = 'style_to_change', children =[dcc.Graph(id='heatmap', figure={}), 
             
         ], style={'position': 'fixed', 'width': '54%', 'top': '50px', 'right': '0px', 'backgroundColor': '#f9f9f9','visibility':'hidden'}), 
    
],style={'backgroundColor': '#f9f9f9'})

@app.callback(dash.dependencies.Output('simulation', 'value'),               
              [dash.dependencies.Input('update_button', 'n_clicks')],
              [dash.dependencies.State('both_axis', 'children')])

def _simulation_update(button, si):
    ctx = dash.callback_context
    trigger_loaded = ctx.triggered[0]['prop_id'].split('.')[0]
    if (trigger_loaded == 'update_button') and button != 0:
        for item in hm.lib.list_symbols():
            hm.load_data(item)
            dict_of_df[item] = hm.df_data.copy()
        return None
    else:
        raise dash.exceptions.PreventUpdate


@app.callback(
    dash.dependencies.Output('both_axis', 'children'),
    [dash.dependencies.Input('simulation', 'value')],
    [dash.dependencies.State('both_axis', 'children')])

def display_dropdowns_axis(simulation, children):
    dropdowns = []
    if simulation != None:
        df = dict_of_df[simulation].copy()
        cat_name, not_cat_name = _is_cat(df)
        for col in ['x_axis', 'y_axis', 'z_axis']:
            if col != 'z_axis':
                dropdowns.append(html.Div([html.B(col),
                                dcc.Dropdown(id= {'type': 'both_axis',
                                                  'index': col},
                                options=[{'label': i, 'value': i} for i in cat_name],
                                value = None,
                                style={'width': '49%'},              
                                placeholder=col)]))
            else:
                dropdowns.append(html.Div([html.B(col),
                                dcc.Dropdown(id= {'type': 'both_axis',
                                                  'index': col},
                                options=[{'label': i, 'value': i} for i in not_cat_name],
                                value = None,
                                style={'width': '49%'},
                                placeholder=col)]))
        return dropdowns
    else:
         raise dash.exceptions.PreventUpdate

@app.callback(
    dash.dependencies.Output('features', 'children'),
    [dash.dependencies.Input('simulation', 'value')],
    
    [dash.dependencies.State('features', 'children')])
def display_dropdowns(simulation, children):
    ctx = dash.callback_context
    trigger_loaded = ctx.triggered[0]['prop_id'].split('.')[0]
    if simulation != None:
        if trigger_loaded == 'simulation':
            df = dict_of_df[simulation].copy()
            cat_name, not_cat_name = _is_cat(df)
            dropdowns = []
            for col in cat_name:
                values_to_display = df[col].value_counts().index        
                dropdowns.append(html.Div([html.B(col),
                                 dcc.Dropdown(id= {'type': 'features',
                                                   'index': col},
                                    options=[{'label': i, 'value': i} if i not in [True, False] else {'label': str(i), 'value': str(i)} for i in values_to_display],
                                    style={'width': '95%'},
                                    value = [None if len(values_to_display) > 1 else values_to_display[0] if values_to_display[0] not in [True, False] else str(values_to_display[0])][0],
                                    placeholder = col)]))
            return dropdowns
        else:
            raise dash.exceptions.PreventUpdate
    else:
        raise dash.exceptions.PreventUpdate

@app.callback(
    dash.dependencies.Output({'type': 'both_axis', 'index': 'x_axis'}, 'options'),
    [dash.dependencies.Input({'type': 'both_axis', 'index': 'y_axis'}, 'value')],
    [dash.dependencies.State('simulation', 'value')])

def return_name_x_axis(y_axis, simulation):
    if simulation != None:
        df = dict_of_df[simulation].copy()
        cat_name, not_cat_name = _is_cat(df)
        return [{'label': i, 'value': i} for i in cat_name if i != y_axis]
    else:
        raise dash.exceptions.PreventUpdate

        
@app.callback(
    dash.dependencies.Output({'type': 'both_axis', 'index': 'y_axis'}, 'options'),
    [dash.dependencies.Input({'type': 'both_axis', 'index': 'x_axis'}, 'value')],
    [dash.dependencies.State('simulation', 'value')])

def return_name_y_axis(x_axis, simulation):
    if simulation != None:
        df = dict_of_df[simulation].copy()
        cat_name, not_cat_name = _is_cat(df)
        return [{'label': i, 'value': i} for i in cat_name if i != x_axis]
    else:
        raise dash.exceptions.PreventUpdate

        
@app.callback([dash.dependencies.Output({'type': 'features', 'index': ALL}, 'options'),
              dash.dependencies.Output({'type': 'features', 'index': ALL}, 'disabled')],
              
              [dash.dependencies.Input({'type': 'features', 'index': ALL}, 'value'),
               dash.dependencies.Input({'type': 'both_axis', 'index': 'y_axis'}, 'value'),
              dash.dependencies.Input({'type': 'both_axis', 'index': 'x_axis'}, 'value'),
              dash.dependencies.Input('reset_button', 'n_clicks')], 
             [dash.dependencies.State('simulation', 'value')])
         
def _modify_df(features, y_axis, x_axis, reset_button, simulation):
    ctx = dash.callback_context
    all_columns = []
    disabled = []

    if all(v is None for v in features) or (x_axis == None) or (y_axis == None):
        raise dash.exceptions.PreventUpdate
    else:
        if simulation != None:
            dl = dict_of_df[simulation].copy() 
            cat_name, not_cat_name = _is_cat(dl)
            input_ = ctx.triggered[0]['value']

            try:
                trigger_loaded = json.loads((ctx.triggered[0]['prop_id']).split('.')[0])['index']
            except:
                trigger_loaded = ctx.triggered[0]['prop_id'].split('.')[0]

            if input_ == 'False':
                input_ = False
            if input_ == 'True':
                input_ = True

            if trigger_loaded not in ['x_axis', 'y_axis', 'reset_button', 'simulation']:
                names_and_values.append([trigger_loaded, input_])

            try:
                if ctx.triggered[0]['prop_id'].split('.')[0] == 'reset_button':
                    names_and_values.clear()
            except:
                pass
                
            if len(names_and_values) > 0:
                for tupla in names_and_values:
                    if (tupla[0] != None) and (tupla[1] != None):
                        dl = dl[dl[tupla[0]] == tupla[1]]   
            for col in cat_name:
                values_to_display_final = dl[col].value_counts().index  
                all_columns.append([{'label': i, 'value': i} if i not in [True, False] else {'label': str(i), 'value': str(i)} for i in values_to_display_final])
                if col not in [x_axis, y_axis]:
                    disabled.append(False)
                else:
                    disabled.append(True)

            return [all_columns,disabled]

@app.callback(
    [dash.dependencies.Output({'type': 'features', 'index': ALL}, 'value')],
    [dash.dependencies.Input('reset_button', 'n_clicks')],
    [dash.dependencies.State('simulation', 'value')])
    
def button(reset, simulation):
    A = []
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id']
    if trigger.split('.')[0] != 'reset_button' or reset == 0: 
        raise dash.exceptions.PreventUpdate
    else:                 
        dl = dict_of_df[simulation].copy() 
        cat_name, not_cat_name = _is_cat(dl)
        
        for col in cat_name:
            values = dl[col].value_counts().index
            if len(values) == 1 :
                A.append([values[0] if values[0] not in [True, False] else str(values[0])][0])
            else:                 
                A.append(None)
        return [A]
    
@app.callback(
    [dash.dependencies.Output('style_to_change', 'style'),
    dash.dependencies.Output('heatmap', 'figure')],
    
    [dash.dependencies.Input({'type': 'features', 'index': ALL}, 'value'),
     dash.dependencies.Input({'type': 'both_axis', 'index': 'x_axis'}, 'value'),
     dash.dependencies.Input({'type': 'both_axis', 'index': 'y_axis'}, 'value'),
     dash.dependencies.Input({'type': 'both_axis', 'index': 'z_axis'}, 'value')], 
    
    [dash.dependencies.State('simulation', 'value')])
     
def _create_graph(features, x_axis, y_axis, z_axis, simulation):   

    if simulation is not None:
        dataframe_to_plot = dict_of_df[simulation].copy()
        ctx = dash.callback_context
        input_ = ctx.triggered[0]['value']
        if input_ == 'False':
            input_ = False
        if input_ == 'True':
            input_ = True
        if (sum([1 for v in features if v is None]) > 2) or (x_axis is None) or (y_axis is None) or (z_axis is None):     
            raise dash.exceptions.PreventUpdate
        else:
            for tupla in names_and_values:
                if (tupla[0] != None) and (tupla[1] != None):
                    dataframe_to_plot = dataframe_to_plot[dataframe_to_plot[tupla[0]] == tupla[1]]
                    
                    
            dataframe_to_plot = (dataframe_to_plot.groupby([y_axis, x_axis])[z_axis].sum()).to_frame()
            dataframe_to_plot = dataframe_to_plot.pivot_table(columns =x_axis, index = y_axis, values =z_axis)
            dataframe_to_plot = dataframe_to_plot.round().astype('Int64')
            dataframe_to_plot.fillna(0, inplace = True)

            fig1 = ff.create_annotated_heatmap(x=dataframe_to_plot.columns.to_list(), y=dataframe_to_plot.index.to_list(), z=dataframe_to_plot.values, annotation_text = dataframe_to_plot.values, colorscale='greens',  showscale = True)

            fig = plotly.subplots.make_subplots(rows=1, cols=1, subplot_titles=("HEATMAP", 'dfdf'))
            fig.add_trace(fig1.data[0], 1, 1)
            annot1 = list(fig1.layout.annotations)
            for k in range(len(annot1)):
                annot1[k]['xref'] = 'x1'
                annot1[k]['yref'] = 'y1'
                annot1[k]['align']= 'center'
            for anno in annot1:
                fig.add_annotation(anno)
                
            fig['layout'].update(
                    xaxis_title=x_axis,
                    yaxis_title=y_axis,
                    height=700,
                    yaxis=go.YAxis(ticks='', dtick = [86400000.0 if y_axis == 'date' else ""][0]),
                    xaxis=go.YAxis(ticks='', dtick = [86400000.0 if x_axis == 'date' else ""][0]),
                    autosize = True,
                     
                    paper_bgcolor = '#f9f9f9')
            stilo = {'position': 'fixed', 'width': '54%', 'top': '50px', 'right': '0px', 'backgroundColor': '#f9f9f9'}

            
            return [stilo, fig]
    else:
        raise dash.exceptions.PreventUpdate


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, host='10.112.1.22', port = 1234)
