import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Configuração da página
st.set_page_config(page_title="Sistema de Prêmios - Construart", layout="wide")

# 2. Conexão com o Banco de Dados (puxando a senha das Secrets)
db_url = st.secrets["DATABASE_URL"]
engine = create_engine(db_url)
conn = st.connection("postgresql", type="sql", url=db_url)

# 3. Função para ler os dados do banco com segurança
def carregar_dados():
    try:
        return conn.query("SELECT * FROM public.pagamentos_premios;", ttl="0")
    except Exception:
        return pd.DataFrame()

# 4. Interface Principal (Título)
st.title("🏆 Sistema de Prêmios - Construart")
st.markdown("---")

# 5. Barra Lateral (Upload da Planilha)
st.sidebar.header("📥 Importar Planilha")
st.sidebar.write("Faça o upload do arquivo Excel com os dados dos colaboradores.")
arquivo_excel = st.sidebar.file_uploader("Selecione o arquivo Excel", type=["xlsx", "xls"])

if arquivo_excel is not None:
    try:
        # Lê a planilha que o usuário enviou
        df_excel = pd.read_excel(arquivo_excel)
        st.sidebar.success(f"Planilha lida com sucesso! ({len(df_excel)} linhas)")
        
        # Botão para salvar no banco
        if st.sidebar.button("Salvar no Banco de Dados"):
            with st.spinner("Salvando dados no sistema..."):
                # Insere os dados da planilha na tabela do Supabase
                df_excel.to_sql('pagamentos_premios', con=engine, if_exists='append', index=False)
                st.sidebar.success("✅ Dados salvos com sucesso!")
                st.rerun() # Atualiza a página automaticamente
    except Exception as e:
        st.sidebar.error(f"Erro ao processar a planilha: {e}")

# 6. Exibição dos Dados na Tela Principal
df_banco = carregar_dados()

if df_banco.empty:
    st.info("💡 O banco de dados está conectado, mas a tabela está vazia. Por favor, use o menu lateral esquerdo para fazer o upload da planilha Excel.")
else:
    st.success(f"✅ Exibindo {len(df_banco)} registros do banco de dados.")
    st.dataframe(df_banco, use_container_width=True)
