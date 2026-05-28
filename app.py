import sqlalchemy

# Criamos a conexão
conn = st.connection("postgresql", type="sql")

# Função segura para ler dados
def carregar_dados_seguro():
    try:
        # Tenta ler a tabela
        return conn.query("SELECT * FROM public.pagamentos_premios;", ttl="0")
    except Exception:
        # Se a tabela não existir ou der erro, retorna um DataFrame vazio em vez de travar
        return pd.DataFrame()

# Chamada da função
df_visualizacao = carregar_dados_seguro()

if df_visualizacao.empty:
    st.info("💡 O banco de dados está pronto, mas a tabela está vazia. Por favor, faça a importação da planilha abaixo para começar.")
else:
    st.write(f"Exibindo {len(df_visualizacao)} colaboradores.")
    st.dataframe(df_visualizacao)
