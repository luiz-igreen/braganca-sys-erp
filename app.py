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

# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- MIGRAÇÃO AUTOMÁTICA ---
try:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_salarial (
                id SERIAL PRIMARY KEY,
                id_colaborador VARCHAR(50),
                data_alteracao DATE,
                motivo VARCHAR(100),
                salario_anterior VARCHAR(50),
                novo_salario VARCHAR(50)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_afastamentos (
                id SERIAL PRIMARY KEY,
                id_colaborador VARCHAR(50),
                data_inicio DATE,
                data_fim DATE,
                codigo_situacao VARCHAR(200),
                observacao TEXT
            )
        """))
except Exception as e: st.error(f"Erro ao inicializar tabelas: {e}")

try:
    with engine.begin() as conn:
        correcoes_esocial = {
            "6 - Doença": "6 - Doenca periodo superior a 15 dias",
            "6 - Doenca periodo igual ou superior a 15 dias": "6 - Doenca periodo superior a 15 dias",
            "18 - Doença": "18 - Doenca periodo igual ou inferior a 15 dias",
        }
        for errado, correto in correcoes_esocial.items():
            conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = :c WHERE situacao = :e"), {"c": correto, "e": errado})
            conn.execute(text("UPDATE historico_afastamentos SET codigo_situacao = :c WHERE codigo_situacao = :e"), {"c": correto, "e": errado})
except: pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS data_afastamento VARCHAR(50);"))
except: pass
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS data_retorno VARCHAR(50);"))
except: pass
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS situacao VARCHAR(100) DEFAULT '1 - Trabalhando';"))
        conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = '8 - Demitido' WHERE demissao IS NOT NULL AND (situacao IS NULL OR situacao = '');"))
        conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = '1 - Trabalhando' WHERE demissao IS NULL AND (situacao IS NULL OR situacao = '');"))
except: pass

try:
    with engine.begin() as conn:
        cnt = conn.execute(text("SELECT COUNT(*) FROM historico_afastamentos")).fetchone()[0]
        if cnt == 0:
            conn.execute(text("""
                INSERT INTO historico_afastamentos (id_colaborador, data_inicio, codigo_situacao) 
                SELECT id, COALESCE(CAST(NULLIF(data_afastamento, '') AS DATE), CAST(NULLIF(admissao, '') AS DATE), CURRENT_DATE), situacao 
                FROM cadastro_geral_colaborador 
                WHERE situacao IS NOT NULL AND situacao != ''
            """))
except: pass

try:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM historico_afastamentos WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id IS NULL OR TRIM(CAST(id AS TEXT)) = '' OR CAST(id AS TEXT) ILIKE 'nan' OR CAST(id AS TEXT) ILIKE 'none'"))
except: pass

# --- ESTILIZAÇÃO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .panel-glass { 
        background: rgba(30, 41, 59, 0.45); 
        border: 1px solid rgba(51, 65, 85, 0.7); 
        padding: 25px; 
        border-radius: 16px; 
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; padding-left: 5px; padding-right: 5px; }
    .field-label { color: #94a3b8; font-size: 0.9rem; font-weight: bold; }
    .field-value { color: #f8fafc; font-size: 1.1rem; margin-bottom: 12px; background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }
    .field-highlight { color: #10b981; font-size: 1.4rem; font-weight: bold; margin-bottom: 12px; background: rgba(16, 185, 129, 0.1); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3); }
    .fake-label { color: #f8fafc; font-size: 0.85rem; font-weight: 500; margin-bottom: -15px; display: block; }
    div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none; }
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: center !important;
        gap: 10px !important;
        width: 100% !important;
    }
    div[data-testid="stRadio"] label {
        background: rgba(30, 41, 59, 0.8);
        padding: 10px 16px;
        border-radius: 8px;
        border: 1px solid rgba(51, 65, 85, 0.8);
        color: #cbd5e1;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.85rem;
        transition: all 0.2s ease-in-out;
        white-space: nowrap;
        flex: 1;
        text-align: center;
    }
    div[data-testid="stRadio"] label:hover { background: rgba(59, 130, 246, 0.1); border-color: #3b82f6; }
    div[data-testid="stRadio"] label[data-testid="stWidgetSelected"] {
        background: #2563eb !important; color: #ffffff !important; border-color: #60a5fa !important; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
    }
    div[data-testid="stRadio"]:nth-of-type(2) > div { justify-content: center !important; gap: 16px !important; }
    div[data-testid="stRadio"]:nth-of-type(2) label { flex: 0 1 auto !important; min-width: 200px; }
    button[kind="primary"] { background-color: #2563eb !important; border-color: #2563eb !important; color: #ffffff !important; }
    button[kind="primary"]:hover { background-color: #1d4ed8 !important; border-color: #1d4ed8 !important; }
    section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- JAVASCRIPT ---
components.html("""
<script>
const doc = window.parent.document;
const setNativeValue = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
setInterval(function(){
    doc.querySelectorAll('input').forEach(function(el){
        el.setAttribute('autocomplete', 'new-password');
        el.setAttribute('autofill', 'off');
        if (!el.hasAttribute('data-name-set')) { el.setAttribute('name', 'input_' + Math.random().toString(36).substring(7)); el.setAttribute('data-name-set', 'true'); }
    });
    doc.querySelectorAll('input[aria-label="CPF"]').forEach(function(el){
        if (!el.hasAttribute('data-cpf-mask')) {
            el.setAttribute('data-cpf-mask', 'true');
            el.addEventListener('input', function(e) {
                let v = e.target.value.replace(/\D/g, '');
                if(v.length > 11) v = v.substring(0, 11);
                let f = v;
                if(v.length > 9) f = v.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, "$1.$2.$3-$4");
                else if(v.length > 6) f = v.replace(/(\d{3})(\d{3})(\d{1,3})/, "$1.$2.$3");
                else if(v.length > 3) f = v.replace(/(\d{3})(\d{1,3})/, "$1.$2");
                if (e.target.value !== f) {
                    setNativeValue.call(e.target, f);
                    e.target.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }
    });
}, 150);
if (!window.parent.CustomKeyboardNav) {
    window.parent.CustomKeyboardNav = true;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            if (e.ctrlKey) {
                e.preventDefault();
                var saveBtn = doc.querySelector('button[kind="primary"]');
                if (saveBtn && !saveBtn.disabled) saveBtn.click();
                return;
            }
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'TEXTAREA' || e.target.getAttribute('aria-expanded') === 'true' || e.target.closest('[data-testid="stDataFrame"]')) { return; }
            e.preventDefault(); e.stopPropagation();
            var selectors = 'input:not([disabled]):not([type="hidden"]), button:not([disabled]), textarea:not([disabled]), [tabindex="0"]:not([disabled])';
            var focusable = Array.from(doc.querySelectorAll(selectors)).filter(el => (el.offsetWidth > 0 || el.offsetHeight > 0) && el.style.display !== 'none' && el.style.visibility !== 'hidden');
            var index = focusable.indexOf(e.target);
            if (index > -1 && index < focusable.length - 1) {
                var nextEl = focusable[index + 1]; 
                nextEl.focus();
                if (nextEl.tagName === 'INPUT' && (nextEl.type === 'text' || nextEl.type === 'number')) { setTimeout(() => nextEl.select(), 10); }
            }
        }
    }, true); 
}
</script>
""", height=0, width=0)

# --- FUNÇÕES UTILITÁRIAS ---
def injetar_autofoco(pular_busca=False, painel=""):
    pular_js = "true" if pular_busca else "false"
    components.html(f"""
    <script>
    setTimeout(function() {{
        var doc = window.parent.document;
        var inputs = Array.from(doc.querySelectorAll('input[type="text"]:not([disabled]), input[type="number"]:not([disabled])')).filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);
        if(inputs.length > 0) {{
            if({pular_js} && inputs.length > 1) {{ inputs[1].focus(); }} 
            else {{ inputs[0].focus(); }}
        }}
    }}, 400);
    </script>
    """, height=0, width=0)

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
        if dfs:
            df = dfs[0]
            if nrows is not None: df = df.head(nrows)
            return df
    except: pass
    raise ValueError("O arquivo não pode ser lido. Abra no Excel e salve como '.xlsx', depois tente de novo!")

def clean_money_to_db(val):
    if not val or str(val).strip() == "" or str(val).strip().lower() == "none": return None
    s = str(val).upper().replace('R$', '').strip()
    if '.' in s and ',' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    try: return str(float(s))
    except: return None

def format_brl_number(val):
    try:
        if val is None or str(val).strip() == "" or str(val).lower() in ["nan", "none"]: return ""
        return f"{float(val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return val

def format_currency_brl(val):
    try:
        if val is None or str(val).strip() == "" or str(val).lower() in ["nan", "none"]: return ""
        return f"R$ {float(val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return val

def parse_br_date_smart(d_input):
    if not d_input or str(d_input).strip() == "" or str(d_input).lower() in ["none", "nat", "nan"]: return None
    s = str(d_input).strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        try: return pd.to_datetime(s).date()
        except: return None
    digitos = re.sub(r'[^\d]', '', s)
    if len(digitos) == 8:
        try: return date(int(digitos[4:8]), int(digitos[2:4]), int(digitos[0:2]))
        except: pass
    elif len(digitos) == 6:
        try: return date(2000 + int(digitos[4:6]), int(digitos[2:4]), int(digitos[0:2]))
        except: pass
    try: return pd.to_datetime(s, dayfirst=True).date()
    except: return None

def format_date_br(d_val):
    if not d_val or pd.isna(d_val) or str(d_val).lower() in ["none", "nat", "nan"]: return ""
    try: return pd.to_datetime(d_val).strftime("%d/%m/%Y")
    except: return ""

def format_competencia_smart(val):
    if not val or str(val).strip() == "" or str(val).lower() in ["none", "nan"]: return ""
    s = str(val).strip()
    if '/' in s:
        p = s.split('/')
        if len(p) == 2: return f"{p[0].zfill(2)}/{'20'+p[1] if len(p[1])==2 else p[1]}"
        return s
    digitos = re.sub(r'[^\d]', '', s)
    if len(digitos) == 6: return f"{digitos[:2].zfill(2)}/{digitos[2:]}"
    elif len(digitos) == 4: return f"{digitos[:2].zfill(2)}/20{digitos[2:]}"
    return s

def sort_historico_chronological(df):
    if not df.empty and 'competencia' in df.columns:
        df['competencia'] = df['competencia'].apply(format_competencia_smart)
        df['data_ordenacao'] = pd.to_datetime(df['competencia'], format='%m/%Y', errors='coerce')
        df = df.sort_values(by=['data_ordenacao', 'id'], ascending=[False, False]).drop(columns=['data_ordenacao'])
    return df

def format_cpf(cpf_str):
    if not cpf_str or str(cpf_str).strip().lower() in ["nan", "none", ""]: return ""
    s = str(cpf_str).strip()
    if s.endswith('.0'): s = s[:-2]
    v = re.sub(r'\D', '', s)
    if not v: return ""
    v = v.zfill(11)
    if len(v) == 11: return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
    return str(cpf_str)

LISTA_CARGOS = [
    "PEDREIRO", "SERVENTE", "AJUDANTE PRATICO", "CARPINTEIRO", "PINTOR", "ELETRICISTA",
    "ENCANADOR", "MESTRE DE OBRAS", "ENCARREGADO",
    "APRENDIZ LEGAL EM ARCO ADMINISTRATIVO", "ESTAGIÁRIO", "OUTRO (DIGITAR MANUALMENTE)"
]

LISTA_SERVICOS_PREMIO = [
    "211 PRÊMIO META CRONOGRAMA", "212 PRÊMIO REVESTIMENTO EXTERNO", "213 PRÊMIO PINTURA",
    "215 PRÊMIO INSTALAÇÕES", "216 PRÊMIO REVESTIMENTO INTERNO", "225 PREMIO ESTRUTURA", "OUTRO (DIGITAR MANUALMENTE)"
]

LISTA_SITUACOES_ESOCIAL = [
    "1 - Trabalhando", "2 - Afastado Direitos Integrais",
    "3 - Acid. Trabalho periodo superior a 15 dias", "4 - Servico Militar",
    "5 - Licenca maternidade", "6 - Doenca periodo superior a 15 dias",
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
    from pages.cadastros import render
    render(engine, injetar_autofoco, parse_br_date_smart, format_date_br, format_currency_brl, format_brl_number, format_cpf, format_competencia_smart, clean_money_to_db, sort_historico_chronological, LISTA_CARGOS, LISTA_SITUACOES_ESOCIAL)

elif menu == "🏆 Gestão de Prêmios (ZAUT)":
    from pages.premios import render
    render(engine, format_brl_number, format_currency_brl, clean_money_to_db, injetar_autofoco, LISTA_SERVICOS_PREMIO)

elif menu == "🔎 Auditoria CCT (IA)":
    from pages.auditoria import render
    render(engine, clean_money_to_db, format_brl_number)
