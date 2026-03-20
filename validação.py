import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
from PIL import Image

# Configuração da página (Conversa: PEPOResponseFlow)
st.set_page_config(page_title="PEPO 2026", layout="wide")

# Constantes e Configurações
ARQUIVO_EXCEL = 'base_pepo.xlsx'
ABA_BASE = 'Base_Dados'
NOME_IMAGEM = 'mascote_pepo.png'

# Substitua pela URL gerada no seu Power Automate (Trial do HTTP Post)
WEBHOOK_URL = "https://pepo-validacao-2026-o9lbk9qypdscnufgnjye9x.streamlit.app/"

@st.cache_data
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL):
        return None
    # Carrega a planilha e padroniza nomes de colunas
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_BASE)
    df.columns = df.columns.str.strip().str.lower()
    return df

df_base = carregar_dados()

if df_base is not None:
    # Cabeçalho com o Mascote Centralizado
    try:
        col_esq, col_meio, col_dir = st.columns([1, 2, 1])
        with col_meio:
            st.image(Image.open(NOME_IMAGEM), width=250)
    except: 
        st.write("🤖 **PEPO**")
    
    st.title("Validação Pesquisa Pepo 2026")
    
    # 2. NOVA FRASE DE BOAS-VINDAS
    st.markdown("Olá gestor, por favor Selecione o seu nome e confirme as informações abaixo:")

    st.divider()

    # Seleção do Gestor Avaliador (Coluna 'gestor avaliador' na planilha)
    col_gestor_fada = 'gestor avaliador'
    if col_gestor_fada in df_base.columns:
        gestores = sorted(df_base[col_gestor_fada].dropna().unique())
        gestor_sel = st.selectbox("Selecione seu nome para começar:", [""] + list(gestores))

        if gestor_sel:
            # Filtra a equipe do gestor selecionado
            equipe = df_base[df_base[col_gestor_fada] == gestor_sel]
            
            # 5. E-MAIL DO VALIDADOR (Busca da coluna J 'e-mail gestor validador')
            col_email_validador = 'e-mail gestor validador'
            if col_email_validador in equipe.columns:
                email_validador = equipe[col_email_validador].iloc[0]
            else:
                st.error(f"Não encontrei a coluna '{col_email_validador}' na sua base.")
                email_validador = ""
            
            respostas_equipe = []

            st.subheader(f"Equipe de {gestor_sel}")
            
            for i, row in equipe.iterrows():
                nome_func = row.get('nome', f"Colaborador {i}")
                
                # 3. PERGUNTAS IMPORTANTES E 4. SELEÇÃO DE PARES
                with st.expander(f"👤 {nome_func}", expanded=True):
                    st.write(f"**Cargo:** {row.get('cargo')} | **Unidade:** {row.get('unidade')}")
                    
                    # Botões de confirmação rápida
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: g_ok = st.radio("Gestor correto?", ["Sim", "Não"], key=f"g_{i}", horizontal=True)
                    with c2: c_ok = st.radio("Cargo correto?", ["Sim", "Não"], key=f"c_{i}", horizontal=True)
                    with c3: u_ok = st.radio("Unidade correta?", ["Sim", "Não"], key=f"u_{i}", horizontal=True)
                    with c4: d_ok = st.radio("Depto correto?", ["Sim", "Não"], key=f"d_{i}", horizontal=True)

                    st.divider()
                    # Seleção de Pares (Pode ser qualquer um da base)
                    lista_todos = sorted(df_base['nome'].unique())
                    p1_col, p2_col = st.columns(2)
                    with p1_col: p1 = st.selectbox(f"Selecione o 1º Par para {nome_func}:", [""] + lista_todos, key=f"p1_{i}")
                    with p2_col: p2 = st.selectbox(f"Selecione o 2º Par para {nome_func}:", [""] + lista_todos, key=f"p2_{i}")

                    # Armazena os dados para envio em lote
                    respostas_equipe.append({
                        "colaborador": nome_func,
                        "p1": p1,
                        "p2": p2,
                        "status_gestor": g_ok,
                        "status_cargo": c_ok,
                        "status_unidade": u_ok,
                        "status_depto": d_ok
                    })

            st.divider()
            obs_geral = st.text_area("Deseja deixar algum recado sobre a validação da sua equipe?")

            if st.button("🚀 Enviar Validação Finalizada", type="primary"):
                # Prepara os dados para envio (incluindo o e-mail do validador)
                payload = {
                    "gestor_avaliador": gestor_sel,
                    "email_validador": email_validador,
                    "observacoes": obs_geral,
                    "data_envio": datetime.now().strftime("%d/%m/%Y"),
                    "lista_equipe": respostas_equipe
                }
                
                try:
                    response = requests.post(WEBHOOK_URL, json=payload)
                    # 200/202 significa que o Power Automate aceitou o pedido
                    if response.status_code in [200, 202]:
                        st.balloons()
                        # Mensagem de sucesso incluindo o e-mail de destino
                        st.success(f"Tudo certo! As informações foram enviadas para validação de {email_validador}.")
                    else:
                        st.error("Houve um problema técnico ao enviar os dados. O Power Automate recusou.")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")
    else:
        st.error(f"Coluna '{col_gestor_fada}' não encontrada na sua base.")
else:
    st.error("Não encontrei a planilha base_pepo.xlsx. Verifique se o arquivo está na mesma pasta do script.")