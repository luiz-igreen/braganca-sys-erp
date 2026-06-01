import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

# --- ESTILIZAÇÃO PADRÃO (DARK GLASS) ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .panel-glass { background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(51, 65, 85, 0.7); padding: 20px; border-radius: 16px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

engine = create_engine(st.secrets["DATABASE_URL"])

# --- CONTROLE DE ESTADO ---
if 'aba_ativa' not in st.session_state: st.session_state['aba_ativa'] = "Listagem"
if 'id_edicao' not in st.session_state: st.session_state['id_edicao'] = None

# --- FUNÇÕES ---
def carregar_dados(): return pd.read_sql("SELECT * FROM cadastro_geral_colaborador", engine)

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "🛠️ Gestão de Cadastros"])

if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    st.dataframe(carregar_dados(), use_container_width=True)

elif menu == "🛠️ Gestão de Cadastros":
    aba1, aba2, aba3, aba4 = st.tabs(["🔍 Consultar", "➕ Novo", "✏️ Alterar", "❌ Excluir"])

    # ABA NOVO: PADRONIZAÇÃO DE BOTÕES
    with aba2:
        with st.form("form_novo", clear_on_submit=True):
            i_id = st.text_input("ID")
            i_nome = st.text_input("Nome")
            
            # Botões alinhados no padrão
            cols = st.columns(2)
            if cols[0].form_submit_button("Salvar Registro"):
                with engine.begin() as conn: conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome)"), {"id": i_id, "nome": i_nome})
                st.success("Salvo!")
            if cols[1].form_submit_button("Cancelar"):
                st.rerun()

    # ABA ALTERAR: PADRONIZAÇÃO DE BOTÕES
    with aba3:
        if st.session_state['id_edicao'] is None:
            lista = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
            sel = st.selectbox("Selecione:", lista)
            if st.button("Carregar Ficha"): st.session_state['id_edicao'] = sel.split(" - ")[0]; st.rerun()
        else:
            id_alt = st.session_state['id_edicao']
            dados = engine.connect().execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_alt}).fetchone()
            with st.form("form_alt"):
                n_nome = st.text_input("Nome", value=dados.nome)
                cols = st.columns(2)
                if cols[0].form_submit_button("Salvar Alterações"):
                    with engine.begin() as conn: conn.execute(text("UPDATE cadastro_geral_colaborador SET nome = :n WHERE id = :id"), {"n": n_nome, "id": id_alt})
                    st.session_state['id_edicao'] = None; st.rerun()
                if cols[1].form_submit_button("Cancelar e Voltar"):
                    st.session_state['id_edicao'] = None; st.rerun()

    # ABA EXCLUIR: PADRONIZAÇÃO DE BOTÕES
    with aba4:
        lista_del = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
        sel_del = st.selectbox("Selecione para excluir:", lista_del)
        cols = st.columns(2)
        if cols[0].button("Remover Definitivamente"):
            with engine.begin() as conn: conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": sel_del.split(" - ")[0]})
            st.rerun()
        if cols[1].button("Cancelar"):
            st.rerun()    
