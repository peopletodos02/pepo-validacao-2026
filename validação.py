import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import uuid

# Configurações Iniciais da Página
st.set_page_config(page_title="PEPO 2026", layout="wide")

# URL do Webhook do Power Automate
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

# --- DESIGN: LOGOS CENTRALIZADAS ---
c1, c2, c_logo, c_mascote, c5, c6 = st.columns([2, 1, 1.2, 0.8, 1, 2])
with c_logo:
    if os.path.exists("LOGO.png"): st.image("LOGO.png", width=180)
with c_mascote:
    if os.path.exists("mascote_pepo.png"): st.image("mascote_pepo.png", width=65)

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
    st.markdown("---")

    col_gestor_ref = 'gestor avaliador' # Coluna A
    col_setor = 'unidade' # Ajuste aqui se o nome da coluna de setor/unidade for outro

    if col_gestor_ref in df_base.columns:
        lista_gestores_unicos = sorted(df_base[col_gestor_ref].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + lista_gestores_unicos)

        if gestor_sel:
            equipe = df_base[df_base[col_gestor_ref] == gestor_sel].copy()
            data_limite = pd.to_datetime('2026-01-31')
            
            # Função para colocar o selo de elegibilidade
            def selo(row):
                if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
                    return f"{row['nome']}"
                return f"{row['nome']} ❌"

            respostas_lote = []
            erro_vazio = False

            for i, row in equipe.iterrows():
                nome_colab = row['nome']
                setor_colab = row[col_setor]

                with st.expander(f"👤 Validar: {nome_colab}", expanded=True):
                    # --- FILTRO INTELIGENTE DE PARES ---
                    # 1. Pessoas do mesmo setor
                    # 2. Todos os gestores (coluna A)
                    filtro = df_base[
                        (df_base[col_setor] == setor_colab) | 
                        (df_base['nome'].isin(lista_gestores_unicos))
                    ].copy()
                    
                    filtro['display'] = filtro.apply(selo, axis=1)
                    opcoes_pares = [""] + sorted(filtro['display'].unique())

                    c_g, c_c, c_u, c_d = st.columns(4)
                    with c_g: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c_c: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c_u: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c_d: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(f"1º Par para {nome_colab} *", opcoes_pares, key=f"p1_{i}")
                    p2 = st.selectbox(f"2º Par para {nome_colab} *", opcoes_pares, key=f"p2_{i}")

                    if p1 == "" or p2 == "": erro_vazio = True

                    respostas_lote.append({
                        "colaborador": nome_colab, "p1": p1, "p2": p2,
                        "status_gestor": g_ok, "status_cargo": c_ok,
                        "status_unidade": u_ok, "status_depto": d_ok
                    })

            st.markdown("---")
            campo_obs = st.text_area("Observações Gerais (Opcional):")

            if st.button("🚀 Enviar Validação Final", type="primary"):
                if erro_vazio:
                    st.error("⚠️ Atenção: Preencha os pares de todos.")
                elif any("❌" in r['p1'] or "❌" in r['p2'] for r in respostas_lote):
                    st.error("⚠️ Você selecionou um par não elegível (❌).")
                else:
                    id_protocolo = f"PEPO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
                    pacote = {
                        "gestor_avaliador": gestor_sel, "protocolo": id_protocolo,
                        "observacoes": campo_obs, "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "lista_equipe": respostas_lote
                    }
                    try:
                        resp = requests.post(WEBHOOK_URL, json=pacote, timeout=20)
                        if resp.status_code <= 202:
                            st.balloons(); st.success(f"✅ Enviado! Protocolo: {id_protocolo}")
                        else: st.error(f"Erro: {resp.status_code}")
                    except Exception as e: st.error(f"Erro: {e}")
