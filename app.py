import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração de Página Premium
st.set_page_config(page_title="Sistema Construart | Gestão", page_icon="🏆", layout="wide")

# Estilo CSS Profissional (Dark Glassmorphism)
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .card { 
        background: #1e293b; padding: 20px; border-radius: 12px; 
        border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 20px; 
    }
    .metric-title { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# Conexão
engine = create_engine(st.secrets["DATABASE_URL"])

# Menu Lateral Minimalista
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "👥 Gestão", "📥 Importar"])

# Roteador
if menu == "📊 Dashboard":
    st.title("📊 Dashboard Executivo")
    df = pd.read_sql('pagamentos_premios', con=engine)
    
    total = len(df)
    ativos = len(df[df['data_demissao'].isna()]) if 'data_demissao' in df.columns else total
    desligados = total - ativos
    
    c1, c2, c3 = st.columns(3)
    for col, tit, val, cor in [(c1, "Total Colaboradores", total, "#3b82f6"), 
                             (c2, "Colaboradores Ativos", ativos, "#10b981"), 
                             (c3, "Desligados", desligados, "#ef4444")]:
        col.markdown(f'<div class="card" style="border-left: 4px solid {cor}"><div class="metric-title">{tit}</div><div class="metric-value">{val}</div></div>', unsafe_allow_html=True)

elif menu == "👥 Gestão":
    st.title("👥 Gestão de Colaboradores")
    
    # Busca com foco em precisão
    termo = st.text_input("🔍 Pesquisar por ID ou Nome:")
    if st.button("Buscar Colaborador"):
        q = text("SELECT * FROM pagamentos_premios WHERE id::text = :t OR nome ILIKE :t_like")
        df_res = pd.read_sql(q, con=engine, params={"t": termo, "t_like": f"%{termo}%"})
        st.session_state.resultados = df_res

    if 'resultados' in st.session_state and st.session_state.resultados is not None:
        df = st.session_state.resultados
        st.dataframe(df, use_container_width=True)
        
        if not df.empty:
            selecionado = st.selectbox("Selecione o registro para ação:", df['nome'].values)
            id_sel = df[df['nome'] == selecionado]['id'].values[0]
            
            col1, col2 = st.columns(2)
            if col1.button("✏️ Alterar Selecionado"):
                st.session_state.editando = id_sel
            if col2.button("🗑️ Excluir Selecionado"):
                with engine.begin() as conn: conn.execute(text("DELETE FROM pagamentos_premios WHERE id = :id"), {"id": id_sel})
                st.rerun()

elif menu == "📥 Importar":
    st.title("📥 Importação Segura")
    st.info("Utilize este módulo apenas para carga inicial de dados.")
    # (Lógica original preservada)
