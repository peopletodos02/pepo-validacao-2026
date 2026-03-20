import streamlit as st
import pandas as pd
import requests
import os
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="PEPO 2026", layout="wide")

# 🔴 COLE SUA URL HTTP CORRETA AQUI
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/dd8f08aa19674bb3951643917c0b69df/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=npw2e02HKff8Zew6sizpxu1EzwGu2U0TPkU7ef_IWo0"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'
NOME_IMAGEM = 'mascote_pepo.png'
PASTA_BACKUP = 'backup_envios'

# Criar pasta de backup se não existir
os.makedirs(PASTA_BACKUP, exist_ok=True)

@st.cache_data(ttl=10)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL):
        return None
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower()

    if 'data de admissão' in df.columns:
        df['data de admissão'] = pd.to_datetime(df['data de admissão'], errors='coerce')

    # Criar coluna de status se não existir
    if 'status_resposta' not in df.columns:
        df['status_resposta'] = 'Não Respondido'

    return df

df_base = carregar_dados()

if df_base is not None:

    try:
        col_esq, col_meio, col_dir = st.columns([1, 2, 1])
        with col_meio:
            st.image(Image.open(NOME_IMAGEM), width=180)
    except:
        st.write("🤖 **PEPO**")

    st.title("Validação Pesquisa PEPO 2026")
    st.markdown("### Olá gestor, selecione seu nome e valide sua equipe:")
    st.divider()

    col_gestor = 'gestor avaliador'

    if col_gestor in df_base.columns:

        gestores = sorted(df_base[col_gestor].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome:", [""] + list(gestores))

        if gestor_sel:

            # 🔹 FILTRO DA EQUIPE DO GESTOR
            equipe = df_base[df_base[col_gestor] == gestor_sel].copy()

            # 🔹 REGRA DE ELEGIBILIDADE
            data_limite = pd.to_datetime('2026-01-31')

            def formatar_nome(row):
                if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
                    return f"{row['nome']} ✅"
                return f"{row['nome']} ❌"

            equipe['nome_formatado'] = equipe.apply(formatar_nome, axis=1)

            # 🔹 LISTA DE PARES APENAS DA EQUIPE
            lista_pares_formatada = sorted(equipe['nome_formatado'].unique())

            respostas_lote = []
            pendencia_pares = False

            for i, row in equipe.iterrows():
                nome_f = row.get('nome', f"Colab {i}")

                with st.expander(f"👤 {nome_f}", expanded=True):
                    st.write(f"**Cargo:** {row.get('cargo')} | **Unidade:** {row.get('unidade')}")

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c2:
                        c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c3:
                        u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c4:
                        d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(
                        f"Selecione o 1º Par para {nome_f} *",
                        [""] + lista_pares_formatada,
                        key=f"p1_{i}"
                    )

                    p2 = st.selectbox(
                        f"Selecione o 2º Par para {nome_f} *",
                        [""] + lista_pares_formatada,
                        key=f"p2_{i}"
                    )

                    if p1 == "" or p2 == "":
                        pendencia_pares = True

                    respostas_lote.append({
                        "colaborador": nome_f,
                        "p1": p1,
                        "p2": p2,
                        "status_gestor": g_ok,
                        "status_cargo": c_ok,
                        "status_unidade": u_ok,
                        "status_depto": d_ok
                    })

            st.divider()
            comentario_geral = st.text_area("Observações (Opcional):")

            if st.button("🚀 Finalizar e Salvar Dados", type="primary"):

                if pendencia_pares:
                    st.error("⚠️ Todos os pares devem ser selecionados.")
                
                elif any("❌" in r['p1'] or "❌" in r['p2'] for r in respostas_lote):
                    st.error("⚠️ Você selecionou um par não elegível.")
                
                else:
                    payload = {
                        "gestor_avaliador": gestor_sel,
                        "observacoes": comentario_geral,
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

                            # ✅ BACKUP LOCAL
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            arquivo_backup = f"{PASTA_BACKUP}/backup_{gestor_sel}_{timestamp}.csv"

                            pd.DataFrame(respostas_lote).to_csv(
                                arquivo_backup,
                                index=False,
                                encoding='utf-8-sig'
                            )

                            # ✅ ATUALIZA STATUS LOCAL
                            df_base.loc[df_base[col_gestor] == gestor_sel, 'status_resposta'] = 'Respondido'

                            st.balloons()
                            st.success("✅ Dados enviados e salvos com sucesso!")
                           

                        else:
                            st.error(f"Erro {res.status_code}: {res.text}")

                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")

    else:
        st.error(f"Coluna '{col_gestor}' não encontrada.")

else:
    st.error("Arquivo base_pepo.xlsx não encontrado.")
