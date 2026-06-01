import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- CONFIGURAÇÃO DE DESIGN (UI/UX PREMIUM) ---
st.set_page_config(page_title="BRAGANÇA SYS - Módulo de Prêmios", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
    .card { background: #1e293b; padding: 25px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 20px; }
    .metric-title { color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; }
    .metric-value { font-size: 2rem; font-weight: 800; color: #ffffff; }
    .stButton>button { border-radius: 8px; width: 100%; font-weight: 600; }
    input, select { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM BANCO DE DADOS ---
engine = create_engine(st.secrets["DATABASE_URL"])

# --- INICIALIZAÇÃO E BLINDAGEM DA ESTRUTURA FÍSICA (DDL) ---
def inicializar_estrutura_banco():
    """Garante a criação das tabelas com restrições rígidas de integridade diretamente no Supabase."""
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

inicializar_estrutura_banco()

# --- FUNÇÕES AUXILIARES DE TRATAMENTO DE ENGENHARIA DE DADOS ---
def validar_id_clt(id_texto):
    """Bloqueia o ID 1 (Chave Mestra) em conformidade com as normas do MTE/CLT."""
    id_limpo = str(id_texto).split('.')[0].strip()
    if id_limpo in ['1', '01', '001', '0001']:
        return False
    return True

def formatar_id_limpo(id_original):
    """Remove pontos flutuantes vindos de leituras incorretas de arquivos (ex: 2.0 vira 2)."""
    if pd.isna(id_original):
        return None
    return str(id_original).split('.')[0].strip()

def converter_data_excel(valor_coluna):
    """Converte números seriais do Excel (ex: 44460.0) ou strings comuns para objetos de data reais."""
    if pd.isna(valor_coluna) or str(valor_coluna).strip() == "":
        return None
    try:
        # Tenta converter caso o Excel tenha enviado como número serial bruto
        num_serial = float(valor_coluna)
        return pd.to_datetime(num_serial, unit='D', origin='1899-12-30').date()
    except ValueError:
        try:
            # Caso venha como string de data tradicional
            return pd.to_datetime(valor_coluna).date()
        except:
            return None

# --- FUNÇÕES SEGURAS DE LEITURA DE DADOS ---
def carregar_colaboradores():
    try:
        return pd.read_sql("SELECT id, nome, cpf, cargo, admissao, demissao, chave_pix FROM cadastro_geral_colaborador ORDER BY admissao ASC", engine)
    except Exception:
        return pd.DataFrame(columns=['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao', 'chave_pix'])

def carregar_premios_historico():
    try:
        return pd.read_sql("SELECT * FROM premios_funcionarios", engine)
    except Exception:
        return pd.DataFrame(columns=['id_funcionario', 'competencia_mes_ano', 'salario_base', 'salario_hora'])

# --- NAVEGAÇÃO SPA ---
st.sidebar.markdown("## 🏗️ BRAGANÇA SYS")
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros"])

df_colab = carregar_colaboradores()
df_premios = carregar_premios_historico()

# --- ABA 1: VISÃO GERAL ---
if menu == "👥 Visão Geral":
    st.title("👥 Painel Consolidado de Obras")
    
    if df_colab.empty:
        st.info("💡 Nenhum dado foi detectado no Supabase. Vá até a aba **📥 Importação Inteligente** para processar a planilha de empregados.")
    else:
        total_folha = df_premios['salario_base'].sum() if not df_premios.empty else 0.0
        
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="card"><div class="metric-title">Colaboradores Cadastrados</div><div class="metric-value">{len(df_colab)}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="card"><div class="metric-title">Massa Salarial Histórica Acumulada</div><div class="metric-value">R$ {total_folha:,.2f}</div></div>', unsafe_allow_html=True)
        
        st.subheader("📋 Lista Geral de Funcionários (Ordenado por Data de Admissão)")
        st.dataframe(df_colab, use_container_width=True, hide_index=True)

# --- ABA 2: IMPORTAÇÃO INTELIGENTE (COM CONVERSOR DE DATA EXCEL E FILTRO CLT) ---
elif menu == "📥 Importação Inteligente":
    st.title("📥 Importação e Ingestão de Dados")
    st.markdown("Carregue a planilha `Empregados-Bragança.xlsx` para realizar a carga automática segura no Supabase.")
    
    uploaded_file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx", "csv"])
    
    if uploaded_file:
        if st.button("Executar Ingestão Certificada", type="primary"):
            with st.spinner("Processando dados e aplicando travas de integridade..."):
                
                # Leitura dinâmica para aceitar Excel ou CSV convertidos
                if uploaded_file.name.endswith('.csv'):
                    df_raw = pd.read_csv(uploaded_file, sep=None, engine='python')
                else:
                    df_raw = pd.read_excel(uploaded_file, sheet_name=0)
                
                df_raw.columns = [col.strip().lower() for col in df_raw.columns]
                
                # Ajusta o ID removendo o ".0" flutuante
                if 'id' in df_raw.columns:
                    df_raw['id'] = df_raw['id'].apply(formatar_id_limpo)
                
                # 1. Tratamento e Isolamento do Cadastro Geral
                campos_cadastro = ['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao']
                # Mapeia sinônimos caso a coluna possua acentuação na planilha
                df_raw = df_raw.rename(columns={'admissão': 'admissao', 'demissão': 'demissao'})
                
                campos_existentes = [c for c in campos_cadastro if c in df_raw.columns]
                df_cadastro_final = df_raw[campos_existentes].drop_duplicates(subset=['id']).copy()
                
                # Executa filtros rígidos de proteção
                df_cadastro_final = df_cadastro_final[df_cadastro_final['id'].apply(validar_id_clt)]
                df_cadastro_final['admissao'] = df_cadastro_final['admissao'].apply(converter_data_excel)
                df_cadastro_final['demissao'] = df_cadastro_final['demissao'].apply(converter_data_excel)
                
                if 'cpf' in df_cadastro_final.columns:
                    df_cadastro_final['cpf'] = df_cadastro_final['cpf'].astype(str).str.replace(r'\.0$', '', regex=True)
                
                if 'chave_pix' in df_raw.columns:
                    df_cadastro_final['chave_pix'] = df_raw['chave_pix']
                else:
                    df_cadastro_final['chave_pix'] = None
                
                # Garante o posicionamento correto e imutável das colunas
                ordem_obrigatoria = ['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao', 'chave_pix']
                df_cadastro_final = df_cadastro_final.reindex(columns=ordem_obrigatoria)
                
                # Trava Anti-Duplicidade contra chaves primárias existentes
                if not df_colab.empty:
                    ids_existentes = df_colab['id'].astype(str).tolist()
                    df_cadastro_final = df_cadastro_final[~df_cadastro_final['id'].isin(ids_existentes)]
                
                # Persiste os novos cadastros estáveis
                if not df_cadastro_final.empty:
                    df_cadastro_final.to_sql('cadastro_geral_colaborador', engine, if_exists='append', index=False)
                
                # 2. Processamento Dinâmico dos Prêmios/Salários
                linhas_historico = []
                colunas_salario = [col for col in df_raw.columns if col.startswith('salario_mes')]
                
                for _, row in df_raw.iterrows():
                    id_func = formatar_id_limpo(row.get('id'))
                    if not id_func or not validar_id_clt(id_func):
                        continue
                        
                    for col_sal in colunas_salario:
                        sal_base = row[col_sal]
                        if pd.notna(sal_base) and str(sal_base).strip() != "":
                            try:
                                sal_float = float(str(sal_base).replace(',', '.'))
                                if sal_float > 0:
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
                
                st.success("🎉 Ingestão concluída! Dados limpos, datas convertidas e IDs amarrados por admissão.")
                st.rerun()

# --- ABA 3: GESTÃO DE CADASTROS MANUAIS ---
elif menu == "🛠️ Gestão de Cadastros":
    st.title("🛠️ Administração Manual de Funcionários")
    
    col_pesq, col_novo = st.columns([4, 1])
    termo = col_pesq.text_input("🔍 Pesquisar na tabela por qualquer termo...")
    
    if col_novo.button("➕ Adicionar Colaborador"): 
        st.session_state.modo_cadastro = 'novo'
        
    if st.session_state.get('modo_cadastro') == 'novo':
        with st.form("form_novo_colaborador"):
            c1, c2 = st.columns(2)
            fid = c1.text_input("Nº de Registro de Empregado (Não pode ser 1)")
            fnome = c2.text_input("Nome Completo")
            fcpf = c1.text_input("CPF")
            fcargo = c2.text_input("Cargo Atual")
            fadmissao = c1.date_input("Data de Admissão")
            fdemissao = c2.text_input("Data de Demissão (Opcional - AAAA-MM-DD)")
            fpix = st.text_input("Chave PIX (Último campo)")
            
            if st.form_submit_button("💾 Persistir Dados"):
                fid_limpo = formatar_id_limpo(fid)
                
                if not validar_id_clt(fid_limpo):
                    st.error("❌ Violação MTE: O ID '1' é a chave mestra de auditoria e está bloqueado.")
                elif not df_colab.empty and fid_limpo in df_colab['id'].astype(str).tolist():
                    st.error(f"❌ Erro: O ID de matrícula '{fid_limpo}' já está em uso por outro funcionário.")
                elif fid_limpo and fnome:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, chave_pix) 
                                VALUES (:id, :n, :c, :car, :a, :d, :pix)
                            """),
                            {
                                "id": fid_limpo, "n": fnome, "c": fcpf, "car": fcargo, 
                                "a": fadmissao, "d": fdemissao if fdemissao else None, "pix": fpix if fpix else None
                            }
                        )
                    st.success("Funcionário registrado com sucesso!")
                    st.session_state.modo_cadastro = 'listagem'
                    st.rerun()
                else:
                    st.error("Campos ID e Nome são obrigatórios.")

    if not df_colab.empty:
        if termo:
            df_colab = df_colab[
                df_colab['nome'].astype(str).str.contains(termo, case=False) | 
                df_colab['cpf'].astype(str).str.contains(termo, case=False) |
                df_colab['cargo'].astype(str).str.contains(termo, case=False) |
                df_colab['id'].astype(str).str.contains(termo, case=False)
            ]
        st.dataframe(df_colab, use_container_width=True, hide_index=True)
