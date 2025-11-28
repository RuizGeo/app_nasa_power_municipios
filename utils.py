import pandas as pd
import geopandas as gpd
import json
import requests
import streamlit as st
from datetime import datetime, date

hora_atual = datetime.now().time()

@st.cache_data
def obter_shapefile_municipios(uf):
    
    # URL para municípios (v4 da API)
    url = f"https://servicodados.ibge.gov.br/api/v4/malhas/estados/{uf}?formato=application/json&intrarregiao=Municipio&qualidade=intermediaria"
    # Obtendo acesso a URL
    response = requests.get(url) #  Envia uma requisição HTTP GET para a url.
    # Verificar se
    if response.status_code == 200: #  Se for 200, significa que os dados foram baixados corretamente

        municipios  = gpd.read_file(response.text)# contém os dados retornados pela URL, que devem estar em um formato compatível com geopandas, como GeoJSON,
        st.sidebar.write(f'Hora {hora_atual}')
        return municipios
    
    else:
        print("Erro:", response.status_code, response.text)  # Debug detalhado

@st.cache_data
def obter_municipios_por_estado(uf: str):
    """
    Obtém a lista de municípios de um estado específico com códigos IBGE
    
    Parâmetros:
    uf (str): Sigla da UF (ex: 'SP', 'RJ', 'MG')
    
    Retorna:
    DataFrame com colunas: ['codigo_ibge', 'municipio', 'uf']
    """
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        dados = response.json()
        
        municipios = [{
            'codigo_ibge': mun['id'],
            'municipio': mun['nome'],
            'uf': uf.upper()
        } for mun in dados]
        
        return pd.DataFrame(municipios)
        
    else:
        print(f"Erro {response.status_code}: {response.text}")
        return pd.DataFrame()
    
@st.cache_data
def obter_dados_climaticos(long_x, lat_y, start_date, end_date):
    """
    Obtém os dados climáticos de precipitação e temperatura da API da NASA POWER            "
    """
    # Definir os parâmetros do EndPoint
    variavel = 'PRECTOTCORR,T2M'#'RH2M',#T2M_MAX,T2M_MIN,T2M,QV2M'
    # URL NASA Power
    endpoint_nasa_power = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={variavel}&community=SB&longitude={long_x}&latitude={lat_y}&start={start_date}&end={end_date}&format=JSON"

    # Aplicar a requisição e obter o conteúdo
    req_power = requests.get(endpoint_nasa_power).content

    # Carregar o conteúdo como json
    json_power = json.loads(req_power)

    # Converter json para DataFrame
    df = pd.DataFrame(json_power['properties']['parameter'])

    # renomear colunas
    df.rename(columns = {'PRECTOTCORR':'prec','T2M':'temp'},inplace=True)

    #@title Agrupar os dados por ano e mês
    # Convertendo o índice para datetime
    df.index = pd.to_datetime(df.index)
    
    # Extrair o mês
    df['month'] = df.index.month
    # Extrair o ano
    df['year'] = df.index.year

    return df
