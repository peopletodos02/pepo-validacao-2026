import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta, timezone
import uuid
import base64
import json

# --- CONFIGURAÇÕES DE SEGURANÇA (VIA STREAMLIT SECRETS) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    BRANCH = "main"
except:
    st.error("Erro: Verifique os Secrets do Streamlit (GITHUB_TOKEN e REPO_NAME).")

# Configurações Iniciais da Página
st.set_page_config(page_title="PEPO 2026", layout="wide")

# Webhook do Power Automate
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

# --- FUNÇÃO DE BACKUP NO GITHUB ---
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

# --- CARREGAR DADOS ---
@st.cache_data(ttl=60)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL): return None
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    # Garante que os nomes das colunas estão em minúsculo e sem espaços
    df.columns = df.columns.str.strip().str.lower()
    return df

df_base = carregar_dados()

# --- DESIGN: LOGOS CENTRALIZADAS ---
# Certifique-se de que os arquivos LOGO.png e mascote_pepo.png estão na raiz do GitHub
c1, c2, c_logo, c_mascote, c5, c6 = st.columns([2, 1, 1.2, 0.8, 1, 2])
with c_logo:
    if os.path.exists("LOGO.png"): st.image("LOGO.png", width=180)
with c_mascote:
    if os.path.exists("mascote_pepo.png"): st.image("mascote_pepo.png", width=190)

if df_base is not None:
    st.markdown("<h2 style='text-align: center;'>Validação - PEPO 2026</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; font-size: 18px; color: #555;'>Olá Gestor, selecione abaixo o seu nome e confirme os dados da sua equipe.</div>", unsafe_allow_html=True)
    st.markdown("---")

    col_gestor_ref = 'gestor avaliador' # Nome exato da coluna na planilha
    lista_gestores_full = sorted(df_base[col_gestor_ref].dropna().unique())
    gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + lista_gestores_full)

    if gestor_sel:
        # --- CONFIGURAÇÃO DA EQUIPE (MAIOR E EM NEGRITO) ---
        tipo_avaliacao = st.radio(
            "**A equipe será avaliada por pares do mesmo setor?**",
            ["Sim", "Não"], index=0, horizontal=True, key="tipo_av"
        )
        st.markdown("---")

        equipe = df_base[df_base[col_gestor_ref] == gestor_sel].copy()
        
        # Listas globais para as correções (comboboxes)
        all_cargos = sorted(df_base['cargo'].dropna().unique())
        all_unidades = sorted(df_base['unidade'].dropna().unique())
        all_deptos = sorted(df_base['departamento'].dropna().unique())
        lista_nomes_full = sorted(df_base['nome'].dropna().unique())

        respostas_lote = []
        erro_vazio = False
        erro_duplicado = False

        for i, row in equipe.iterrows():
            nome_colab = row['nome']
            with st.expander(f"👤 Validar: {nome_colab}", expanded=True):
                # --- EXIBIÇÃO DOS DADOS ATUAIS (COM EMOJIS/GIFS) ---
                # Garante que os dados vêm como texto para formatação
                cargo_at = str(row['cargo'])
                unidade_at = str(row['unidade'])
                depto_at = str(row['departamento'])

                st.markdown(f"**Dados cadastrados:**")
                info1, info2, info3 = st.columns(3)
                info1.caption(f"💼 Cargo: {cargo_at}")
                info2.caption(f"🏢 Unidade: {unidade_at}")
                info3.caption(f"📁 Departamento: {depto_at}")
                
                st.write("") # Pequeno espaço visual

                # --- PERGUNTAS DE VALIDAÇÃO E CORREÇÃO ---
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
                    d_corr = st.selectbox("Novo Depto:", [""] + all_deptos, key=f"dc_{i}") if d_ok == "Não" else ""

                # Lógica de Pares (Setor vs Geral)
                if tipo_avaliacao == "Sim":
                    df_par = df_base[df_base['departamento'] == row['departamento']].copy()
                    op_pares = sorted(df_par['nome'].unique())
                    if len(op_pares) <= 1:
                        op_pares = op_pares + ["----------"] + lista_nomes_full
                else:
                    op_pares = lista_nomes_full
                
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
                    "status_depto": d_ok, "corr_depto": d_corr
                })

        campo_obs = st.text_area("Observações Gerais (opcional)")

        if st.button("🚀 Enviar Validação Final", type="primary"):
            if erro_vazio:
                st.error("⚠️ Por favor, selecione os pares de todos os colaboradores.")
            elif erro_duplicado:
                st.error("⚠️ Erro: O Par 1 e o Par 2 não podem ser a mesma pessoa para o mesmo colaborador.")
            else:
                # --- AJUSTE DE FUSO HORÁRIO BRASÍLIA (UTC-3) ---
                fuso_br = timezone(timedelta(hours=-3))
                agora_br = datetime.now(fuso_br)
                id_p = f"PEPO-{agora_br.strftime('%Y%m%d%H%M')}"
                data_envio_br = agora_br.strftime("%d/%m/%Y %H:%M")

                pacote = {
                    "gestor_avaliador": gestor_sel, 
                    "protocolo": id_p, 
                    "observacoes": campo_obs, 
                    "data_envio": data_envio_br, 
                    "lista_equipe": respostas_lote
                }
                
                try:
                    # Backup GitHub
                    salvar_backup_github(pacote, id_p)
                    # Envio Power Automate
                    resp = requests.post(WEBHOOK_URL, json=pacote, timeout=20)
                    if resp.status_code <= 202:
                        st.balloons(); st.success(f"✅ Enviado com Sucesso! Protocolo: {id_p}")
                    else: st.error(f"Erro no envio: {resp.status_code}")
                except Exception as e: st.error(f"Erro de conexão: {e}")
else:
    st.error("Arquivo base_pepo.xlsx não encontrado no repositório.")
