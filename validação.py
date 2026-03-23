import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import uuid
import base64
import json

# --- CONFIGURAÇÕES DO GITHUB PARA BACKUP ---
# As variáveis abaixo buscam os dados que você salvou nos Secrets do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    BRANCH = "main"
except:
    st.error("Erro: Verifique se GITHUB_TOKEN e REPO_NAME estão configurados nos Secrets do Streamlit.")

# Configurações Iniciais
st.set_page_config(page_title="PEPO 2026", layout="wide")

# Webhook do Power Automate
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

# Função para salvar backup no GitHub
def salvar_backup_github(dados, protocolo):
    try:
        path = f"backups/{protocolo}.json"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{path}"
        conteudo_json = json.dumps(dados, indent=4, ensure_ascii=False)
        conteudo_base64 = base64.b64encode(conteudo_json.encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        payload = {"message": f"Backup: {protocolo}", "content": conteudo_base64, "branch": BRANCH}
        requests.put(url, json=payload, headers=headers)
    except:
        pass

# --- DESIGN: LOGOS CENTRALIZADAS ---
c1, c2, c_logo, c_mascote, c5, c6 = st.columns([2, 1, 1.2, 0.8, 1, 2])
with c_logo:
    if os.path.exists("LOGO.png"): st.image("LOGO.png", width=180)
with c_mascote:
    if os.path.exists("mascote_pepo.png"): st.image("mascote_pepo.png", width=120)

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
    st.markdown("<h2 style='text-align: center;'>Validação - PEPO 2026</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; font-size: 18px; color: #555;'>
    Olá Gestor, selecione abaixo o seu nome e confirme os dados da sua equipe.<br>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    col_gestor_ref = 'gestor avaliador'

    if col_gestor_ref in df_base.columns:
        lista_gestores = sorted(df_base[col_gestor_ref].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + lista_gestores)

        if gestor_sel:
            equipe = df_base[df_base[col_gestor_ref] == gestor_sel].copy()
           
            data_limite = pd.to_datetime('2026-01-31')
            def selo(row):
                if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
                    return f"{row['nome']} "
                return f"{row['nome']} ❌"

            equipe['display_par'] = equipe.apply(selo, axis=1)
            opcoes_da_equipe = sorted(equipe['display_par'].unique())

            # REGRA: Se só tiver 1 pessoa no setor, adiciona os gestores avaliadores na lista
            if len(opcoes_da_equipe) <= 1:
                opcoes_gestores = sorted(df_base[df_base['nome'].isin(lista_gestores)].apply(selo, axis=1).unique())
                opcoes_pares = opcoes_da_equipe + ["----------"] + opcoes_gestores
            else:
                opcoes_pares = opcoes_da_equipe
           
            opcoes_pares = [""] + opcoes_pares

            respostas_lote = []
            erro_vazio = False
            erro_duplicado = False

            for i, row in equipe.iterrows():
                nome_colab = row['nome']
                with st.expander(f"👤 Validar: {nome_colab}", expanded=True):
                    c_g, c_c, c_u, c_d = st.columns(4)
                    with c_g: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c_c: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c_u: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c_d: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(f"1º Par para {nome_colab} *", opcoes_pares, key=f"p1_{i}")
                    p2 = st.selectbox(f"2º Par para {nome_colab} *", opcoes_pares, key=f"p2_{i}")

                    # Validação de preenchimento
                    if p1 == "" or p2 == "" or "---" in str(p1): 
                        erro_vazio = True
                    
                    # NOVA REGRA: Verifica se Par 1 e Par 2 são iguais para o mesmo funcionário
                    if p1 != "" and p1 == p2:
                        erro_duplicado = True

                    respostas_lote.append({
                        "colaborador": nome_colab, "p1": p1, "p2": p2,
                        "status_gestor": g_ok, "status_cargo": c_ok,
                        "status_unidade": u_ok, "status_depto": d_ok
                    })

            st.markdown("---")
            campo_obs = st.text_area("Observações Gerais (opcional)")

            if st.button("🚀 Enviar Validação Final", type="primary"):
                if erro_vazio:
                    st.error("⚠️ Por favor, selecione os pares de todos os colaboradores corretamente.")
                elif erro_duplicado:
                    st.error("⚠️ Erro: O Par 1 e o Par 2 não podem ser a mesma pessoa para o mesmo colaborador.")
                else:
                    id_protocolo = f"PEPO-{datetime.now().strftime('%Y%m%d%H%M')}-{str(uuid.uuid4())[:4].upper()}"
                    pacote = {
                        "gestor_avaliador": gestor_sel, "protocolo": id_protocolo,
                        "observacoes": campo_obs, "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "lista_equipe": respostas_lote
                    }
                    try:
                        salvar_backup_github(pacote, id_protocolo)
                        resp = requests.post(WEBHOOK_URL, json=pacote, timeout=20)
                       
                        if resp.status_code <= 202:
                            st.balloons(); st.success(f"✅ Enviado! Protocolo: {id_protocolo}")
                        else: st.error(f"Erro: {resp.status_code}")
                    except Exception as e: st.error(f"Erro de conexão: {e}")
