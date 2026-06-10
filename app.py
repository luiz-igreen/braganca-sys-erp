import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import re
from datetime import datetime, date
import calendar
import uuid
import io
import json
import streamlit.components.v1 as components
import numpy as np # Adicionado para pd.NA e np.nan

# --- FUNÇÕES AUXILIARES (MOVIDAS PARA O INÍCIO) ---
def format_brl_number(value):
    if pd.isna(value): return "-"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_currency_brl(value):
    if pd.isna(value): return "R$ -"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def clean_money_to_db(money_str):
    if isinstance(money_str, (int, float)):
        return money_str
    if not money_str:
        return None
    clean_str = money_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(clean_str)
    except ValueError:
        return None

def parse_br_date_smart(date_str):
    if pd.isna(date_str) or not date_str:
        return None
    if isinstance(date_str, date):
        return date_str
    if isinstance(date_str, datetime):
        return date_str.date()

    date_str = str(date_str).strip()

    # Tenta formatos comuns
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    # Tenta com ano de 2 dígitos
    for fmt in ('%d/%m/%y', '%d-%m-%y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    # Tenta com mês abreviado (ex: 01-Jan-2023)
    try:
        return datetime.strptime(date_str, '%d-%b-%Y').date()
    except ValueError:
        pass

    # Se for apenas o ano (ex: 2023), retorna o primeiro dia do ano
    if re.fullmatch(r'\d{4}', date_str):
        try:
            return date(int(date_str), 1, 1)
        except ValueError:
            pass

    # Se for apenas mês e ano (ex: 01/2023), retorna o primeiro dia do mês
    if re.fullmatch(r'\d{2}/\d{4}', date_str):
        try:
            mes, ano = map(int, date_str.split('/'))
            return date(ano, mes, 1)
        except ValueError:
            pass

    # Se for um número que pode ser um timestamp (ex: 44927.0)
    try:
        if re.fullmatch(r'\d+\.?\d*', date_str):
            excel_date = float(date_str)
            # Excel epoch is 1899-12-30. Python's epoch is 1970-01-01.
            # Convert Excel serial date to datetime object
            return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2).date()
    except ValueError:
        pass

    st.warning(f"Formato de data desconhecido: {date_str}. Retornando None.")
    return None

def format_date_br(date_obj):
    if pd.isna(date_obj) or not date_obj:
        return "-"
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d/%m/%Y')
    if isinstance(date_obj, date):
        return date_obj.strftime('%d/%m/%Y')
    return str(date_obj)

def format_cpf(cpf_str):
    if pd.isna(cpf_str) or not cpf_str:
        return "-"
    cpf_digits = re.sub(r'\D', '', str(cpf_str))
    if len(cpf_digits) == 11:
        return f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"
    return cpf_digits # Retorna apenas os dígitos para consistência com o ID

def format_competencia_smart(competencia_str):
    if pd.isna(competencia_str) or not competencia_str:
        return "-"
    competencia_str = str(competencia_str).strip()
    if re.fullmatch(r'\d{4}-\d{2}', competencia_str): # Formato YYYY-MM
        return datetime.strptime(competencia_str, '%Y-%m').strftime('%m/%Y')
    if re.fullmatch(r'\d{2}/\d{4}', competencia_str): # Formato MM/YYYY
        return competencia_str
    if re.fullmatch(r'\d{6}', competencia_str): # Formato MMYYYY
        return f"{competencia_str[:2]}/{competencia_str[2:]}"
    return competencia_str

def ler_planilha_inteligente(uploaded_file):
    if uploaded_file is None:
        return None

    file_name = uploaded_file.name
    df = None

    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif file_name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Formato de arquivo não suportado. Por favor, envie um arquivo CSV ou Excel.")
            return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return None

    # Padronizar nomes de colunas para minúsculas e sem acentos/caracteres especiais
    df.columns = [re.sub(r'[^a-z0-9_]', '', col.lower().replace(' ', '_')) for col in df.columns]

    return df

def sort_historico_chronological(df_historico):
    if 'data_alteracao' in df_historico.columns:
        df_historico['data_alteracao'] = pd.to_datetime(df_historico['data_alteracao'], errors='coerce')
        df_historico = df_historico.sort_values(by='data_alteracao', ascending=False).reset_index(drop=True)
    elif 'data_inicio' in df_historico.columns:
        df_historico['data_inicio'] = pd.to_datetime(df_historico['data_inicio'], errors='coerce')
        df_historico = df_historico.sort_values(by='data_inicio', ascending=False).reset_index(drop=True)
    return df_historico

def get_current_month_year():
    today = date.today()
    return today.strftime("%m/%Y")

# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

@st.cache_resource
def get_engine():
    # Acessa a DATABASE_URL do Streamlit Secrets
    # Agora busca diretamente a chave DATABASE_URL, como configurado nos secrets do Streamlit Cloud
    try:
        database_url = st.secrets["DATABASE_URL"]
    except KeyError:
        st.error("DATABASE_URL não encontrada nos Streamlit Secrets. Verifique a configuração.")
        st.stop()
    return create_engine(database_url)

engine = get_engine()

# --- MIGRAÇÃO AUTOMÁTICA E AJUSTES DE TABELAS ---
# Esta seção tenta criar tabelas e ajustar colunas.
# As mensagens de sucesso/erro são importantes para depuração inicial,
# mas podem ser removidas ou transformadas em logs mais tarde.

try:
    with engine.begin() as conn:
        # Criação da tabela historico_afastamentos
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_afastamentos (
                id SERIAL PRIMARY KEY,
                id_colaborador VARCHAR(50),
                data_inicio DATE,
                data_fim DATE,
                tipo_afastamento VARCHAR(200),
                observacao TEXT
            )
        """))
        # Criação da tabela cadastro_financeiro_colaborador
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cadastro_financeiro_colaborador (
                id SERIAL PRIMARY KEY,
                id_colaborador VARCHAR(50) UNIQUE,
                banco VARCHAR(100),
                agencia VARCHAR(20),
                conta VARCHAR(50),
                tipo_conta VARCHAR(50),
                chave_pix VARCHAR(255)
            )
        """))
        # Criação da tabela historico_premiacoes_e_folha
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_premiacoes_e_folha (
                id SERIAL PRIMARY KEY,
                id_colaborador VARCHAR(50),
                competencia VARCHAR(7),
                tipo_lancamento VARCHAR(100),
                valor_lancamento NUMERIC(10, 2),
                status_pagamento VARCHAR(50),
                retroativo_pago BOOLEAN DEFAULT FALSE,
                data_pagamento DATE
            )
        """))
        # Criação da tabela cadastro_geral_colaborador
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cadastro_geral_colaborador (
                id VARCHAR(50) PRIMARY KEY,
                nome VARCHAR(255),
                cpf VARCHAR(14),
                cargo VARCHAR(100),
                admissao DATE,
                demissao DATE,
                status_esocial VARCHAR(100),
                salario_mes_12_24 NUMERIC(10, 2),
                salario_hora_12_24 NUMERIC(10, 2)
            )
        """))
    # st.success("Tabelas verificadas/criadas com sucesso.") # Comentado para reduzir mensagens na inicialização
except Exception as e:
    st.error(f"Erro ao inicializar tabelas: {e}")

# Renomear coluna 'situacao' para 'status_esocial' se existir e não houver 'status_esocial'
try:
    with engine.begin() as conn:
        # Verifica se 'situacao' existe e 'status_esocial' não existe
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'cadastro_geral_colaborador' AND column_name = 'situacao';
        """)).fetchone()
        if result:
            result_new = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'cadastro_geral_colaborador' AND column_name = 'status_esocial';
            """)).fetchone()
            if not result_new:
                conn.execute(text("ALTER TABLE cadastro_geral_colaborador RENAME COLUMN situacao TO status_esocial;"))
                st.success("Coluna 'situacao' renomeada para 'status_esocial'.")
            else:
                st.info("Coluna 'status_esocial' já existe. 'situacao' não foi renomeada.")
        else:
            st.info("Coluna 'situacao' não encontrada para renomear.")
except Exception as e:
    st.warning(f"Erro ao tentar renomear 'situacao' para 'status_esocial': {e}")

# Renomear coluna 'salario_hora' para 'salario_hora_12_24' se existir e não houver 'salario_hora_12_24'
try:
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'cadastro_geral_colaborador' AND column_name = 'salario_hora';
        """)).fetchone()
        if result:
            result_new = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'cadastro_geral_colaborador' AND column_name = 'salario_hora_12_24';
            """)).fetchone()
            if not result_new:
                conn.execute(text("ALTER TABLE cadastro_geral_colaborador RENAME COLUMN salario_hora TO salario_hora_12_24;"))
                st.success("Coluna 'salario_hora' renomeada para 'salario_hora_12_24'.")
            else:
                st.info("Coluna 'salario_hora_12_24' já existe. 'salario_hora' não foi renomeada.")
        else:
            st.info("Coluna 'salario_hora' não encontrada para renomear.")
except Exception as e:
    st.warning(f"Erro ao tentar renomear 'salario_hora' para 'salario_hora_12_24': {e}")

# Remover colunas data_afastamento e data_retorno se existirem
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador DROP COLUMN IF EXISTS data_afastamento;"))
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador DROP COLUMN IF EXISTS data_retorno;"))
    st.success("Colunas 'data_afastamento' e 'data_retorno' removidas de 'cadastro_geral_colaborador'.")
except Exception as e:
    st.warning(f"Erro ao tentar remover colunas 'data_afastamento' ou 'data_retorno': {e}")

# Correções de valores de situações eSocial
try:
    with engine.begin() as conn:
        correcoes_esocial = {
            "6 - Doença": "6 - Doenca periodo superior a 15 dias",
            "6 - Doenca periodo igual ou superior a 15 dias": "6 - Doenca periodo igual ou superior a 15 dias",
            "18 - Doença": "18 - Doenca periodo igual ou inferior a 15 dias",
        }
        for errado, correto in correcoes_esocial.items():
            conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :c WHERE status_esocial = :e"), {"c": correto, "e": errado})
            conn.execute(text("UPDATE historico_afastamentos SET tipo_afastamento = :c WHERE tipo_afastamento = :e"), {"c": correto, "e": errado})
    st.success("Correções de situações eSocial aplicadas.")
except Exception as e:
    st.warning(f"Erro ao aplicar correções de situações eSocial: {e}")

# Adicionar colunas 'data_afastamento' e 'data_retorno' à tabela 'cadastro_geral_colaborador' se não existirem
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS data_afastamento DATE;"))
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS data_retorno DATE;"))
    st.success("Colunas 'data_afastamento' e 'data_retorno' adicionadas a 'cadastro_geral_colaborador'.")
except Exception as e:
    st.warning(f"Erro ao adicionar colunas 'data_afastamento' ou 'data_retorno': {e}")

# Preencher 'data_afastamento' e 'data_retorno' com base no histórico de afastamentos
try:
    with engine.begin() as conn:
        # Para data_afastamento: pegar a data_inicio do afastamento mais recente (se houver)
        conn.execute(text("""
            UPDATE cadastro_geral_colaborador cgc
            SET data_afastamento = (
                SELECT ha.data_inicio
                FROM historico_afastamentos ha
                WHERE ha.id_colaborador = cgc.id
                ORDER BY ha.data_inicio DESC
                LIMIT 1
            )
            WHERE cgc.data_afastamento IS NULL;
        """))
        # Para data_retorno: pegar a data_fim do afastamento mais recente (se houver)
        conn.execute(text("""
            UPDATE cadastro_geral_colaborador cgc
            SET data_retorno = (
                SELECT ha.data_fim
                FROM historico_afastamentos ha
                WHERE ha.id_colaborador = cgc.id
                ORDER BY ha.data_inicio DESC
                LIMIT 1
            )
            WHERE cgc.data_retorno IS NULL;
        """))
    st.success("Colunas 'data_afastamento' e 'data_retorno' preenchidas com base no histórico.")
except Exception as e:
    st.warning(f"Erro ao preencher 'data_afastamento' ou 'data_retorno': {e}")

# Migração de dados de afastamento da tabela antiga para a nova, se necessário
try:
    with engine.begin() as conn:
        # Verifica se a tabela historico_afastamentos está vazia
        cnt_afastamentos = conn.execute(text("SELECT COUNT(*) FROM historico_afastamentos")).fetchone()[0]
        if cnt_afastamentos == 0:
            # Verifica se a tabela cadastro_geral_colaborador tem dados de afastamento para migrar
            df_colaboradores_com_afastamento = pd.read_sql_query("""
                SELECT id, admissao, status_esocial, data_afastamento, data_retorno
                FROM cadastro_geral_colaborador
                WHERE status_esocial IS NOT NULL AND status_esocial != '' AND status_esocial != '1 - Trabalhando'
            """, conn)

            if not df_colaboradores_com_afastamento.empty:
                for index, row in df_colaboradores_com_afastamento.iterrows():
                    id_colaborador = row['id']

                    # --- CORREÇÃO AQUI: TRATAMENTO DE DATAS COM parse_br_date_smart ---
                    raw_data_afastamento = row['data_afastamento']
                    raw_admissao = row['admissao']

                    # Prioriza data_afastamento, se não, usa admissao
                    data_inicio_val = raw_data_afastamento if pd.notna(raw_data_afastamento) else raw_admissao
                    data_inicio = parse_br_date_smart(data_inicio_val) # Usa a função auxiliar

                    # Garante que data_fim seja um objeto date ou None
                    data_fim = parse_br_date_smart(row['data_retorno']) # Usa a função auxiliar
                    # --- FIM DA CORREÇÃO ---

                    tipo_afastamento = row['status_esocial']

                    if data_inicio and tipo_afastamento: # Apenas insere se tiver data de início válida e tipo de afastamento
                        conn.execute(text("""
                            INSERT INTO historico_afastamentos (id_colaborador, data_inicio, data_fim, tipo_afastamento)
                            VALUES (:id_colaborador, :data_inicio, :data_fim, :tipo_afastamento)
                        """), {
                            "id_colaborador": id_colaborador,
                            "data_inicio": data_inicio,
                            "data_fim": data_fim,
                            "tipo_afastamento": tipo_afastamento
                        })
                st.success("Dados de afastamento migrados para 'historico_afastamentos'.")
            else:
                st.info("Nenhum dado de afastamento para migrar.")
        else:
            st.info("Tabela 'historico_afastamentos' já contém dados, migração ignorada.")
except Exception as e:
    st.warning(f"Erro na migração de dados de afastamento: {e}")

# Limpeza de registros com ID nulo ou vazio em todas as tabelas
try:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM historico_afastamentos WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id IS NULL OR TRIM(CAST(id AS TEXT)) = '' OR CAST(id AS TEXT) ILIKE 'nan' OR CAST(id AS TEXT) ILIKE 'none'"))
    st.success("Registros com ID nulo/vazio limpos em todas as tabelas.")
except Exception as e:
    st.warning(f"Erro ao limpar registros com ID nulo/vazio: {e}")

# --- LISTAS DE OPÇÕES ---
LISTA_CARGOS = [
    "AJUDANTE PRATICO DE PEDREIRO", "AJUDANTE PRATICO CARPINTEIRO", "AJUDANTE PRAT DE ELETRICISTA",
    "AJUDANTE PRAT DE ENCANADOR", "AJUDANTE PRAT DE GESSEIRO", "ALMOXARIFE", "APRENDIZ LEGAL EM ARCO ADMINISTRATIVO",
    "ARMADOR", "ASSISTENTE ADMINISTRATIVO", "AUXILIAR DE ESCRITORIO", "AUXILIAR DE SERVICOS GERAIS",
    "CARPINTEIRO", "ELETRICISTA", "ENCANADOR", "ENCARREGADO DE OBRAS", "ENCARREGADO DE PEDREIRO",
    "ENCARREGADO DE PINTURA", "ENCARREGADO GERAL DE ELETRICISTA", "ESTAGIARIO DE ENGENHARIA",
    "ESTAGIARIO TÉCNICO EM SEGURANÇA NO TRABALHO", "GESSEIRO", "GUINCHEIRO", "MESTRE DE OBRAS",
    "MOTORISTA", "OPERADOR BETONEIRA", "OPERADOR DE RETROESCAVADEIRA", "PEDREIRO", "PINTOR",
    "SERVENTE DE OBRAS", "TEC DE SEGURANCA DO TRABALHO", "Técnico de Edificações"
]

LISTA_SERVICOS_PREMIO = [
    "PRODUÇÃO", "QUALIDADE", "SEGURANÇA", "ASSIDUIDADE", "OUTROS"
]

LISTA_SITUACOES_ESOCIAL = [
    "1 - Trabalhando", "2 - Acidente/Doença não relacionada ao trabalho",
    "3 - Acidente de trabalho", "4 - Doença relacionada ao trabalho",
    "5 - Licença maternidade", "6 - Doenca periodo superior a 15 dias",
    "7 - Licenca sem Vencimento", "8 - Demitido", "8136 - Licença paternidade",
    "8701 - Ausencia justificada", "9 - Ferias",
    "10 - Novo afast. mesmo acid. trabalho",
    "11 - Antecipacao e/ou prorrogacao Licenca Maternidade",
    "12 - Novo afast. mesma doenca", "13 - Exercicio de mandato sindical",
    "14 - Aposent. por invalid. acidente de trabalho",
    "15 - Aposent. por invalid. doenca profissional",
    "16 - Aposent. por invalid. exceto acid. trab. e doenca profissional",
    "17 - Acid. Trabalho periodo igual ou inferior a 15 dias",
    "18 - Doenca periodo igual ou inferior a 15 dias", "19 - Aborto nao criminoso",
    "20 - Licenca maternidade adocao 1 ano", "21 - Licenca maternidade adocao 1 a 4 anos",
    "22 - Licenca maternidade adocao 4 a 8 anos", "24 - Outros motivos de afastamento",
    "90 - Suspensão contratual decorrente ação trabalhista por rescisão indireta",
    "91 - Suspensão contratual para inquérito de apuração de falta grave"
]

# --- SESSION STATE ---
for k in ['busca_selecionada_id', 'status_acao', 'zaut_acao']:
    if k not in st.session_state: st.session_state[k] = None
if 'sub_menu_index' not in st.session_state: st.session_state['sub_menu_index'] = 0
if 'redirect_to_consulta' not in st.session_state: st.session_state['redirect_to_consulta'] = False

if st.session_state['redirect_to_consulta']:
    st.session_state['sub_menu_index'] = 0
    st.session_state['redirect_to_consulta'] = False
    st.rerun()

# --- CABEÇALHO E MENU ---
st.markdown("<h3 style='text-align: center; color: #f8fafc; margin-bottom: 10px; margin-top: -30px;'>🏗️ BRAGANÇA SYS <span style='color: #3b82f6;'>| ERP</span></h3>", unsafe_allow_html=True)
menu = st.radio("Menu Principal", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros", "🏆 Gestão de Prêmios (ZAUT)", "🔎 Auditoria CCT (IA)"], horizontal=True, label_visibility="collapsed")
st.markdown("---")

# --- ROTEAMENTO PARA AS PÁGINAS ---
if menu == "👥 Visão Geral":
    from pages.visao_geral import render
    render(engine, parse_br_date_smart, format_currency_brl, format_cpf, clean_money_to_db)

elif menu == "📥 Importação Inteligente":
    from pages.importacao import render
    render(engine, ler_planilha_inteligente, parse_br_date_smart, format_cpf, format_competencia_smart, LISTA_SITUACOES_ESOCIAL)

elif menu == "🛠️ Gestão de Cadastros":
    # CORREÇÃO AQUI: O arquivo é 'cadastros.py', não 'gestao_cadastros.py'
    from pages.cadastros import render
    # injetar_autofoco não está definido neste app.py, então foi removido da chamada
    render(engine, parse_br_date_smart, format_date_br, format_currency_brl, format_brl_number, format_cpf, format_competencia_smart, clean_money_to_db, sort_historico_chronological, LISTA_CARGOS, LISTA_SITUACOES_ESOCIAL)

elif menu == "🏆 Gestão de Prêmios (ZAUT)":
    from pages.premios import render
    # injetar_autofoco não está definido neste app.py, então foi removido da chamada
    render(engine, format_brl_number, format_currency_brl, clean_money_to_db, LISTA_SERVICOS_PREMIO)

elif menu == "🔎 Auditoria CCT (IA)":
    from pages.auditoria import render
    render(engine, clean_money_to_db, format_brl_number)
