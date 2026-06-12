import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
import re
import os

# --- Configurações do Banco de Dados ---
# Carrega as variáveis de ambiente do Supabase
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Constrói a string de conexão
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Cria o engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# --- Constantes ---
LISTA_SITUACOES_ESOCIAL = [
    "1 - Trabalhando",
    "2 - Afastamento Temporário - Doença",
    "3 - Afastamento Temporário - Acidente de Trabalho",
    "4 - Afastamento Temporário - Licença Maternidade",
    "5 - Afastamento Temporário - Serviço Militar",
    "6 - Afastamento Temporário - Outros",
    "7 - Afastamento Definitivo - Aposentadoria",
    "8 - Afastamento Definitivo - Demissão",
    "9 - Férias" # Adicionado Status eSocial Férias
]

# --- Funções Utilitárias ---
def parse_br_date_smart(date_str):
    if pd.isna(date_str) or not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None

def format_cpf(cpf_str):
    if pd.isna(cpf_str) or not cpf_str:
        return None
    cpf_str = str(cpf_str).replace('.', '').replace('-', '').strip()
    if len(cpf_str) == 11 and cpf_str.isdigit():
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    return None

def format_competencia_smart(comp_str):
    if pd.isna(comp_str) or not comp_str:
        return None
    comp_str = str(comp_str).strip()
    match = re.match(r'(\d{2})/(\d{4})', comp_str)
    if match:
        return comp_str
    match = re.match(r'(\d{2})(\d{4})', comp_str)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None

# --- Função de Leitura de Planilha Inteligente (Ajustada para CSV) ---
def ler_planilha_inteligente(uploaded_file, nrows=None, header='infer'):
    if uploaded_file is None:
        return None

    file_name = uploaded_file.name
    df = None

    try:
        if file_name.endswith('.csv'):
            # Tenta diferentes separadores e engines para CSV
            # Tenta com ponto e vírgula, engine 'python' para lidar com aspas e EOF
            try:
                uploaded_file.seek(0) # Garante que o ponteiro está no início
                df = pd.read_csv(uploaded_file, sep=';', nrows=nrows, header=header, encoding='utf-8', engine='python')
            except Exception as e_semicolon:
                uploaded_file.seek(0) # Volta o ponteiro do arquivo para o início
                # Tenta com vírgula, engine 'python'
                try:
                    df = pd.read_csv(uploaded_file, sep=',', nrows=nrows, header=header, encoding='utf-8', engine='python')
                except Exception as e_comma:
                    uploaded_file.seek(0) # Volta o ponteiro do arquivo para o início
                    # Tenta com ponto e vírgula, engine 'c' (padrão)
                    try:
                        df = pd.read_csv(uploaded_file, sep=';', nrows=nrows, header=header, encoding='utf-8')
                    except Exception as e_semicolon_c:
                        uploaded_file.seek(0) # Volta o ponteiro do arquivo para o início
                        # Tenta com vírgula, engine 'c' (padrão)
                        try:
                            df = pd.read_csv(uploaded_file, sep=',', nrows=nrows, header=header, encoding='utf-8')
                        except Exception as e_final:
                            st.error(f"Não foi possível ler o arquivo CSV com nenhum separador ou engine. Erros: [;python]: {e_semicolon}, [,python]: {e_comma}, [;c]: {e_semicolon_c}, [,c]: {e_final}")
                            return None
        elif file_name.endswith(('.xls', '.xlsx')):
            uploaded_file.seek(0) # Garante que o ponteiro está no início
            df = pd.read_excel(uploaded_file, nrows=nrows, header=header)
        else:
            st.error("Formato de arquivo não suportado. Por favor, envie um arquivo CSV ou Excel.")
            return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return None

    if df is None: # Se df ainda for None após as tentativas de leitura
        return None

    # Padronizar nomes de colunas para minúsculas e sem acentos/caracteres especiais
    # Isso é importante para que o código possa referenciar as colunas de forma consistente
    df.columns = [re.sub(r'[^a-z0-9_]', '', col.lower().replace(' ', '_')) for col in df.columns]

    return df

# --- Criação de Tabelas no Banco de Dados (se não existirem) ---
def criar_tabelas():
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS cadastro_geral_colaborador (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                cpf TEXT UNIQUE,
                cargo TEXT,
                admissao DATE,
                demissao DATE,
                status_esocial TEXT,
                salario_mes_12_24 NUMERIC(10, 2),
                salario_hora_12_24 NUMERIC(10, 2)
            );
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_afastamentos (
                id SERIAL PRIMARY KEY,
                id_colaborador TEXT NOT NULL,
                data_inicio DATE NOT NULL,
                tipo_afastamento TEXT NOT NULL,
                FOREIGN KEY (id_colaborador) REFERENCES cadastro_geral_colaborador(id)
            );
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_premiacoes_e_folha (
                id SERIAL PRIMARY KEY,
                id_colaborador TEXT NOT NULL,
                competencia TEXT NOT NULL,
                tipo_lancamento TEXT NOT NULL,
                valor_lancamento NUMERIC(10, 2) NOT NULL,
                status_pagamento TEXT,
                retroativo_pago NUMERIC(10, 2),
                data_pagamento DATE,
                FOREIGN KEY (id_colaborador) REFERENCES cadastro_geral_colaborador(id),
                UNIQUE (id_colaborador, competencia, tipo_lancamento)
            );
        """))
        # Tabela de Prêmios para Funcionários
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS premios_funcionarios (
                id SERIAL PRIMARY KEY,
                codigo_funcionario TEXT NOT NULL,
                nome_funcionario TEXT,
                salario_hora NUMERIC(10, 2),
                horas_premio NUMERIC(10, 2),
                descricao_servico TEXT,
                data_lancamento DATE,
                valor_total_premio NUMERIC(10, 2),
                status_pagamento TEXT,
                cargo TEXT,
                FOREIGN KEY (codigo_funcionario) REFERENCES cadastro_geral_colaborador(id)
            );
        """))
        connection.commit()

# --- Executa a criação das tabelas ao iniciar o aplicativo ---
criar_tabelas()

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="BRAGANÇA SYS ERP",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Importa as páginas do aplicativo (APÓS criar as tabelas) ---
# Corrigido o nome do arquivo de importação de 'gestao_cadastros' para 'cadastros'
from pages import cadastros as gestao_cadastros_page # Renomeado para evitar conflito
from pages import importacao_inteligente
from pages

    
