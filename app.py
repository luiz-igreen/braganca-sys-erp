import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text, exc
import plotly.express as px
import datetime

# ==========================================
# 1. CONFIGURAÇÃO E ESTILO VISUAL PREMIUM
# ==========================================
st.set_page_config(page_title="Sistema Construart", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    .glass-container {
        background-color: rgba(15, 23, 42, 0.7);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        color: white;
    }
    .metric-card {
        background-color: rgba(30, 41, 59, 0.8);
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #ffffff; }
    .metric-label { font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXÃO E ESTADO
# ==========================================
@st.cache_resource
def iniciar_conexao():
    return create_engine(st.secrets["DATABASE_URL"])

engine = iniciar_conexao()

if 'gestao_modo' not in st.session_state: st.session_state.gestao_modo = 'pesquisa'
if 'gestao_resultados' not in st.session_state: st.session_state.gestao_resultados = None
if 'colab_edit_id' not in st.session_state: st.session_state.colab_edit_id = None

# ==========================================
# 3. ROTEAMENTO
# ==========================================
st.sidebar.markdown("## 🏗️ Construart Sys")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "👥 Gestão", "📥 Importar"])

# ==========================================
# MÓDULO DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 Painel de Controle")
    df_banco = pd.read_sql('pagamentos_premios', con=engine)
    total = len(df_banco)
    ativos = len(df_banco[df_banco['data_demissao'].isna()]) if 'data_demissao' in df_banco.columns else total
    desligados = total - ativos
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Total</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card" style="border-left-color: #10b981;"><div class="metric-label">Ativos</div><div class="metric-value">{ativos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card" style="border-left-color: #ef4444;"><div class="metric-label">Desligados</div><div class="metric-value">{desligados}</div></div>', unsafe_allow_html=True)

# ==========================================
# MÓDULO GESTÃO
# ==========================================
elif menu == "👥 Gestão":
    st.title("👥 Gestão de Colaboradores")
    if st.session_state.gestao_modo == 'pesquisa':
        termo = st.text_input("🔍 Pesquisar colaborador:")
        if st.button("Buscar"):
            q = text("SELECT * FROM pagamentos_premios WHERE id::text = :t OR nome ILIKE :t_like")
            st.session_state.gestao_resultados = pd.read_sql(q, con=engine, params={"t": termo, "t_like": f"%{termo}%"})
        
        if st.session_state.gestao_resultados is not None:
            st.dataframe(st.session_state.gestao_resultados, use_container_width=True)
            if st.button("✏️ Alterar Selecionado"): st.session_state.gestao_modo = 'editar'; st.rerun()
            if st.button("🗑️ Excluir"): 
                # (Lógica de exclusão aqui)
                st.rerun()
    
    elif st.session_state.gestao_modo == 'novo':
        with st.form("novo"):
            id_n = st.number_input("REG", min_value=1)
            nome_n = st.text_input("Nome")
            if st.form_submit_button("Salvar"):
                # (Lógica de insert aqui)
                st.session_state.gestao_modo = 'pesquisa'; st.rerun()

# ==========================================
# MÓDULO IMPORTAR
# ==========================================
elif menu == "📥 Importar":
    st.title("📥 Importar Planilha")
    # (Lógica original de importação)
