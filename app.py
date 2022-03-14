import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

import numpy as np
import pandas as pd

#Declaration de l'app + CSS stylesheet pour customiser la page
app = dash.Dash(__name__)

#Cleaning
df = pd.read_csv('C://Users//hp//Projects VS CODE//DataVizP//ExportData - Copyy.csv')
df.drop(columns= 'Unnamed: 119', inplace = True)
df.dropna(inplace = True)
df.drop(columns = ["Code de la section CTCI","Code de la division CTCI","Code du groupe CTCI"],inplace =True)

#Fonctions qui facilite la création de liste de colonnes
def value_maker(n,m):
    l = []
    for i in df.columns :
        if m== 0 and ('Valeur DHS' in i) and (str(n) in i):
            l.append(i)
        if m== 1 and ('Poids en KG' in i) and (str(n) in i):
            l.append(i)
    return l

#Créer les colonnes d'année en fonction du revenue et du poids
for i in range(2017,2020):
    df['Year DHS '+str(i)] = df[value_maker(i,0)].sum(axis = 1)
    df['Poids KG '+str(i)] = df[value_maker(i,1)].sum(axis = 1)

#Group by continent et type de flux
cont_grp = df.groupby(['Continent',"Libellé du flux"])
y_list = ['Year DHS 2017','Year DHS 2018','Year DHS 2019']
w_list = ["Poids KG 2017", "Poids KG 2018","Poids KG 2019"]

#Imp Exp selon l'année en poids et en dhs
cont_DHS = cont_grp[y_list].apply(sum).reset_index()
cont_KG = cont_grp[w_list].apply(sum).reset_index()

#Benefice par continent par an
t = cont_DHS.groupby(["Libellé du flux"])
imp = t[["Continent"]+y_list].get_group("Importations CAF").reset_index(drop = True)
exp = t[["Continent"]+y_list].get_group("Exportations FAB").reset_index(drop = True)
for i in range(2017,2020):
    exp["Benefice DHS "+str(i)] = exp["Year DHS "+str(i)].subtract(imp["Year DHS "+str(i)])
benefice = exp[["Continent","Benefice DHS 2017","Benefice DHS 2018","Benefice DHS 2019"]]

#Import export par nation par année
country_grp = df.groupby(["Code du pays","Libellé du flux"])
country_DHS = country_grp[y_list].apply(sum).reset_index()

#Normlisation du code des pays en Alpha-3 code
df2 = pd.read_csv('C://Users//hp//Projects VS CODE//DataVizP//Iso_country_code.csv')
t1 = country_DHS.set_index("Code du pays")
t2 = df2.set_index("Alpha-2 code")
country_iso3 = pd.merge(t1,t2[["Alpha-3 code","English short name lower case"]],how = "inner",left_index =True,right_index=True)
country_iso3= country_iso3.reset_index(drop=True)

#Préparation de la pie chart
products = df.groupby(["Libellé de la section CTCI","Libellé du flux"])
products = products[y_list+w_list+value_maker(2017,0)+value_maker(2018,0)+value_maker(2019,0)].apply(sum).reset_index()

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}
lay={
        'plot_bgcolor': colors['background'],
        'paper_bgcolor': colors['background'],
        'font': {
            'color': colors['text']
        }
    }
#DashApp
app.layout = html.Div(children=[
    html.Div([
            dcc.Slider(
                id='year-slider',
                min=2017,
                max=2019,
                value=2017,
                marks={str(year): str(year) for year in range(2017,2020)},
                step=None
            )
        ],className="row"),#failsafe(xQzcxop)
    html.Div([
        html.Div([
            dcc.Graph(id ='bar_graph')
        ],className="six columns",style={'color': colors['text']}),
        html.Div([
            dcc.Graph(id ='pie_graph')
        ],className="six columns")
    ], className="row"),
    html.Div([
        html.Div([
            dcc.Graph('map_graph')
        ],className="six columns"),
        html.Div([
            dcc.Graph('line_graph')
        ],className="six columns")
    ], className="row"),
    dcc.RadioItems(
        id = 'radio',
        options=[
            {'label': 'Importations CAF', 'value':'Importations CAF'},
            {'label': 'Exportations FAB', 'value':'Exportations FAB'}
        ],
        value='Exportations FAB',
        labelStyle={'display': 'inline-block'},
        style={'color': colors['text']}
    )
],style={
  'verticalAlign':'middle',
  'textAlign': 'center',
  'position':'fixed',
  'width':'100%',
  'height':'100%',
  'top':'0px',
  'left':'0px',
  'z-index':'1000'
})


@app.callback(
    Output('bar_graph','figure'),
    Output('map_graph','figure'),
    Output('pie_graph','figure'),
    Output('line_graph','figure'),
    Input('year-slider', 'value'),
    Input('radio','value'))
def update_figure(selected_year,selected_flux):
    filt_map= country_iso3["Libellé du flux"] == selected_flux
    filt_pie= products["Libellé du flux"] == selected_flux
    
    products_line= products[filt_pie].reset_index(drop=True)
    products_line= products_line[["Libellé de la section CTCI"]+value_maker(selected_year,0)].set_index("Libellé de la section CTCI").transpose(copy=True).reset_index()
    months =["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Aout","Septembre","Octobre","Novembre","Décembre"]
    products_line.drop("index", axis = 1, inplace = True)
    products_line["index"] = months

    fig_map=go.Figure(data=go.Choropleth(
        locations = country_iso3[filt_map]['Alpha-3 code'],
        z = country_iso3[filt_map]['Year DHS '+str(selected_year)],
        text = country_iso3[filt_map]['English short name lower case'],
        colorscale = 'brbg',
        autocolorscale=False,
        reversescale=True,
        marker_line_color='darkgrey',
        marker_line_width=0.5,
        colorbar_tickprefix = '$',
        colorbar_title = 'Cost<br>Billions DHS',
    ),layout=lay)
    
    fig_bar = px.bar(benefice, x="Benefice DHS "+str(selected_year) , y = "Continent",color_discrete_sequence=px.colors.sequential.Plasma,title='Benefice Par Continent')

    fig_pie = px.pie(products[filt_pie].reset_index(drop=True),values="Poids KG "+str(selected_year),names="Libellé de la section CTCI",
    color_discrete_sequence=px.colors.sequential.Plasma,title='Pourcentage des Imp/Exp en KG')

    fig_line=px.line(products_line,x="index",y=products_line.columns[1:],color_discrete_sequence=px.colors.sequential.Plasma,title="Evolution de l'Imp/Exp par produits",template="plotly_dark")

    
    fig_bar.update_layout(transition_duration=500,showlegend=False,template="plotly_dark")
    fig_map.update_layout(transition_duration=500,showlegend=False,title="Degré d'Imp/Exp par pays")
    fig_pie.update_layout(transition_duration=500,showlegend=False,template="plotly_dark")
    fig_line.update_layout(transition_duration=500,showlegend=False)

    fig_map.update_geos(showocean=True,oceancolor="LightBlue")

    return fig_bar,fig_map,fig_pie,fig_line

if __name__ == '__main__':
    app.run_server(debug=True)
