import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import sqlalchemy.exc
import datetime
import io

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

# --- VARIÁVEIS DE SESSÃO ---
if 'id_alterar' not in st.session_state: st.session_state['id_alterar'] = None
if 'id_excluir' not in st.session_state: st.session_state['id_excluir'] = None

# --- ESTILIZAÇÃO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .panel-glass { background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(51, 65, 85, 0.7); padding: 30px; border-radius: 16px; margin-bottom: 24px; }
    .ficha-colaborador { background: rgba(15, 23, 42, 0.8); border-left: 5px solid #2563eb; padding: 20px; border-radius: 8px; margin-top: 15px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

engine = create_engine(st.secrets["DATABASE_URL"])

# --- FUNÇÕES DE APOIO ---
def inicializar_banco():
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS cadastro_geral_colaborador (id TEXT PRIMARY KEY, nome TEXT, cpf TEXT, cargo TEXT, admissao DATE, demissao DATE, chave_pix TEXT);"))

inicializar_banco()

def formatar_id_limpo(id_original): return str(id_original).split('.')[0].strip() if pd.notna(id_original) else ""
def limpar_cpf(cpf): return ''.join(filter(str.isdigit, str(cpf)))
def sanitizar_texto(t): return str(t).strip() if pd.notna(t) else ""

# --- ROTEAMENTO ---
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação", "🛠️ Gestão de Cadastros"])

# --- VISÃO GERAL ---
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    df = pd.read_sql("SELECT * FROM cadastro_geral_colaborador", engine)
    st.dataframe(df, use_container_width=True)

# --- IMPORTAÇÃO ---
elif menu == "📥 Importação":
    st.title("📥 Importação Inteligente")
    arquivo = st.file_uploader("Suba o arquivo (.xlsx)", type=["xlsx"])
    if arquivo and st.button("Executar Carga"):
        df_bruto = pd.read_excel(arquivo)
        with engine.begin() as conn:
            for _, row in df_bruto.iterrows():
                conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome) ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome"), 
                             {"id": formatar_id_limpo(row[0]), "nome": sanitizar_texto(row[1])})
        st.success("Carga realizada!")

# --- GESTÃO DE CADASTROS ---
elif menu == "🛠️ Gestão de Cadastros":
    aba1, aba2, aba3, aba4 = st.tabs(["🔍 Consultar", "➕ Novo", "✏️ Alterar", "❌ Excluir"])
    
    with aba1:
        termo = st.text_input("Busca:")
        if termo:
            res = engine.connect().execute(text("SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t"), {"t": f"%{termo}%"}).fetchall()
            for r in res: st.markdown(f"<div class='ficha-colaborador'>👤 {r.nome} (ID: {r.id})</div>", unsafe_allow_html=True)

    with aba2:
        if st.button("Cancelar Operação"): st.rerun()
        with st.form("form_novo"):
            i_id = st.text_input("ID")
            i_nome = st.text_input("Nome")
            if st.form_submit_button("Salvar"):
                with engine.begin() as conn: conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome)"), {"id": i_id, "nome": i_nome})
                st.success("Gravado!")

    with aba3:
        if st.session_state['id_alterar'] is None:
            lista = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
            sel = st.selectbox("Selecione para alterar:", lista)
            if st.button("Carregar Ficha"): st.session_state['id_alterar'] = sel.split(" - ")[0]; st.rerun()
        else:
            id_alt = st.session_state['id_alterar']
            dados = engine.connect().execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_alt}).fetchone()
            with st.form("form_alt"):
                n_nome = st.text_input("Nome", value=dados.nome)
                col1, col2 = st.columns(2)
                if col1.form_submit_button("Salvar"):
                    with engine.begin() as conn: conn.execute(text("UPDATE cadastro_geral_colaborador SET nome = :n WHERE id = :id"), {"n": n_nome, "id": id_alt})
                    st.session_state['id_alterar'] = None; st.rerun()
                if col2.form_submit_button("Cancelar e Voltar"): st.session_state['id_alterar'] = None; st.rerun()

    with aba4:
        if st.session_state['id_excluir'] is None:
            lista_del = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
            sel_del = st.selectbox("Selecione para excluir:", lista_del)
            if st.button("Confirmar Exclusão?"): st.session_state['id_excluir'] = sel_del.split(" - ")[0]; st.rerun()
        else:
            id_del = st.session_state['id_excluir']
            st.warning(f"Confirma a exclusão de {id_del}?")
            col1, col2 = st.columns(2)
            if col1.button("Remover Definitivamente"):
                with engine.begin() as conn: conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_del})
                st.session_state['id_excluir'] = None; st.rerun()
            if col2.button("Cancelar"): st.session_state['id_excluir'] = None; st.rerun()
