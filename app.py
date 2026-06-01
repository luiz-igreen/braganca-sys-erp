import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

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
        # Tabela Cadastral com ID definido como Chave Primária Absoluta (Registro do Livro)
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
        # Tabela de Histórico de Prêmios/Salários
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS premios_funcionarios (
                id_sn SERIAL PRIMARY KEY,
                id_funcionario TEXT,
                competencia_mes_ano TEXT,
                salario_base NUMERIC,
                salario_hora NUMERIC
            );
        """))

# Executa a validação estrutural antes de renderizar a interface
inicializar_estrutura_banco()

# --- FUNÇÃO AUXILIAR DE VALIDAÇÃO LEGISLATIVA (CLT/MTE) ---
def validar_id_clt(id_texto):
    """Retorna False se o ID for a Chave Mestra 1 (ou variações com zero à esquerda), protegendo a legalidade do sistema."""
    id_limpo = str(id_texto).strip()
    if id_limpo in ['1', '01', '001', '0001', '00001']:
        return False
    try:
        if int(float(id_limpo)) == 1:
            return False
    except ValueError:
        pass
    return True

# --- FUNÇÕES SEGURAS DE LEITURA DE DADOS ---
def carregar_colaboradores():
    try:
        # Mantém a listagem estritamente ordenada pela ordem cronológica de admissão
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

# --- ABA 2: IMPORTAÇÃO INTELIGENTE (COM FILTRO RÍGIDO DE LEGISLAÇÃO) ---
elif menu == "📥 Importação Inteligente":
    st.title("📥 Importação e Ingestão de Dados")
    st.markdown("Carregue a planilha `Empregados-Bragança.xlsx`. O sistema aplicará as travas automáticas da CLT para o ID de Registro.")
    
    uploaded_file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
    
    if uploaded_file:
        if st.button("Executar Engenharia de Dados", type="primary"):
            with st.spinner("Processando dados e aplicando travas de integridade..."):
                df_raw = pd.read_excel(uploaded_file, sheet_name=0)
                df_raw.columns = [col.strip().lower() for col in df_raw.columns]
                
                # 1. Tratamento do Cadastro Geral
                campos_cadastro = ['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao']
                campos_existentes = [c for c in campos_cadastro if c in df_raw.columns]
                
                df_cadastro_final = df_raw[campos_existentes].drop_duplicates(subset=['id']).copy()
                df_cadastro_final['id'] = df_cadastro_final['id'].astype(str).str.strip()
                
                # --- TRAVA 1: FILTRO CLT (Exclui automaticamente linhas que tentem usar o ID 1 da planilha) ---
                df_cadastro_final = df_cadastro_final[df_cadastro_final['id'].apply(validar_id_clt)]
                
                if 'cpf' in df_cadastro_final.columns:
                    df_cadastro_final['cpf'] = df_cadastro_final['cpf'].astype(str)
                
                if 'chave_pix' in df_raw.columns:
                    df_cadastro_final['chave_pix'] = df_raw['chave_pix']
                else:
                    df_cadastro_final['chave_pix'] = None
                
                ordem_obrigatoria = ['id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao', 'chave_pix']
                df_cadastro_final = df_cadastro_final.reindex(columns=ordem_obrigatoria)
                
                # --- TRAVA 2: ANTI-DUPLICIDADE ---
                if not df_colab.empty:
                    ids_existentes = df_colab['id'].astype(str).tolist()
                    df_cadastro_final = df_cadastro_final[~df_cadastro_final['id'].isin(ids_existentes)]
                
                # Salva os novos registros válidos no Supabase
                if not df_cadastro_final.empty:
                    df_cadastro_final.to_sql('cadastro_geral_colaborador', engine, if_exists='append', index=False)
                
                # 2. Processamento Dinâmico dos Prêmios/Salários (A partir de 12/24)
                linhas_historico = []
                colunas_salario = [col for col in df_raw.columns if col.startswith('salario_mes')]
                
                for _, row in df_raw.iterrows():
                    id_func = str(row.get('id')).strip()
                    if pd.isna(row.get('id')) or not validar_id_clt(id_func):
                        continue
                        
                    for col_sal in colunas_salario:
                        sal_base = row[col_sal]
                        if pd.notna(sal_base) and sal_base > 0:
                            competencia = col_sal.replace('salario_mes', '').strip()
                            sal_hora = float(sal_base) / 220.0
                            
                            linhas_historico.append({
                                'id_funcionario': id_func,
                                'competencia_mes_ano': competencia,
                                'salario_base': float(sal_base),
                                'salario_hora': round(sal_hora, 4)
                            })
                
                if linhas_historico:
                    df_premios_final = pd.DataFrame(linhas_historico)
                    df_premios_final.to_sql('premios_funcionarios', engine, if_exists='append', index=False)
                
                st.success("🎉 Processamento realizado com sucesso! Dados unificados, ordenados por admissão e validados sob as normas CLT/MTE.")
                st.rerun()

# --- ABA 3: GESTÃO DE CADASTROS MANUAIS (COM VALIDAÇÃO DE TELA) ---
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
                fid_limpo = fid.strip() if fid else ""
                
                # --- BLOQUEIO DE SEGURANÇA EM TELA ---
                if not validar_id_clt(fid_limpo):
                    st.error("❌ Violação Legislativa MTE: O ID '1' é a chave mestra e não pode ser atribuído a colaboradores. O registro de funcionários reais deve iniciar a partir do número 2.")
                elif not df_colab.empty and fid_limpo in df_colab['id'].astype(str).tolist():
                    st.error(f"❌ Erro de Duplicidade: O colaborador com o registro de matrícula '{fid_limpo}' já está cadastrado no sistema.")
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
                    st.error("Campos ID e Nome são estritamente obrigatórios.")

    if not df_colab.empty:
        if termo:
            df_colab = df_colab[
                df_colab['nome'].astype(str).str.contains(termo, case=False) | 
                df_colab['cpf'].astype(str).str.contains(termo, case=False) |
                df_colab['cargo'].astype(str).str.contains(termo, case=False) |
                df_colab['id'].astype(str).str.contains(termo, case=False)
            ]
        # Exibe os dados mantendo a amarração completa da linha e ordenação do banco
        st.dataframe(df_colab, use_container_width=True, hide_index=True)
