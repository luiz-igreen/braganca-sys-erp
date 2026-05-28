import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO VISUAL (DARK MODE + ESMERALDA)
st.set_page_config(page_title="Premio-Obras-Construart", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #0E1117; color: #FFFFFF; }
        .stButton>button { background-color: #50C878 !important; color: #0E1117 !important; font-weight: bold !important; width: 100%; border-radius: 8px; }
        h1, h2, h3 { color: #50C878 !important; }
        .stDataFrame { border: 1px solid #50C878; }
    </style>
""", unsafe_allow_html=True)

# BANCO DE DADOS
DB_NAME = "premios_construart.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""CREATE TABLE IF NOT EXISTS premios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, chave_pix TEXT, mes_ano TEXT, valor REAL)""")
    conn.commit()
    conn.close()

init_db()

def rodar_query(query, params=(), commit=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    res = cursor.fetchall() if not commit else cursor.lastrowid
    if commit: conn.commit()
    conn.close()
    return res

# INTERFACE PRINCIPAL
st.title("🏗️ Gestão de Prêmios 2026")
st.subheader("Painel de Controle - Obras Construart")

# BOTÕES OBRIGATÓRIOS
col1, col2, col3, col4, col5 = st.columns(5)
with col1: btn_novo = st.button("✨ Novo")
with col2: btn_incluir = st.button("📥 Incluir")
with col3: btn_consultar = st.button("🔍 Consultar")
with col4: btn_alterar = st.button("✏️ Alterar")
with col5: btn_excluir = st.button("❌ Excluir")

if btn_novo: st.session_state.aba = "Novo"
if btn_incluir: st.session_state.aba = "Incluir"
if btn_consultar: st.session_state.aba = "Consultar"
if btn_alterar: st.session_state.aba = "Alterar"
if btn_excluir: st.session_state.aba = "Excluir"

aba_atual = st.session_state.get("aba", "Consultar")

# --- LÓGICA DE IMPORTAÇÃO (NOVO) ---
if aba_atual == "Novo":
    st.markdown("### ✨ Cadastrar ou Importar Planilha")
    st.info("Você pode cadastrar manualmente ou subir sua planilha Excel/CSV abaixo.")
    
    arquivo_upload = st.file_uploader("Arraste aqui a planilha (Ex: PremioBraganca.xlsx)", type=["xlsx", "csv"])
    
    if arquivo_upload:
        try:
            if arquivo_upload.name.endswith('.csv'):
                df_import = pd.read_csv(arquivo_upload)
            else:
                df_import = pd.read_excel(arquivo_upload)
            
            st.write("Visualização dos dados detectados:")
            st.dataframe(df_import.head(5))
            
            if st.button("Confirmar Importação de todos os registros"):
                for _, row in df_import.iterrows():
                    # Mapeamento dinâmico baseado na sua planilha
                    nome = str(row.get('Nome', row.get('NOME', '')))
                    pix = str(row.get('Chave PIX', row.get('PIX', '')))
                    valor = float(row.get('Valor', row.get('VALOR', 0)))
                    mes = datetime.now().strftime("%m/%Y")
                    
                    rodar_query("INSERT INTO premios (nome, chave_pix, mes_ano, valor) VALUES (?,?,?,?)", 
                               (nome, pix, mes, valor), commit=True)
                st.success("✅ Todos os colaboradores foram importados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

# --- LÓGICA DE CONSULTA ---
elif aba_atual == "Consultar":
    st.markdown("### 🔍 Registros no Banco de Dados")
    dados = rodar_query("SELECT id, nome, chave_pix, mes_ano, valor FROM premios ORDER BY id DESC")
    if dados:
        df = pd.DataFrame(dados, columns=["ID", "Nome", "Chave PIX", "Mês/Ano", "Valor"])
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("O banco de dados está vazio. Vá em 'Novo' para importar sua planilha.")

# --- DEMAIS OPERAÇÕES (RESUMO) ---
elif aba_atual == "Incluir":
    with st.form("form_add"):
        n = st.text_input("Nome")
        p = st.text_input("PIX")
        v = st.number_input("Valor", min_value=0.0)
        m = st.text_input("Mês/Ano", value=datetime.now().strftime("%m/%Y"))
        if st.form_submit_button("Salvar Registro"):
            rodar_query("INSERT INTO premios (nome, chave_pix, mes_ano, valor) VALUES (?,?,?,?)", (n,p,m,v), commit=True)
            st.success("Salvo!")

elif aba_atual == "Excluir":
    id_del = st.number_input("ID para excluir", min_value=1, step=1)
    if st.button("Confirmar Exclusão"):
        rodar_query("DELETE FROM premios WHERE id=?", (id_del,), commit=True)
        st.success("Removido!")
