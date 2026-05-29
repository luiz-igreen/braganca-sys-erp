import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, exc

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Sistema de Prêmios - Construart", 
    page_icon="🏆", 
    layout="wide"
)

# 2. TÍTULO PRINCIPAL
st.title("🏆 Sistema de Prêmios - Construart")
st.markdown("---")

# 3. INICIALIZAÇÃO DE VARIÁVEIS DE ESTADO (Para manter o arquivo na memória)
if 'df_lido' not in st.session_state:
    st.session_state.df_lido = None

# 4. CONSTRUÇÃO DO MENU LATERAL (Sidebar)
with st.sidebar:
    st.markdown("### 📥 Importar Planilha")
    st.write("Faça o upload do arquivo Excel com os dados dos colaboradores.")
    arquivo_excel = st.file_uploader("Selecione o arquivo Excel", type=['xlsx', 'xls'])
    
    # Processamento imediato do upload
    if arquivo_excel is not None:
        try:
            # Lê o Excel e guarda na sessão
            df = pd.read_excel(arquivo_excel)
            st.session_state.df_lido = df
            st.success(f"✅ Planilha lida com sucesso! ({len(df)} linhas)")
        except Exception as e:
            st.error(f"❌ Erro ao ler a planilha: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botão de ação principal
    salvar_btn = st.button("Salvar no Banco de Dados", type="primary")

# 5. ÁREA PRINCIPAL DA INTERFACE
if st.session_state.df_lido is None:
    # Mensagem de alerta padrão quando não há arquivo
    st.info("💡 O banco de dados está conectado, mas a tabela está vazia. Por favor, use o menu lateral esquerdo para fazer o upload da planilha Excel.")
else:
    # Mostra um preview dos dados lidos
    st.markdown("#### Pré-visualização dos Dados")
    st.dataframe(st.session_state.df_lido, use_container_width=True)

# 6. LÓGICA DE GRAVAÇÃO NO SUPABASE
if salvar_btn:
    if st.session_state.df_lido is not None:
        try:
            # Conecta usando a Secret exata que configuramos no painel
            db_url = st.secrets["DATABASE_URL"]
            engine = create_engine(db_url)
            
            with st.spinner("Salvando dados no Supabase... Aguarde."):
                # IMPORTANTE: Nome correto da tabela é 'pagamentos_premios' no schema 'public'
                # if_exists='append' garante que os dados sejam adicionados sem apagar os existentes
                st.session_state.df_lido.to_sql(
                    'pagamentos_premios',
                    con=engine,
                    schema='public',
                    if_exists='append',
                    index=False
                )
            
            st.success("✅ Dados salvos com sucesso no banco de dados!")
            st.balloons()
            
        except exc.OperationalError as e:
            st.error(f"❌ Erro de conexão com o servidor: {e}")
            st.info("💡 Verifique se a DATABASE_URL nas Secrets está correta")
        except Exception as e:
            st.error(f"❌ Erro ao processar a planilha: {e}")
    else:
        st.warning("⚠️ Por favor, faça o upload da planilha Excel antes de tentar salvar no banco de dados.")
