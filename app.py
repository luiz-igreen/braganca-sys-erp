import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import re
from datetime import datetime, date
import calendar
import io
import json
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO INICIAL E CONEXÃO ---
st.set_page_config(page_title="BRAGANÇA SYS | ERP", page_icon="🏗️", layout="wide")
engine = create_engine(st.secrets["DATABASE_URL"])

# --- 2. MOTOR DE HIGIENE DE DADOS (AUTO-LIMPEZA) ---
def realizar_limpeza_base():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM historico_situacoes WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id IS NULL OR TRIM(CAST(id AS TEXT)) = '' OR CAST(id AS TEXT) ILIKE 'nan' OR CAST(id AS TEXT) ILIKE 'none'"))

realizar_limpeza_base()

# --- 3. UTILITÁRIOS ---
def format_cpf(cpf_str):
    if not cpf_str or str(cpf_str).strip().lower() in ["nan", "none", ""]: return ""
    s = str(cpf_str).strip()
    if s.endswith('.0'): s = s[:-2]
    v = re.sub(r'\D', '', s)
    if not v: return ""
    v = v.zfill(11)
    return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}" if len(v) == 11 else str(cpf_str)

def ler_planilha_inteligente(arquivo, nrows=None, header=0):
    file_bytes = arquivo.getvalue()
    try: return pd.read_excel(io.BytesIO(file_bytes), header=header, nrows=nrows)
    except: pass
    try: return pd.read_csv(io.BytesIO(file_bytes), sep=',', encoding='latin1', header=header, nrows=nrows, on_bad_lines='skip', low_memory=False)
    except: pass
    try: return pd.read_csv(io.BytesIO(file_bytes), sep=';', encoding='latin1', header=header, nrows=nrows, on_bad_lines='skip', low_memory=False)
    except: pass
    try:
        str_data = file_bytes.decode('latin1', errors='ignore')
        dfs = pd.read_html(io.StringIO(str_data), header=header)
        if dfs: return dfs[0].head(nrows) if nrows else dfs[0]
    except: pass
    raise ValueError("Formato de ficheiro não reconhecido.")

# --- 4. LISTAS E CONFIGURAÇÕES ---
LISTA_CARGOS = ["PEDREIRO", "SERVENTE", "AJUDANTE PRATICO", "CARPINTEIRO", "PINTOR", "ELETRICISTA", "ENCANADOR", "MESTRE DE OBRAS", "ENCARREGADO", "APRENDIZ LEGAL EM ARCO ADMINISTRATIVO", "ESTAGIÁRIO", "OUTRO (DIGITAR MANUALMENTE)"]
LISTA_SERVICOS_PREMIO = ["211 PRÊMIO META CRONOGRAMA", "212 PRÊMIO REVESTIMENTO EXTERNO", "213 PRÊMIO PINTURA", "215 PRÊMIO INSTALAÇÕES", "216 PRÊMIO REVESTIMENTO INTERNO", "225 PREMIO ESTRUTURA", "OUTRO (DIGITAR MANUALMENTE)"]
LISTA_SITUACOES_ESOCIAL = ["1 - Trabalhando", "2 - Afastado Direitos Integrais", "3 - Acid. Trabalho periodo superior a 15 dias", "4 - Servico Militar", "5 - Licenca maternidade", "6 - Doenca periodo superior a 15 dias", "7 - Licenca sem Vencimento", "8 - Demitido", "9 - Ferias", "10 - Novo afast. mesmo acid. trabalho", "11 - Antecipacao e/ou prorrogacao Licenca Maternidade", "12 - Novo afast. mesma doenca", "13 - Exercicio de mandato sindical", "14 - Aposent. por invalid. acidente de trabalho", "15 - Aposent. por invalid. doenca profissional", "16 - Aposent. por invalid. exceto acid. trabalho", "17 - Acid. Trabalho periodo igual ou inferior a 15 dias", "18 - Doenca periodo igual ou inferior a 15 dias", "19 - Aborto nao criminoso", "20 - Licenca maternidade adocao 1 ano", "21 - Licenca maternidade adocao 1 a 4 anos", "22 - Licenca maternidade adocao 4 a 8 anos", "23 - Transferido", "24 - Outros motivos de afastamento", "39 - Ausência Justificada", "8136 - Licença Paternidade", "90 - Suspensão contratual decorrente de forca maior", "91 - Suspensão contratual para inquerito falta grave"]

# --- 5. INTERFACE ---
st.markdown("<h3 style='text-align: center; color: #f8fafc;'>🏗️ BRAGANÇA SYS | ERP</h3>", unsafe_allow_html=True)
menu = st.radio("Menu", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros"], horizontal=True)
st.markdown("---")

if menu == "📥 Importação Inteligente":
    aba_imp1, aba_imp2, aba_imp3, aba_imp4, aba_imp5 = st.tabs(["Base", "ETL", "eSocial", "CPFs", "Leitor IA"])
    
    with aba_imp5:
        st.subheader("🤖 Injeção Universal de Histórico (JSON)")
        pacote_ia = st.text_area("Cole o Pacote JSON aqui:", height=200)
        if st.button("🚀 Executar Injeção", type="primary"):
            if pacote_ia.strip():
                try:
                    dados = json.loads(pacote_ia)
                    with engine.begin() as conn:
                        for colab in dados:
                            v_id = str(colab['id'])
                            conn.execute(text("DELETE FROM historico_situacoes WHERE id_colaborador = :id"), {"id": v_id})
                            for ev in colab['eventos']:
                                conn.execute(text("INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) VALUES (:id, :dt, :desc)"), {"id": v_id, "dt": ev[0], "desc": ev[1]})
                    st.success("✅ Histórico reconstruído com sucesso!")
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

# ... (MANTENHA AQUI TODO O SEU RESTANTE CÓDIGO DE VISÃO GERAL E GESTÃO)
