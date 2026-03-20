import streamlit as st
import pandas as pd
import requests
import io
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="PEPO 2026", layout="wide")

# 🔗 LINK DO SHAREPOINT (FUNCIONANDO)
ARQUIVO_EXCEL = "https://desenvolvimentocartaodetodo-my.sharepoint.com/:x:/g/personal/regianeandrade_cartaodetodos_com/IQBGxVER1ruUTbcxWH65p0f1AU4M4VWNfst1N2R-sxfmeA4?e=BILlwo"

ABA_BASE = 'Base_Dados'
ABA_RESPOSTAS = 'Respostas'

# 🔴 COLE SUA URL DO POWER AUTOMATE (HTTP)
WEBHOOK_URL = "COLE_AQUI_SUA_URL_HTTP"

# 🔄 BOTÃO DE ATUALIZAÇÃO
if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()

@st.cache_data(ttl=30)
def carregar_dados():
    response = requests.get(ARQUIVO_EXCEL)

    if response.status_code != 200:
        st.error(f"Erro ao acessar Excel: {response.status_code}")
        return None, None

    arquivo = io.BytesIO(response.content)

    df_base = pd.read_excel(arquivo, sheet_name=ABA_BASE)
    df_respostas = pd.read_excel(arquivo, sheet_name=ABA_RESPOSTAS)

    df_base.columns = df_base.columns.str.strip().str.lower()
    df_respostas.columns = df_respostas.columns.str.strip().str.lower()

    return df_base, df_respostas

df_base, df_respostas = carregar_dados()

if df_base is None:
    st.stop()

# 🎯 DASHBOARD
st.subheader("📊 Dashboard Geral")

gestores_total = df_base['gestor avaliador'].nunique()
gestores_respondidos = df_respostas['gestor'].nunique()

percentual = (gestores_respondidos / gestores_total * 100) if gestores_total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Gestores", gestores_total)
col2.metric("Respondidos", gestores_respondidos)
col3.metric("% Conclusão", f"{percentual:.1f}%")

st.divider()

# 🎯 SELEÇÃO DE GESTOR
gestores = sorted(df_base['gestor avaliador'].dropna().unique())
gestor_sel = st.selectbox("Selecione seu nome:", [""] + list(gestores))

if gestor_sel:

    # 🔒 BLOQUEIO DE REENVIO
    if gestor_sel in df_respostas['gestor'].values:
        st.warning("⚠️ Você já respondeu essa pesquisa.")
        st.stop()

    equipe = df_base[df_base['gestor avaliador'] == gestor_sel].copy()

    data_limite = pd.to_datetime('2026-01-31')

    def formatar_nome(row):
        if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
            return f"{row['nome']} ✅"
        return f"{row['nome']} ❌"

    equipe['nome_formatado'] = equipe.apply(formatar_nome, axis=1)

    lista_pares = sorted(equipe['nome_formatado'].unique())

    respostas_lote = []
    pendencia = False

    for i, row in equipe.iterrows():
        nome = row['nome']

        with st.expander(f"👤 {nome}", expanded=True):
            st.write(f"**Cargo:** {row.get('cargo')} | **Unidade:** {row.get('unidade')}")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}")
            with c2:
                c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}")
            with c3:
                u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}")
            with c4:
                d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}")

            p1 = st.selectbox(f"1º Par", [""] + lista_pares, key=f"p1_{i}")
            p2 = st.selectbox(f"2º Par", [""] + lista_pares, key=f"p2_{i}")

            if p1 == "" or p2 == "":
                pendencia = True

            respostas_lote.append({
                "colaborador": nome,
                "p1": p1,
                "p2": p2,
                "status_gestor": g_ok,
                "status_cargo": c_ok,
                "status_unidade": u_ok,
                "status_depto": d_ok
            })

    comentario = st.text_area("Observações")

    if st.button("🚀 Enviar"):

        if pendencia:
            st.error("Preencha todos os pares.")
            st.stop()

        if any("❌" in r['p1'] or "❌" in r['p2'] for r in respostas_lote):
            st.error("Você selecionou colaborador não elegível.")
            st.stop()

        payload = {
            "gestor_avaliador": gestor_sel,
            "observacoes": comentario,
            "data_envio": datetime.now().strftime("%d/%m/%Y"),
            "lista_equipe": respostas_lote
        }

        try:
            res = requests.post(
                WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )

            if res.status_code in [200, 202]:
                st.success("✅ Enviado com sucesso!")
                st.balloons()
            else:
                st.error(f"Erro {res.status_code}: {res.text}")

        except Exception as e:
            st.error(f"Erro: {e}")
