import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    st.title("🏆 Gestão de Prêmios (ZAUT)")
    st.markdown("Visualização e gerenciamento dos prêmios lançados no sistema.")

    try:
        with engine.connect() as conn:
            # Busca os dados ordenados do mais recente para o mais antigo
            df = pd.read_sql(text("SELECT * FROM premios_funcionarios ORDER BY id DESC"), conn)

        if not df.empty:
            # Remove a coluna 'id' (chave primária do banco) para evitar duplicidade com 'codigo_funcionario'
            if 'id' in df.columns:
                df = df.drop(columns=['id'])

            # Renderiza o dataframe sem o índice lateral do Pandas
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum prêmio registrado no sistema.")

    except Exception as e:
        st.error(f"Falha na extração de dados do banco PostgreSQL: {e}")
