import streamlit as st

# --- CRÍTICO: CONFIGURAÇÃO DE PAGINAÇÃO DEVE SER O PRIMEIRO COMANDO ---
st.set_page_config(page_title="BRAGANÇA SYS - Gestão Corporativa", page_icon="🏗️", layout="wide")

import pandas as pd
from sqlalchemy import create_engine, text
import datetime
import io

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

    /* Customização de Inputs e Botões */
    .stButton>button { 
        border-radius: 8px; 
        font-weight: 600; 
        background-color: #2563eb !important; 
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        transition: background-color 0.15s ease;
    }
    .stButton>button:hover { background-color: #1d4ed8 !important; }
    
    div[data-testid="stForm"] .stButton>button[type="submit"] {
        width: 100%;
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
    # Ignora lixo eletrônico, títulos repetidos ou IDs padrão do sistema
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
# 2. MENU: IMPORTAÇÃO INTELIGENTE (SISTEMA DE MAPEAMENTO DINÂMICO E POSICIONAL)
# =========================================================================
elif menu == "📥 Importação Inteligente":
    st.markdown("<h2>📥 Importação e Ingestão de Dados</h2>", unsafe_allow_html=True)
    st.markdown("Carregue a planilha exportada. O motor executará varreduras tolerantes a falhas estruturais ou linhas malformadas.")
    
    # --- SISTEMA DE FEEDBACK SEGURO ---
    if 'flash_sucesso' in st.session_state:
        st.success(st.session_state['flash_sucesso'])
        del st.session_state['flash_sucesso']
    if 'flash_aviso' in st.session_state:
        st.warning(st.session_state['flash_aviso'])
        del st.session_state['flash_aviso']
    if 'flash_erro' in st.session_state:
        st.error(st.session_state['flash_erro'])
        del st.session_state['flash_erro']
        
    arquivo_carregado = st.file_uploader("Selecione o arquivo de migração (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])
    
    if arquivo_carregado:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        if st.button("Executar Ingestão Certificada", type="primary"):
            with st.spinner("Mapeando colunas e cruzando dados com o Supabase..."):
                
                conteudo_bytes = arquivo_carregado.read()
                nome_arquivo = arquivo_carregado.name.lower()
                df_bruto = None
                
                # Camada 1: Excel Moderno
                if nome_arquivo.endswith('.xlsx'):
                    try:
                        df_bruto = pd.read_excel(io.BytesIO(conteudo_bytes), sheet_name=0, engine='openpyxl')
                    except Exception:
                        pass
                
                # Camada 2: Excel Antigo
                if (df_bruto is None or df_bruto.empty) and nome_arquivo.endswith('.xls'):
                    try:
                        df_bruto = pd.read_excel(io.BytesIO(conteudo_bytes), sheet_name=0, engine='xlrd')
                    except Exception:
                        pass
                
                # Camada 3: CSV Dinâmico
                if df_bruto is None or df_bruto.empty:
                    for caractere_separador in [';', ',', '\t']:
                        for codificacao_texto in ['utf-8', 'latin1', 'iso-8859-1']:
                            try:
                                df_tentativa = pd.read_csv(
                                    io.BytesIO(conteudo_bytes), 
                                    sep=caractere_separador, 
                                    encoding=codificacao_texto,
                                    on_bad_lines='skip'
                                )
                                if not df_tentativa.empty and len(df_tentativa.columns) > 1:
                                    df_bruto = df_tentativa
                                    break
                            except Exception:
                                continue
                        if df_bruto is not None and not df_bruto.empty:
                            break
                
                # Processamento com Mapeamento Tolerante
                if df_bruto is None or df_bruto.empty:
                    st.session_state['flash_erro'] = "❌ Erro Crítico: Não foi possível estruturar o arquivo enviado."
                    st.rerun()
                else:
                    # --- ALGORITMO DE MAPEAMENTO POR SINÔNIMOS OU FALLBACK POSICIONAL ---
                    cols = df_bruto.columns
                    
                    # Procura coluna de ID por sinônimo, senão adota a 1ª coluna (Índice 0)
                    col_id = next((c for c in cols if any(x in str(c).lower() for x in ['id', 'matr', 'cod', 'nº', 'num'])), cols[0] if len(cols) > 0 else None)
                    
                    # Procura coluna de Nome por sinônimo, senão adota a 2ª coluna (Índice 1)
                    col_nome = next((c for c in cols if any(x in str(c).lower() for x in ['nome', 'colab', 'func', 'empreg'])), cols[1] if len(cols) > 1 else None)
                    
                    # Procura coluna de CPF, senão adota a 3ª coluna (Índice 2)
                    col_cpf = next((c for c in cols if 'cpf' in str(c).lower()), cols[2] if len(cols) > 2 else None)
                    
                    # Procura coluna de Cargo, senão adota a 4ª coluna (Índice 3)
                    col_cargo = next((c for c in cols if any(x in str(c).lower() for x in ['cargo', 'funç', 'ocupa'])), cols[3] if len(cols) > 3 else None)
                    
                    # Procura coluna de Admissão, senão adota a 5ª coluna (Índice 4)
                    col_adm = next((c for c in cols if any(x in str(c).lower() for x in ['adm', 'ingr', 'data'])), cols[4] if len(cols) > 4 else None)
                    
                    # Procura coluna de Demissão, senão adota a 6ª coluna (Índice 5)
                    col_dem = next((c for c in cols if any(x in str(c).lower() for x in ['dem', 'saida', 'deslig'])), cols[5] if len(cols) > 5 else None)
                    
                    # Canal PIX opcional
                    col_pix = next((c for c in cols if any(x in str(c).lower() for x in ['pix', 'chave'])), None)
                    
                    # CARGA INICIAL DE VALIDAÇÃO EM LOTE
                    with engine.connect() as conn:
                        ids_existentes = set(str(r[0]).strip() for r in conn.execute(text("SELECT id FROM cadastro_geral_colaborador")).fetchall())
                    
                    novos_cadastros = 0
                    ja_existentes = 0
                    linhas_invalidas = 0
                    
                    with engine.begin() as conn:
                        for _, row in df_bruto.iterrows():
                            val_id = row[col_id] if col_id is not None else None
                            id_func = formatar_id_limpo(val_id)
                            
                            # Validação rigorosa do ID extraído da coluna mapeada
                            if not id_func or not validar_id_clt(id_func):
                                linhas_invalidas += 1
                                continue
                            
                            if id_func in ids_existentes:
                                ja_existentes += 1
                                continue
                            
                            # Coleta resiliente de metadados
                            nome_func = str(row[col_nome]).strip() if col_nome is not None and pd.notna(row[col_nome]) else "Colaborador Sem Nome"
                            cpf_func = limpar_cpf(row[col_cpf]) if col_cpf is not None else ""
                            cargo_func = str(row[col_cargo]).strip() if col_cargo is not None and pd.notna(row[col_cargo]) else ""
                            
                            dt_adm = converter_data_resiliente(row[col_adm]) if col_adm is not None else None
                            dt_dem = converter_data_resiliente(row[col_dem]) if col_dem is not None else None
                            
                            pix_func = str(row[col_pix]).strip() if col_pix is not None and pd.notna(row[col_pix]) else None
                            
                            conn.execute(
                                text("""
                                    INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, chave_pix)
                                    VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :pix)
                                """),
                                {
                                    "id": id_func, "nome": nome_func, "cpf": cpf_func, "cargo": cargo_func,
                                    "admissao": dt_adm, "demissao": dt_dem, "pix": pix_func
                                }
                            )
                            novos_cadastros += 1
                    
                    # --- CRITÉRIOS DE FEEDBACK DE AUDITORIA ---
                    if novos_cadastros > 0:
                        st.session_state['flash_sucesso'] = f"🎉 Sucesso! {novos_cadastros} novos colaboradores foram integrados ao Supabase. (Já mapeados anteriormente: {ja_existentes} | Linhas vazias ou cabeçalhos filtrados: {linhas_invalidas})"
                    elif ja_existentes > 0:
                        st.session_state['flash_aviso'] = f"⚠️ Ingestão Concluída: Nenhum registro novo foi adicionado porque todos os {ja_existentes} colaboradores localizados no arquivo já constam na base do Supabase."
                    else:
                        st.session_state['flash_erro'] = f"❌ Erro de Leitura: Não foi possível extrair dados válidos. O sistema analisou o arquivo e processou {linhas_invalidas} linhas como inválidas ou cabeçalhos de texto. Verifique o conteúdo interno da tabela."
                    
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 3. MENU: GESTÃO DE CADASTROS (MOTORES CRUD DINÂMICOS)
# =========================================================================
elif menu == "🛠️ Gestão de Cadastros":
    st.markdown("<h2>🛠️ Painel Operacional de Cadastros (CRUD)</h2>", unsafe_allow_html=True)
    
    aba_consultar, aba_novo, aba_alterar, aba_excluir = st.tabs([
        "🔍 Consultar Colaborador", 
        "➕ Novo Registro", 
        "✏️ Alterar Cadastro", 
        "❌ Excluir do Banco"
    ])
    
    # --- CONSULTAR ---
    with aba_consultar:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("🔍 Localizar Ficha Individual de Registro")
        termo_busca = st.text_input("Campo de Busca Inteligente (Qualquer termo):", key="busca_consulta").strip()
        
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
                        <div class="ficha-item"><span class="ficha-label">CPF (Apenas Números):</span> {r.cpf if r.cpf else 'Não Informado'}</div>
                        <div class="ficha-item"><span class="ficha-label">Cargo Atual:</span> {r.cargo if r.cargo else 'Não Mapeado'}</div>
                        <div class="ficha-item"><span class="ficha-label">Data de Admissão:</span> {r.admissao.strftime('%d/%m/%Y') if r.admissao else '-'}</div>
                        <div class="ficha-item"><span class="ficha-label">Data de Demissão:</span> {r.demissao.strftime('%d/%m/%Y') if r.demissao else 'Ativo'}</div>
                        <div class="ficha-item"><span class="ficha-label">Canal / Chave PIX:</span> {r.chave_pix if r.chave_pix else 'Não Cadastrada'}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Nenhum registro localizado com os dados informados.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # --- NOVO ---
    with aba_novo:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("➕ Inserção Direta de Colaborador")
        with st.form("form_novo_registro", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_id = c1.text_input("ID / Número de Matrícula:")
            n_nome = c2.text_input("Nome Completo:")
            n_cpf = c1.text_input("CPF (Pontuação opcional):")
            n_cargo = c2.text_input("Cargo Ocupado:")
            n_adm = c1.date_input("Data de Admissão:", value=datetime.date.today())
            n_dem = c2.date_input("Data de Demissão (Se aplicável):", value=None, min_value=datetime.date(2000, 1, 1))
            n_pix = st.text_input("Chave PIX de Destino:")
            
            if st.form_submit_button("Gravar Registro Definitivo"):
                id_limpo = formatar_id_limpo(n_id)
                cpf_limpo = limpar_cpf(n_cpf)
                
                if not id_limpo or not n_nome:
                    st.error("❌ Os campos ID e Nome são estritamente obrigatórios.")
                elif not validar_id_clt(id_limpo):
                    st.error("❌ Erro de Segurança: Este formato de ID é protegido ou inválido para fins do sistema.")
                elif not df_colab.empty and id_limpo in df_colab['id'].astype(str).tolist():
                    st.error(f"❌ Conflito de Chave: O ID '{id_limpo}' já está cadastrado.")
                else:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, chave_pix)
                                VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :pix)
                            """),
                            {
                                "id": id_limpo, "nome": n_nome.strip(), "cpf": cpf_limpo,
                                "cargo": n_cargo.strip(), "admissao": n_adm,
                                "demissao": n_dem, "pix": n_pix.strip()
                            }
                        )
                    st.success("🎉 Colaborador inserido com sucesso absoluto no Supabase!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ALTERAR ---
    with aba_alterar:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("✏️ Edição de Registro Existente")
        if df_colab.empty:
            st.warning("Base de dados vazia para alteração.")
        else:
            lista_funcs = [f"{r['id']} - {r['nome']}" for _, r in df_colab.iterrows()]
            selecionado = st.selectbox("Selecione o funcionário que deseja modificar:", lista_funcs, key="sb_alterar")
            id_alterar = selecionado.split(" - ")[0]
            
            dados_atuais = df_colab[df_colab['id'] == id_alterar].iloc[0]
            
            with st.form("form_alterar_registro"):
                st.info(f"Modificando a Matrícula: {id_alterar}")
                a_nome = st.text_input("Nome Completo:", value=str(dados_atuais['nome']))
                a_cpf = st.text_input("CPF:", value=str(dados_atuais['cpf'] if dados_atuais['cpf'] else ''))
                a_cargo = st.text_input("Cargo Ocupado:", value=str(dados_atuais['cargo'] if dados_atuais['cargo'] else ''))
                
                val_adm = dados_atuais['admissao']
                if isinstance(val_adm, str):
                    val_adm = datetime.datetime.strptime(val_adm, '%Y-%m-%d').date()
                elif pd.isna(val_adm):
                    val_adm = datetime.date.today()
                    
                val_dem = dados_atuais['demissao']
                if isinstance(val_dem, str):
                    val_dem = datetime.datetime.strptime(val_dem, '%Y-%m-%d').date()
                elif pd.isna(val_dem):
                    val_dem = None
                
                a_adm = st.date_input("Data de Admissão:", value=val_adm)
                a_dem = st.date_input("Data de Demissão:", value=val_dem)
                a_pix = st.text_input("Chave PIX:", value=str(dados_atuais['chave_pix'] if dados_atuais['chave_pix'] else ''))
                
                if st.form_submit_button("Atualizar Dados Cadastrais"):
                    if not a_nome.strip():
                        st.error("O campo de Nome não pode ser deixado em branco.")
                    else:
                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    UPDATE cadastro_geral_colaborador 
                                    SET nome = :nome, cpf = :cpf, cargo = :cargo, admissao = :admissao, demissao = :demissao, chave_pix = :pix
                                    WHERE id = :id
                                """),
                                {
                                    "nome": a_nome.strip(), "cpf": limpar_cpf(a_cpf), "cargo": a_cargo.strip(),
                                    "admissao": a_adm, "demissao": a_dem, "pix": a_pix.strip(), "id": id_alterar
                                }
                            )
                        st.success("🎉 Alterações sincronizadas com o Supabase com sucesso!")
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- EXCLUIR ---
    with aba_excluir:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("❌ Remoção Crítica de Funcionário")
        if df_colab.empty:
            st.warning("Nenhum registro ativo disponível para remoção.")
        else:
            lista_funcs_del = [f"{r['id']} - {r['nome']}" for _, r in df_colab.iterrows()]
            selecionado_del = st.selectbox("Selecione o registro a ser removido:", lista_funcs_del, key="sb_excluir")
            id_deletar = selecionado_del.split(" - ")[0]
            
            st.warning(f"Atenção: Você selecionou a matrícula '{id_deletar}'. Esta ação não poderá ser desfeita.")
            trava_seguranca = st.checkbox("Confirmo que desejo apagar este colaborador e todo o seu histórico relarial.")
            
            if st.button("Remover Definitivamente do Supabase", type="primary"):
                if not trava_seguranca:
                    st.error("❌ Operação Rejeitada: Você precisa marcar a caixa de confirmação de segurança.")
                else:
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM premios_funcionarios WHERE id_funcionario = :id"), {"id": id_deletar})
                        conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_deletar})
                    st.success(f"💥 Matrícula {id_deletar} removida permanentemente do banco de dados.")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)    
