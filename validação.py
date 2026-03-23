import streamlit as st
import pandas as pd
import requests
import os
from PIL import Image
from datetime import datetime
import uuid

# Configurações Iniciais
st.set_page_config(page_title="PEPO 2026", layout="wide")

# 🔴 ATENÇÃO: Verifique se este link é o atual do seu Power Automate
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

# --- EXIBIÇÃO DAS LOGOS CENTRALIZADAS ---
col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns([1, 1, 2, 1, 1])
with col_l3:
    try:
        st.image("LOGO.png", use_container_width=True)
        st.image("mascote_pepo.png", width=150)
    except:
        st.write("### 🤖 PEPO 2026")

@st.cache_data(ttl=10)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL): return None
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower()
    if 'data de admissão' in df.columns:
        df['data de admissão'] = pd.to_datetime(df['data de admissão'], errors='coerce')
    return df

df_base = carregar_dados()

if df_base is not None:
    st.title("Validação Pesquisa Pepo 2026")
    st.markdown("---")

    col_gestor = 'gestor avaliador'
    if col_gestor in df_base.columns:
        gestores = sorted(df_base[col_gestor].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + list(gestores))

        if gestor_sel:
            equipe = df_base[df_base[col_gestor] == gestor_sel].copy()
            
            # --- REGRA DE ELEGIBILIDADE (Gestores inclusos na lista geral) ---
            data_limite = pd.to_datetime('2026-01-31')
            def formatar_nome(row):
                if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
                    return f"{row['nome']} ✅"
                return f"{row['nome']} ❌"
            
            df_base['nome_formatado'] = df_base.apply(formatar_nome, axis=1)
            lista_geral_pares = sorted(df_base['nome_formatado'].unique())

            respostas_lote = []
            pendencia_pares = False

            for i, row in equipe.iterrows():
                nome_f = row.get('nome', f"Colab {i}")
                with st.expander(f"👤 Validar: {nome_f}", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c2: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c3: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c4: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(f"1º Par para {nome_f} *", [""] + lista_geral_pares, key=f"p1_{i}")
                    p2 = st.selectbox(f"2º Par para {nome_f} *", [""] + lista_geral_pares, key=f"p2_{i}")

                    if p1 == "" or p2 == "": pendencia_pares = True

                    respostas_lote.append({
                        "colaborador": nome_f, "p1": p1, "p2": p2,
                        "status_gestor": g_ok, "status_cargo": c_ok,
                        "status_unidade": u_ok, "status_depto": d_ok
                    })

            st.divider()
            obs_geral = st.text_area("Observações (Opcional):")

            if st.button("🚀 Finalizar e Salvar Dados", type="primary"):
                if pendencia_pares:
                    st.error("⚠️ Por favor, selecione os dois pares para todos os colaboradores.")
                elif any("❌" in r['p1'] or "❌" in r['p2'] for r in respostas_lote):
                    st.error("⚠️ Você selecionou um par não elegível (❌).")
                else:
                    # Geração do Protocolo Único
                    protocolo = f"PEPO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
                    
                    payload = {
                        "gestor_avaliador": gestor_sel,
                        "protocolo": protocolo,
                        "observacoes": obs_geral,
                        "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "lista_equipe": respostas_lote
                    }
                    
                    try:
                        res = requests.post(WEBHOOK_URL, json=payload, timeout=20)
                        if res.status_code in [200, 202]:
                            st.balloons()
                            st.success(f"✅ Sucesso! Protocolo: {protocolo}")
                            st.info("Os dados foram enviados para a planilha oficial.")
                        else:
                            st.error(f"Erro no servidor ({res.status_code}).")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
