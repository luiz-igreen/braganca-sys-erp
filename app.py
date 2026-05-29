import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, exc

# ==========================================
# 1. CONFIGURAÇÃO E ESTILO VISUAL PREMIUM
# ==========================================
st.set_page_config(page_title="Sistema de Prêmios - Construart", page_icon="🏆", layout="wide")

# CSS para o efeito Glassmorphism (Dark Navy Blue)
st.markdown("""
<style>
    .glass-container {
        background-color: rgba(15, 23, 42, 0.6);
        border-radius: 15px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE CONEXÃO GLOBAL
# ==========================================
@st.cache_resource
def iniciar_conexao():
    db_url = st.secrets["DATABASE_URL"]
    return create_engine(db_url)

engine = iniciar_conexao()

# ==========================================
# 3. ROTEADOR DO SISTEMA (MENU LATERAL)
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=60)
st.sidebar.markdown("## Construart Sys")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação de Módulos", 
    ["📊 Dashboard Principal", "👥 Gestão de Colaboradores", "📥 Importar Planilha"]
)
st.sidebar.markdown("---")

# ==========================================
# MÓDULO A: DASHBOARD PRINCIPAL
# ==========================================
if menu == "📊 Dashboard Principal":
    st.title("📊 Painel de Controle")
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    try:
        df_banco = pd.read_sql('pagamentos_premios', con=engine)
        total_colab = len(df_banco)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Total Colaboradores", f"{total_colab}")
        col2.metric("⏳ Prêmios Pendentes", "0")
        col3.metric("💰 Prêmios Pagos (Mês)", "R$ 0,00")
        col4.metric("⚠️ Alertas", "0")
        
        st.markdown("---")
        st.markdown("#### Últimos Registros Sincronizados")
        st.dataframe(df_banco.tail(5), use_container_width=True)
        
    except Exception as e:
        st.info("Nenhum dado encontrado no momento. Faça a importação da planilha.")
        
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# MÓDULO B: GESTÃO DE COLABORADORES
# ==========================================
elif menu == "👥 Gestão de Colaboradores":
    st.title("👥 Central de Colaboradores")
    
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    # Barra de Ferramentas Superior
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    with col1:
        termo_pesquisa = st.text_input("🔍 Pesquisar por Nome, REG ou Cargo:")
    with col2:
        st.write("") 
        btn_buscar = st.button("🔍 Buscar", use_container_width=True)
    with col3:
        st.write("")
        btn_novo = st.button("➕ Novo", type="primary", use_container_width=True)
    with col4:
        st.write("")
        btn_alterar = st.button("✏️ Alterar", use_container_width=True)
    with col5:
        st.write("")
        btn_excluir = st.button("🗑️ Excluir", use_container_width=True)
        
    st.markdown("---")
    
    # Grid de Exibição com Lógica de Pesquisa
    try:
        # Lê os dados do banco
        df_gestao = pd.read_sql('pagamentos_premios', con=engine)
        
        # Se o botão de buscar for clicado e houver algo digitado
        if btn_buscar and termo_pesquisa:
            # Converte tudo para string minúscula para facilitar a busca
            termo = termo_pesquisa.lower()
            mascara = (
                df_gestao['nome'].str.lower().str.contains(termo, na=False) |
                df_gestao['cargo'].str.lower().str.contains(termo, na=False) |
                df_gestao['id'].astype(str).str.contains(termo, na=False)
            )
            df_gestao = df_gestao[mascara]
            
            if len(df_gestao) > 0:
                st.success(f"✅ {len(df_gestao)} colaborador(es) encontrado(s)!")
            else:
                st.warning("⚠️ Nenhum colaborador encontrado com esse termo.")
        elif btn_buscar and not termo_pesquisa:
            st.info("💡 Digite algo na caixa de texto antes de buscar.")

        # Exibe a tabela (filtrada ou completa)
        st.dataframe(df_gestao, use_container_width=True, height=400)
        
    except Exception as e:
        st.warning(f"Erro ao carregar a lista de colaboradores: {e}")
        
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# MÓDULO C: IMPORTAÇÃO (INTOCÁVEL)
# ==========================================
elif menu == "📥 Importar Planilha":
    st.title("📥 Importação de Dados")
    
    if 'df_lido' not in st.session_state:
        st.session_state.df_lido = None

    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.write("Faça o upload do arquivo Excel com os dados dos colaboradores para alimentar a base central.")
    
    arquivo_excel = st.file_uploader("Selecione o arquivo Excel", type=['xlsx', 'xls'])
    
    if arquivo_excel is not None:
        try:
            df = pd.read_excel(arquivo_excel)
            
            primeira_coluna = df.columns[0]
            df.rename(columns={primeira_coluna: 'REG'}, inplace=True)
            
            if 'Nome.1' in df.columns:
                df.rename(columns={'Nome.1': 'Cargo'}, inplace=True)
            
            df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
            df = df.dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            
            st.session_state.df_lido = df
            st.success(f"✅ Planilha pronta! ({len(df)} colaboradores lidos)")
            
        except Exception as e:
            st.error(f"❌ Erro ao ler a planilha: {e}")
            
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.df_lido is not None:
        st.markdown("#### Pré-visualização dos Dados")
        st.dataframe(st.session_state.df_lido, use_container_width=True)
        
        salvar_btn = st.button("Gravar no Banco de Dados", type="primary")
        
        if salvar_btn:
            try:
                db_url = st.secrets["DATABASE_URL"]
                engine_temp = create_engine(db_url)
                
                df_banco = st.session_state.df_lido.copy()
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
                        con=engine_temp,
                        schema='public',
                        if_exists='append',
                        index=False
                    )
                st.success("✅ Tudo certo! Colaboradores salvos com sucesso no Supabase!")
                st.balloons()
            except exc.OperationalError as e:
                st.error("❌ Erro de conexão com o banco de dados.")
            except Exception as e:
                st.error(f"❌ Erro interno ao processar: {e}")
