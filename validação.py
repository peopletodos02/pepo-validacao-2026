import streamlit as st
import pandas as pd
import requests
import os
from PIL import Image
from datetime import datetime

# PEPOResponseFlow
st.set_page_config(page_title="PEPO 2026", layout="wide")

# Verifique se o link está correto e o fluxo LIGADO no Power Automate
WEBHOOK_URL = "https://defaulte93279240f9745ba871f4a124f3343.19.environment.api.powerplatform.com/powerautomate/automations/direct/workflows/14f4e4ebe95f4087bdf0959d5768773c/triggers/manual/paths/invoke?api-version=1"

ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'
NOME_IMAGEM = 'mascote_pepo.png'

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
    try:
        col_esq, col_meio, col_dir = st.columns([1, 2, 1])
        with col_meio: st.image(Image.open(NOME_IMAGEM), width=180)
    except: st.write("🤖 **PEPO**")
    
    st.title("Validação Pesquisa Pepo 2026")
    st.markdown("### Olá gestor, selecione seu nome e valide sua equipe:")
    st.divider()

    col_gestor = 'gestor avaliador'
    if col_gestor in df_base.columns:
        gestores = sorted(df_base[col_gestor].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome:", [""] + list(gestores))

        if gestor_sel:
            equipe = df_base[df_base[col_gestor] == gestor_sel]
            
            # --- REGRA DE ELEGIBILIDADE ---
            data_limite = pd.to_datetime('2026-01-31')
            def formatar_nome(row):
                if pd.notnull(row['data de admissão']) and row['data de admissão'] <= data_limite:
                    return f"{row['nome']} ✅"
                return f"{row['nome']} ❌ (Não Elegível)"
            
            df_base['nome_formatado'] = df_base.apply(formatar_nome, axis=1)
            lista_pares_formatada = sorted(df_base['nome_formatado'].unique())

            respostas_lote = []
            pendencia_pares = False # Marcador de erro

            for i, row in equipe.iterrows():
                nome_f = row.get('nome', f"Colab {i}")
                with st.expander(f"👤 {nome_f}", expanded=True):
                    st.write(f"**Cargo:** {row.get('cargo')} | **Unidade:** {row.get('unidade')}")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c2: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c3: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c4: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    p1 = st.selectbox(f"Selecione o 1º Par para {nome_f} *", [""] + lista_pares_formatada, key=f"p1_{i}")
                    p2 = st.selectbox(f"Selecione o 2º Par para {nome_f} *", [""] + lista_pares_formatada, key=f"p2_{i}")

                    # Verifica se algum par ficou vazio
                    if p1 == "" or p2 == "":
                        pendencia_pares = True

                    respostas_lote.append({
                        "colaborador": nome_f,
                        "p1": p1, "p2": p2,
                        "status_gestor": g_ok, "status_cargo": c_ok,
                        "status_unidade": u_ok, "status_depto": d_ok
                    })

            st.divider()
            comentario_geral = st.text_area("Observações (Opcional):")

            if st.button("🚀 Finalizar e Salvar Dados", type="primary"):
                # 1. VERIFICAÇÃO DE OBRIGATORIEDADE
                if pendencia_pares:
                    st.error("⚠️ Erro: Todos os pares de todos os colaboradores devem ser selecionados antes de enviar.")
                
                # 2. VERIFICAÇÃO DE ELEGIBILIDADE
                elif any("❌" in r['p1'] or "❌" in r['p2'] for r in respostas_lote):
                    st.error("⚠️ Erro: Você selecionou um par 'Não Elegível' (❌). Por favor, corrija.")
                
                else:
                    payload = {
                        "gestor_avaliador": gestor_sel,
                        "observacoes": comentario_geral,
                        "data_envio": datetime.now().strftime("%d/%m/%Y"),
                        "lista_equipe": respostas_lote
                    }
                    try:
                        res = requests.post(WEBHOOK_URL, json=payload, timeout=15)
                        if res.status_code in [200, 202]:
                            st.balloons()
                            st.success("✅ Validação concluída! Os dados foram salvos.")
                        else:
                            st.error(f"Erro {res.status_code}: O servidor recusou. Verifique se o fluxo está LIGADO.")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
    else:
        st.error(f"Coluna '{col_gestor}' não encontrada.")
else:
    st.error("Arquivo base_pepo.xlsx não encontrado no GitHub.")
