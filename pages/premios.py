import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, parse_br_date_smart):
    st.title("Gestao de Premios (ZAUT)")
    st.write("Visualizacao e gerenciamento dos premios lancados no sistema.")

    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM premios_funcionarios ORDER BY id DESC")
            df = pd.read_sql(query, conn)

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum premio registrado no banco de dados no momento.")

    except Exception as e:
        st.error(f"Falha na extracao de dados do banco: {e}")
