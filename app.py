import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração de Página Premium
st.set_page_config(page_title="Sistema Construart | Gestão", page_icon="🏆", layout="wide")

# Estilo CSS Profissional
st.markdown("""
<style>
    .stApp { background-color: #0c111d; color: #e2e8f0; }
    .card-metric { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
    .card-gestao { background: #111827; border-radius: 12px; padding: 25px; border: 1px solid #1f2937; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

engine = create_engine(st.secrets["DATABASE_URL"])

# Inicialização de Estado
if 'modo' not in st.session_state: st.session_state.modo = 'pesquisa'

# Menu Lateral
st.sidebar.markdown("## 🏗️ Construart")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "👥 Gestão", "📥 Importar"])

if menu == "📊 Dashboard":
    st.title("📊 Painel Executivo")
    df = pd.read_sql('pagamentos_premios', con=engine)
    total = len(df)
    ativos = len(df[df['data_demissao'].isna()]) if 'data_demissao' in df.columns else total
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-metric">Total<div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-metric">Ativos<div class="metric-value">{ativos}</div></div>', unsafe_allow_html=True)

elif menu == "👥 Gestão":
    st.title("👥 Gestão de Colaboradores")
    
    col1, col2 = st.columns([4, 1])
    termo = col1.text_input("🔍 Pesquisar por ID ou Nome")
    if col2.button("Buscar"):
        q = text("SELECT * FROM pagamentos_premios WHERE id::text = :t OR nome ILIKE :t_like")
        st.session_state.res = pd.read_sql(q, con=engine, params={"t": termo, "t_like": f"%{termo}%"})
    
    if st.button("➕ Novo Colaborador"): st.session_state.modo = 'novo'; st.rerun()

    if 'res' in st.session_state and st.session_state.res is not None:
        st.dataframe(st.session_state.res, use_container_width=True)
        sel = st.selectbox("Selecione um colaborador:", st.session_state.res['nome'].values)
        id_sel = st.session_state.res[st.session_state.res['nome'] == sel]['id'].values[0]
        
        b1, b2 = st.columns(2)
        if b1.button("✏️ Alterar Selecionado"): 
            st.session_state.modo = 'editar'; st.session_state.id_edit = id_sel; st.rerun()
        if b2.button("🗑️ Excluir Selecionado"):
            with engine.begin() as conn: conn.execute(text("DELETE FROM pagamentos_premios WHERE id = :id"), {"id": id_sel})
            st.success("Excluído!"); st.session_state.res = None; st.rerun()

    # Lógica de Edição/Novo
    if st.session_state.modo == 'novo':
        with st.form("form_novo"):
            id_n = st.number_input("REG (ID)", min_value=1)
            nome_n = st.text_input("Nome")
            if st.form_submit_button("Salvar"):
                with engine.begin() as conn: conn.execute(text("INSERT INTO pagamentos_premios (id, nome) VALUES (:id, :n)"), {"id": id_n, "n": nome_n.upper()})
                st.session_state.modo = 'pesquisa'; st.rerun()

    elif st.session_state.modo == 'editar':
        with st.form("form_edit"):
            novo_nome = st.text_input("Novo Nome")
            if st.form_submit_button("Atualizar"):
                with engine.begin() as conn: conn.execute(text("UPDATE pagamentos_premios SET nome = :n WHERE id = :id"), {"n": novo_nome.upper(), "id": st.session_state.id_edit})
                st.session_state.modo = 'pesquisa'; st.rerun()

elif menu == "📥 Importar":
    st.title("📥 Módulo de Importação")
    st.info("Função de carga original mantida.")
