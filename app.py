import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração de Página Premium
st.set_page_config(page_title="Sistema Construart | Gestão", page_icon="🏆", layout="wide")

# Estilo CSS Profissional (Design System Inspirado nos Modelos)
st.markdown("""
<style>
    .stApp { background-color: #0c111d; color: #e2e8f0; }
    .card-metric { 
        background: #1e293b; border-radius: 16px; padding: 24px;
        border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    .card-gestao { 
        background: #111827; border-radius: 16px; padding: 30px;
        border: 1px solid #1f2937;
    }
    .metric-title { color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #f8fafc; margin-top: 5px; }
    div[data-testid="stDataFrame"] { border-radius: 10px; border: 1px solid #1f2937; }
</style>
""", unsafe_allow_html=True)

# Conexão
engine = create_engine(st.secrets["DATABASE_URL"])

# Menu Lateral (Estilo Sidebar Slim)
st.sidebar.markdown("## 🏗️ Construart")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "👥 Gestão", "📥 Importar"])

# Roteador Principal
if menu == "📊 Dashboard":
    st.title("📊 Painel Executivo")
    df = pd.read_sql('pagamentos_premios', con=engine)
    
    total = len(df)
    ativos = len(df[df['data_demissao'].isna()]) if 'data_demissao' in df.columns else total
    desligados = total - ativos
    
    c1, c2, c3 = st.columns(3)
    for col, tit, val, cor in [(c1, "Total Geral", total, "#3b82f6"), 
                             (c2, "Colaboradores Ativos", ativos, "#10b981"), 
                             (c3, "Desligamentos", desligados, "#ef4444")]:
        col.markdown(f'<div class="card-metric"><div class="metric-title">{tit}</div><div class="metric-value">{val}</div></div>', unsafe_allow_html=True)

elif menu == "👥 Gestão":
    st.title("👥 Gestão de Colaboradores")
    
    # container de busca elegante
    with st.container():
        col_pesq, col_btn = st.columns([4, 1])
        termo = col_pesq.text_input("🔍 Pesquisar por ID ou Nome", label_visibility="collapsed", placeholder="Digite o nome ou ID...")
        if col_btn.button("Buscar"):
            q = text("SELECT * FROM pagamentos_premios WHERE id::text = :t OR nome ILIKE :t_like")
            st.session_state.resultados = pd.read_sql(q, con=engine, params={"t": termo, "t_like": f"%{termo}%"})

    if 'resultados' in st.session_state and st.session_state.resultados is not None:
        df = st.session_state.resultados
        st.markdown('<div class="card-gestao">', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        
        if not df.empty:
            selecionado = st.selectbox("Selecione para Ação:", df['nome'].values)
            id_sel = df[df['nome'] == selecionado]['id'].values[0]
            
            c_alt, c_exc = st.columns(2)
            if c_alt.button("✏️ Alterar Selecionado"):
                st.session_state.editando = id_sel
            if c_exc.button("🗑️ Excluir Selecionado"):
                with engine.begin() as conn: conn.execute(text("DELETE FROM pagamentos_premios WHERE id = :id"), {"id": id_sel})
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif menu == "📥 Importar":
    st.title("📥 Módulo de Importação")
    st.markdown('<div class="card-gestao">', unsafe_allow_html=True)
    st.info("Utilize este espaço para carregar a base principal.")
    st.markdown('</div>', unsafe_allow_html=True)
