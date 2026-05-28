import streamlit as st
import pandas as pd
import sqlalchemy

# Criamos a conexão com o banco de dados
conn = st.connection("postgresql", type="sql")

# Função segura para ler dados sem travar a tela
def carregar_dados_seguro():
    try:
        # Tenta ler a tabela
        return conn.query("SELECT * FROM public.pagamentos_premios;", ttl="0")
    except Exception:
        # Se der erro, retorna um DataFrame vazio
        return pd.DataFrame()

# Chamada da função
df_visualizacao = carregar_dados_seguro()

# Exibição na tela
if df_visualizacao.empty:
    st.info("💡 O banco de dados está pronto, mas a tabela está vazia. Por favor, faça a importação da planilha abaixo para começar.")
else:
    st.write(f"Exibindo {len(df_visualizacao)} colaboradores.")
    st.dataframe(df_visualizacao)
