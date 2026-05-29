import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import datetime

# --- CONFIGURAÇÃO DE DESIGN (UI/UX) ---
st.set_page_config(page_title="Sistema de Prêmios - Construart", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
    .card { background: #1e293b; padding: 25px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 20px; }
    .metric-title { color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; }
    .metric-value { font-size: 2rem; font-weight: 800; color: #ffffff; }
    .stButton>button { border-radius: 8px; width: 100%; font-weight: 600; }
    input, select { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM BANCO DE DADOS ---
# Utilizando a string de conexão obrigatória conforme doc de infraestrutura
engine = create_engine(st.secrets["DATABASE_URL"])

# --- LÓGICA DE IMPORTAÇÃO (LOOP DE ABAS) ---
def processar_planilha(arquivo):
    xls = pd.ExcelFile(arquivo)
    todos_dados = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Extração de Competência (ex: PremiaAbril2024 -> Abril 2024)
        df['competencia_mes_ano'] = sheet_name.replace('Premio', '')
        todos_dados.append(df)
    return pd.concat(todos_dados, ignore_index=True)

# --- NAVEGAÇÃO ---
st.sidebar.markdown("## 🏗️ Construart ERP")
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação", "🛠️ Gestão Manual"])

if menu == "👥 Visão Geral":
    st.title("👥 Visão Geral de Premiações")
    df = pd.read_sql("SELECT * FROM premios_funcionarios", engine)
    
    # KPIs
    total_func = df['codigo_funcionario'].nunique()
    total_valor = df['valor_premio_final'].sum()
    
    col1, col2 = st.columns(2)
    col1.markdown(f'<div class="card"><div class="metric-title">Funcionários</div><div class="metric-value">{total_func}</div></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="card"><div class="metric-title">Valor Total (R$)</div><div class="metric-value">R$ {total_valor:,.2f}</div></div>', unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)

elif menu == "📥 Importação":
    st.title("📥 Importação de Planilha")
    uploaded_file = st.file_uploader("Selecione o arquivo PremioBraganca.xlsx", type=["xlsx"])
    if uploaded_file:
        if st.button("Processar Todas as Abas", type="primary"):
            df_final = processar_planilha(uploaded_file)
            df_final.to_sql('premios_funcionarios', engine, if_exists='append', index=False)
            st.success("Dados importados com sucesso!")

elif menu == "🛠️ Gestão Manual":
    st.title("🛠️ Gestão de Prêmios")
    
    # Botões de Ação
    col_pesq, col_novo = st.columns([4, 1])
    termo = col_pesq.text_input("🔍 Pesquisar por Nome, CPF ou Competência")
    if col_novo.button("➕ Novo Registro"): st.session_state.modo = 'novo'
    
    # CRUD - Lógica de Exibição e Botões
    df = pd.read_sql("SELECT * FROM premios_funcionarios", engine)
    
    if st.session_state.get('modo') == 'novo':
        with st.form("form_novo"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome do Funcionário")
            cpf = c2.text_input("CPF")
            valor = c1.number_input("Valor Prêmio Final (R$)", format="%.2f")
            comp = c2.text_input("Competência (Ex: 04-2024)")
            if st.form_submit_button("💾 Salvar"):
                conn = engine.connect()
                conn.execute(text("INSERT INTO premios_funcionarios (nome, cpf, valor_premio_final, competencia_mes_ano) VALUES (:n, :c, :v, :m)"), 
                             {"n": nome, "c": cpf, "v": valor, "m": comp})
                st.session_state.modo = 'listagem'; st.rerun()

    # Botões de Ação na Tabela
    if st.button("✏️ Alterar Selecionado"): pass # Lógica de UPDATE
    if st.button("🗑️ Excluir Selecionado"): 
        if st.checkbox("Confirmar deleção?"):
            pass # Lógica de DELETE    
