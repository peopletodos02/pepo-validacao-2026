import streamlit as st
import pandas as pd
import requests # Importante para falar com o Automate
from PIL import Image

st.set_page_config(page_title="PEPO 2026", layout="wide")

# COLE A URL QUE O POWER AUTOMATE GEROU AQUI
URL_AUTOMATE = "SUA_URL_AQUI"

# Para ler os dados, vamos usar o link do Google Sheets que já funciona
URL_DADOS = "https://docs.google.com/spreadsheets/d/1BLGYQzPxbHgHFRIUALfLqj-Sdls9mKFLgUyH5YXH-qk/gviz/tq?tqx=out:csv&sheet=Dados"

@st.cache_data(ttl=60)
def carregar():
    return pd.read_csv(URL_DADOS)

df = carregar()

if df is not None:
    st.title("Validação Pesquisa Pepo 2026")
    
    # Filtro de Gestor
    gestor_sel = st.selectbox("Quem é você?", [""] + list(df['Gestor Avaliador'].unique()))

    if gestor_sel:
        equipe = df[df['Gestor Avaliador'] == gestor_sel]
        
        for i, row in equipe.iterrows():
            nome = row['Nome']
            with st.expander(f"👤 {nome}", expanded=True):
                g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}")
                p1 = st.selectbox("1º Par:", df['Nome'].unique(), key=f"p1_{i}")
                
                if st.button(f"Enviar Validação de {nome}", key=f"btn_{i}"):
                    dados_envio = {
                        "Data Envio": pd.Timestamp.now().strftime("%d/%m/%Y"),
                        "Gestor": gestor_sel,
                        "Colaborador": nome,
                        "Gestor OK": g_ok,
                        "P1": p1
                    }
                    # Envia para o Power Automate
                    resposta = requests.post(URL_AUTOMATE, json=dados_envio)
                    if resposta.status_code == 202:
                        st.success(f"Enviado com sucesso!")
                    else:
                        st.error("Erro no envio.")