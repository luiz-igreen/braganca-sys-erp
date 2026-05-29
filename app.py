import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Captura da URL de conexão diretamente das Secrets
# O nome da chave aqui precisa ser exatamente igual ao que configuramos no painel
db_url = st.secrets["DATABASE_URL"]

# 2. Criação do motor de conexão (Engine) do SQLAlchemy
engine = create_engine(db_url)

# ... (seu código de upload e leitura do Excel aqui) ...

# 3. Lógica de inserção ao clicar no botão
if st.button("Salvar no Banco de Dados"):
    try:
        # df é a variável onde você leu o Excel (pd.read_excel)
        # Substitua 'nome_da_sua_tabela' pelo nome exato da tabela criada no Supabase
        df.to_sql('nome_da_sua_tabela', con=engine, if_exists='append', index=False)
        
        st.success("Dados salvos com sucesso!")
        
    except Exception as e:
        # É exatamente aqui que aquele erro longo em vermelho estava sendo impresso
        st.error(f"Erro ao processar a planilha: {e}")
