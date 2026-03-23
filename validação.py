import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import uuid

# Configurações Iniciais
st.set_page_config(page_title="PEPO 2026", layout="wide")

# URL do seu Webhook do Power Automate
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

# --- TOPO: LOGOS CENTRALIZADAS E LADO A LADO ---
col_esp_esq, col_central, col_esp_dir = st.columns([1, 3, 1])

with col_central:
    c1, c2 = st.columns([3, 1]) # Proporção 3 para a logo e 1 para o mascote
    with c1:
        if os.path.exists("LOGO.png"):
            st.image("LOGO.png", use_container_width=True)
    with c2:
        if os.path.exists("mascote_pepo.png"):
            st.image("mascote_pepo.png", width=100)

@st.cache_data(ttl=60)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL):
        return None
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower()
    if 'data de admissão' in df.columns:
        df['data de admissão'] = pd.to_datetime(df['data de admissão'], errors='coerce')
    return df

df_base = carregar_dados()

if df_base is not None:
    st.markdown("<h2 style='text-align: center;'>Validação Pesquisa Pepo 2026</h2>", unsafe_allow_html=True)
    st.markdown("---")

    col_gestor = 'gestor avaliador'
    if col_gestor in df_base.columns:
        gestores = sorted(df_base[col_gestor].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + list(gestores))

        if gestor_sel:
            # Filtra a equipe do gestor
            equipe = df_base[df_base[col_gestor] == gestor_sel].copy()
            
            # Regra de Elegibilidade (Data de admissão até 31/01/2026)
            data_limite = pd.to_datetime('2026-01-31')
            
            def formatar_nome_elegivel(row):
                if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
                    return f"{row['nome']} "
                return f"{row['nome']} ❌"
            
            # Lista Geral para seleção de pares (incluindo gestores)
            df_base['nome_formatado'] = df_base.apply(formatar_nome_elegivel, axis=1)
            lista_geral_pares = sorted(df_base['nome_formatado'].unique())

            respostas_lote = []
            pendencia_vazia = False

            for i, row in equipe.iterrows():
                nome_colab = row.get('nome', f"Colaborador {i}")
                with st.expander(f"👤 Validar: {nome_colab}", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c2: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c3: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c4: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(f"Selecione o 1º Par para {nome_colab} *", [""] + lista_geral_pares, key=f"p1_{i}")
                    p2 = st.selectbox(f"Selecione o 2º Par para {nome_colab} *", [""] + lista_geral_pares, key=f"p2_{i}")

                    if p1 == "" or p2 == "":
                        pendencia_vazia = True

                    respostas_lote.append({
                        "colaborador": nome_colab,
                        "p1": p1,
                        "p2": p2,
                        "status_gestor": g_ok,
                        "status_cargo": c_ok,
                        "status_unidade": u_ok,
                        "status_depto": d_ok
                    })

            st.markdown("---")
            obs_texto = st.text_area("Alguma observação sobre a validação da sua equipe?")

            if st.button("🚀 Enviar Validação Final", type="primary"):
                if pendencia_vazia:
                    st.error("⚠️ Por favor, selecione ambos os pares para todos os colaboradores da lista.")
                elif any("❌" in r['p1'] or "❌" in r['p2'] for r in respostas_lote):
                    st.error("⚠️ Você selecionou pares que não são elegíveis (marcados com ❌).")
                else:
                    # Gera um Protocolo Único (Data + Código Aleatório)
                    id_protocolo = f"PEPO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
                    
                    dados_finais = {
                        "gestor_avaliador": gestor_sel,
                        "protocolo": id_protocolo,
                        "observacoes": obs_texto,
                        "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "lista_equipe": respostas_lote
                    }
                    
                    try:
                        response = requests.post(WEBHOOK_URL, json=dados_finais, timeout=15)
                        if response.status_code in [200, 202]:
                            st.balloons()
                            st.success(f"✅ Validação enviada com sucesso! Protocolo: {id_protocolo}")
                            st.info("As informações já foram registradas na base oficial.")
                        else:
                            st.error(f"Falha ao enviar. Erro técnico: {response.status_code}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
else:
    st.error("Arquivo base_pepo.xlsx não encontrado no repositório.")
