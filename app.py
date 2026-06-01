import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

# Database ID: 1n-LpTzN9IiBF5TgcBqMW9vgQE_VYtrsKbiy73RP5kYI
engine = create_engine(st.secrets["DATABASE_URL"])

# --- ESTILIZAÇÃO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .panel-glass { background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(51, 65, 85, 0.7); padding: 20px; border-radius: 16px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- CONTROLE DE ESTADO ---
if 'id_edicao' not in st.session_state: 
    st.session_state['id_edicao'] = None

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros"])

# --- 1. VISÃO GERAL ---
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    try:
        df = pd.read_sql("SELECT * FROM cadastro_geral_colaborador", engine)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error("Erro ao carregar dados: " + str(e))

# --- 2. IMPORTAÇÃO INTELIGENTE ---
elif menu == "📥 Importação Inteligente":
    st.title("📥 Importação Inteligente")
    arquivo = st.file_uploader("Selecione o arquivo (.xlsx, .csv)", type=["xlsx", "csv"])
    
    if arquivo and st.button("Executar Ingestão Certificada"):
        try:
            if arquivo.name.endswith('.xlsx'):
                df_bruto = pd.read_excel(arquivo, engine='openpyxl')
            else:
                df_bruto = pd.read_csv(arquivo)
            
            with engine.begin() as conn:
                for _, row in df_bruto.iterrows():
                    conn.execute(text("""
                        INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome)
                        ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome
                    """), {"id": str(row[0]), "nome": str(row[1])})
            st.success("Importação concluída com sucesso!")
        except Exception as e:
            st.error(f"Erro na importação: {e}")

# --- 3. GESTÃO DE CADASTROS ---
elif menu == "🛠️ Gestão de Cadastros":
    # As abas só são definidas aqui, dentro desta condicional
    aba1, aba2, aba3, aba4 = st.tabs(["🔍 Consultar", "➕ Novo", "✏️ Alterar", "❌ Excluir"])

    with aba1: # CONSULTAR
        st.subheader("Consultar")
        termo = st.text_input("Busca (ID ou Nome):", key="busca_consulta")
        if st.button("Buscar"):
            if termo:
                # Verifica se o termo é um número para busca exata (ID)
                if termo.isdigit():
                    sql = "SELECT * FROM cadastro_geral_colaborador WHERE id = :t"
                    params = {"t": int(termo)}
                else:
                    sql = "SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t"
                    params = {"t": f"%{termo}%"}
                
                res = engine.connect().execute(text(sql), params).fetchall()
                if res:
                    for r in res: st.write(f"ID: {r.id} | Nome: {r.nome}")
                else:
                    st.warning("Nenhum registro encontrado.")

    with aba2: # NOVO
        st.subheader("Novo Cadastro")
        if st.button("Cancelar Operação", key="canc_novo"): 
            st.rerun()
        
        with st.form("form_novo", clear_on_submit=True):
            i_id = st.text_input("ID")
            i_nome = st.text_input("Nome")
            
            if st.form_submit_button("Salvar Registro"):
                if not i_id or not i_nome:
                    st.error("⚠️ Erro: Os campos ID e Nome são obrigatórios.")
                else:
                    try:
                        with engine.begin() as conn: 
                            conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome)"), {"id": i_id, "nome": i_nome})
                        st.success("Salvo com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    with aba3: # ALTERAR
        st.subheader("Alterar Cadastro")
        if st.session_state['id_edicao'] is None:
            lista = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
            sel = st.selectbox("Selecione para alterar:", lista)
            if st.button("Carregar Ficha"): 
                st.session_state['id_edicao'] = sel.split(" - ")[0]
                st.rerun()
        else:
            id_alt = st.session_state['id_edicao']
            if st.button("Cancelar Edição", key="canc_alt"): 
                st.session_state['id_edicao'] = None
                st.rerun()
            
            dados = engine.connect().execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_alt}).fetchone()
            with st.form("form_alt"):
                n_nome = st.text_input("Nome", value=dados.nome)
                if st.form_submit_button("Salvar Alterações"):
                    if not n_nome:
                        st.error("⚠️ Erro: O campo Nome não pode estar vazio.")
                    else:
                        with engine.begin() as conn: 
                            conn.execute(text("UPDATE cadastro_geral_colaborador SET nome = :n WHERE id = :id"), {"n": n_nome, "id": id_alt})
                        st.session_state['id_edicao'] = None
                        st.success("Alterado com sucesso!")
                        st.rerun()

    with aba4: # EXCLUIR
        st.subheader("Excluir Cadastro")
        lista_del = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
        sel_del = st.selectbox("Selecione para excluir:", lista_del)
        cols = st.columns(2)
        if cols[0].button("Confirmar Exclusão"):
            with engine.begin() as conn: conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": sel_del.split(" - ")[0]})
            st.rerun()
        if cols[1].button("Cancelar"):
            st.rerun()
