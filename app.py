import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
import re
import os
import csv

try:
    DB_HOST = st.secrets["HOST"]
    DB_PORT = st.secrets["PORT"]
    DB_DATABASE = st.secrets["DATABASE"]
    DB_USER = st.secrets["USER"]
    DB_PASSWORD = st.secrets["PASSWORD"]
    DATABASE_URL = st.secrets["DATABASE_URL"]
except KeyError as e:
    st.error(f"Erro: Variável de ambiente não encontrada em st.secrets: {e}")
    st.stop()

try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    st.error(f"Erro ao criar o engine do banco de dados: {e}")
    st.stop()

LISTA_SITUACOES_ESOCIAL = [
    "1 - Trabalhando", "2 - Afastamento Temporário - Doença",
    "3 - Afastamento Temporário - Acidente de Trabalho", "4 - Afastamento Temporário - Licença Maternidade",
    "5 - Afastamento Temporário - Serviço Militar", "6 - Afastamento Temporário - Outros",
    "7 - Afastamento Definitivo - Aposentadoria", "8 - Afastamento Definitivo - Demissão", "9 - Férias"
]

def parse_br_date_smart(date_str):
    if pd.isna(date_str) or not date_str: return None
    date_str = str(date_str).strip()
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y'):
        try: return datetime.strptime(date_str, fmt).date()
        except ValueError: pass
    return None

def format_cpf(cpf_str):
    if pd.isna(cpf_str) or not cpf_str: return None
    cpf_str = str(cpf_str).replace('.', '').replace('-', '').strip()
    if len(cpf_str) == 11 and cpf_str.isdigit():
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    return None

def format_competencia_smart(comp_str):
    if pd.isna(comp_str) or not comp_str: return None
    comp_str = str(comp_str).strip()
    match = re.match(r'(\d{2})/(\d{4})', comp_str)
    if match: return comp_str
    match = re.match(r'(\d{2})(\d{4})', comp_str)
    if match: return f"{match.group(1)}/{match.group(2)}"
    return None

def ler_planilha_inteligente(uploaded_file, nrows=None, header='infer'):
    if uploaded_file is None: return None
    file_name = uploaded_file.name
    df = None
    uploaded_file.seek(0)

    if file_name.endswith('.csv'):
        try:
            sample = uploaded_file.read(1024).decode('utf-8', errors='ignore')
            uploaded_file.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=';,')
            detected_sep = dialect.delimiter
        except Exception:
            detected_sep = None

        separators_to_try = [detected_sep] if detected_sep else [';', ',', '\t', '|']
        encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1']

        for sep in separators_to_try:
            if sep is None: continue
            for enc in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    # quoting=csv.QUOTE_NONE ignora erros de aspas no meio do texto
                    df = pd.read_csv(uploaded_file, sep=sep, nrows=nrows, header=header, encoding=enc, engine='python', quoting=csv.QUOTE_NONE, on_bad_lines='skip')
                    if df.shape[1] >= 11: 
                        break
                except Exception:
                    continue
            if df is not None and df.shape[1] >= 11: break

        if df is None or df.shape[1] < 11:
            st.error("Falha na leitura do CSV ou colunas insuficientes (mínimo 11).")
            return None

    elif file_name.endswith(('.xls', '.xlsx')):
        try:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, nrows=nrows, header=header)
        except Exception as e:
            st.error(f"Erro Excel: {e}")
            return None

    if df is not None:
        df.columns = [re.sub(r'[^a-z0-9_]', '', str(col).lower().replace(' ', '_')) for col in df.columns]
    return df

def criar_tabelas():
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS cadastro_geral_colaborador (
                id TEXT PRIMARY KEY, nome TEXT NOT NULL, cpf TEXT UNIQUE, cargo TEXT,
                admissao DATE, demissao DATE, status_esocial TEXT,
                salario_mes_12_24 NUMERIC(10, 2), salario_hora_12_24 NUMERIC(10, 2)
            );
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_afastamentos (
                id SERIAL PRIMARY KEY, id_colaborador TEXT NOT NULL, data_inicio DATE NOT NULL,
                tipo_afastamento TEXT NOT NULL, FOREIGN KEY (id_colaborador) REFERENCES cadastro_geral_colaborador(id)
            );
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_premiacoes_e_folha (
                id SERIAL PRIMARY KEY, id_colaborador TEXT NOT NULL, competencia TEXT NOT NULL,
                tipo_lancamento TEXT NOT NULL, valor_lancamento NUMERIC(10, 2) NOT NULL,
                status_pagamento TEXT, retroativo_pago NUMERIC(10, 2), data_pagamento DATE,
                FOREIGN KEY (id_colaborador) REFERENCES cadastro_geral_colaborador(id),
                UNIQUE (id_colaborador, competencia, tipo_lancamento)
            );
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS premios_funcionarios (
                id SERIAL PRIMARY KEY, codigo_funcionario TEXT NOT NULL, nome_funcionario TEXT,
                salario_hora NUMERIC(10, 2), horas_premio NUMERIC(10, 2), descricao_servico TEXT,
                data_lancamento DATE, valor_total_premio NUMERIC(10, 2), status_pagamento TEXT, cargo TEXT,
                FOREIGN KEY (codigo_funcionario) REFERENCES cadastro_geral_colaborador(id)
            );
        """))

        # Alterações estruturais para incluir as 11 colunas da planilha
        connection.execute(text("ALTER TABLE premios_funcionarios ADD COLUMN IF NOT EXISTS competencia TEXT;"))
        connection.execute(text("ALTER TABLE premios_funcionarios ADD COLUMN IF NOT EXISTS salario_mes NUMERIC(10, 2);"))
        connection.execute(text("ALTER TABLE premios_funcionarios ADD COLUMN IF NOT EXISTS total_vlr NUMERIC(10, 2);"))
        connection.execute(text("ALTER TABLE premios_funcionarios ADD COLUMN IF NOT EXISTS vlr_premio NUMERIC(10, 2);"))
        connection.execute(text("ALTER TABLE premios_funcionarios ADD COLUMN IF NOT EXISTS valor_rs NUMERIC(10, 2);"))
        connection.execute(text("ALTER TABLE premios_funcionarios ADD COLUMN IF NOT EXISTS pix TEXT;"))
        connection.execute(text("ALTER TABLE premios_funcionarios ADD COLUMN IF NOT EXISTS taxa_zaut NUMERIC(10, 2);"))
        connection.commit()

criar_tabelas()

st.set_page_config(page_title="BRAGANÇA SYS ERP", page_icon="🧊", layout="wide", initial_sidebar_state="expanded")

from pages import cadastros as gestao_cadastros_page
from pages import importacao_inteligente
from pages import premios as premios_page

st.sidebar.title("Navegação")
selection = st.sidebar.radio("Ir para", ["Visão Geral", "Importação Inteligente", "Gestão de Cadastros", "Gestão de Prêmios (ZAUT)", "Auditoria CCT (IA)"])

if selection == "Visão Geral":
    st.title("Visão Geral do Sistema")
elif selection == "Importação Inteligente":
    importacao_inteligente.render(engine, ler_planilha_inteligente, parse_br_date_smart, format_cpf, format_competencia_smart, LISTA_SITUACOES_ESOCIAL)
elif selection == "Gestão de Cadastros":
    gestao_cadastros_page.render(engine, parse_br_date_smart, format_cpf, LISTA_SITUACOES_ESOCIAL)
elif selection == "Gestão de Prêmios (ZAUT)":
    premios_page.render(engine, parse_br_date_smart)
elif selection == "Auditoria CCT (IA)":
    st.title("Auditoria CCT (IA)")
