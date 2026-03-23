import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import uuid
import json
import base64

# --- CONFIGURAÇÕES ---
GITHUB_TOKEN = "COLE_SEU_TOKEN_AQUI" 
REPO_NAME = "peopletodos02/pepo-validacao-2026" 
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

st.set_page_config(page_title="PEPO 2026", layout="wide")

# Função de Backup Permanente
def salvar_backup_github(dados, protocolo):
    try:
        path = f"backups/{protocolo}.json"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{path}"
        conteudo_json = json.dumps(dados, indent=4, ensure_ascii=False)
        conteudo_base64 = base64.b64encode(conteudo_json.encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        payload = {"message": f"Backup: {protocolo}", "content": conteudo_base64}
        requests.put(url, json=payload, headers=headers)
    except:
        pass

# --- LOGOS ---
c_l1, c_l2, c_l3 = st.columns([1, 2, 1])
with c_l2:
    col_img1, col_img2 = st.columns([3, 1])
    with col_img1:
        if os.path.exists("LOGO.png"): st.image("LOGO.png", use_container_width=True)
    with col_img2:
        if os.path.exists("mascote_pepo.png"): st.image("mascote_pepo.png", width=70)

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
    st.info("Olá Gestor, selecione seu nome e confirme os dados da sua equipe. Obrigado!")

    col_gestor_ref = 'gestor avaliador' # Coluna B
    col_depto = 'unidade' # Coluna H

    gestores_lista = sorted(df_base[col_gestor_ref].dropna().unique())
    gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + gestores_lista)

    if gestor_sel:
        equipe = df_base[df_base[col_gestor_ref] == gestor_sel].copy()
        data_limite = pd.to_datetime('2026-01-31')
        
        def selo(row):
            check = "✅" if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite else "❌"
            return f"{row['nome']} {check}"

        respostas_lote = []
        erro_vazio = False

        for i, row in equipe.iterrows():
            nome_colab = row['nome']
            depto_colab = row[col_depto]

            with st.expander(f"👤 Validar: {nome_colab}", expanded=True):
                # LÓGICA DE PARES INTELIGENTE
                pessoal_depto = df_base[df_base[col_depto] == depto_colab].copy()
                pessoal_depto['display'] = pessoal_depto.apply(selo, axis=1)
                lista_par_final = sorted(pessoal_depto['display'].unique())

                # Se o departamento tiver 2 pessoas ou menos, adicionamos os gestores como opção
                if len(lista_par_final) <= 2:
                    gestores_obs = df_base[df_base['nome'].isin(gestores_lista)].copy()
                    gestores_obs['display'] = gestores_obs.apply(selo, axis=1)
                    lista_par_final += ["----------", "OPÇÕES DE GESTORES:"] + sorted(gestores_obs['display'].unique())

                c1, c2, c3, c4 = st.columns(4)
                with c1: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}")
                with c2: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}")
                with c3: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}")
                with c4: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}")

                p1 = st.selectbox(f"1º Par para {nome_colab}", [""] + lista_par_final, key=f"p1_{i}")
                p2 = st.selectbox(f"2º Par para {nome_colab}", [""] + lista_par_final, key=f"p2_{i}")

                if p1 == "" or p2 == "" or "---" in str(p1): erro_vazio = True
                respostas_lote.append({
                    "colaborador": nome_colab, "p1": p1, "p2": p2,
                    "status_gestor": g_ok, "status_cargo": c_ok,
                    "status_unidade": u_ok, "status_depto": d_ok
                })

        obs = st.text_area("Observações gerais ou indicação de par manual (opcional):")
        
        if st.button("🚀 Enviar Validação"):
            if erro_vazio:
                st.error("Preencha todos os pares corretamente.")
            else:
                protocolo = f"PEPO-{datetime.now().strftime('%Y%m%d%H%M')}-{str(uuid.uuid4())[:4].upper()}"
                pacote = {
                    "gestor_avaliador": gestor_sel, "protocolo": protocolo,
                    "observacoes": obs, "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "lista_equipe": respostas_lote
                }
                # Salva Backup e Envia Webhook
                salvar_backup_github(pacote, protocolo)
                requests.post(WEBHOOK_URL, json=pacote)
                st.success(f"Enviado! Protocolo: {protocolo}")
                st.balloons()
