import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="Sistema de Prêmios", layout="wide")
st.title("🏆 Sistema de Prêmios - CONSTRUART")

# 1. Captura da URL de conexão das Secrets
db_url = st.secrets["DATABASE_URL"]

# 2. Criação do motor de conexão
engine = create_engine(db_url)

# 3. Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Lê o Excel
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Planilha lida com sucesso! ({len(df)} linhas)")
        
        # Mostra preview
        st.dataframe(df.head())
        
        # Botão para salvar
        if st.button("Salvar no Banco de Dados"):
            try:
                # Insere na tabela pagamentos_premios no schema public
                df.to_sql(
                    'pagamentos_premios',
                    con=engine,
                    schema='public',
                    if_exists='append',
                    index=False
                )
                st.success("✅ Dados salvos com sucesso no Supabase!")
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Erro ao processar a planilha: {str(e)}")

else:
    st.info("💡 Faça upload de um arquivo Excel para começar")
