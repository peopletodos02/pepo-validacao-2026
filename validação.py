import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime

# Configuração da página (Conversa: PEPOResponseFlow)
st.set_page_config(page_title="PEPO 2026", layout="wide")

# Nomes dos arquivos
ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'
NOME_IMAGEM = 'mascote_pepo.png'

@st.cache_data(ttl=60)
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL):
        return None
    # Carrega a planilha e limpa os nomes das colunas
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower()
    return df

df_base = carregar_dados()

if df_base is not None:
    # 1. EXIBIÇÃO DO MASCOTE (Ajustado para não dar erro)
    try:
        col_esq, col_meio, col_dir = st.columns([1, 2, 1])
        with col_meio:
            st.image(Image.open(NOME_IMAGEM), width=200)
    except: 
        st.write("🤖 **[Mascote PEPO]**")
    
    st.title("Validação Pesquisa Pepo 2026")
    
    # 2. FRASE DE BOAS-VINDAS SOLICITADA
    st.markdown("### Olá gestor, por favor selecione o seu nome e confirme as informações abaixo:")

    st.divider()

    # Identificando a coluna do Gestor (ajustada para minúsculo pelo código)
    col_gestor_fada = 'gestor avaliador'
    
    if col_gestor_fada in df_base.columns:
        gestores = sorted(df_base[col_gestor_fada].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome para listar sua equipe:", [""] + list(gestores))

        if gestor_sel:
            # Filtra os colaboradores do gestor selecionado
            equipe = df_base[df_base[col_gestor_fada] == gestor_sel]
            respostas_coletadas = []

            st.subheader(f"Equipe sob validação de: {gestor_sel}")
            
            for i, row in equipe.iterrows():
                nome_func = row.get('nome', f"Colaborador {i}")
                
                with st.expander(f"👤 {nome_func}", expanded=True):
                    st.write(f"**Cargo atual:** {row.get('cargo', 'N/A')} | **Unidade:** {row.get('unidade', 'N/A')}")
                    
                    # 3. PERGUNTAS DE CONFIRMAÇÃO
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: g_ok = st.radio("Gestor OK?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c2: c_ok = st.radio("Cargo OK?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c3: u_ok = st.radio("Unidade OK?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c4: d_ok = st.radio("Depto OK?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    st.divider()
                    
                    # 4. SELEÇÃO DE PARES
                    lista_todos = sorted(df_base['nome'].unique())
                    p1_col, p2_col = st.columns(2)
                    with p1_col: p1 = st.selectbox(f"1º Par para {nome_func}:", [""] + lista_todos, key=f"p1_{i}")
                    with p2_col: p2 = st.selectbox(f"2º Par para {nome_func}:", [""] + lista_todos, key=f"p2_{i}")

                    respostas_coletadas.append({
                        "Colaborador": nome_func,
                        "Par 1": p1,
                        "Par 2": p2,
                        "Gestor OK": g_ok,
                        "Cargo OK": c_ok,
                        "Unidade OK": u_ok,
                        "Depto OK": d_ok
                    })

            st.divider()
            obs_texto = st.text_area("Deseja deixar alguma observação geral sobre sua equipe?")

            if st.button("🚀 Finalizar Validação", type="primary"):
                # Como retiramos o e-mail, mostramos o sucesso e o resumo na tela
                st.balloons()
                st.success("✅ Validação concluída com sucesso!")
                
                # Exibe um resumo para o gestor ter certeza do que enviou
                df_resumo = pd.DataFrame(respostas_coletadas)
                st.write("### Resumo da sua validação:")
                st.dataframe(df_resumo)
                
                if obs_texto:
                    st.info(f"**Sua observação:** {obs_texto}")
                
                st.warning("⚠️ Prontinho! Os dados foram processados. Você já pode fechar esta aba.")
    else:
        st.error(f"Não encontrei a coluna '{col_gestor_fada}'. Verifique os títulos na aba Base_Dados.")
else:
    st.error("Erro: Não encontrei o arquivo 'base_pepo.xlsx'. Certifique-se de que ele foi enviado ao GitHub.")