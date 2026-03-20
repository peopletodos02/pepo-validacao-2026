import streamlit as st
import pandas as pd
import requests
import os
from PIL import Image
from datetime import datetime

# PEPOResponseFlow
st.set_page_config(page_title="PEPO 2026", layout="wide")

# COLE AQUI O LINK DO POWER AUTOMATE (Numa única linha e sem aspas extras)
# Verifique se o fluxo está "LIGADO" na tela inicial dele.
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com/powerautomate/automations/direct/workflows/14f4e4ebe95f4087bdf0959d5768773c/triggers/manual/paths/invoke?api-version=1"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'
NOME_IMAGEM = 'mascote_pepo.png'

@st.cache_data(ttl=20)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL):
        return None
    # Carrega e limpa os nomes das colunas
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower()
    
    # Converte coluna de admissão para data (ajustado para minúsculo pelo código)
    if 'data de admissão' in df.columns:
        df['data de admissão'] = pd.to_datetime(df['data de admissão'], errors='coerce')
    return df

df_base = carregar_dados()

if df_base is not None:
    # Mascote
    try:
        col_esq, col_meio, col_dir = st.columns([1, 2, 1])
        with col_meio: st.image(Image.open(NOME_IMAGEM), width=200)
    except: st.write("🤖 **PEPO**")
    
    st.title("Validação Pesquisa Pepo 2026")
    st.markdown("### Olá gestor, selecione seu nome e confirme as informações abaixo:")
    st.divider()

    col_gestor = 'gestor avaliador'
    if col_gestor in df_base.columns:
        gestores = sorted(df_base[col_gestor].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome:", [""] + list(gestores))

        if gestor_sel:
            equipe = df_base[df_base[col_gestor] == gestor_sel]
            
            # FILTRO DE ELEGIBILIDADE POR DATA
            # Regra: Admitidos até 31/01/2026
            if 'data de admissão' in df_base.columns:
                data_limite = pd.to_datetime('2026-01-31')
                # Filtra apenas quem tem data preenchida e está dentro da regra
                df_elegiveis = df_base[df_base['data de admissão'] <= data_limite]
                lista_pares = sorted(df_elegiveis['nome'].unique())
            else:
                lista_pares = sorted(df_base['nome'].unique())

            respostas_lote = []

            for i, row in equipe.iterrows():
                nome_f = row.get('nome', f"Colab {i}")
                with st.expander(f"👤 {nome_f}", expanded=True):
                    st.write(f"**Cargo:** {row.get('cargo')} | **Unidade:** {row.get('unidade')}")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c2: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c3: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c4: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(f"1º Par para {nome_f}:", [""] + lista_pares, key=f"p1_{i}")
                    p2 = st.selectbox(f"2º Par para {nome_f}:", [""] + lista_pares, key=f"p2_{i}")

                    respostas_lote.append({
                        "colaborador": nome_f,
                        "p1": p1, "p2": p2,
                        "status_gestor": g_ok, "status_cargo": c_ok,
                        "status_unidade": u_ok, "status_depto": d_ok
                    })

            if st.button("🚀 Finalizar e Salvar Dados", type="primary"):
                # Garanta que o JSON que o Power Automate recebe é este:
                payload = {
                    "gestor_avaliador": gestor_sel,
                    "data_envio": datetime.now().strftime("%d/%m/%Y"),
                    "lista_equipe": respostas_lote
                }
                try:
                    res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
                    if res.status_code in [200, 202]:
                        st.balloons()
                        st.success("✅ Tudo pronto! Dados salvos na planilha da Regi.")
                    else:
                        st.error(f"Erro {res.status_code}: O servidor recusou. Verifique se o fluxo está ATIVO no Power Automate.")
                except Exception as e:
                    st.error(f"Erro de conexão com o servidor: {e}. Verifique a URL no código.")
    else:
        st.error(f"Coluna '{col_gestor}' não encontrada na aba Base_Dados.")
else:
    st.error("Erro: Planilha base_pepo.xlsx não encontrada no GitHub.")
