import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import uuid
import base64
import json

# --- CONFIGURAÇÕES DE SEGURANÇA (VIA STREAMLIT SECRETS) ---
#-se de que cadastrou verifique GITHUB_TOKEN e REPO_NAME nos Secrets do Streamlit
tentar:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
exceto:
    st.error("Erro: Configurações de Token ou Repositório não encontradas nos Secrets.")

# Webhook para Power Automate
WEBHOOK_URL = " https:// defaulte93279240f9745ba871f4a1 24f3343.19.environment.api. powerplatform.com:443/ powerautomate/automations/ direct/workflows/ dd8f08aa19674bb3951643917c0b69 df/triggers/manual/paths/ invoke?api-version=1&sp=% 2Ftriggers%2Fmanual%2Frun&sv= 1.0&sig= npw2e02HKff8Zew6sizpxu1EzwGu2U 0TPkU7ef_IWo0 "

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'

# Configuração da Página
st.set_page_config(page_title= "PEPO 2026", layout="wide")

# --- FUNÇÃO DE BACKUP NO GITHUB ---
def salvar_backup_github(dados, protocolo):
    tentar:
        caminho = f"backups/{protocolo}.json"
        url = f" https://api.github.com/ repos/{REPO_NAME}/contents/{ path} "
        conteudo_json = json.dumps(dados, indent=4, garanta_ascii=False)
        conteudo_base64 = base64.b64encode(conteudo_ json.encode("utf-8")).decode(" utf-8")
        cabeçalhos = {
            "Autorização": f"token {GITHUB_TOKEN}",
            "Aceitar": "application/vnd.github.v3+ json"
        }
        carga útil = {
            "message": f"Backup Automático: {protocolo}",
            "conteúdo": conteudo_base64
        }
        requests.put(url, json=payload, headers=headers)
    exceto Exception como e:
        print(f"Erro sem backup: {e}")

# --- DESIGN: LOGOS CENTRALIZADOS ---
c1, c2, c_logo, c_mascote, c5, c6 = st.columns([2, 1, 1.2, 0.8, 1, 2])
com c_logo:
    if os.path.exists("LOGO.png"): st.image("LOGO.png", width=180)
com c_mascote:
    if os.path.exists("mascote_pepo. png"): st.image("mascote_pepo.png", largura=65)

@st.cache_data(ttl=60)
def carregar_dados():
    Se não os.path.exists(ARQUIVO_EXCEL): retorne None
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower ()
    if 'dados de admissão' em df.columns:
        df['dados de admissão'] = pd.to_datetime(df['dados de admissão'], erros='coercer')
    retornar df

df_base = carregar_dados()

se df_base não for None:
    st.markdown("<h2 style='text-align: center;'>Validação Pesquisa Pepo 2026</h2>", unsafe_allow_html=True)
    
    saudacao = "Olá Gestor, selecione abaixo seu nome e confirme os dados de sua equipe.<br>"
    st.markdown(f"<div style='text-align: center; font-size: 18px; color: #555;'>{saudacao}</div>", unsafe_allow_html=True)
    
    st.markdown("---")

    col_gestor_ref = 'gestor avaliador' 

    se col_gestor_ref estiver em df_base.columns:
        lista_gestores = sorted(df_base[col_gestor_ref] .dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome (Gestor):", [""] + lista_gestores)

        se gestor_sel:
            # FILTRO: Apenas a equipe direta do gestor
            equipe = df_base[df_base[col_gestor_ref ] == gestor_sel].copy()
            data_limite = pd.to_datetime('2026-01-31')
            
            def selo(linha):
                if pd.notnull(row['dados de admissão']) e row['dados de admissão'] <= data_limite:
                    retornar f"{row['nome']} "
                retornar f"{row['nome']} ❌"

            # LÓGICA DE PARES: Se a equipe tiver apenas 1 pessoa, abra os gestores
            equipe['display_par'] = equipe.apply(selo, eixo=1)
            opcoes_pares = sorted(equipe['display_par']. unique())

            se len(opcoes_pares) <= 1:
                opcoes_gestores = sorted(df_base[df_base['nome'] .isin(lista_gestores)].apply( selo, eixo=1).unique())
                opcoes_pares = opcoes_pares + ["----------"] + opcoes_gestores
            
            opcoes_pares = [""] + opcoes_pares

            respostas_lote = []
            erro_vazio = Falso

            para i, linha em equipe.iterrows():
                nome_colab = linha['nome']
                com st.expander(f" 👤Validar: {nome_colab}", expanded=True):
                    c_g, c_c, c_u, c_d = st.columns(4)
                    com c_g: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    com c_c: c_ok = st.radio("Carga OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    com c_u: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    com c_d: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(f"1º Par para {nome_colab} *", opcoes_pares, key=f"p1_{i}")
                    p2 = st.selectbox(f"2º Par para {nome_colab} *", opcoes_pares, key=f"p2_{i}")

                    se p1 == "" ou p2 == "" ou "---" em str(p1): erro_vazio = True

                    respostas_lote.append({
                        "colaborador": nome_colab, "p1": p1, "p2": p2,
                        "status_gestor": g_ok, "status_cargo": c_ok,
                        "status_unidade": u_ok, "status_depto": d_ok
                    })

            st.markdown("---")
            label_obs = "Observações gerais ou indicação de par não descrito na lista (opcional)"
            campo_obs = st.text_area(label_obs)

            if st.button(" 🚀Enviar Validação Final", type="primary"):
                # TRAVA 1: Campos Vazios
                se erro_vazio:
                    st.error(" ⚠️Por favor, selecione os pares de todos os colaboradores.")
                
                # TRAVA 2: Pares Idênticos para o mesmo colaborador
                elif any(r['p1'] == r['p2'] for r in respostas_lote):
                    st.error(" ⚠️Erro: O Par 1 e o Par 2 não podem ser a mesma pessoa.")
                
                outro:
                    id_protocolo = f"PEPO-{datetime.now(). strftime('%Y%m%d%H%M')}-{str( uuid.uuid4())[:4].upper()}"
                    pacote = {
                        "gestor_avaliador": gestor_sel, "protocolo": id_protocolo,
                        "observações": campo_obs, "data_envio": datetime.now().strftime("%d/% m/%Y %H:%M"),
                        "lista_equipe": respostas_lote
                    }
                    tentar:
                        # Enviar backup para GitHub
                        salvar_backup_github(pacote, id_protocolo)
                        
                        # Enviar para o Power Automate
                        resp = requests.post (WEBHOOK_URL, json=pacote, timeout=20)
                        
                        se resp.status_code <= 202:
                            st.balões(); st.success(f" ✅Enviado com sucesso! Protocolo: {id_protocolo}")
                        senão: st.error(f"Erro no envio: {resp.status_code}")
                    exceto Exceção como e: st.error(f"Erro de conexão: {e}")
outro:
    st.error("Arquivo base_pepo.xlsx não encontrado no repositório.")
