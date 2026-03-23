import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import uuid

st.set_page_config(page_title="PEPO 2026", layout="wide")

# Verifique sempre se este link é o último gerado pelo Power Automate
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

# --- LOGOS LADO A LADO ---
col_logo, col_mascote = st.columns([2, 1]) 
with col_logo:
    if os.path.exists("LOGO.png"): st.image("LOGO.png", width=250)
with col_mascote:
    if os.path.exists("mascote_pepo.png"): st.image("mascote_pepo.png", width=80)

@st.cache_data(ttl=60)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL): return None
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower()
    if 'data de admissão' in df.columns:
        df['data de admissão'] = pd.to_datetime(df['data de admissão'], errors='coerce')
    return df

df_base = carregar_dados()

if df_base is not None:
    st.markdown("<h2 style='text-align: center;'>Validação Pesquisa Pepo 2026</h2>", unsafe_allow_html=True)
    
    col_gestor_ref = 'gestor avaliador'
    if col_gestor_ref in df_base.columns:
        gestores_lista = sorted(df_base[col_gestor_ref].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + list(gestores_lista))

        if gestor_sel:
            equipe = df_base[df_base[col_gestor_ref] == gestor_sel].copy()
            data_limite = pd.to_datetime('2026-01-31')
            
            # Identifica quem é gestor (Coluna A da planilha)
            # Supondo que a coluna A no Excel seja 'gestor avaliador'
            todos_gestores = set(df_base[col_gestor_ref].dropna().unique())

            respostas_lote = []
            pendencia = False

            for i, row in equipe.iterrows():
                nome_colab = row['nome']
                unidade_colab = row['unidade'] # Filtro por área/unidade

                with st.expander(f"👤 Validar: {nome_colab}", expanded=True):
                    # Lógica de Filtro de Pares: Mesma Unidade OU ser Gestor
                    filtro_pares = df_base[
                        (df_base['unidade'] == unidade_colab) | 
                        (df_base['nome'].isin(todos_gestores))
                    ].copy()
                    
                    def sel_elegivel(r):
                        check = "" if pd.notnull(r['data de admissão']) and r['data de admissão'] <= data_limite else "❌"
                        return f"{r['nome']} {check}"
                    
                    filtro_pares['display'] = filtro_pares.apply(sel_elegivel, axis=1)
                    opcoes_pares = [""] + sorted(filtro_pares['display'].unique())

                    c1, c2, c3, c4 = st.columns(4)
                    with c1: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}")
                    with c2: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}")
                    with c3: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}")
                    with c4: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}")

                    p1 = st.selectbox(f"1º Par para {nome_colab} *", opcoes_pares, key=f"p1_{i}")
                    p2 = st.selectbox(f"2º Par para {nome_colab} *", opcoes_pares, key=f"p2_{i}")

                    if p1 == "" or p2 == "": pendencia = True
                    respostas_lote.append({
                        "colaborador": nome_colab, "p1": p1, "p2": p2,
                        "status_gestor": g_ok, "status_cargo": c_ok,
                        "status_unidade": u_ok, "status_depto": d_ok
                    })

            obs = st.text_area("Observações:")
            if st.button("🚀 Enviar Dados"):
                if pendencia: st.error("Selecione os pares!")
                else:
                    protocolo = f"PEPO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
                    payload = {
                        "gestor_avaliador": gestor_sel, "protocolo": protocolo,
                        "observacoes": obs, "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "lista_equipe": respostas_lote
                    }
                    res = requests.post(WEBHOOK_URL, json=payload)
                    if res.status_code <= 202: st.success(f"Enviado! Protocolo: {protocolo}"); st.balloons()
                    else: st.error("Erro no envio.")
