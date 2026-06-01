import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import re

# --- CONFIGURAÇÃO DE DIRETRIZES VISUAIS (DARK PREMIUM GLASSMORPHISM) ---
st.set_page_config(page_title="BRAGANÇA SYS - Gestão Corporativa", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
    /* Fundo Navy Blue / Dark Gray Premium */
    .stApp { 
        background-color: #0f172a; 
        color: #f8fafc; 
        font-family: 'Inter', sans-serif; 
    }
    /* Efeito Glassmorphism para os Paineis e Cards */
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
    
    /* Customização de Inputs e Botões */
    .stButton>button { 
        border-radius: 8px; 
        font-weight: 600; 
        background-color: #2563eb !important; 
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        transition: background-color 0.15s ease;
    }
    .stButton>button:hover { background-color: #1d4ed8 !important; }
    input, select, textarea { font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO DIRETA E BLINDADA COM O BANCO DE DADOS (SUPABASE) ---
# O DATABASE_URL deve estar configurado no arquivo .streamlit/secrets.toml
engine = create_engine(st.secrets["DATABASE_URL"])

# --- INICIALIZAÇÃO DA INFRAESTRUTURA FÍSICA NO BANCO (DDL) ---
def inicializar_banco_de_dados():
    """Garante que a estrutura relacional exista de forma estável no banco de dados."""
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

# --- MOTORES DE HIGIENIZAÇÃO E ENGENHARIA DE DADOS ---
def validar_id_clt(id_texto):
    """Garante que o ID 1 (Chave Mestra de Auditoria) seja ignorado conforme as diretrizes legais."""
    id_limpo = str(id_texto).split('.')[0].strip()
    if id_limpo in ['1', '01', '001', '0001', '']:
        return False
    return True

def formatar_id_limpo(id_original):
    """Remove resíduos de ponto flutuante gerados pela leitura de arquivos (ex: 2.0 vira 2)."""
    if pd.isna(id_original):
        return None
    return str(id_original).split('.')[0].strip()

def converter_data_serial_excel(valor):
    """Transforma os números seriais do Excel (ex: 44460.0) em objetos de data reais do SQL."""
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    try:
        num_serial = float(valor)
        return pd.to_datetime(num_serial, unit='D', origin='1899-12-30').date()
    except ValueError:
        try:
            return pd.to_datetime(valor).date()
        except:
            return None

def obter_colaboradores_banco():
    try:
        return pd.read_sql("SELECT id, nome, cpf, cargo, admissao, demissao, chave_pix FROM cadastro_geral_colaborador ORDER BY admissao ASC", engine)
    except Exception:
        return pd.DataFrame(columns=['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao', 'chave_pix'])

def obter_premios_banco():
    try:
        return pd.read_sql("SELECT id_funcionario, competencia_mes_ano, salario_base, salario_hora FROM premios_funcionarios", engine)
    except Exception:
        return pd.DataFrame(columns=['id_funcionario', 'competencia_mes_ano', 'salario_base', 'salario_hora'])

# --- NAVEGAÇÃO INTERNA DA SPA ---
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>🏗️ BRAGANÇA SYS</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação do Ecossistema", ["👥 Painel Corporativo", "📥 Ingestão Mestra (Migração)", "🛠️ Administração do Banco"])

df_colab = obter_colaboradores_banco()
df_premios = obter_premios_banco()

# --- ABA 1: PAINEL CORPORATIVO (VISUALIZAÇÃO DE DADOS REAIS DO BANCO) ---
if menu == "👥 Painel Corporativo":
    st.markdown("<h2 style='margin-bottom: 20px;'>👥 Painel de Controle de Operações</h2>", unsafe_allow_html=True)
    
    if df_colab.empty:
        st.info("💡 O banco de dados está vazio. Utilize o menu lateral para acessar a aba de **Ingestão Mestra** e carregar os dados históricos.")
    else:
        total_funcionarios = len(df_colab)
        massa_salarial = df_premios['salario_base'].sum() if not df_premios.empty else 0.0
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="card-metric"><div class="metric-title">Colaboradores no Banco</div><div class="metric-value">{total_funcionarios}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card-metric"><div class="metric-title">Volume de Histórico Salarial</div><div class="metric-value">R$ {massa_salarial:,.2f}</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        st.subheader("📋 Funcionários Ativos e Históricos (Ordenação Física por Admissão)")
        st.dataframe(df_colab, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- ABA 2: INGESTÃO MESTRA (CONVERSOR E MIGRATOR DO EXCEL PARA O SUPABASE) ---
elif menu == "📥 Ingestão Mestra (Migração)":
    st.markdown("<h2>📥 Ingestão de Dados e Carga de Banco</h2>", unsafe_allow_html=True)
    st.markdown("Utilize este espaço exclusivamente para subir o arquivo extraído. O sistema fará a varredura, conversão e armazenamento definitivo no banco.")
    
    arquivo_carregado = st.file_uploader("Arraste ou selecione o arquivo de extração (.csv ou .xlsx)", type=["xlsx", "csv"])
    
    if arquivo_carregado:
        st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
        if st.button("Executar Migração e Gravar no Banco de Dados", type="primary"):
            with st.spinner("Decodificando payload e injetando registros no banco..."):
                
                # Leitura flexível do arquivo fonte
                if arquivo_carregado.name.endswith('.csv'):
                    df_bruto = pd.read_csv(arquivo_carregado, sep=None, engine='python')
                else:
                    df_bruto = pd.read_excel(arquivo_carregado, sheet_name=0)
                
                # Padroniza nomes de colunas limpando espaços e acentos
                df_bruto.columns = [col.strip().lower().replace('admissão', 'admissao').replace('demissão', 'demissao') for col in df_bruto.columns]
                
                if 'id' in df_bruto.columns:
                    df_bruto['id'] = df_bruto['id'].apply(formatar_id_limpo)
                
                # --- PARTE 1: TABELA DE CADASTRO GERAL ---
                campos_cadastro = ['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao']
                campos_validos = [c for c in campos_cadastro if c in df_bruto.columns]
                
                df_cadastro_final = df_bruto[campos_validos].drop_duplicates(subset=['id']).copy()
                
                # Aplica filtros rigorosos de higienização
                df_cadastro_final = df_cadastro_final[df_cadastro_final['id'].apply(validar_id_clt)]
                df_cadastro_final['admissao'] = df_cadastro_final['admissao'].apply(converter_data_serial_excel)
                df_cadastro_final['demissao'] = df_cadastro_final['demissao'].apply(converter_data_serial_excel)
                
                if 'cpf' in df_cadastro_final.columns:
                    df_cadastro_final['cpf'] = df_cadastro_final['cpf'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                # Adiciona a chave_pix garantindo o seu posicionamento como última coluna absoluta
                if 'chave_pix' in df_bruto.columns:
                    df_cadastro_final['chave_pix'] = df_bruto['chave_pix'].astype(str).str.strip()
                else:
                    df_cadastro_final['chave_pix'] = None
                
                # Reindexação de segurança das colunas primárias
                ordem_campos = ['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao', 'chave_pix']
                df_cadastro_final = df_cadastro_final.reindex(columns=ordem_campos)
                
                # Trava de Segurança contra Chaves Duplicadas já gravadas anteriormente
                if not df_colab.empty:
                    ids_ja_gravados = df_colab['id'].astype(str).tolist()
                    df_cadastro_final = df_cadastro_final[~df_cadastro_final['id'].isin(ids_ja_gravados)]
                
                # Inserção física estável na tabela cadastral do Supabase
                if not df_cadastro_final.empty:
                    df_cadastro_final.to_sql('cadastro_geral_colaborador', engine, if_exists='append', index=False)
                
                # --- PARTE 2: EVOLUÇÃO SALARIAL HISTÓRICA (PREMIOS) ---
                linhas_historico = []
                colunas_salario = [col for col in df_bruto.columns if col.startswith('salario_mes')]
                
                for _, row in df_bruto.iterrows():
                    id_func = formatar_id_limpo(row.get('id'))
                    if not id_func or not validar_id_clt(id_func):
                        continue
                    
                    for col_sal in colunas_salario:
                        valor_sal = row[col_sal]
                        if pd.notna(valor_sal) and str(valor_sal).strip() != "":
                            try:
                                sal_float = float(str(valor_sal).replace(',', '.'))
                                if sal_float > 0:
                                    # Captura a competência (ex: "12/24") limpando o prefixo da coluna
                                    competencia = col_sal.replace('salario_mes', '').strip()
                                    sal_hora = sal_float / 220.0
                                    
                                    linhas_historico.append({
                                        'id_funcionario': id_func,
                                        'competencia_mes_ano': competencia,
                                        'salario_base': sal_float,
                                        'salario_hora': round(sal_hora, 4)
                                    })
                            except ValueError:
                                continue
                
                if linhas_historico:
                    df_premios_final = pd.DataFrame(linhas_historico)
                    df_premios_final.to_sql('premios_funcionarios', engine, if_exists='append', index=False)
                
                st.success(f"🎉 Carga executada com sucesso absoluto! Banco alimentado e sincronizado.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- ABA 3: ADMINISTRAÇÃO MANUAl DIRETA NO BANCO ---
elif menu == "🛠️ Administração do Banco":
    st.markdown("<h2>🛠️ Gerenciamento Direto de Registros</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='panel-glass'>", unsafe_allow_html=True)
    st.subheader("➕ Inserção Manual de Novo Colaborador")
    with st.form("form_banco_novo"):
        c1, c2 = st.columns(2)
        in_id = c1.text_input("ID da Matrícula (Não pode ser 1)")
        in_nome = c2.text_input("Nome Completo")
        in_cpf = c1.text_input("CPF")
        in_cargo = c2.text_input("Cargo Administrativo / Operacional")
        in_adm = c1.date_input("Data de Admissão")
        in_dem = c2.text_input("Data de Demissão (Opcional - AAAA-MM-DD)")
        in_pix = st.text_input("Chave PIX do Favorecido")
        
        if st.form_submit_button("Salvar Diretamente no Banco de Dados"):
            id_processado = formatar_id_limpo(in_id)
            if not validar_id_clt(id_processado):
                st.error("❌ Erro de Validação: O ID '1' é exclusivo para fins do sistema e não pode ser usado.")
            elif not df_colab.empty and id_processado in df_colab['id'].astype(str).tolist():
                st.error(f"❌ Conflito de Chave Primária: O ID '{id_processado}' já existe no banco.")
            elif id_processado and in_nome:
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, chave_pix)
                            VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :pix)
                        """),
                        {
                            "id": id_processado, "nome": in_nome.strip(), "cpf": in_cpf.strip(),
                            "cargo": in_cargo.strip(), "admissao": in_adm,
                            "demissao": in_dem.strip() if in_dem else None, "pix": in_pix.strip() if in_pix else None
                        }
                    )
                st.success("🎉 Colaborador salvo com sucesso no Supabase!")
                st.rerun()
            else:
                st.error("Os campos ID e Nome são estritamente obrigatórios.")
    st.markdown("</div>", unsafe_allow_html=True)
