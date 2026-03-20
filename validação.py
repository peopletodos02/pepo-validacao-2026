import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

st.set_page_config(page_title="PEPO 2026", layout="wide")

# 🔗 SEU LINK (mantém esse mesmo)
ARQUIVO_EXCEL = "https://desenvolvimentocartaodetodo-my.sharepoint.com/:x:/g/personal/regianeandrade_cartaodetodos_com/IQBGxVER1ruUTbcxWH65p0f1AU4M4VWNfst1N2R-sxfmeA4?e=r3Udaa"

ABA_BASE = 'Base_Dados'
ABA_RESPOSTAS = 'Respostas'

WEBHOOK_URL = "COLE_AQUI_SUA_URL_HTTP"

# 🔄 Atualizar cache
if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        response = requests.get(ARQUIVO_EXCEL, allow_redirects=True)

        # 🔍 DEBUG (remova depois)
        content_type = response.headers.get("Content-Type", "")
        
        if "excel" not in content_type and "spreadsheet" not in content_type:
            st.error("❌ O SharePoint não retornou um arquivo Excel válido.")
            st.write("Content-Type:", content_type)
            st.write(response.text[:500])
            st.stop()

        arquivo = io.BytesIO(response.content)

        df_base = pd.read_excel(arquivo, sheet_name=ABA_BASE)
        df_respostas = pd.read_excel(arquivo, sheet_name=ABA_RESPOSTAS)

        df_base.columns = df_base.columns.str.strip().str.lower()
        df_respostas.columns = df_respostas.columns.str.strip().str.lower()

        return df_base, df_respostas

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

df_base, df_respostas = carregar_dados()

# 📊 DASHBOARD
st.subheader("📊 Dashboard")

total = df_base['gestor avaliador'].nunique()
respondidos = df_respostas['gestor'].nunique()

pct = (respondidos / total * 100) if total > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total Gestores", total)
c2.metric("Respondidos", respondidos)
c3.metric("% Conclusão", f"{pct:.1f}%")

st.divider()

# 👤 SELEÇÃO
gestores = sorted(df_base['gestor avaliador'].dropna().unique())
gestor_sel = st.selectbox("Selecione seu nome:", [""] + gestores)

if gestor_sel:

    if gestor_sel in df_respostas['gestor'].values:
        st.warning("⚠️ Você já respondeu.")
        st.stop()

    equipe = df_base[df_base['gestor avaliador'] == gestor_sel].copy()

    data_limite = pd.to_datetime('2026-01-31')

    def formatar_nome(row):
        if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
            return f"{row['nome']} ✅"
        return f"{row['nome']} ❌"

    equipe['nome_formatado'] = equipe.apply(formatar_nome, axis=1)
    lista_pares = sorted(equipe['nome_formatado'].unique())

    respostas = []
    erro = False

    for i, row in equipe.iterrows():
        nome = row['nome']

        with st.expander(nome, expanded=True):
            p1 = st.selectbox("Par 1", [""] + lista_pares, key=f"p1_{i}")
            p2 = st.selectbox("Par 2", [""] + lista_pares, key=f"p2_{i}")

            if not p1 or not p2:
                erro = True

            respostas.append({
                "colaborador": nome,
                "p1": p1,
                "p2": p2,
                "status_gestor": "Sim",
                "status_cargo": "Sim",
                "status_unidade": "Sim",
                "status_depto": "Sim"
            })

    if st.button("🚀 Enviar"):

        if erro:
            st.error("Preencha todos os pares.")
            st.stop()

        payload = {
            "gestor_avaliador": gestor_sel,
            "observacoes": "",
            "data_envio": datetime.now().strftime("%d/%m/%Y"),
            "lista_equipe": respostas
        }

        res = requests.post(WEBHOOK_URL, json=payload)

        if res.status_code in [200, 202]:
            st.success("✅ Enviado!")
        else:
            st.error(f"Erro: {res.status_code}")
