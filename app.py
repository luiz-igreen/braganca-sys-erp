import streamlit as st
import psycopg2
import pandas as pd
import os

# Pega a string de conexão das Secrets
DATABASE_URL = st.secrets["DATABASE_URL"]

try:
    # Conecta ao banco
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Busca os dados
    cursor.execute("SELECT * FROM public.pagamentos_premios")
    dados = cursor.fetchall()
    
    # Pega os nomes das colunas
    colunas = [desc[0] for desc in cursor.description]
    
    # Cria DataFrame
    df = pd.DataFrame(dados, columns=colunas)
    
    st.success(f"✅ {len(df)} registros carregados!")
    st.dataframe(df)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    st.error(f"❌ Erro: {e}")
