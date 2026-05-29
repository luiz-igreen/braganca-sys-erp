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

# 3. INICIALIZAÇÃO DE VARIÁVEIS
if 'df_lido' not in st.session_state:
    st.session_state.df_lido = None

# 4. MENU LATERAL E IMPORTAÇÃO
with st.sidebar:
    st.markdown("### 📥 Importar Planilha")
    st.write("Faça o upload do arquivo Excel com os dados dos colaboradores.")
    arquivo_excel = st.file_uploader("Selecione o arquivo Excel", type=['xlsx', 'xls'])
    
    if arquivo_excel is not None:
        try:
            # Leitura bruta do Excel
            df = pd.read_excel(arquivo_excel)
            
            # --- LIMPEZA E FORMATAÇÃO ---
            primeira_coluna = df.columns[0]
            df.rename(columns={primeira_coluna: 'REG'}, inplace=True)
            
            if 'Nome.1' in df.columns:
                df.rename(columns={'Nome.1': 'Cargo'}, inplace=True)
            
            df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
            df = df.dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            # --- FIM DA LIMPEZA ---
            
            st.session_state.df_lido = df
            st.success(f"✅ Planilha pronta! ({len(df)} colaboradores)")
            
        except Exception as e:
            st.error(f"❌ Erro ao ler a planilha: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    salvar_btn = st.button("Salvar no Banco de Dados", type="primary")

# 5. ÁREA PRINCIPAL DA INTERFACE
if st.session_state.df_lido is None:
    st.info("💡 Bem-vindo ao novo sistema. Faça o upload da planilha no menu lateral para começar a importação.")
else:
    st.markdown("#### Pré-visualização dos Dados (Validação)")
    st.dataframe(st.session_state.df_lido, use_container_width=True)

# 6. CONEXÃO COM O BANCO DE DADOS (FERRAMENTA)
if salvar_btn:
    if st.session_state.df_lido is not None:
        try:
            db_url = st.secrets["DATABASE_URL"]
            engine = create_engine(db_url)
            
            # --- O GRANDE TRUQUE: TRADUÇÃO DE COLUNAS ---
            # Cria uma cópia isolada para enviar ao banco sem mudar a tela do usuário
            df_banco = st.session_state.df_lido.copy()
            
            # Traduz os nomes do Excel para os nomes exatos do Supabase
            df_banco.rename(columns={
                'REG': 'id',
                'Nome': 'nome',
                'Cargo': 'cargo',
                'Admissão': 'data_admissao',
                'Demissão': 'data_demissao'
            }, inplace=True)
            
            with st.spinner("Conectando ao banco e enviando colaboradores..."):
                df_banco.to_sql(
                    'pagamentos_premios',
                    con=engine,
                    schema='public',
                    if_exists='append',
                    index=False
                )
            
            st.success("✅ Tudo certo! Colaboradores salvos com sucesso no Supabase!")
            st.balloons()
            
        except exc.OperationalError as e:
            st.error("❌ Erro de conexão: O banco de dados recusou a senha ou o endereço.")
        except Exception as e:
            st.error(f"❌ Erro interno ao processar: {e}")
    else:
        st.warning("⚠️ Importe a planilha de colaboradores primeiro.")    
