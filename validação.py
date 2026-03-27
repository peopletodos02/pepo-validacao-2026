import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta, timezone
import uuid
import base64
import json

# --- CONFIGURAÇÕES DE SEGURANÇA ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    BRANCH = "main"
except:
    st.error("Erro: Verifique os Secrets do Streamlit.")

st.set_page_config(page_title="PEPO 2026", layout="wide")

# --- ESTILO VISUAL PEPO (VERDE #009E80) ---
st.markdown("""
    <style>
    /* Cor primária nos botões e rádio */
    div[data-baseweb="radio"] div[role="presentation"] {
        background-color: #009E80 !important;
        border-color: #009E80 !important;
    }
    button[kind="primary"] {
        background-color: #009E80 !important;
        border-color: #009E80 !important;
    }
    </style>
    """, unsafe_allow_html=True)

WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"
ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

def salvar_backup_github(dados, protocolo):
    try:
        path = f"backups/{protocolo}.json"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{path}"
        conteudo_json = json.dumps(dados, indent=4, ensure_ascii=False)
        conteudo_base64 = base64.b64encode(conteudo_json.encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        payload = {"message": f"Backup: {protocolo}", "content": conteudo_base64, "branch": BRANCH}
        requests.put(url, json=payload, headers=headers)
    except: pass

@st.cache_data(ttl=3600)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL): return None
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = [c.lower().strip() for c in df.columns]
    return df

df_base = carregar_dados()

# --- DESIGN: LOGOS CENTRALIZADAS ---
c1, c2, c_logo, c_mascote, c5, c6 = st.columns([2, 1, 1.2, 0.8, 1, 2])
with c_logo:
    if os.path.exists("LOGO.png"): st.image("LOGO.png", width=180)
with c_mascote:
    if os.path.exists("mascote_pepo.png"): st.image("mascote_pepo.png", width=190)

if df_base is not None:
    st.markdown("<h2 style='text-align: center;'>Validação - PEPO 2026</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #555;'>Olá Gestor, selecione seu nome e confirme os dados da equipe.</div>", unsafe_allow_html=True)
    st.markdown("---")

    col_gestor_ref = 'gestor avaliador'
    lista_gestores_full = sorted(df_base[col_gestor_ref].dropna().unique())
    gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + lista_gestores_full)

    if gestor_sel:
        # --- BLOCO DE ATENÇÃO COM TAMANHO MAIOR ---
        st.markdown("###### **ATENÇÃO:** Cada colaborador do seu setor deve ser avaliado por dois pares. Caso o ocupante desse cargo não tenha pares na sua estrutura, favor recomendar abaixo pares de outro setor.")
        
        tipo_avaliacao = st.radio(
            "**A equipe será avaliada por pares do mesmo setor?**",
            ["Sim", "Não"], index=0, horizontal=True, key="tipo_av"
        )
        st.markdown("---")

        equipe = df_base[df_base[col_gestor_ref] == gestor_sel].copy()
        
        all_cargos = sorted(df_base['cargo'].dropna().unique())
        all_unidades = sorted([str(u).strip().upper() for u in df_base['unidade'].dropna().unique()])
        all_deptos = sorted(df_base['departamento'].dropna().unique())
        lista_nomes_full = sorted(df_base['nome'].dropna().unique())

        respostas_lote = []
        erro_vazio = False
        erro_duplicado = False

        for i, row in equipe.iterrows():
            nome_colab = row['nome']
            with st.expander(f"👤 Validar: {nome_colab}", expanded=True):
                st.markdown(f"**Dados cadastrados:**")
                info1, info2, info3 = st.columns(3)
                info1.caption(f"💼 Cargo: {row['cargo']}")
                info2.caption(f"🏢 Unidade: {row['unidade']}")
                info3.caption(f"📁 Departamento: {row['departamento']}")
                
                st.write("")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    g_corr = st.selectbox("Novo Gestor:", [""] + lista_gestores_full, key=f"gc_{i}") if g_ok == "Não" else ""
                with c2:
                    c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    c_corr = st.selectbox("Novo Cargo:", [""] + all_cargos, key=f"cc_{i}") if c_ok == "Não" else ""
                with c3:
                    u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    u_corr = st.selectbox("Nova Unidade:", [""] + all_unidades, key=f"uc_{i}") if u_ok == "Não" else ""
                with c4:
                    d_ok = st.radio("Departamento OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)
                    d_corr = st.selectbox("Novo Departamento:", [""] + all_deptos, key=f"dc_{i}") if d_ok == "Não" else ""

                if tipo_avaliacao == "Sim":
                    df_par = df_base[df_base['departamento'] == row['departamento']].copy()
                    op_pares = sorted(df_par['nome'].unique())
                    if len(op_pares) <= 1: op_pares = op_pares + ["----------"] + lista_nomes_full
                else: op_pares = lista_nomes_full
                
                op_pares = [""] + op_pares
                p1 = st.selectbox(f"1º Par para {nome_colab} *", op_pares, key=f"p1_{i}")
                p2 = st.selectbox(f"2º Par para {nome_colab} *", op_pares, key=f"p2_{i}")

                if p1 == "" or p2 == "" or "---" in str(p1): erro_vazio = True
                if p1 != "" and p1 == p2: erro_duplicado = True

                respostas_lote.append({
                    "colaborador": nome_colab, "p1": p1, "p2": p2,
                    "status_gestor": g_ok, "corr_gestor": g_corr,
                    "status_cargo": c_ok, "corr_cargo": c_corr,
                    "status_unidade": u_ok, "corr_unidade": u_corr,
                    "status_departamento": d_ok, "corr_departamento": d_corr
                })

        campo_obs = st.text_area("Observações Gerais (opcional)")

        if st.button("Enviar Validação", type="primary"):
            if erro_vazio: st.error("⚠️ Selecione os pares de todos os colaboradores.")
            elif erro_duplicado: st.error("⚠️ Par 1 e Par 2 não podem ser a mesma pessoa.")
            else:
                fuso_br = timezone(timedelta(hours=-3))
                agora_br = datetime.now(fuso_br)
                id_p = f"PEPO-{agora_br.strftime('%Y%m%d%H%M')}"
                pacote = {
                    "gestor_avaliador": gestor_sel, "protocolo": id_p,
                    "observacoes": campo_obs, "data_envio": agora_br.strftime("%d/%m/%Y %H:%M"),
                    "lista_equipe": respostas_lote
                }
                salvar_backup_github(pacote, id_p)
                requests.post(WEBHOOK_URL, json=pacote)
                st.success(f"✅ Enviado! Protocolo: {id_p}"); st.balloons()
