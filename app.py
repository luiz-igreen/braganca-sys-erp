import streamlit as st

# --- CRÍTICO: CONFIGURAÇÃO DE PAGINAÇÃO DEVE SER O PRIMEIRO COMANDO ---
st.set_page_config(page_title="BRAGANÇA SYS - Gestão Corporativa", page_icon="🏗️", layout="wide")

import pandas as pd
from sqlalchemy import create_engine, text
import sqlalchemy.exc
import datetime
import io

# --- INICIALIZAÇÃO DE VARIÁVEIS DE SESSÃO PARA CONTROLE DE FLUXO ---
if 'id_alterar' not in st.session_state:
    st.session_state['id_alterar'] = None
if 'id_excluir' not in st.session_state:
    st.session_state['id_excluir'] = None

# --- CONFIGURAÇÃO DE DIRETRIZES VISUAIS (DARK PREMIUM GLASSMORPHISM) ---
st.markdown("""
<style>
    /* Fundo Navy Blue / Dark Gray Premium */
    .stApp { 
        background-color: #0f172a; 
        color: #f8fafc; 
        font-family: 'Inter', sans-serif; 
    }
    /* Efeito Glassmorphism para os Painéis e Cards */
    .panel-glass { 
        background: rgba(30, 41, 59, 0.45); 
        backdrop-filter: blur(16px); 
        -webkit-backdrop-filter: blur(16px); 
        padding: 30px; 
        border-radius: 16px; 
        border: 1px solid rgba(51, 65, 85, 0.7); 
        margin-bottom: 24px; 
    }
    .panel-danger { 
        background: rgba(220, 38, 38, 0.1); 
        backdrop-filter: blur(16px); 
        -webkit-backdrop-filter: blur(16px); 
        padding: 25px; 
        border-radius: 16px; 
        border: 1px solid rgba(220, 38, 38, 0.4); 
        margin-top: 30px; 
    }
    .card-metric { 
        background: rgba(15, 23, 42, 0.6); 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #334155; 
    }
    .metric-title { color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; font-weight: 600; }
    .metric-value { font-size: 2.25rem; font-weight: 800; color: #ffffff; margin-top: 5px; }
    
    /* Customização de Fichas de Consulta Isolada */
    .ficha-colaborador {
        background: rgba(15, 23, 42, 0.8);
        border-left: 5px solid #2563eb;
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .ficha-titulo { font-size: 1.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 15px; }
    .ficha-item { font-size: 0.95rem; color: #e2e8f0; margin-bottom: 8px; }
    .ficha-label { font-weight: 600; color: #94a3b8; }

    /* Customização Global de Botões */
    .stButton>button { 
        border-radius: 8px; 
        font-weight: 600; 
        padding: 10px 20px !important;
        transition: all 0.2s ease;
        width: 100%;
    }
    /* Botões Primários (Avançar/Salvar/Carregar) */
    button[data-testid="baseButton-primary"] {
        background-color: #2563eb !important;
        color: white !important;
        border: 1px solid #2563eb !important;
    }
    button[data-testid="baseButton-primary"]:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    /* Botões Secundários (Cancelar/Voltar) */
    button[data-testid="baseButton-secondary"] {
        background-color: #475569 !important;
        color: white !important;
        border: 1px solid #475569 !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #334155 !important;
        border-color: #334155 !important;
    }

    input, select, textarea { font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO DIRETA E BLINDADA COM O BANCO DE DADOS (SUPABASE) ---
engine = create_engine(st.secrets["DATABASE_URL"])

# --- INICIALIZAÇÃO DA INFRAESTRUTURA FÍSICA NO BANCO (DDL) ---
def inicializar_banco_de_dados():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cadastro_geral_colaborador (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                cpf TEXT,
                cargo TEXT,
                admissao DATE,
                demissao DATE,
                chave_pix TEXT
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS premios_funcionarios (
                id_sn SERIAL PRIMARY KEY,
                id_funcionario TEXT,
                competencia_mes_ano TEXT,
                salario_base NUMERIC,
                salario_hora NUMERIC
            );
        """))

inicializar_banco_de_dados()

# --- REGRAS DE NEGÓCIO E AUXILIARES ---
def validar_id_clt(id_texto):
    id_limpo = str(id_texto).split('.')[0].strip().lower()
    if id_limpo in ['1', '01', '001', '0001', '', 'nan', 'null', 'id', 'matricula', 'matrícula', 'código', 'codigo', 'num', 'número']:
        return False
    return True

def formatar_id_limpo(id_original):
    if pd.isna(id_original):
        return ""
    return str(id_original).split('.')[0].strip()

def limpar_cpf(cpf_bruto):
    if not cpf_bruto:
        return ""
    return ''.join(filter(str.isdigit, str(cpf_bruto)))

def sanitizar_texto(texto):
    if pd.isna(texto) or not str(texto).strip():
        return ""
    return str(texto).strip()

def converter_data_resiliente(val):
    if pd.isna(val):
        return None
    if isinstance(val, (datetime.date, datetime.datetime)):
        if hasattr(val, 'date'):
            return val.date()
        return val
    val_str = str(val).strip()
    if val_str.replace('.0','').isdigit():
        try:
            return pd.to_datetime(float(val_str), unit='D', origin='1899-12-30').date()
        except Exception:
            pass
    try:
        return pd.to_datetime(val_str).date()
    except Exception:
        return None

def obter_colaboradores_banco():
    try:
        return pd.read_sql("SELECT id, nome, cpf, cargo, admissao, demissao, chave_pix FROM cadastro_geral_colaborador ORDER BY admissao ASC", engine)
    except Exception:
        return pd.DataFrame(columns=['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao', 'chave_pix'])

# --- ROTEADOR DA SPA (MENU LATERAL) ---
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>BRAGANÇA SYS</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros"])

df_colab = obter_colaboradores_banco()

# =========================================================================
# 1. MENU: VISÃO GERAL
# =========================================================================
if menu == "👥 Visão Geral":
    st.markdown("<h2 style='margin-bottom: 20px;'>📊 Painel de Controle Corporativo</h2>", unsafe_allow_html=True)
    
    if df_colab.empty:
        st.info("💡 Nenhum colaborador encontrado no Supabase. Vá até a aba 'Importação Inteligente' para realizar a carga inicial.")
    else:
        total_funcionarios = len(df_colab)
        st.markdown(f'<div class="card-metric"><div class="metric-title">Total de Colaboradores Cadastrados no Banco</div><div class="metric-value">{total_funcionarios}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("📋 Listagem Completa de Registros Ativos")
        
        df_exibicao = df_colab.copy()
        df_exibicao.columns = ['ID / Matrícula', 'Nome Completo', 'CPF', 'Cargo', 'Data de Admissão', 'Data de Demissão', 'Chave PIX']
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 2. MENU: IMPORTAÇÃO INTELIGENTE
# =========================================================================
elif menu == "📥 Importação Inteligente":
    st.markdown("<h2>📥 Importação e Ingestão de Dados</h2>", unsafe_allow_html=True)
    st.markdown("Carregue a planilha exportada. O motor executará sincronizações resilientes via UPSERT.")
    
    if 'flash_sucesso' in st.session_state:
        st.success(st.session_state['flash_sucesso'])
        del st.session_state['flash_sucesso']
    if 'flash_aviso' in st.session_state:
        st.warning(st.session_state['flash_aviso'])
        del st.session_state['flash_aviso']
    if 'flash_erro' in st.session_state:
        st.error(st.session_state['flash_erro'])
        del st.session_state['flash_erro']
        
    arquivo_carregado = st.file_uploader("Selecione o arquivo de migração (.xlsx, .csv)", type=["xlsx", "csv"])
    
    if arquivo_carregado:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        if st.button("Executar Ingestão Certificada", type="primary"):
            with st.spinner("Sincronizando dados e validando integridade estrutural..."):
                
                conteudo_bytes = arquivo_carregado.read()
                nome_arquivo = arquivo_carregado.name.lower()
                df_bruto = None
                
                if nome_arquivo.endswith('.xlsx'):
                    try:
                        df_bruto = pd.read_excel(io.BytesIO(conteudo_bytes), sheet_name=0, engine='openpyxl')
                    except Exception as e:
                        st.session_state['flash_erro'] = f"❌ Erro ao ler arquivo XLSX: {str(e)}"
                        st.rerun()
                else:
                    codificacoes_prioritarias = ['utf-8-sig', 'utf-8', 'cp1252', 'latin1']
                    separadores_prioritarios = [';', ',', '\t']
                    
                    descoberto = False
                    for enc in codificacoes_prioritarias:
                        for sep in separadores_prioritarios:
                            try:
                                df_tentativa = pd.read_csv(io.BytesIO(conteudo_bytes), sep=sep, encoding=enc, on_bad_lines='skip')
                                if not df_tentativa.empty and len(df_tentativa.columns) > 1:
                                    cols_teste = "".join(str(c) for c in df_tentativa.columns).lower()
                                    termos_validos = ['id', 'matr', 'cod', 'nº', 'num', 'nome', 'colab', 'func', 'cargo', 'funç', 'cpf', 'pix', 'chave', 'adm']
                                    if any(term in cols_teste for term in termos_validos):
                                        df_bruto = df_tentativa
                                        descoberto = True
                                        break
                            except Exception:
                                continue
                        if descoberto:
                            break
                
                if df_bruto is None or df_bruto.empty:
                    st.session_state['flash_erro'] = "❌ Erro Crítico: Formato incompatível ou ausência de colunas reconhecíveis."
                    st.rerun()
                else:
                    cols = df_bruto.columns
                    
                    col_id = next((c for c in cols if any(x in str(c).lower() for x in ['id', 'matr', 'cod', 'nº', 'num'])), cols[0] if len(cols) > 0 else None)
                    col_nome = next((c for c in cols if any(x in str(c).lower() for x in ['nome', 'colab', 'func', 'empreg'])), cols[1] if len(cols) > 1 else None)
                    col_cpf = next((c for c in cols if 'cpf' in str(c).lower()), cols[2] if len(cols) > 2 else None)
                    col_cargo = next((c for c in cols if any(x in str(c).lower() for x in ['cargo', 'funç', 'ocupa'])), cols[3] if len(cols) > 3 else None)
                    col_adm = next((c for c in cols if any(x in str(c).lower() for x in ['adm', 'ingr', 'data'])), cols[4] if len(cols) > 4 else None)
                    col_dem = next((c for c in cols if any(x in str(c).lower() for x in ['dem', 'saida', 'deslig'])), cols[5] if len(cols) > 5 else None)
                    col_pix = next((c for c in cols if any(x in str(c).lower() for x in ['pix', 'chave'])), None)
                    
                    with engine.connect() as conn:
                        ids_existentes = set(str(r[0]).strip() for r in conn.execute(text("SELECT id FROM cadastro_geral_colaborador")).fetchall())
                    
                    novos_cadastros, atualizados_cadastros, linhas_invalidas = 0, 0, 0
                    ids_processados_nesta_execucao = set()
                    
                    try:
                        with engine.begin() as conn:
                            for _, row in df_bruto.iterrows():
                                val_id = row[col_id] if col_id is not None else None
                                id_func = formatar_id_limpo(val_id)
                                
                                if not id_func or not validar_id_clt(id_func):
                                    linhas_invalidas += 1
                                    continue
                                
                                if id_func in ids_existentes or id_func in ids_processados_nesta_execucao:
                                    atualizados_cadastros += 1
                                else:
                                    novos_cadastros += 1
                                
                                ids_processados_nesta_execucao.add(id_func)
                                
                                nome_func = sanitizar_texto(row[col_nome]) if col_nome is not None else "Sem Nome"
                                cpf_func = limpar_cpf(row[col_cpf]) if col_cpf is not None else ""
                                cargo_func = sanitizar_texto(row[col_cargo]) if col_cargo is not None else ""
                                dt_adm = converter_data_resiliente(row[col_adm]) if col_adm is not None else None
                                dt_dem = converter_data_resiliente(row[col_dem]) if col_dem is not None else None
                                pix_func = sanitizar_texto(row[col_pix]) if col_pix is not None else None
                                
                                conn.execute(
                                    text("""
                                        INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, chave_pix)
                                        VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :pix)
                                        ON CONFLICT (id) DO UPDATE SET
                                            nome = EXCLUDED.nome, cpf = EXCLUDED.cpf, cargo = EXCLUDED.cargo,
                                            admissao = EXCLUDED.admissao, demissao = EXCLUDED.demissao, chave_pix = EXCLUDED.chave_pix
                                    """),
                                    {
                                        "id": id_func, "nome": nome_func, "cpf": cpf_func, "cargo": cargo_func,
                                        "admissao": dt_adm, "demissao": dt_dem, "pix": pix_func
                                    }
                                )
                        
                        if novos_cadastros > 0 or atualizados_cadastros > 0:
                            st.session_state['flash_sucesso'] = f"🎉 Ingestão concluída com sucesso! {novos_cadastros} novos registros e {atualizados_cadastros} atualizados."
                        else:
                            st.session_state['flash_aviso'] = f"⚠️ O processamento não identificou novas linhas úteis."
                    except sqlalchemy.exc.IntegrityError:
                        st.session_state['flash_erro'] = "❌ Erro de Integridade Estrutural no banco."
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ZONA DE RESET TOTAL DO BANCO DE DADOS ---
    st.markdown("""<div class="panel-danger">""", unsafe_allow_html=True)
    st.subheader("⚠️ Zona de Reset Crítico do Sistema")
    confirmou_reset = st.checkbox("Confirmo que desejo esvaziar todo o banco de dados definitivamente.", key="chk_reset_total")
    if st.button("Zerar Todas as Tabelas do Banco", type="secondary"):
        if not confirmou_reset:
            st.error("❌ Operação Bloqueada: Você precisa marcar a caixa de seleção acima para autorizar esta ação.")
        else:
            with st.spinner("Limpando infraestrutura física..."):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("TRUNCATE TABLE premios_funcionarios RESTART IDENTITY;"))
                        conn.execute(text("TRUNCATE TABLE cadastro_geral_colaborador CASCADE;"))
                    st.session_state['flash_sucesso'] = "💥 Banco de dados limpo com sucesso!"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Falha ao resetar tabelas: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 3. MENU: GESTÃO DE CADASTROS (MOTORES CRUD DINÂMICOS)
# =========================================================================
elif menu == "🛠️ Gestão de Cadastros":
    st.markdown("<h2>🛠️ Painel Operacional de Cadastros (CRUD)</h2>", unsafe_allow_html=True)
    
    aba_consultar, aba_novo, aba_alterar, aba_excluir = st.tabs([
        "🔍 Consultar", 
        "➕ Novo Registro", 
        "✏️ Alterar Cadastro", 
        "❌ Excluir do Banco"
    ])
    
    # --- ABA: CONSULTAR ---
    with aba_consultar:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("🔍 Localizar Ficha de Registro")
        termo_busca = st.text_input("Busca por ID, Nome ou CPF:", key="busca_consulta").strip()
        
        if termo_busca:
            query_busca = text("""
                SELECT id, nome, cpf, cargo, admissao, demissao, chave_pix 
                FROM cadastro_geral_colaborador 
                WHERE id ILIKE :termo OR nome ILIKE :termo OR cpf ILIKE :termo
            """)
            with engine.connect() as conn:
                resultados = conn.execute(query_busca, {"termo": f"%{termo_busca}%"}).fetchall()
            
            if resultados:
                st.write(f"🎯 {len(resultados)} correspondência(s) encontrada(s):")
                for r in resultados:
                    st.markdown(f"""
                    <div class="ficha-colaborador">
                        <div class="ficha-titulo">👤 {r.nome}</div>
                        <div class="ficha-item"><span class="ficha-label">Matrícula / ID:</span> {r.id}</div>
                        <div class="ficha-item"><span class="ficha-label">CPF:</span> {r.cpf if r.cpf else 'Não Informado'}</div>
                        <div class="ficha-item"><span class="ficha-label">Cargo Atual:</span> {r.cargo if r.cargo else 'Não Mapeado'}</div>
                        <div class="ficha-item"><span class="ficha-label">Data de Admissão:</span> {r.admissao.strftime('%d/%m/%Y') if r.admissao else '-'}</div>
                        <div class="ficha-item"><span class="ficha-label">Data de Demissão:</span> {r.demissao.strftime('%d/%m/%Y') if r.demissao else 'Ativo'}</div>
                        <div class="ficha-item"><span class="ficha-label">Canal PIX:</span> {r.chave_pix if r.chave_pix else 'Não Cadastrada'}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Nenhum registro localizado.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # --- ABA: NOVO REGISTRO ---
    with aba_novo:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("➕ Inserir Novo Colaborador")
        with st.form("form_novo_registro", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_id = c1.text_input("ID / Número de Matrícula:")
            n_nome = c2.text_input("Nome Completo:")
            n_cpf = c1.text_input("CPF (Somente números):")
            n_cargo = c2.text_input("Cargo Ocupado:")
            n_adm = c1.date_input("Data de Admissão:", value=datetime.date.today())
            n_dem = c2.date_input("Data de Demissão (Opcional):", value=None, min_value=datetime.date(2000, 1, 1))
            n_pix = st.text_input("Chave PIX:")
            
            # Botões de Ação com Cancelar
            col_save, col_cancel = st.columns(2)
            btn_salvar = col_save.form_submit_button("Gravar Registro", type="primary")
            btn_cancelar = col_cancel.form_submit_button("Cancelar Operação", type="secondary")
            
            if btn_cancelar:
                st.rerun() # Limpa o formulário instantaneamente

            if btn_salvar:
                id_limpo = formatar_id_limpo(n_id)
                if not id_limpo or not n_nome:
                    st.error("❌ Os campos ID e Nome são obrigatórios.")
                elif not validar_id_clt(id_limpo):
                    st.error("❌ Erro: Formato de ID inválido.")
                else:
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, chave_pix)
                                    VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :pix)
                                    ON CONFLICT (id) DO UPDATE SET
                                        nome = EXCLUDED.nome, cpf = EXCLUDED.cpf, cargo = EXCLUDED.cargo,
                                        admissao = EXCLUDED.admissao, demissao = EXCLUDED.demissao, chave_pix = EXCLUDED.chave_pix
                                """),
                                {"id": id_limpo, "nome": n_nome.strip(), "cpf": limpar_cpf(n_cpf), "cargo": n_cargo.strip(), "admissao": n_adm, "demissao": n_dem, "pix": n_pix.strip()}
                            )
                        st.success("🎉 Colaborador gravado com sucesso!")
                    except Exception as e:
                        st.error(f"❌ Erro ao gravar: {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ABA: ALTERAR REGISTRO ---
    with aba_alterar:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("✏️ Alterar Dados do Colaborador")
        
        if df_colab.empty:
            st.warning("O banco de dados está vazio.")
        else:
            # ETAPA 1: Busca e Carregamento
            if st.session_state['id_alterar'] is None:
                lista_funcs = [f"{r['id']} - {r['nome']}" for _, r in df_colab.iterrows()]
                selecionado = st.selectbox("1. Digite para buscar o funcionário:", lista_funcs, key="sb_busca_alt")
                
                if st.button("Carregar Ficha para Edição", type="primary"):
                    st.session_state['id_alterar'] = selecionado.split(" - ")[0]
                    st.rerun()
            
            # ETAPA 2: Edição dos Dados Carregados
            else:
                id_alt = st.session_state['id_alterar']
                dados_atuais = df_colab[df_colab['id'] == id_alt].iloc[0]
                
                st.info(f"Modificando a ficha da Matrícula: **{id_alt}**")
                
                with st.form("form_alterar_registro"):
                    a_nome = st.text_input("Nome Completo:", value=str(dados_atuais['nome']))
                    a_cpf = st.text_input("CPF:", value=str(dados_atuais['cpf'] if dados_atuais['cpf'] else ''))
                    a_cargo = st.text_input("Cargo Ocupado:", value=str(dados_atuais['cargo'] if dados_atuais['cargo'] else ''))
                    
                    val_adm = dados_atuais['admissao']
                    val_adm = datetime.datetime.strptime(val_adm, '%Y-%m-%d').date() if isinstance(val_adm, str) else (val_adm if pd.notna(val_adm) else datetime.date.today())
                    
                    val_dem = dados_atuais['demissao']
                    val_dem = datetime.datetime.strptime(val_dem, '%Y-%m-%d').date() if isinstance(val_dem, str) else (val_dem if pd.notna(val_dem) else None)
                    
                    a_adm = st.date_input("Data de Admissão:", value=val_adm)
                    a_dem = st.date_input("Data de Demissão:", value=val_dem)
                    a_pix = st.text_input("Chave PIX:", value=str(dados_atuais['chave_pix'] if dados_atuais['chave_pix'] else ''))
                    
                    # Botões Lado a Lado
                    col_save, col_cancel = st.columns(2)
                    btn_atualizar = col_save.form_submit_button("Salvar Alterações", type="primary")
                    btn_cancelar = col_cancel.form_submit_button("Cancelar e Voltar", type="secondary")
                    
                    if btn_cancelar:
                        st.session_state['id_alterar'] = None
                        st.rerun()
                        
                    if btn_atualizar:
                        if not a_nome.strip():
                            st.error("O Nome não pode ficar em branco.")
                        else:
                            with engine.begin() as conn:
                                conn.execute(
                                    text("""UPDATE cadastro_geral_colaborador SET nome = :nome, cpf = :cpf, cargo = :cargo, admissao = :admissao, demissao = :demissao, chave_pix = :pix WHERE id = :id"""),
                                    {"nome": a_nome.strip(), "cpf": limpar_cpf(a_cpf), "cargo": a_cargo.strip(), "admissao": a_adm, "demissao": a_dem, "pix": a_pix.strip(), "id": id_alt}
                                )
                            st.success("🎉 Alterações salvas com sucesso!")
                            st.session_state['id_alterar'] = None # Volta pro estado inicial limpo
                            # Refresh manual ou instruir usuário
                            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ABA: EXCLUIR REGISTRO ---
    with aba_excluir:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("❌ Remover Colaborador")
        
        if df_colab.empty:
            st.warning("O banco de dados está vazio.")
        else:
            # ETAPA 1: Busca e Carregamento para Exclusão
            if st.session_state['id_excluir'] is None:
                lista_funcs_del = [f"{r['id']} - {r['nome']}" for _, r in df_colab.iterrows()]
                selecionado_del = st.selectbox("1. Digite para buscar o funcionário:", lista_funcs_del, key="sb_busca_del")
                
                if st.button("Analisar Exclusão", type="primary"):
                    st.session_state['id_excluir'] = selecionado_del.split(" - ")[0]
                    st.rerun()
                    
            # ETAPA 2: Confirmação e Cancelamento
            else:
                id_del = st.session_state['id_excluir']
                nome_del = df_colab[df_colab['id'] == id_del].iloc[0]['nome']
                
                st.error(f"⚠️ Atenção: Você está prestes a apagar **{nome_del}** (Matrícula: {id_del}) do sistema.")
                
                with st.form("form_exclusao"):
                    trava_seguranca = st.checkbox("Sim, confirmo que desejo apagar os dados deste colaborador.")
                    
                    col_del, col_cancel = st.columns(2)
                    btn_del = col_del.form_submit_button("Remover Definitivamente", type="primary")
                    btn_cancelar = col_cancel.form_submit_button("Cancelar e Voltar", type="secondary")
                    
                    if btn_cancelar:
                        st.session_state['id_excluir'] = None
                        st.rerun()
                        
                    if btn_del:
                        if not trava_seguranca:
                            st.error("❌ Operação Rejeitada: Marque a caixa de confirmação para prosseguir.")
                        else:
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM premios_funcionarios WHERE id_funcionario = :id"), {"id": id_del})
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_del})
                            st.success(f"💥 Colaborador removido com sucesso.")
                            st.session_state['id_excluir'] = None # Volta pro estado inicial limpo
                            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
