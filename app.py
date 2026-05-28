import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Premio-Obras-Construart", layout="wide")

st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #0E1117; color: #FFFFFF; }
        .stButton>button { background-color: #50C878 !important; color: #0E1117 !important; font-weight: bold !important; }
        h1, h2, h3 { color: #50C878 !important; }
    </style>
""", unsafe_allow_html=True)

DB_NAME = "premios_construart.db"

def rodar_query(query, params=(), commit=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit: conn.commit()
        return cursor.fetchall()
    finally:
        conn.close()

# --- TÍTULO ---
st.title("🏗️ Gestão de Prêmios 2026")

# --- ÁREA DE IMPORTAÇÃO COM FILTRO DE LIMPEZA ---
st.markdown("### 📥 Importação e Ajustes de Dados")
col_imp1, col_imp2 = st.columns([3, 1])

with col_imp1:
    arquivo = st.file_uploader("Arraste seu arquivo .xlsx aqui", type=["xlsx"])
with col_imp2:
    st.write("Cuidado:")
    if st.button("🗑️ Resetar Banco (Apagar Tudo)"):
        rodar_query("DELETE FROM premios", commit=True)
        rodar_query("DELETE FROM sqlite_sequence WHERE name='premios'", commit=True) # Reseta o ID para 1
        st.warning("Banco de dados resetado!")
        st.rerun()

if arquivo:
    try:
        df_import = pd.read_excel(arquivo)
        
        # LIMPEZA: Remove linhas onde o nome é vazio ou "nan"
        df_import = df_import.dropna(subset=['Nome']) # Remove nulos na coluna Nome
        df_import = df_import[df_import['Nome'].astype(str).str.strip() != ""] # Remove vazios
        
        st.write(f"Linhas válidas encontradas: {len(df_import)}")
        
        if st.button("🔥 CONFIRMAR IMPORTAÇÃO LIMPA"):
            for _, row in df_import.iterrows():
                nome = str(row.get('Nome', '')).strip()
                pix = str(row.get('Chave PIX', '')).strip()
                valor = float(row.get('Valor', 0))
                mes = datetime.now().strftime("%m/%Y")
                
                if nome and nome.lower() != "nan":
                    rodar_query("INSERT INTO premios (nome, chave_pix, mes_ano, valor) VALUES (?,?,?,?)", 
                               (nome, pix, mes, valor), commit=True)
            st.success("✅ Importação limpa concluída!")
            st.rerun()
    except Exception as e:
        st.error(f"Erro ao processar: {e}")

st.markdown("---")
# BOTÕES DE NAVEGAÇÃO
col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
with col_b1: st.button("✨ Novo")
with col_b2: st.button("📥 Incluir")
with col_b3: st.button("🔍 Consultar")
with col_b4: st.button("✏️ Alterar")
with col_b5: st.button("❌ Excluir")

# LISTAGEM FINAL
st.markdown("### 📋 Lista Oficial de Prêmios")
dados = rodar_query("SELECT id, nome, chave_pix, valor FROM premios ORDER BY id ASC")
if dados:
    df_final = pd.DataFrame(dados, columns=["ID", "Nome", "Chave PIX", "Valor"])
    st.dataframe(df_final, use_container_width=True)
else:
    st.info("O sistema está limpo. Suba a planilha para começar.")
