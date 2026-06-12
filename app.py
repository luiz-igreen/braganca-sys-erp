import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
import re
import os
import csv # Importar o módulo csv para detecção de dialeto

# --- Configurações do Banco de Dados ---
# Carrega as variáveis de ambiente do Supabase usando st.secrets
try:
    DB_HOST = st.secrets["HOST"]
    DB_PORT = st.secrets["PORT"]
    DB_DATABASE = st.secrets["DATABASE"]
    DB_USER = st.secrets["USER"]
    DB_PASSWORD = st.secrets["PASSWORD"]
    DATABASE_URL = st.secrets["DATABASE_URL"]
except KeyError as e:
    st.error(f"Erro: Variável de ambiente não encontrada em st.secrets: {e}. Verifique suas secrets no Streamlit Cloud.")
    st.stop()

# Cria o engine SQLAlchemy
try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    st.error(f"Erro ao criar o engine do banco de dados: {e}. Verifique a DATABASE_URL e as credenciais.")
    st.stop()


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

    # Resetar o ponteiro do arquivo para o início antes de qualquer leitura
    uploaded_file.seek(0)

    if file_name.endswith('.csv'):
        # Tenta detectar o separador automaticamente
        detected_sep = ',' # Valor padrão se a detecção falhar
        try:
            # Ler um pedaço do arquivo para o sniffer
            sample = uploaded_file.read(1024).decode('utf-8')
            uploaded_file.seek(0) # Resetar o ponteiro após a leitura da amostra

            # Tenta snifar com vírgula e ponto e vírgula
            dialect = csv.Sniffer().sniff(sample, delimiters=',;')
            detected_sep = dialect.delimiter
            st.info(f"Separador detectado automaticamente: '{detected_sep}'")
        except Exception:
            st.warning("Não foi possível detectar o separador automaticamente. Usando separador padrão: vírgula (',').")

        # Lista de encodings para tentar
        encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1']

        for enc in encodings_to_try:
            try:
                uploaded_file.seek(0) # Garante que o ponteiro está no início para cada tentativa
                # Usar o separador detectado ou o padrão (vírgula)
                df = pd.read_csv(uploaded_file, sep=detected_sep, nrows=nrows, header=header, encoding=enc, engine='python')
                # Verifica se o DataFrame tem um número razoável de colunas (pelo menos 5 para ser um CSV válido)
                if df.shape[1] > 4: 
                    st.success(f"Arquivo CSV lido com sucesso usando separador '{detected_sep}' e encoding '{enc}'.")
                    break # Sai do loop de encodings
            except Exception as e:
                st.warning(f"Tentativa de leitura com separador '{detected_sep}' e encoding '{enc}' falhou: {e}")
                continue # Tenta o próximo encoding

        if df is None or df.shape[1] <= 4: # Se ainda não conseguiu ler com colunas suficientes
            st.error("Não foi possível ler o arquivo CSV com o separador detectado ou padrão, ou o número de colunas é insuficiente. Verifique o formato do arquivo.")
            return None

    elif file_name.endswith(('.xls', '.xlsx')):
        try:
            uploaded_file.seek(0) # Garante que o ponteiro está no início
            df = pd.read_excel(uploaded_file, nrows=nrows, header=header)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Excel: {e}")
            return None
    else:
        st.error("Formato de arquivo não suportado. Por favor, envie um arquivo CSV ou Excel.")
        return None

    if df is None: # Se df ainda for None após as tentativas de leitura
        return None

    # Padronizar nomes de colunas para minúsculas e sem acentos/caracteres especiais
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
from pages import cadastros as gestao_cadastros_page
from pages import importacao_inteligente
from pages import premios as premios_page

# --- Navegação na Barra Lateral ---
st.sidebar.title("Navegação")
selection = st.sidebar.radio("Ir para", [
    "Visão Geral",
    "Importação Inteligente",
    "Gestão de Cadastros",
    "Gestão de Prêmios (ZAUT)",
    "Auditoria CCT (IA)"
])

# --- Renderiza a página selecionada ---
if selection == "Visão Geral":
    st.title("Visão Geral do Sistema")
    st.write("Bem-vindo ao BRAGANÇA SYS ERP. Use o menu lateral para navegar.")
elif selection == "Importação Inteligente":
    importacao_inteligente.render(
        engine,
        ler_planilha_inteligente,
        parse_br_date_smart,
        format_cpf,
        format_competencia_smart,
        LISTA_SITUACOES_ESOCIAL
    )
elif selection == "Gestão de Cadastros":
    gestao_cadastros_page.render(
        engine,
        parse_br_date_smart,
        format_cpf,
        LISTA_SITUACOES_ESOCIAL
    )
elif selection == "Gestão de Prêmios (ZAUT)":
    premios_page.render(
        engine,
        parse_br_date_smart
    )
elif selection == "Auditoria CCT (IA)":
    st.title("Auditoria CCT (IA)")
    st.write("Funcionalidade em desenvolvimento.")
