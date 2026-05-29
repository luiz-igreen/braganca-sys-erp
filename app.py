import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text, exc
import plotly.express as px
import datetime

# ==========================================
# 1. CONFIGURAÇÃO E ESTILO VISUAL PREMIUM
# ==========================================
st.set_page_config(page_title="Sistema de Prêmios - Construart", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    .glass-container {
        background-color: rgba(15, 23, 42, 0.7);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: rgba(30, 41, 59, 0.8);
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #ffffff; }
    .metric-label { font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
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
# 3. VARIÁVEIS DE ESTADO (MEMÓRIA DO SISTEMA)
# ==========================================
if 'gestao_modo' not in st.session_state:
    st.session_state.gestao_modo = 'pesquisa' # Pode ser: pesquisa, novo, editar
if 'gestao_resultados' not in st.session_state:
    st.session_state.gestao_resultados = None
if 'colab_edit_id' not in st.session_state:
    st.session_state.colab_edit_id = None

# ==========================================
# 4. ROTEADOR DO SISTEMA (MENU LATERAL)
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
# MÓDULO A: DASHBOARD PRINCIPAL PROFISSIONAL
# ==========================================
if menu == "📊 Dashboard Principal":
    st.title("📊 Painel de Controle - Visão Geral")
    
    try:
        df_banco = pd.read_sql('pagamentos_premios', con=engine)
        total_colab = len(df_banco)
        
        # Criação dos Cartões de Métricas Estilizados
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">👥 Total Colaboradores</div><div class="metric-value">{total_colab}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card" style="border-left-color: #f59e0b;"><div class="metric-label">⏳ Prêmios Pendentes</div><div class="metric-value">0</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card" style="border-left-color: #10b981;"><div class="metric-label">💰 Valor Pago (Mês)</div><div class="metric-value">R$ 0,00</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card" style="border-left-color: #ef4444;"><div class="metric-label">⚠️ Desligamentos</div><div class="metric-value">{df_banco["data_demissao"].notna().sum() if "data_demissao" in df_banco.columns else 0}</div></div>', unsafe_allow_html=True)
        
        st.write("<br>", unsafe_allow_html=True)
        
        # Área de Gráficos Profissionais
        col_grafico, col_tabela = st.columns([6, 4])
        
        with col_grafico:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.markdown("#### Distribuição por Cargo (Top 5)")
            if not df_banco.empty:
                cargo_counts = df_banco['cargo'].value_counts().head(5).reset_index()
                cargo_counts.columns = ['Cargo', 'Quantidade']
                fig = px.bar(cargo_counts, x='Quantidade', y='Cargo', orientation='h', 
                             color='Quantidade', color_continuous_scale='Blues',
                             template='plotly_dark')
                fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados suficientes para o gráfico.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_tabela:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.markdown("#### Últimos Registros")
            if not df_banco.empty:
                st.dataframe(df_banco[['id', 'nome', 'cargo']].tail(8), use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum registro encontrado.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erro ao carregar o Dashboard: {e}")

# ==========================================
# MÓDULO B: GESTÃO DE COLABORADORES (CRUD COMPLETO)
# ==========================================
elif menu == "👥 Gestão de Colaboradores":
    st.title("👥 Central de Colaboradores")
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # TELA DE PESQUISA (PADRÃO)
    # ---------------------------------------------------------
    if st.session_state.gestao_modo == 'pesquisa':
        col_busca, col_btn_busca, col_btn_novo = st.columns([6, 2, 2])
        
        with col_busca:
            termo = st.text_input("🔍 Buscar por REG (ID) ou Nome do colaborador:", placeholder="Ex: 168 ou Maria...")
        with col_btn_busca:
            st.write("")
            btn_buscar = st.button("🔍 Pesquisar", use_container_width=True)
        with col_btn_novo:
            st.write("")
            if st.button("➕ Novo Colaborador", type="primary", use_container_width=True):
                st.session_state.gestao_modo = 'novo'
                st.rerun()

        st.markdown("---")

        # Lógica de Pesquisa
        if btn_buscar and termo:
            try:
                # Usa query parametrizada para segurança e exatidão
                query = text("""
                    SELECT * FROM pagamentos_premios 
                    WHERE id::text = :termo OR nome ILIKE :termo_like
                """)
                df_res = pd.read_sql(query, con=engine, params={"termo": termo, "termo_like": f"%{termo}%"})
                st.session_state.gestao_resultados = df_res
            except Exception as e:
                st.error(f"Erro na pesquisa: {e}")

        # Exibe Resultados e Ações (Se houver)
        if st.session_state.gestao_resultados is not None:
            df_res = st.session_state.gestao_resultados
            
            if df_res.empty:
                st.warning("⚠️ Nenhum colaborador encontrado com esta pesquisa.")
            else:
                st.success(f"✅ {len(df_res)} colaborador(es) encontrado(s).")
                st.dataframe(df_res, use_container_width=True, hide_index=True)
                
                # Seleção Específica para Alterar/Excluir
                st.markdown("#### Ações para o Colaborador")
                opcoes = df_res['id'].astype(str) + " - " + df_res['nome']
                colab_selecionado = st.selectbox("Selecione qual colaborador deseja gerenciar:", opcoes)
                
                # Extrai o ID do colaborador selecionado na caixa
                id_selecionado = int(colab_selecionado.split(" - ")[0])
                
                col_alt, col_exc, col_vazio = st.columns([2, 2, 6])
                with col_alt:
                    if st.button("✏️ Alterar Selecionado", use_container_width=True):
                        st.session_state.colab_edit_id = id_selecionado
                        st.session_state.gestao_modo = 'editar'
                        st.rerun()
                with col_exc:
                    if st.button("🗑️ Excluir Selecionado", use_container_width=True):
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM pagamentos_premios WHERE id = :id"), {"id": id_selecionado})
                            st.success("🗑️ Colaborador excluído com sucesso!")
                            st.session_state.gestao_resultados = None # Limpa a tela
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")

    # ---------------------------------------------------------
    # TELA DE NOVO COLABORADOR
    # ---------------------------------------------------------
    elif st.session_state.gestao_modo == 'novo':
        st.subheader("➕ Inserir Novo Colaborador")
        
        with st.form("form_novo_colab"):
            col1, col2 = st.columns(2)
            with col1:
                novo_reg = st.number_input("REG (ID)*", min_value=1, step=1)
                novo_nome = st.text_input("Nome Completo*")
            with col2:
                novo_cargo = st.text_input("Cargo*")
                nova_adm = st.date_input("Data de Admissão", value=None)
                
            st.markdown("*Campos obrigatórios")
            
            col_salvar, col_cancelar = st.columns([2, 2])
            with col_salvar:
                submit_novo = st.form_submit_button("💾 Salvar Colaborador", use_container_width=True)
            with col_cancelar:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.gestao_modo = 'pesquisa'
                    st.rerun()

        if submit_novo:
            if not novo_nome or not novo_cargo:
                st.error("Preencha o Nome e o Cargo!")
            else:
                try:
                    with engine.begin() as conn:
                        query = text("INSERT INTO pagamentos_premios (id, nome, cargo, data_admissao) VALUES (:id, :nome, :cargo, :adm)")
                        conn.execute(query, {"id": novo_reg, "nome": novo_nome.upper(), "cargo": novo_cargo.upper(), "adm": nova_adm})
                    st.success("✅ Colaborador cadastrado com sucesso!")
                    st.session_state.gestao_modo = 'pesquisa'
                    st.session_state.gestao_resultados = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # ---------------------------------------------------------
    # TELA DE ALTERAR COLABORADOR
    # ---------------------------------------------------------
    elif st.session_state.gestao_modo == 'editar':
        st.subheader(f"✏️ Editando Colaborador REG: {st.session_state.colab_edit_id}")
        
        # Puxa os dados atuais do banco para preencher o formulário
        df_atual = pd.read_sql(text("SELECT * FROM pagamentos_premios WHERE id = :id"), con=engine, params={"id": st.session_state.colab_edit_id})
        
        if not df_atual.empty:
            dados = df_atual.iloc[0]
            
            with st.form("form_edit_colab"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_nome = st.text_input("Nome Completo", value=dados['nome'])
                    edit_cargo = st.text_input("Cargo", value=dados['cargo'] if pd.notna(dados['cargo']) else "")
                with col2:
                    # Tratamento seguro para as datas vindas do banco
                    val_adm = dados['data_admissao'] if pd.notna(dados['data_admissao']) else None
                    val_dem = dados['data_demissao'] if 'data_demissao' in dados and pd.notna(dados['data_demissao']) else None
                    
                    edit_adm = st.date_input("Data de Admissão", value=val_adm)
                    edit_dem = st.date_input("Data de Demissão (Deixe em branco se ativo)", value=val_dem)

                col_salvar, col_cancelar = st.columns([2, 2])
                with col_salvar:
                    submit_edit = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with col_cancelar:
                    if st.form_submit_button("❌ Cancelar", use_container_width=True):
                        st.session_state.gestao_modo = 'pesquisa'
                        st.rerun()
            
            if submit_edit:
                try:
                    with engine.begin() as conn:
                        query = text("UPDATE pagamentos_premios SET nome=:nome, cargo=:cargo, data_admissao=:adm, data_demissao=:dem WHERE id=:id")
                        conn.execute(query, {
                            "nome": edit_nome.upper(), 
                            "cargo": edit_cargo.upper(), 
                            "adm": edit_adm, 
                            "dem": edit_dem, 
                            "id": st.session_state.colab_edit_id
                        })
                    st.success("✅ Dados alterados com sucesso!")
                    st.session_state.gestao_modo = 'pesquisa'
                    st.session_state.gestao_resultados = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        else:
            st.error("Erro: Dados do colaborador não encontrados.")
            if st.button("Voltar"):
                st.session_state.gestao_modo = 'pesquisa'
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# MÓDULO C: IMPORTAÇÃO (INTOCÁVEL - 100% PRESERVADO)
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
                df_banco.rename(columns={'REG': 'id', 'Nome': 'nome', 'Cargo': 'cargo', 'Admissão': 'data_admissao', 'Demissão': 'data_demissao'}, inplace=True)
                with st.spinner("Conectando ao banco e enviando colaboradores..."):
                    df_banco.to_sql('pagamentos_premios', con=engine_temp, schema='public', if_exists='append', index=False)
                st.success("✅ Tudo certo! Colaboradores salvos com sucesso no Supabase!")
                st.balloons()
            except exc.OperationalError as e:
                st.error("❌ Erro de conexão com o banco de dados.")
            except Exception as e:
                st.error(f"❌ Erro interno ao processar: {e}")
