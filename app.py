import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, exc

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Sistema de Prêmios - Construart", 
    page_icon="🏆", 
    layout="wide"
)

# 2. TÍTULO PRINCIPAL
st.title("🏆 Sistema de Prêmios - Construart")
st.markdown("---")

# 3. INICIALIZAÇÃO DE VARIÁVEIS DE ESTADO
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
            # Lê o Excel
            df = pd.read_excel(arquivo_excel)
            
            # --- INÍCIO DA LIMPEZA E FORMATAÇÃO DE DADOS ---
            # 1. Renomeia a primeira coluna para 'ORD'
            primeira_coluna = df.columns[0]
            df.rename(columns={primeira_coluna: 'ORD'}, inplace=True)
            
            # 2. Renomeia a coluna 'Nome.1' para 'Cargo'
            if 'Nome.1' in df.columns:
                df.rename(columns={'Nome.1': 'Cargo'}, inplace=True)
            
            # 3. Remove outras colunas indesejadas (blindado contra float)
            df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
            
            # 4. Remove colunas que estejam 100% vazias
            df = df.dropna(axis=1, how='all')
            # --- FIM DA LIMPEZA DE DADOS ---
            
            # Guarda na sessão
            st.session_state.df_lido = df
            st.success(f"✅ Planilha lida e formatada com sucesso! ({len(df)} linhas)")
        except Exception as e:
            st.error(f"❌ Erro ao ler a planilha: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botão de ação principal
    salvar_btn = st.button("Salvar no Banco de Dados", type="primary")

# 5. ÁREA PRINCIPAL DA INTERFACE
if st.session_state.df_lido is None:
    st.info("💡 O banco de dados está conectado, mas a tabela está vazia. Por favor, use o menu lateral esquerdo para fazer o upload da planilha Excel.")
else:
    st.markdown("#### Pré-visualização dos Dados Prontos para Envio")
    st.dataframe(st.session_state.df_lido, use_container_width=True)

# 6. LÓGICA DE GRAVAÇÃO NO SUPABASE
if salvar_btn:
    if st.session_state.df_lido is not None:
        try:
            # Puxa a URL única configurada nas Secrets
            db_url = st.secrets["DATABASE_URL"]
            engine = create_engine(db_url)
            
            with st.spinner("Salvando dados no Supabase... Aguarde."):
                # Envia os dados limpos para a tabela pagamentos_premios
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
        except Exception as e:
            st.error(f"❌ Erro ao processar a planilha: {e}")
    else:
        st.warning("⚠️ Por favor, faça o upload da planilha Excel antes de tentar salvar no banco de dados.")
