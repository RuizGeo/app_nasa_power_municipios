# Importar as bibliotecas
import pandas as pd
import geopandas as gpd
import json
import requests
import matplotlib.pyplot as plt
import streamlit as st

import folium
from streamlit_folium import st_folium
import datetime
import plotly.express as px
import plotly.graph_objects as go

import matplotlib.colors as mcolors
from utils import obter_shapefile_municipios, obter_municipios_por_estado , obter_dados_climaticos

st.set_page_config(layout="wide",page_title="Análise Climática por Município")  # Permite usar toda a largura da tela

st.title("🌍 Análise da Temperatura e da Precipitação por Município")
st.markdown('Explore os dados meteorológicos de temperatura e precipitação de diferentes municípios de forma interativa 📊🌦️')

# Parâmetros
uf = 'MT'

# Dicionários de códigos IBGE
dict_uf = {'MT':'51', 'SP':'35', 'RJ':'33', 'MG':'31', 'AM':'13', 'PA':'15'
           , 'BA':'29', 'RS':'43', 'PR':'41', 'SC':'42', 'GO':'52', 'MS':'50'
           , 'TO':'17', 'RO':'11', 'AC':'12', 'RR':'14', 'AP':'16', 'MA':'21'
           , 'PI':'22', 'CE':'23', 'RN':'24', 'PB':'25', 'PE':'26', 'AL':'27'
           , 'SE':'28', 'DF':'53', 'ES':'32'}

# Criando um selectbox para escolher a cidade
uf_selecionado = st.sidebar.selectbox("Escolha o Estado:",dict_uf.keys())

# Obter o shapefile
gdf = obter_shapefile_municipios(uf_selecionado)

# Setar o CRS
gdf = gdf.set_crs(epsg=4674)

# Exemplo de uso:
df_mun = obter_municipios_por_estado(uf_selecionado)

# nomes municípios
municipios = df_mun['municipio'].values

# Para criar um dicionário de código -> nome:
dict_mun = dict(zip(df_mun['codigo_ibge'], df_mun['municipio']))

# Criando um selectbox para escolher a cidade
cidade_selecionada = st.sidebar.selectbox("Escolha uma cidade:", df_mun['municipio'])

# Selecionar o código IBGE da cidade a partir da cidade_selecionada
geocod = str(df_mun[df_mun['municipio'] == cidade_selecionada]['codigo_ibge'].to_list()[0])

# Informar no sidebar a cidade selecionada
st.sidebar.write(f"**Código do IBGE da cidade selecionada:** {geocod}")

# Selecionar o GeoDataFrame
gdf_municipio = gdf[gdf.codarea == geocod]

# Obter as coordenadas
long_x = gdf_municipio.geometry.centroid.x.values[0]
lat_y = gdf_municipio.geometry.centroid.y.values[0]

# Criar o mapa com Folium
mapa = folium.Map(location=[lat_y, long_x], zoom_start=10)
# Exibir no Streamlit
st.header("Município selecionado")

# Adicionar a camada de Imóveis Rurais
folium.GeoJson(
    data=gdf_municipio,  # GeoDataFrame convertido diretamente em GeoJson
    name = 'Município',  # Nome da camada no LayerControl
    tooltip=folium.GeoJsonTooltip(  # Configurar tooltip
        fields=['codarea'],  # Coluna(s) para mostrar no tooltip
        aliases=['Código município: '],  # Nomes amigáveis no tooltip
        localize=True
    ),
    style_function=lambda x: {
        'fillColor': 'red',  # Cor de preenchimento
        'color': 'black',       # Cor das bordas
        'weight': 1,            # Largura das bordas
        'fillOpacity': 0.2     # Opacidade do preenchimento
    }
).add_to(mapa)
# Adicionar Folium
st_folium(mapa, use_container_width=True, height=1000)

# Definir data mínima e máxima
start_date = datetime.date(2022, 1, 1)
end_date = datetime.date(2025, 11, 24)

# Obtendo as datas de início e fim
# Criar o seletor de intervalo de datas no sidebar
date_range = st.sidebar.date_input(
    "Selecione o intervalo de datas:",
    value=(start_date, end_date),
    min_value=datetime.date(2020, 1, 1),
    max_value=datetime.date(2025, 12, 31),
)
# Verificar se o usuário selecionou um intervalo válido
if isinstance(date_range, tuple) and len(date_range) == 2:
    # As datas
    start_date = date_range[0].strftime("%Y%m%d")  # Exemplo: '20240101'
    end_date = date_range[1].strftime("%Y%m%d")  # Exemplo: '20240131'

    # Exibir as datas formatadas
    st.sidebar.write(f"**Data de Início:** {start_date}")
    st.sidebar.write(f"**Data de Fim:** {end_date}")

    # Obter os dados climáticos
    df = obter_dados_climaticos(long_x, lat_y, start_date, end_date)

    # Calcular a média dos dados por ano e mês
    df_mean = df.groupby(['year', 'month']).mean()

    # Calcular o desvio padrão dos dados por ano e mês
    df_std = df.groupby(['year', 'month']).std()

    # Calcular a suma dos dados por ano e mês
    df_sum = df.groupby(['year', 'month']).sum()

    #@title Plotar o gráfico do comportamento da Precipitação (Ano e Mês)
    # Transformar índices em colunas
    dfp = df_sum.reset_index()

    # Criar o gráfico com Plotly
    fig = px.line(
        dfp, x="month", y="prec", color="year",
        markers=True, title="Precipitação Mensal por Ano",
        labels={"month": "Mês", "prec": "Precipitação", "year": "Ano"},
        color_discrete_sequence=px.colors.sequential.Blues  # Usando a paleta do Plotly

        # Suaviza a linha
    )
    # Melhorar layout do gráfico
    fig.update_layout(
        xaxis=dict(title="Mês",
            tickmode="array",
            tickvals=list(range(1, 13)),  # Posições dos meses
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]  # Nomes dos meses
        ),
        yaxis=dict(title="Precipitação (mm)"),
        legend_title="Ano",
        template="plotly_white"
    )

    # Exibir no Streamlit
    st.plotly_chart(fig)

    # Transformar índices em colunas
    dft = df_mean.reset_index()

    # Criar o gráfico com Plotly
    fig = px.line(
        dft, x="month", y="temp", color="year",
        markers=True, title="Temperatura média Mensal por Ano",
        labels={"month": "Mês", "temp": "Temperatura", "year": "Ano"},
        color_discrete_sequence=px.colors.sequential.Reds  # Usando a paleta do Plotly

        # Suaviza a linha
    )

    # Melhorar layout do gráfico
    fig.update_layout(
        xaxis=dict(title="Mês",
            tickmode="array",
            tickvals=list(range(1, 13)),  # Posições dos meses
            ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]  # Nomes dos meses
        ),
        yaxis=dict(title="Temperatura média (°C)"),
        legend_title="Ano",
        template="plotly_white"
    )

    # Exibir no Streamlit
    st.plotly_chart(fig)

    #Mostrar o dataframe
    st.subheader("Dados Climáticos")   
    st.dataframe(df, use_container_width=True)
else:

    st.sidebar.warning("Por favor, selecione um intervalo válido de datas.")




