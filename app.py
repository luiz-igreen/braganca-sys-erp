import streamlit as pd
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E TEMA (DARK MODE / VERDE ESMERALDA)
# ==============================================================================
st.set_page_config(
    page_title="Premio-Obras-Construart",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS para garantir o visual "Gestão de Prêmios 2026" (Dark Mode + Verde Esmeralda)
st.markdown("""
    <style>
        /* Cores principais em Verde Esmeralda */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0E1117;
            color: #FFFFFF;
        }
        .stButton>button {
            background-color: #50C878 !important; /* Verde Esmeralda */
            color: #0E1117 !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            border: none !important;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #40A860 !important;
            transform: scale(1.02);
        }
        /* Estilização de inputs e tabelas */
        div[data-baseweb="select"] {
            cursor: pointer;
        }
        h1, h2, h3 {
            color: #50C878 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO E FUNÇÕES DO BANCO DE DADOS (SQLite)
# ==============================================================================
DB_NAME = "premios_construart.db"

def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS premios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            chave_pix TEXT NOT NULL,
            mes_ano TEXT NOT NULL,
            valor REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def rodar_query(query, params=(), commit=False):
    """Executa queries no banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if commit:
        conn.commit()
        resultado = cursor.lastrowid
    else:
        resultado = cursor.fetchall()
    conn.close()
    return resultado

# ==============================================================================
# 3. INTERFACE DO DASHBOARD
# ==============================================================================
st.title("🏗️ Gestão de Prêmios 2026")
st.subheader("Painel de Controle - Premio-Obras-Construart")
st.markdown("---")

# Inicialização de estados de sessão para controle de fluxo dos botões
if "acao_atual" not in st.session_state:
    st.session_state.acao_atual = "Consultar"
if "id_alterar" not in st.session_state:
    st.session_state.id_alterar = None

# ---- MENU DE BOTÕES OBRIGATÓRIOS ----
col_btn1, col_btn2, col_btn3, col_btn4, col_btn5 = st.columns(5)

with col_btn1:
    if st.button("✨ Novo", use_container_width=True):
        st.session_state.acao_atual = "Novo"
with col_btn2:
    if st.button("📥 Incluir", use_container_width=True):
        st.session_state.acao_atual = "Incluir"
with col_btn3:
    if st.button("🔍 Consultar", use_container_width=True):
        st.session_state.acao_atual = "Consultar"
with col_btn4:
    if st.button("✏️ Alterar", use_container_width=True):
        st.session_state.acao_atual = "Alterar"
with col_btn5:
    if st.button("❌ Excluir", use_container_width=True):
        st.session_state.acao_atual = "Excluir"

st.markdown(f"### Operação Ativa: **{st.session_state.acao_atual}**")

# ==============================================================================
# 4. LÓGICA DAS OPERAÇÕES (CRUD)
# ==============================================================================

# ---- OPERAÇÃO: NOVO ----
if st.session_state.acao_atual == "Novo":
    st.info("Campos limpos. Preencha os dados abaixo e clique no botão 'Incluir' no menu superior para salvar.")
    st.session_state.nome_input = ""
    st.session_state.pix_input = ""
    st.session_state.valor_input = 0.0
    st.session_state.acao_atual = "Formulario_Novo"

# ---- OPERAÇÃO: INCLUIR / FORMULÁRIO ----
if st.session_state.acao_atual in ["Incluir", "Formulario_Novo"]:
    with st.form("form_incluir", clear_on_submit=True):
        st.write("### Cadastrar Novo Prêmio")
        nome = st.text_input("Nome do Colaborador")
        chave_pix = st.text_input("Chave PIX")
        
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            mes_ano = st.date_input("Mês/Ano de Referência", value=datetime.today()).strftime("%m/%Y")
        with col_form2:
            valor = st.number_input("Valor do Prêmio (R$)", min_value=0.0, step=50.0, format="%.2f")
            
        btn_gravar = st.form_submit_button("Gravar no Banco de Dados")
        
        if btn_gravar:
            if nome and chave_pix and valor > 0:
                query = "INSERT INTO premios (nome, chave_pix, mes_ano, valor) VALUES (?, ?, ?, ?)"
                rodar_query(query, (nome, chave_pix, mes_ano, valor), commit=True)
                st.success(f"Prêmio de R$ {valor:.2f} para {nome} incluído com sucesso!")
                st.session_state.acao_atual = "Consultar"
                st.rerun()
            else:
                st.error("Por favor, preencha todos os campos corretamente.")

# ---- OPERAÇÃO: CONSULTAR ----
elif st.session_state.acao_atual == "Consultar":
    # Filtros de Busca
    col_filtro1, col_filtro2 = st.columns([3, 1])
    with col_filtro1:
        busca_nome = st.text_input("Filtrar por Nome do Colaborador")
    with col_filtro2:
        # Busca anos/meses dinâmicos
        dados_meses = rodar_query("SELECT DISTINCT mes_ano FROM premios")
        lista_meses = ["Todos"] + [m[0] for m in dados_meses]
        busca_mes = st.selectbox("Filtrar por Mês/Ano", lista_meses)

    # Construção da Query de Busca
    query = "SELECT id, nome, chave_pix, mes_ano, valor FROM premios WHERE 1=1"
    params = []
    if busca_nome:
        query += " AND nome LIKE ?"
        params.append(f"%{busca_nome}%")
    if busca_mes != "Todos":
        query += " AND mes_ano = ?"
        params.append(busca_mes)
        
    query += " ORDER BY id DESC"
    resultados = rodar_query(query, params)

    if resultados:
        df = pd.DataFrame(resultados, columns=["ID", "Nome", "Chave PIX", "Mês/Ano", "Valor (R$)"])
        
        # Cards de KPI informativos no topo da consulta
        col_kpi1, col_kpi2 = st.columns(2)
        col_kpi1.metric("Total de Prêmios Concedidos", len(df))
        col_kpi2.metric("Valor Total Investido", f"R$ {df['Valor (R$)'].sum():,.2f}")
        
        st.dataframe(df.set_index("ID"), use_container_width=True)
    else:
        st.warning("Nenhum registro encontrado para os filtros aplicados.")

# ---- OPERAÇÃO: ALTERAR ----
elif st.session_state.acao_atual == "Alterar":
    st.write("### Selecione o registro que deseja alterar")
    registros = rodar_query("SELECT id, nome, mes_ano, valor FROM premios ORDER BY id DESC")
    
    if registros:
        opcoes = {f"ID: {r[0]} | {r[1]} ({r[2]}) - R$ {r[3]:.2f}": r[0] for r in registros}
        selecionado = st.selectbox("Escolha o registro para modificação:", list(opcoes.keys()))
        id_registro = opcoes[selecionado]
        
        # Busca dados atuais do registro selecionado
        dados_atuais = rodar_query("SELECT nome, chave_pix, mes_ano, valor FROM premios WHERE id = ?", (id_registro,))[0]
        
        with st.form("form_alterar"):
            st.write(f"**Editando ID: {id_registro}**")
            novo_nome = st.text_input("Nome do Colaborador", value=dados_atuais[0])
            nova_chave = st.text_input("Chave PIX", value=dados_atuais[1])
            novo_mes = st.text_input("Mês/Ano (MM/AAAA)", value=dados_atuais[2])
            novo_valor = st.number_input("Valor (R$)", value=float(dados_atuais[3]), min_value=0.0, format="%.2f")
            
            btn_salvar_alteracao = st.form_submit_button("Salvar Alterações")
            
            if btn_salvar_alteracao:
                query_update = """
                    UPDATE premios 
                    SET nome = ?, chave_pix = ?, mes_ano = ?, valor = ? 
                    WHERE id = ?
                """
                rodar_query(query_update, (novo_nome, nova_chave, novo_mes, novo_valor, id_registro), commit=True)
                st.success("Registro atualizado com sucesso!")
                st.session_state.acao_atual = "Consultar"
                st.rerun()
    else:
        st.warning("Não há registros disponíveis para alteração.")

# ---- OPERAÇÃO: EXCLUIR ----
elif st.session_state.acao_atual == "Excluir":
    st.write("### Exclusão de Registros")
    registros = rodar_query("SELECT id, nome, mes_ano, valor FROM premios ORDER BY id DESC")
    
    if registros:
        opcoes = {f"ID: {r[0]} | {r[1]} ({r[2]}) - R$ {r[3]:.2f}": r[0] for r in registros}
        selecionado = st.selectbox("Escolha o registro que deseja deletar permanentemente:", list(opcoes.keys()))
        id_registro = opcoes[selecionado]
        
        st.warning("⚠️ Atenção: Esta ação não pode ser desfeita!")
        btn_confirmar_exclusao = st.button("Confirmar Exclusão Definitiva")
        
        if btn_confirmar_exclusao:
            rodar_query("DELETE FROM premios WHERE id = ?", (id_registro,), commit=True)
            st.success("Registro removido com sucesso do banco de dados!")
            st.session_state.acao_atual = "Consultar"
            st.rerun()
    else:
        st.warning("Não há registros disponíveis para exclusão.")
