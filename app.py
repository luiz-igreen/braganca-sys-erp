import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import re
from datetime import datetime, date
import calendar
from dateutil.relativedelta import relativedelta
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

# Conexão segura com o Banco de Dados
engine = create_engine(st.secrets["DATABASE_URL"])

# --- MIGRAÇÃO AUTOMÁTICA DE BANCO DE DADOS (INSS, HISTÓRICOS E SITUAÇÃO) ---
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
            CREATE TABLE IF NOT EXISTS historico_situacoes (
                id SERIAL PRIMARY KEY,
                id_colaborador VARCHAR(50),
                data_evento DATE,
                descricao VARCHAR(200)
            )
        """))
except Exception as e: st.error(f"Erro ao inicializar tabelas: {e}")

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN data_afastamento VARCHAR(50);"))
except: pass 
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN data_retorno VARCHAR(50);"))
except: pass 
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN situacao VARCHAR(100) DEFAULT '1 - Trabalhando';"))
        conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = '8 - Demitido' WHERE demissao IS NOT NULL AND (situacao IS NULL OR situacao = '');"))
        conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = '1 - Trabalhando' WHERE demissao IS NULL AND (situacao IS NULL OR situacao = '');"))
except: pass

try:
    with engine.begin() as conn:
        cnt = conn.execute(text("SELECT COUNT(*) FROM historico_situacoes")).fetchone()[0]
        if cnt == 0:
            conn.execute(text("""
                INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) 
                SELECT id, COALESCE(CAST(NULLIF(data_afastamento, '') AS DATE), CAST(NULLIF(admissao, '') AS DATE), CURRENT_DATE), situacao 
                FROM cadastro_geral_colaborador 
                WHERE situacao IS NOT NULL AND situacao != ''
            """))
except: pass

# --- ESTILIZAÇÃO VISUAL AVANÇADA (MENU HORIZONTAL E GLASSMORPHISM) ---
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
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .field-label { color: #94a3b8; font-size: 0.9rem; font-weight: bold; }
    .field-value { color: #f8fafc; font-size: 1.1rem; margin-bottom: 12px; background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }
    .field-highlight { color: #10b981; font-size: 1.4rem; font-weight: bold; margin-bottom: 12px; background: rgba(16, 185, 129, 0.1); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3); }
    
    .fake-label { color: #f8fafc; font-size: 0.85rem; font-weight: 500; margin-bottom: -15px; display: block; }

    div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none; }
    div[data-testid="stRadio"] > div { flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 12px; }
    div[data-testid="stRadio"] label {
        background: rgba(30, 41, 59, 0.8); padding: 12px 24px; border-radius: 8px; border: 1px solid rgba(51, 65, 85, 0.8);
        color: #cbd5e1; cursor: pointer; font-weight: 600; transition: all 0.2s ease-in-out;
    }
    div[data-testid="stRadio"] label:hover { background: rgba(59, 130, 246, 0.1); border-color: #3b82f6; }
    div[data-testid="stRadio"] label[data-testid="stWidgetSelected"] {
        background: #2563eb !important; color: #ffffff !important; border-color: #60a5fa !important; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
    }
    
    section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- INJEÇÃO DE JAVASCRIPT PROFISSIONAL ---
components.html("""
<script>
const doc = window.parent.document;
setInterval(function(){
    doc.querySelectorAll('input').forEach(function(el){
        el.setAttribute('autocomplete', 'new-password');
        el.setAttribute('autofill', 'off');
        if (!el.hasAttribute('data-name-set')) { el.setAttribute('name', 'input_' + Math.random().toString(36).substring(7)); el.setAttribute('data-name-set', 'true'); }
    });
}, 150);
if (!window.parent.EnterToTabInjected) {
    window.parent.EnterToTabInjected = true;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'TEXTAREA' || e.target.getAttribute('aria-expanded') === 'true') return;
            e.preventDefault(); e.stopPropagation();
            var selectors = 'input:not([disabled]):not([type="hidden"]), button:not([disabled]), textarea:not([disabled]), [tabindex="0"]:not([disabled])';
            var focusable = Array.from(doc.querySelectorAll(selectors)).filter(el => (el.offsetWidth > 0 || el.offsetHeight > 0) && el.style.display !== 'none' && el.style.visibility !== 'hidden');
            var index = focusable.indexOf(e.target);
            if (index > -1 && index < focusable.length - 1) {
                var nextEl = focusable[index + 1]; nextEl.focus();
                if (nextEl.tagName === 'INPUT' && (nextEl.type === 'text' || nextEl.type === 'number')) { setTimeout(() => nextEl.select(), 10); }
            }
        }
    }, true); 
}
</script>
""", height=0, width=0)

# --- LISTAS PADRÃO ---
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
    "1 - Trabalhando", "2 - Afastado Direitos Integrais", "3 - Acid. Trabalho periodo superior a 15 dias",
    "4 - Servico Militar", "5 - Licenca maternidade", "6 - Doenca periodo superior a 15 dias",
    "7 - Licenca sem Vencimento", "8 - Demitido", "9 - Ferias", "10 - Novo afast. mesmo acid. trabalho",
    "11 - Antecipacao e/ou prorrogacao Licenca Maternidade", "12 - Novo afast. mesma doenca",
    "13 - Exercicio de mandato sindical", "14 - Aposent. por invalid. acidente de trabalho",
    "15 - Aposent. por invalid. doenca profissional", "16 - Aposent. por invalid. exceto acid. trabalho",
    "17 - Acid. Trabalho periodo igual ou inferior a 15 dias", "18 - Doenca periodo igual ou inferior a 15 dias",
    "19 - Aborto nao criminoso", "20 - Licenca maternidade adocao 1 ano", "21 - Licenca maternidade adocao 1 a 4 anos",
    "22 - Licenca maternidade adocao 4 a 8 anos", "23 - Transferido", "24 - Outros motivos de afastamento",
    "90 - Suspensão contratual decorrente de forca maior", "91 - Suspensão contratual para inquerito falta grave"
]

# --- GERENCIADOR DE SESSÃO E ROTEAMENTO SPA ---
for k in ['busca_selecionada_id', 'status_acao', 'zaut_acao']:
    if k not in st.session_state: st.session_state[k] = None
if 'sub_menu_index' not in st.session_state: st.session_state['sub_menu_index'] = 0
if 'redirect_to_consulta' not in st.session_state: st.session_state['redirect_to_consulta'] = False

if st.session_state['redirect_to_consulta']:
    st.session_state['sub_menu_index'] = 0; st.session_state['redirect_to_consulta'] = False; st.rerun()

# --- FUNÇÕES INTELIGENTES ---
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

# ==========================================
# MENU SUPERIOR HORIZONTAL EXCLUSIVO
# ==========================================
st.markdown("<h3 style='text-align: center; color: #f8fafc; margin-bottom: 10px; margin-top: -30px;'>🏗️ BRAGANÇA SYS <span style='color: #3b82f6;'>| ERP</span></h3>", unsafe_allow_html=True)

menu = st.radio("Menu Principal", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros", "🏆 Gestão de Prêmios (ZAUT)", "🔎 Auditoria CCT (IA)"], horizontal=True, label_visibility="collapsed")
st.markdown("---")

# ==========================================
# 1. VISÃO GERAL (PAINEL DE AUDITORIA)
# ==========================================
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo & Auditoria Cadastral")
    
    mostrar_alertas = st.checkbox("🚨 Mostrar Apenas Colaboradores com Alertas/Pendências", value=False)
    
    try:
        df = pd.read_sql("SELECT id, nome, cpf, cargo, situacao, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora FROM cadastro_geral_colaborador ORDER BY nome ASC", engine)
        
        def verificar_alertas(row):
            alertas = []
            sit = str(row['situacao']) if pd.notna(row['situacao']) else ""
            dt_ret = parse_br_date_smart(row['data_retorno'])
            dt_afast = parse_br_date_smart(row['data_afastamento'])
            hoje = datetime.today().date()
            
            if sit not in ['1 - Trabalhando', '8 - Demitido'] and dt_ret and dt_ret <= hoje:
                alertas.append("Retorno Vencido (Abra a ficha)")
            if sit == '1 - Trabalhando' and dt_afast and not dt_ret:
                alertas.append("Afastamento em Aberto")
            if pd.isna(row['cpf']) or str(row['cpf']).strip() == "":
                alertas.append("Falta CPF")
            sal = clean_money_to_db(row['salario_mes_12_24'])
            if not sal or float(sal) == 0:
                alertas.append("Sem Salário Base")
                
            return "⚠️ " + " / ".join(alertas) if alertas else "✅ Atualizado"

        df['Alertas do Sistema'] = df.apply(verificar_alertas, axis=1)
        df['salario_mes_12_24'] = df['salario_mes_12_24'].apply(format_currency_brl)
        df['salario_hora'] = df['salario_hora'].apply(format_currency_brl)
        df.rename(columns={'situacao': 'Status (eSocial)'}, inplace=True)
        
        cols_view = ['Alertas do Sistema', 'id', 'nome', 'Status (eSocial)', 'cpf', 'cargo', 'salario_mes_12_24']
        df_view = df[cols_view].copy()
        
        if mostrar_alertas:
            df_view = df_view[df_view['Alertas do Sistema'].str.contains('⚠️')]
            if df_view.empty: st.success("🎉 Parabéns! Todos os cadastros estão atualizados e sem pendências no momento.")
        
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"Erro ao carregar dados do painel: {e}")

# ==========================================
# 2. IMPORTAÇÃO INTELIGENTE
# ==========================================
elif menu == "📥 Importação Inteligente":
    st.title("📥 Central de Ingestão de Dados")
    aba_imp1, aba_imp2 = st.tabs(["📋 Carga Base (Cadastros)", "💰 Motor ETL (Histórico Salarial)"])
    
    with aba_imp1:
        st.subheader("Importação de Cadastros Novos")
        arquivo = st.file_uploader("Selecione o arquivo de migração de colaboradores (.xlsx, .csv)", type=["xlsx", "csv"])
        if arquivo and st.button("Executar Ingestão de Cadastros", key="btn_imp_cad"):
            try:
                df_bruto = pd.read_excel(arquivo, engine='openpyxl') if arquivo.name.endswith('.xlsx') else pd.read_csv(arquivo)
                with engine.begin() as conn:
                    for _, row in df_bruto.iterrows():
                        try:
                            v_id = str(row.iloc[0]) if len(row) > 0 else None
                            if not v_id or v_id == 'nan': continue 
                            conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, salario_mes_12_24, salario_hora) VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :sal_mes, :sal_hora) ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome, cpf = EXCLUDED.cpf, cargo = EXCLUDED.cargo, admissao = EXCLUDED.admissao, demissao = EXCLUDED.demissao, salario_mes_12_24 = EXCLUDED.salario_mes_12_24, salario_hora = EXCLUDED.salario_hora"), {"id": v_id, "nome": str(row.iloc[1]) if len(row) > 1 else None, "cpf": str(row.iloc[2]) if len(row) > 2 else None, "cargo": str(row.iloc[3]) if len(row) > 3 else None, "admissao": str(row.iloc[4]) if len(row) > 4 else None, "demissao": str(row.iloc[5]) if len(row) > 5 else None, "sal_mes": str(row.iloc[6]) if len(row) > 6 else None, "sal_hora": str(row.iloc[7]) if len(row) > 7 else None})
                        except Exception as inner_e: st.warning(f"Linha ignorada: {inner_e}")
                st.success("Ingestão executada com sucesso!")
            except Exception as e: st.error(f"Erro Crítico: {e}")

    with aba_imp2:
        st.subheader("Extração Inteligente de Matriz Salarial")
        if st.button("🧨 ESVAZIAR TODO O HISTÓRICO DO BANCO", type="primary"):
            try:
                with engine.begin() as conn: conn.execute(text("TRUNCATE TABLE historico_premiacoes_e_folha RESTART IDENTITY"))
                st.success("💥 BANCO DE HISTÓRICO ZERADO!")
            except Exception as e: st.error(f"Erro ao limpar: {e}")
        arquivo_hist = st.file_uploader("Selecione a matriz salarial (.xlsx)", type=["xlsx"], key="file_hist")
        if arquivo_hist and st.button("🚀 Processar e Injetar Histórico", type="primary"):
            with st.spinner("Analisando cruzamentos temporais..."):
                try:
                    df_excel = pd.read_excel(arquivo_hist, engine='openpyxl')
                    with engine.connect() as conn: db_cols = conn.execute(text("SELECT id, nome, admissao, demissao FROM cadastro_geral_colaborador")).fetchall()
                    db_dict = {str(r.nome).strip().upper(): {'id': str(r.id), 'admissao': str(r.admissao) if r.admissao else None, 'demissao': str(r.demissao) if r.demissao else None} for r in db_cols if r.nome}
                    lista_ids_numericos = [int(r.id) for r in db_cols if str(r.id).isdigit()]
                    proximo_id_livre = max(lista_ids_numericos) + 1 if lista_ids_numericos else 1000
                    def get_comp_date(col_name):
                        match = re.search(r'(\d{2})/(\d{2})', str(col_name))
                        return pd.Timestamp(year=2000 + int(match.group(2)), month=int(match.group(1)), day=1) if match else None
                    inserts_pendentes, linhas_processadas = [], 0
                    coluna_nome = next((col for col in df_excel.columns if str(col).strip().upper() == 'NOME'), None)
                    if not coluna_nome: st.error("Erro: A planilha não possui a coluna 'Nome'.")
                    else:
                        for _, row in df_excel.iterrows():
                            nome_xls = str(row[coluna_nome]).strip().upper()
                            if not nome_xls or nome_xls == 'NAN': continue
                            if nome_xls not in db_dict:
                                novo_id = str(proximo_id_livre)
                                proximo_id_livre += 1
                                with engine.begin() as conn_recupera: conn_recupera.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome) ON CONFLICT (id) DO NOTHING"), {"id": novo_id, "nome": nome_xls})
                                db_dict[nome_xls] = {'id': novo_id, 'admissao': None, 'demissao': None}
                            colab = db_dict[nome_xls]
                            dt_adm = pd.Timestamp(year=pd.to_datetime(colab['admissao']).year, month=pd.to_datetime(colab['admissao']).month, day=1) if colab['admissao'] else None
                            dt_dem = pd.Timestamp(year=pd.to_datetime(colab['demissao']).year, month=pd.to_datetime(colab['demissao']).month, day=1) if colab['demissao'] else None
                            for col in df_excel.columns:
                                col_str = str(col).strip().upper()
                                if "SALÁRIO MÊS" in col_str or "SALARIO MES" in col_str:
                                    val = row[col]
                                    if pd.isna(val) or str(val).strip() == "": continue
                                    dt_coluna = get_comp_date(col_str)
                                    if not dt_coluna or dt_coluna < pd.Timestamp(year=2024, month=12, day=1): continue
                                    if dt_adm and dt_coluna < dt_adm: continue
                                    if dt_dem and dt_coluna > dt_dem: continue
                                    try: val_float = float(val) if not isinstance(val, str) else float(val.upper().replace('R$', '').replace('.', '').replace(',', '.').strip())
                                    except: continue
                                    if val_float > 0: inserts_pendentes.append({"id_colab": colab['id'], "comp": f"{dt_coluna.month:02d}/{dt_coluna.year}", "tipo": "Salário Mensal", "valor": val_float})
                            linhas_processadas += 1
                        if inserts_pendentes:
                            with engine.begin() as conn:
                                for item in inserts_pendentes:
                                    if not conn.execute(text("SELECT 1 FROM historico_premiacoes_e_folha WHERE id_colaborador = :id_colab AND competencia = :comp AND tipo_lancamento = :tipo"), item).fetchone():
                                        conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_colab, :comp, :tipo, :valor, 'Pago')"), item)
                            st.success(f"✅ Lidos {linhas_processadas} colaboradores. Injetados {len(inserts_pendentes)} registros.")
                        else: st.warning("Nenhum registro novo importado.")
                except Exception as e: st.error(f"Falha: {e}")

# ==========================================
# 3. GESTÃO DE CADASTROS
# ==========================================
elif menu == "🛠️ Gestão de Cadastros":
    opcoes_sub = ["🔍 Consultar & Gerenciar", "➕ Novo Cadastro"]
    sub_menu = st.radio("Menu de Operações", opcoes_sub, index=st.session_state['sub_menu_index'], label_visibility="collapsed", horizontal=True)
    st.session_state['sub_menu_index'] = opcoes_sub.index(sub_menu)
    st.markdown("<br>", unsafe_allow_html=True)

    if sub_menu == "🔍 Consultar & Gerenciar":
        termo = st.text_input("Digite o ID (Matrícula) ou parte do Nome:", key="k_term_busca")
        btn_buscar = st.button("Buscar Registro")
        
        if btn_buscar and termo:
            st.session_state['status_acao'] = None
            st.session_state['busca_selecionada_id'] = None
            try:
                with engine.connect() as conn:
                    resultados = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :t"), {"t": str(termo).strip()}).fetchall()
                    if not resultados: resultados = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t ORDER BY nome ASC"), {"t": f"%{termo.strip()}%"}).fetchall()
                    if not resultados: st.warning("Nenhum registro encontrado.")
                    elif len(resultados) == 1:
                        st.session_state['busca_selecionada_id'] = str(resultados[0].id)
                        st.rerun() 
                    else:
                        st.info("Múltiplos registros encontrados:")
                        opcoes_lista = {f"ID: {r.id} | Nome: {r.nome}": str(r.id) for r in resultados}
                        escolha = st.selectbox("Selecione:", list(opcoes_lista.keys()))
                        if st.button("Confirmar Seleção"): st.session_state['busca_selecionada_id'] = opcoes_lista[escolha]; st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

        if st.session_state['busca_selecionada_id']:
            colab_id = st.session_state['busca_selecionada_id']
            try:
                with engine.connect() as conn:
                    colab = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)}).fetchone()
                    df_fin = pd.read_sql(text("SELECT * FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), conn, params={"id": str(colab_id)})
                    fin_data = df_fin.iloc[0].to_dict() if not df_fin.empty else None
                    df_hist = pd.read_sql(text("SELECT * FROM historico_premiacoes_e_folha WHERE id_colaborador = :id ORDER BY id DESC"), conn, params={"id": str(colab_id)})
                    df_hist_sit = pd.read_sql(text("SELECT id, data_evento, descricao FROM historico_situacoes WHERE id_colaborador = :id ORDER BY data_evento DESC, id DESC"), conn, params={"id": str(colab_id)})
                
                if colab:
                    sal_mestra_vazio = not colab.salario_mes_12_24 or str(colab.salario_mes_12_24).strip() == "" or str(colab.salario_mes_12_24).lower() in ["nan", "none"]
                    hist_salario = df_hist[df_hist['tipo_lancamento'].str.contains('Salário', na=False, case=False)] if not df_hist.empty else pd.DataFrame()
                    tem_hist = not hist_salario.empty
                    
                    val_atual_base = 0.0
                    
                    if sal_mestra_vazio and tem_hist:
                        ultimo_salario_hist = hist_salario.iloc[0]['valor_lancamento']
                        val_hora_calc = float(ultimo_salario_hist) / 220.0
                        with engine.begin() as conn_sync: conn_sync.execute(text("UPDATE cadastro_geral_colaborador SET salario_mes_12_24 = :sm, salario_hora = :sh WHERE id = :id"), {"sm": str(ultimo_salario_hist), "sh": str(val_hora_calc), "id": str(colab_id)})
                        val_atual_base = float(ultimo_salario_hist)
                        salario_mes_display = format_currency_brl(val_atual_base)
                        salario_hora_display = format_currency_brl(val_hora_calc)
                        
                    elif not sal_mestra_vazio and not tem_hist:
                        sm_val = clean_money_to_db(str(colab.salario_mes_12_24))
                        if sm_val:
                            comp_atual_dt = datetime.today()
                            pode_sincronizar = True
                            if pd.notna(colab.demissao):
                                dt_dem = pd.to_datetime(colab.demissao).date()
                                if date(comp_atual_dt.year, comp_atual_dt.month, 1) > date(dt_dem.year, dt_dem.month, 1): pode_sincronizar = False
                            if pode_sincronizar:
                                comp_atual = comp_atual_dt.strftime('%m/%Y')
                                with engine.begin() as conn_sync: conn_sync.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": str(colab_id), "comp": comp_atual, "val": float(sm_val)})
                                df_hist = pd.read_sql(text("SELECT * FROM historico_premiacoes_e_folha WHERE id_colaborador = :id ORDER BY id DESC"), engine, params={"id": str(colab_id)})
                            val_atual_base = float(sm_val)
                            salario_mes_display = format_currency_brl(val_atual_base)
                            salario_hora_display = format_currency_brl(val_atual_base / 220.0)
                    else:
                        if not sal_mestra_vazio:
                            sm_val = clean_money_to_db(str(colab.salario_mes_12_24))
                            val_atual_base = float(sm_val) if sm_val else 0.0
                            salario_mes_display = format_currency_brl(val_atual_base)
                            salario_hora_display = format_currency_brl(val_atual_base / 220.0)
                        else:
                            salario_mes_display = "Não Informado"
                            salario_hora_display = "Não Informado"
                    
                    v_sit_atual = getattr(colab, "situacao", "1 - Trabalhando") or "1 - Trabalhando"
                    v_afast = getattr(colab, 'data_afastamento', None)
                    v_ret = getattr(colab, 'data_retorno', None)

                    # --- MOTOR DE AUTO-RETORNO INTELIGENTE ---
                    if v_ret and v_sit_atual not in ["1 - Trabalhando", "8 - Demitido"]:
                        dt_ret_obj = parse_br_date_smart(v_ret)
                        if dt_ret_obj and dt_ret_obj <= datetime.today().date():
                            with engine.begin() as conn_auto:
                                conn_auto.execute(text("UPDATE cadastro_geral_colaborador SET situacao = '1 - Trabalhando' WHERE id = :id"), {"id": str(colab_id)})
                                conn_auto.execute(text("INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) VALUES (:id, :dt, '1 - Trabalhando')"), {"id": str(colab_id), "dt": dt_ret_obj.strftime('%Y-%m-%d')})
                            st.toast(f"🤖 Auto-Retorno: O sistema detetou que a data já passou e atualizou {colab.nome} para 'Trabalhando'!")
                            st.rerun()

                    sit_color = "#f8fafc"
                    if v_sit_atual.startswith("8"): sit_color = "#ef4444"
                    elif v_sit_atual.startswith("1"): sit_color = "#10b981"
                    elif v_sit_atual.startswith("9"): sit_color = "#3b82f6"
                    else: sit_color = "#facc15"

                    st.markdown("### 📋 Ficha Completa do Colaborador")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown('<p class="field-label">ID / MATRÍCULA</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.id}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">CARGO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.cargo if colab.cargo else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-MÊS ATUAL</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{salario_mes_display}</p>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<p class="field-label">NOME COMPLETO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.nome}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SITUAÇÃO (eSocial)</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value" style="color: {sit_color}; font-weight: bold;">{v_sit_atual}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-HORA ATUAL</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{salario_hora_display}</p>', unsafe_allow_html=True)
                    with c3:
                        st.markdown('<p class="field-label">CPF</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.cpf if colab.cpf else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE ADMISSÃO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{format_date_br(colab.admissao) or "Não Informada"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE DEMISSÃO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value" style="color: #ef4444;">{format_date_br(colab.demissao) or "Ativo / Sem Demissão"}</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    mostrar_painel_afastamento = False
                    if v_afast or v_ret:
                        mostrar_painel_afastamento = True

                    if mostrar_painel_afastamento:
                        dt_r_obj = parse_br_date_smart(v_ret) if v_ret else None
                        
                        if v_sit_atual == "1 - Trabalhando":
                            if dt_r_obj and dt_r_obj > datetime.today().date():
                                icon_afast = "⚠️"
                                titulo_afast = f"{icon_afast} Inconsistência: Status é 'Trabalhando' mas existe afastamento futuro."
                                alerta_color = "#ef4444"
                            else:
                                icon_afast = "🕒"
                                titulo_afast = f"{icon_afast} Último Afastamento Registado"
                                alerta_color = "#94a3b8"
                        elif v_sit_atual == "8 - Demitido":
                            icon_afast = "🕒"
                            titulo_afast = f"{icon_afast} Último Afastamento Antes da Demissão"
                            alerta_color = "#94a3b8"
                        elif "Ferias" in v_sit_atual:
                            icon_afast = "🏖️"
                            titulo_afast = f"{icon_afast} Afastamento Ativo: {v_sit_atual}"
                            alerta_color = "#3b82f6"
                        else:
                            icon_afast = "🏥"
                            titulo_afast = f"{icon_afast} Afastamento Ativo: {v_sit_atual}"
                            alerta_color = "#facc15"

                        st.markdown(f"### <span style='color:{alerta_color};'>{titulo_afast}</span>", unsafe_allow_html=True)
                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        ca1, ca2 = st.columns(2)
                        with ca1: st.markdown('<p class="field-label">DATA DE INÍCIO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value" style="color:{alerta_color}; font-weight: bold;">{format_date_br(v_afast) or "Pendente"}</p>', unsafe_allow_html=True)
                        with ca2: st.markdown('<p class="field-label">RETORNO PREVISTO / REALIZADO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value" style="color:{alerta_color};">{format_date_br(v_ret) or "Em Aberto"}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 📜 Histórico de Situações (eSocial)")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if not df_hist_sit.empty:
                        df_hist_sit_view = df_hist_sit.copy()
                        df_hist_sit_view['data_evento'] = pd.to_datetime(df_hist_sit_view['data_evento']).dt.strftime('%d/%m/%Y')
                        df_hist_sit_view.rename(columns={'data_evento': 'Data do Evento', 'descricao': 'Descrição da Situação'}, inplace=True)
                        st.dataframe(df_hist_sit_view[['Data do Evento', 'Descrição da Situação']], use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum histórico de situação registrado na base de dados para este colaborador.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 🏦 Dados Bancários (PIX Principal)")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if fin_data or colab.chave_pix:
                        cf1, cf2 = st.columns(2)
                        with cf1: st.markdown('<p class="field-label">BANCO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{(fin_data.get("banco") if fin_data else "") or "Não Informado"}</p>', unsafe_allow_html=True)
                        with cf2: st.markdown('<p class="field-label">CHAVE PIX</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.chave_pix or (fin_data.get("chave_pix") if fin_data else "Não Informado")}</p>', unsafe_allow_html=True)
                    else: st.info("Nenhum dado bancário registrado.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 💰 Histórico Mensal de Prêmios e Folha")
                    if not df_hist.empty:
                        df_hist['competencia'] = df_hist['competencia'].apply(format_competencia_smart)
                        duplicatas = df_hist.groupby(['competencia', 'tipo_lancamento']).size().reset_index(name='contagem')
                        duplicatas = duplicatas[duplicatas['contagem'] > 1]
                        if not duplicatas.empty:
                            st.markdown('<div style="background-color: rgba(220, 38, 38, 0.15); border: 1px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 20px;">🛑 **ALERTA DE AUDITORIA INTERNA: DUPLICIDADE DETETADA!**<br>O sistema encontrou lançamentos repetidos para o mesmo mês. Utilize o botão **Corrigir Hist.** e apague o valor para limpar.</div>', unsafe_allow_html=True)

                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if not df_hist.empty:
                        cols_desejadas = ['competencia', 'tipo_lancamento', 'valor_lancamento', 'status_pagamento', 'retroativo_pago', 'data_pagamento']
                        cols_existentes = [c for c in cols_desejadas if c in df_hist.columns]
                        df_view = df_hist[cols_existentes].copy()
                        df_view['valor_lancamento'] = df_view['valor_lancamento'].apply(format_brl_number)
                        df_view.rename(columns={'competencia': 'Competência', 'tipo_lancamento': 'Tipo', 'valor_lancamento': 'Valor (R$)', 'status_pagamento': 'Status'}, inplace=True)
                        st.dataframe(df_view, use_container_width=True, hide_index=True)
                    else: st.info("Nenhum histórico registrado na base de dados para este colaborador.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # --- BOTÕES DE AÇÃO ---
                    if st.session_state['status_acao'] is None:
                        cb1, cb2, cb3, cb4, cb5, cb6, cb7 = st.columns(7)
                        if cb1.button("✏️ Editar"): st.session_state['status_acao'] = 'solicitou_alterar'; st.rerun()
                        if cb2.button("➕ Pagamento"): st.session_state['status_acao'] = 'solicitou_lancamento_avulso'; st.rerun()
                        if cb3.button("🛠️ Corrigir Pag."): st.session_state['status_acao'] = 'solicitou_corrigir_historico'; st.rerun()
                        if cb4.button("⏳ eSocial"): st.session_state['status_acao'] = 'solicitou_hist_esocial'; st.rerun()
                        if cb5.button("🛑 Demitir"): st.session_state['status_acao'] = 'solicitou_demissao'; st.rerun()
                        if cb6.button("❌ Excluir"): st.session_state['status_acao'] = 'solicitou_excluir'; st.rerun()
                        if cb7.button("🧹 Fechar"): st.session_state['busca_selecionada_id'] = None; st.session_state['status_acao'] = None; st.rerun()

                    # --- MÓDULO EXCLUSIVO DE LINHA DO TEMPO (ESOCIAL) ---
                    if st.session_state['status_acao'] == 'solicitou_hist_esocial':
                        st.info("⏳ **Editor da Linha do Tempo (eSocial):** Adicione eventos passados para sincronizar o histórico com a Contabilidade.")
                        
                        aba_add, aba_del = st.tabs(["➕ Lançar Evento Retroativo", "🗑️ Apagar Evento"])
                        
                        with aba_add:
                            ce_dt, ce_sit = st.columns(2)
                            with ce_dt:
                                nova_dt_esocial = st.text_input("Data do Evento (Sem barras)", placeholder="Ex: 09122025")
                            with ce_sit:
                                nova_sit_esocial = st.selectbox("Selecione a Situação", LISTA_SITUACOES_ESOCIAL)
                            
                            if st.button("💾 Gravar no Histórico", type="primary"):
                                dt_limpa = parse_br_date_smart(nova_dt_esocial)
                                if not dt_limpa: st.error("Data inválida! Digite no formato correto (ex: 09122025).")
                                else:
                                    dt_str = dt_limpa.strftime('%Y-%m-%d')
                                    with engine.begin() as conn:
                                        conn.execute(text("INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) VALUES (:id, :dt, :desc)"), {"id": str(colab_id), "dt": dt_str, "desc": nova_sit_esocial})
                                    st.success("Evento gravado na Linha do Tempo!")
                                    st.session_state['status_acao'] = None; st.rerun()
                                    
                        with aba_del:
                            if not df_hist_sit.empty:
                                opcoes_sit = {f"Data: {pd.to_datetime(row['data_evento']).strftime('%d/%m/%Y')} | {row['descricao']}": row['id'] for _, row in df_hist_sit.iterrows()}
                                id_sit_alvo = opcoes_sit[st.selectbox("Selecione o evento a apagar:", list(opcoes_sit.keys()))]
                                if st.button("🗑️ Apagar Evento Selecionado"):
                                    with engine.begin() as conn:
                                        conn.execute(text("DELETE FROM historico_situacoes WHERE id = :id"), {"id": id_sit_alvo})
                                    st.success("Evento apagado da linha do tempo!")
                                    st.session_state['status_acao'] = None; st.rerun()
                            else:
                                st.warning("Nenhum histórico para apagar.")
                        
                        if st.button("⬅️ Voltar / Cancelar"):
                            st.session_state['status_acao'] = None; st.rerun()

                    # --- MÓDULO EXCLUSIVO DE DEMISSÃO ---
                    if st.session_state['status_acao'] == 'solicitou_demissao':
                        st.info("🛑 **Módulo de Desligamento e Correção de Demissão:**")
                        c_dem1, c_dem2 = st.columns(2)
                        with c_dem1:
                            ja_demitido = pd.notna(colab.demissao)
                            status_atual = f"Demitido em {format_date_br(colab.demissao)}" if ja_demitido else "🟢 Ativo / Sem Demissão"
                            st.markdown(f"**Status Atual:** {status_atual}")
                            nova_dem = st.text_input("Data de Demissão (Sem barras)", value=format_date_br(colab.demissao), placeholder="Ex: 01072025")
                        with c_dem2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            reverter = st.checkbox("🟢 Anular Demissão (Tornar Ativo)", value=not ja_demitido)
                            
                        c_bt1, c_bt2 = st.columns([1, 4])
                        if c_bt1.button("💾 Gravar Demissão", type="primary"):
                            try:
                                dt_nova = None if reverter else parse_br_date_smart(nova_dem)
                                if not reverter and not dt_nova: st.error("⚠️ Data de demissão inválida.")
                                else:
                                    dem_str = dt_nova.strftime('%Y-%m-%d') if dt_nova else None
                                    novo_status = '1 - Trabalhando' if reverter else '8 - Demitido'
                                    dt_hist_evento = dt_nova.strftime('%Y-%m-%d') if dt_nova else datetime.today().strftime('%Y-%m-%d')
                                    with engine.begin() as conn: 
                                        conn.execute(text("UPDATE cadastro_geral_colaborador SET demissao = :d, situacao = :sit WHERE id = :id"), {"d": dem_str, "sit": novo_status, "id": str(colab_id)})
                                        conn.execute(text("INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) VALUES (:id, :dt, :desc)"), {"id": str(colab_id), "dt": dt_hist_evento, "desc": novo_status})
                                    st.success("✅ Atualizado!"); st.session_state['status_acao'] = None; st.rerun()
                            except Exception as e: st.error(f"Erro ao salvar: {e}")
                        if c_bt2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    # --- EXCLUIR ---
                    if st.session_state['status_acao'] == 'solicitou_excluir':
                        st.warning(f"⚠️ Deseja excluir {colab.nome}?")
                        cx1, cx2 = st.columns(2)
                        if cx1.button("🔥 Sim, Excluir"):
                            try:
                                with engine.begin() as conn:
                                    conn.execute(text("DELETE FROM historico_situacoes WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                    conn.execute(text("DELETE FROM historico_salarial WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                    conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                    conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                    conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)})
                                st.success("Excluído!"); st.session_state['busca_selecionada_id'] = None; st.session_state['status_acao'] = None; st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")
                        if cx2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    # --- LANÇAMENTO AVULSO ---
                    if st.session_state['status_acao'] == 'solicitou_lancamento_avulso':
                        st.info("➕ **Inserção Avulsa (Com Validação e Anti-Duplicidade):**")
                        c_av1, c_av2, c_av3 = st.columns(3)
                        val_sugestao = format_brl_number(val_atual_base) if val_atual_base > 0 else ""
                        with c_av1: av_comp = st.text_input("Competência (MM/AAAA)", placeholder="Ex: 092025")
                        with c_av2: av_tipo = st.selectbox("Tipo", ["Salário Mensal", "Prêmio ZAUT", "Férias", "Outros"])
                        with c_av3: av_valor = st.text_input("Valor (R$)", value=val_sugestao, placeholder="Digite o valor")
                        c_bt1, c_bt2 = st.columns([1, 4])
                        
                        if c_bt1.button("💾 Salvar Lançamento"):
                            try:
                                v_clean = clean_money_to_db(av_valor)
                                c_clean = format_competencia_smart(av_comp)
                                if not c_clean or len(c_clean) < 6: st.error("⚠️ Competência inválida.")
                                elif not v_clean: st.error("⚠️ O campo 'Valor' está vazio.")
                                else:
                                    m_c, y_c = map(int, c_clean.split('/'))
                                    dt_comp = date(y_c, m_c, 1)
                                    bloqueado, msg_bloqueio = False, ""
                                    if pd.notna(colab.admissao) and dt_comp < date(pd.to_datetime(colab.admissao).year, pd.to_datetime(colab.admissao).month, 1):
                                        bloqueado, msg_bloqueio = True, f"Anterior à admissão."
                                    if not bloqueado and pd.notna(colab.demissao) and dt_comp > date(pd.to_datetime(colab.demissao).year, pd.to_datetime(colab.demissao).month, 1):
                                        bloqueado, msg_bloqueio = True, f"Colaborador demitido."
                                    if not bloqueado:
                                        with engine.connect() as conn_check:
                                            df_check = pd.read_sql(text("SELECT competencia, tipo_lancamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), conn_check, params={"id": str(colab_id)})
                                            if not df_check.empty:
                                                df_check['competencia'] = df_check['competencia'].apply(format_competencia_smart)
                                                if not df_check[(df_check['competencia'] == c_clean) & (df_check['tipo_lancamento'].str.lower() == av_tipo.lower())].empty:
                                                    bloqueado, msg_bloqueio = True, f"Já existe '{av_tipo}' para {c_clean}."
                                    if bloqueado: st.error(f"🛑 {msg_bloqueio}")
                                    else:
                                        with engine.begin() as conn: conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, :tipo, :valor, 'Pago')"), {"id": str(colab_id), "comp": c_clean, "tipo": av_tipo, "valor": float(v_clean)})
                                        st.success(f"Salvo!"); st.session_state['status_acao'] = None; st.rerun()
                            except Exception as e: st.error(f"Erro ao validar datas: {e}")
                        if c_bt2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    # --- CORRIGIR HISTÓRICO ---
                    if st.session_state['status_acao'] == 'solicitou_corrigir_historico':
                        st.info("🛠️ **Editor de Histórico (Pagamentos):** Apague o valor (ou deixe 0) e clique em Salvar para deletar a linha.")
                        if not df_hist.empty:
                            try:
                                opcoes_hist = {f"ID: {row['id']} | Comp: {format_competencia_smart(row['competencia'])} | Tipo: {row['tipo_lancamento']} | Val: R$ {format_brl_number(row['valor_lancamento'])}": row['id'] for _, row in df_hist.iterrows()}
                                id_alvo = opcoes_hist[st.selectbox("Selecione o registo:", list(opcoes_hist.keys()))]
                                novo_val = st.text_input("Novo Valor", placeholder="Deixe vazio para deletar")
                                ch1, ch2 = st.columns([1, 4])
                                if ch1.button("💾 Salvar / Atualizar"):
                                    try:
                                        vc = clean_money_to_db(novo_val)
                                        with engine.begin() as conn:
                                            if not vc or float(vc) == 0:
                                                conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id = :id"), {"id": id_alvo})
                                                st.success("Registo zerado e removido!")
                                            else:
                                                conn.execute(text("UPDATE historico_premiacoes_e_folha SET valor_lancamento = :v WHERE id = :id"), {"v": float(vc), "id": id_alvo})
                                                st.success("Corrigido!")
                                        st.session_state['status_acao'] = None; st.rerun()
                                    except Exception as e: st.error(f"Erro: {e}")
                                if ch2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()
                            except Exception as e: st.error(f"Erro ao carregar lista: {e}")
                        else: st.warning("Nenhum histórico para corrigir.")

                    # --- EDITAR FICHA MESTRA ---
                    if st.session_state['status_acao'] == 'solicitou_alterar':
                        st.info("📝 Modo de Edição Ativo")
                        cargo_idx = LISTA_CARGOS.index(str(colab.cargo).upper().strip()) if str(colab.cargo).upper().strip() in LISTA_CARGOS else (len(LISTA_CARGOS)-1)
                        sit_idx = LISTA_SITUACOES_ESOCIAL.index(v_sit_atual) if v_sit_atual in LISTA_SITUACOES_ESOCIAL else 0
                        
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            edit_id = st.text_input("ID / Matrícula", value=str(colab.id))
                            edit_nome = st.text_input("Nome Completo", value=str(colab.nome))
                            edit_cpf = st.text_input("CPF", value=str(colab.cpf) if colab.cpf else "")
                            edit_adm = st.text_input("Data de Admissão (Sem barras)", value=format_date_br(colab.admissao))
                            edit_sal_mes = st.text_input("Salário-Mês Base", value=str(colab.salario_mes_12_24) if colab.salario_mes_12_24 else "")
                        with ce2:
                            sel_cargo = st.selectbox("Cargo", LISTA_CARGOS, index=cargo_idx)
                            edit_cargo = st.text_input("Digite o Cargo", value=str(colab.cargo) if cargo_idx == len(LISTA_CARGOS)-1 else "") if sel_cargo == "OUTRO (DIGITAR MANUALMENTE)" else sel_cargo
                            sel_sit = st.selectbox("Situação (eSocial)", LISTA_SITUACOES_ESOCIAL, index=sit_idx)
                            edit_pix = st.text_input("Chave PIX", value=str(colab.chave_pix) if colab.chave_pix else "")
                            edit_sal_hora = st.text_input("Salário-Hora Base", value="Automático (Base / 220)", disabled=True)
                            
                        st.markdown("##### 📅 Datas da Situação Atual")
                        ci1, ci2 = st.columns(2)
                        with ci1: edit_afast = st.text_input("Data de Início", value=format_date_br(v_afast))
                        with ci2: edit_ret = st.text_input("Retorno Previsto", value=format_date_br(v_ret))
                        
                        if st.button("Confirmar e Salvar Alterações"):
                            try:
                                if not edit_id.strip() or not edit_nome.strip(): st.error("ID e Nome são obrigatórios.")
                                else:
                                    dt_a = parse_br_date_smart(edit_adm)
                                    dt_af = parse_br_date_smart(edit_afast)
                                    dt_r = parse_br_date_smart(edit_ret)
                                    
                                    adm_str = dt_a.strftime('%Y-%m-%d') if dt_a else None
                                    af_str = dt_af.strftime('%Y-%m-%d') if dt_af else None
                                    ret_str = dt_r.strftime('%Y-%m-%d') if dt_r else None
                                    
                                    sm_val = clean_money_to_db(edit_sal_mes)
                                    sh_val = str(float(sm_val)/220.0) if sm_val is not None else None
                                    
                                    with engine.begin() as conn:
                                        conn.execute(text("UPDATE cadastro_geral_colaborador SET id=:nid, nome=:n, cpf=:c, cargo=:ca, admissao=:ad, data_afastamento=:afast, data_retorno=:ret, chave_pix=:pix, salario_mes_12_24=:sm, salario_hora=:sh, situacao=:sit WHERE id=:oid"), {"nid": edit_id.strip(), "n": edit_nome, "c": edit_cpf, "ca": edit_cargo, "ad": adm_str, "afast": af_str, "ret": ret_str, "pix": edit_pix, "sm": sm_val, "sh": sh_val, "sit": sel_sit, "oid": str(colab_id)})
                                        if edit_id.strip() != str(colab_id):
                                            conn.execute(text("UPDATE historico_premiacoes_e_folha SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                            conn.execute(text("UPDATE historico_situacoes SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                        
                                        if sel_sit != v_sit_atual:
                                            dt_hist_evento = dt_af if dt_af else datetime.today().date()
                                            if sel_sit.startswith("1 - ") and dt_r: dt_hist_evento = dt_r
                                            dt_str_final = dt_hist_evento.strftime('%Y-%m-%d') if isinstance(dt_hist_evento, date) else datetime.today().strftime('%Y-%m-%d')
                                            conn.execute(text("INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) VALUES (:id, :dt, :desc)"), {"id": edit_id.strip(), "dt": dt_str_final, "desc": sel_sit})
                                        
                                        if sm_val:
                                            existe_hist = conn.execute(text("SELECT id FROM historico_premiacoes_e_folha WHERE id_colaborador = :id AND tipo_lancamento ILIKE '%Salário%' ORDER BY id DESC LIMIT 1"), {"id": edit_id.strip()}).fetchone()
                                            if not existe_hist:
                                                comp_str = dt_a.strftime('%m/%Y') if dt_a else datetime.today().strftime('%m/%Y')
                                                conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": edit_id.strip(), "comp": comp_str, "val": float(sm_val)})
                                            else:
                                                conn.execute(text("UPDATE historico_premiacoes_e_folha SET valor_lancamento = :val WHERE id = :id_hist"), {"val": float(sm_val), "id_hist": existe_hist[0]})
                                                
                                    st.success("Salvo!"); st.session_state['busca_selecionada_id'] = edit_id.strip(); st.session_state['status_acao'] = None; st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")
                        if st.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

    elif sub_menu == "➕ Novo Cadastro":
        st.subheader("Inserir Novo Colaborador")
        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
        cn1, cn2 = st.columns(2)
        with cn1:
            n_id = st.text_input("ID / Matrícula")
            n_cpf = st.text_input("CPF")
            n_adm_str = st.text_input("Admissão (Pode digitar sem barras)", placeholder="Ex: 01072025")
            n_sal_mes = st.text_input("Salário-Mês")
            n_afast_str = st.text_input("Data de Início da Situação Acima", placeholder="Ex: 01072025")
        with cn2:
            n_nome = st.text_input("Nome Completo")
            s_c = st.selectbox("Cargo", LISTA_CARGOS)
            n_cargo = st.text_input("Digite o Cargo") if s_c == "OUTRO (DIGITAR MANUALMENTE)" else s_c
            n_sit = st.selectbox("Situação Inicial", LISTA_SITUACOES_ESOCIAL, index=0)
            n_sal_hora = st.text_input("Salário-Hora", value="Automático (Base / 220)", disabled=True)
            n_ret_str = st.text_input("Retorno Previsto", placeholder="Ex: 01072025")
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("💾 Salvar Registro no Sistema"):
            try:
                dt_a = parse_br_date_smart(n_adm_str)
                dt_af = parse_br_date_smart(n_afast_str)
                dt_r = parse_br_date_smart(n_ret_str)
                
                sm_val = clean_money_to_db(n_sal_mes)
                sh_val = str(float(sm_val)/220.0) if sm_val is not None else None
                
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora, situacao) VALUES (:id, :n, :c, :ca, :ad, :afast, :ret, :sm, :sh, :sit)"), {"id": str(n_id), "n": str(n_nome), "c": str(n_cpf), "ca": str(n_cargo), "ad": dt_a.strftime('%Y-%m-%d') if dt_a else None, "afast": dt_af.strftime('%Y-%m-%d') if dt_af else None, "ret": dt_r.strftime('%Y-%m-%d') if dt_r else None, "sm": sm_val, "sh": sh_val, "sit": n_sit})
                    
                    dt_hist_evento = dt_a.strftime('%Y-%m-%d') if dt_a else datetime.today().strftime('%Y-%m-%d')
                    conn.execute(text("INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) VALUES (:id, :dt, :desc)"), {"id": str(n_id), "dt": dt_hist_evento, "desc": n_sit})
                    
                    if sm_val:
                        comp_str = dt_a.strftime('%m/%Y') if dt_a else datetime.today().strftime('%m/%Y')
                        conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": str(n_id), "comp": comp_str, "val": float(sm_val)})
                        
                st.success("Salvo!"); st.session_state['redirect_to_consulta'] = True; st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

# ==========================================
# 4. GESTÃO DE PRÊMIOS (ZAUT) E 5. AUDITORIA
# ==========================================
elif menu == "🏆 Gestão de Prêmios (ZAUT)":
    st.title("🏆 Lançamento de Prêmios (ZAUT)")
    col_comp1, col_comp2 = st.columns([1, 3])
    with col_comp1:
        hoje = datetime.today()
        meses = [f"{str(m).zfill(2)}/{hoje.year}" for m in range(1, 13)] + [f"{str(m).zfill(2)}/{hoje.year+1}" for m in range(1, 13)]
        comp_sel = st.selectbox("Selecione a Competência:", meses, index=(hoje.month - 1))
    st.markdown("---")
    try:
        df_colabs = pd.read_sql("SELECT id, nome, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, situacao FROM cadastro_geral_colaborador ORDER BY nome ASC", engine)
        data_inicio_comp = pd.Timestamp(year=int(comp_sel.split('/')[1]), month=int(comp_sel.split('/')[0]), day=1)
        data_fim_comp = pd.Timestamp(year=int(comp_sel.split('/')[1]), month=int(comp_sel.split('/')[0]), day=calendar.monthrange(int(comp_sel.split('/')[1]), int(comp_sel.split('/')[0]))[1])
        
        colabs_elegiveis = []
        for _, row in df_colabs.iterrows():
            if pd.notna(row['demissao']) and pd.to_datetime(row['demissao']) < data_inicio_comp: continue 
            dt_afast = pd.to_datetime(row['data_afastamento']) if pd.notna(row['data_afastamento']) else None
            dt_ret = pd.to_datetime(row['data_retorno']) if pd.notna(row['data_retorno']) else None
            if dt_afast and dt_afast < data_inicio_comp and (dt_ret is None or dt_ret > data_fim_comp): continue 
            
            try: sal_base_float = float(str(row['salario_mes_12_24']).upper().replace('R$', '').replace('.', '').replace(',', '.').strip()) if row['salario_mes_12_24'] else 0.0
            except: sal_base_float = 0.0
                
            if sal_base_float == 0.0:
                try:
                    with engine.connect() as conn2:
                        hs = conn2.execute(text("SELECT valor_lancamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id AND tipo_lancamento ILIKE '%Salário%' ORDER BY id DESC LIMIT 1"), {"id": str(row['id'])}).fetchone()
                        if hs: sal_base_float = float(hs[0])
                except: pass
            colabs_elegiveis.append({"id": str(row['id']), "nome": str(row['nome']), "sal_hora": sal_base_float / 220.0 if sal_base_float > 0 else 0.0})
            
        if not colabs_elegiveis: st.warning("Nenhum colaborador elegível para esta competência.")
        else:
            aba_lote, aba_ind = st.tabs(["📊 Planilha de Lote Rápido", "👤 Lançamento Individual"])
            with aba_lote:
                df_lote = pd.DataFrame(colabs_elegiveis); df_lote['Horas Prêmio (HP)'] = 0.00; df_lote['Descrição do Serviço'] = None
                edited_df = st.data_editor(df_lote, column_config={"id": st.column_config.TextColumn("Matrícula", disabled=True), "nome": st.column_config.TextColumn("Colaborador", disabled=True), "sal_hora": st.column_config.NumberColumn("Valor Hora", format="R$ %.2f", disabled=True), "Horas Prêmio (HP)": st.column_config.NumberColumn("Total HP", min_value=0.0, format="%.2f", step=1.0), "Descrição do Serviço": st.column_config.SelectboxColumn("Serviço", options=LISTA_SERVICOS_PREMIO)}, disabled=["id", "nome", "sal_hora"], hide_index=True, use_container_width=True, key="editor_lote_zaut")
                c_btn_lt1, c_btn_lt2 = st.columns([1, 4])
                if c_btn_lt1.button("💾 Salvar Lote Inteiro", type="primary"):
                    lancamentos = edited_df[edited_df['Horas Prêmio (HP)'] > 0]
                    if lancamentos.empty: st.warning("Nenhuma hora preenchida.")
                    else:
                        sucessos, erros = 0, 0
                        with engine.begin() as conn:
                            for _, r in lancamentos.iterrows():
                                try:
                                    conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_c, :comp, :tipo, :val, 'Lançado')"), {"id_c": str(r['id']), "comp": comp_sel, "tipo": f"Prêmio: {r['Descrição do Serviço'] or 'PRÊMIO PRODUÇÃO (ZAUT)'} (Horas: {r['Horas Prêmio (HP)']})", "val": (float(r['sal_hora']) * float(r['Horas Prêmio (HP)'])) + 1.00})
                                    sucessos += 1
                                except: erros += 1
                        if sucessos > 0: st.success(f"✅ {sucessos} recibos gerados."); del st.session_state['editor_lote_zaut']; st.rerun()
                        if erros > 0: st.error(f"{erros} erros.")
                if c_btn_lt2.button("❌ Cancelar / Limpar Planilha", key="btn_canc_lote"): del st.session_state['editor_lote_zaut']; st.rerun()

            with aba_ind:
                opcoes_dropdown = {f"{c['nome']} (ID: {c['id']})": c for c in colabs_elegiveis}
                colab_escolhido = st.selectbox("Selecione o Colaborador:", list(opcoes_dropdown.keys()))
                dados_c = opcoes_dropdown[colab_escolhido]
                try:
                    df_ja_lancado = pd.read_sql(text("SELECT tipo_lancamento, valor_lancamento, status_pagamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id_c AND competencia = :comp"), engine, params={"id_c": dados_c['id'], "comp": comp_sel})
                    if not df_ja_lancado.empty:
                        df_jl_view = df_ja_lancado.copy()
                        df_jl_view['valor_lancamento'] = df_jl_view['valor_lancamento'].apply(format_currency_brl)
                        st.dataframe(df_jl_view.rename(columns={'tipo_lancamento': 'Descrição do Prêmio', 'valor_lancamento': 'Valor', 'status_pagamento': 'Status'}), use_container_width=True, hide_index=True)
                except: pass
                
                if st.session_state.get('zaut_acao') != 'lancando':
                    if st.button(f"➕ Iniciar Lançamento para {dados_c['nome']}", type="primary"): st.session_state['zaut_acao'] = 'lancando'; st.rerun()
                else:
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    sal_hora_base = dados_c['sal_hora']
                    if sal_hora_base == 0.0:
                        sal_hora_manual = st.text_input("Valor Hora (R$)", key="k_sh_manual", placeholder="Ex: 9,38")
                        try: sal_hora_base = float(clean_money_to_db(sal_hora_manual)) if clean_money_to_db(sal_hora_manual) else 0.0
                        except: sal_hora_base = 0.0
                    else: st.markdown(f"**Valor Hora Calculado:** R$ {format_brl_number(sal_hora_base)}")
                    
                    cli1, cli2 = st.columns(2)
                    with cli1: hp_ind = st.text_input("Horas (ENTER para calcular)", key="k_hpi")
                    with cli2: desc_final_str = st.text_input("Especificar:", key="k_d_outro") if (desc_ind := st.selectbox("Serviço", LISTA_SERVICOS_PREMIO, key="k_di")) == "OUTRO (DIGITAR MANUALMENTE)" else desc_ind
                    
                    try: hp_ind_float = float(clean_money_to_db(hp_ind)) if clean_money_to_db(hp_ind) else 0.0
                    except: hp_ind_float = 0.0
                    val_final_ind = (sal_hora_base * hp_ind_float) + 1.00 if hp_ind_float > 0 else 0.00
                    
                    if hp_ind_float > 0 and sal_hora_base > 0: st.markdown(f'<p class="field-highlight">R$ {format_brl_number(val_final_ind)}</p>', unsafe_allow_html=True)
                    
                    c_btn_i1, c_btn_i2 = st.columns([1, 4])
                    if c_btn_i1.button("💾 Gravar", type="primary", key="btn_ind_gravar"):
                        if hp_ind_float <= 0 or sal_hora_base <= 0 or not desc_final_str.strip(): st.error("⚠️ Dados inválidos.")
                        else:
                            with engine.begin() as conn: conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_c, :comp, :tipo, :val, 'Lançado')"), {"id_c": dados_c['id'], "comp": comp_sel, "tipo": f"Prêmio: {desc_final_str} (Horas: {hp_ind_float})", "val": val_final_ind})
                            st.success("✅ Gravado!"); [st.session_state.pop(k, None) for k in ['k_hpi', 'k_sh_manual', 'k_d_outro', 'zaut_acao']]; st.rerun()
                    if c_btn_i2.button("❌ Cancelar", key="btn_ind_fechar"): [st.session_state.pop(k, None) for k in ['k_hpi', 'k_sh_manual', 'k_d_outro', 'zaut_acao']]; st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

elif menu == "🔎 Auditoria CCT (IA)":
    st.title("🔎 Auditoria Automatizada da Folha")
    if st.button("🚀 Executar Varredura", type="primary"):
        df_folha = pd.read_sql("SELECT id, nome, cargo, admissao, demissao, situacao, salario_mes_12_24 FROM cadastro_geral_colaborador", engine)
        def calcular_auditoria(row):
            if pd.notna(row['demissao']): return pd.Series(["Demitido", "-", "Ok"])
            sal_atual = float(clean_money_to_db(row['salario_mes_12_24']) or 0.0)
            piso = 4068.99 if "MESTRE" in str(row['cargo']).upper() else (2063.92 if any(x in str(row['cargo']).upper() for x in ["PEDREIRO", "CARPINTEIRO", "PINTOR", "ENCANADOR"]) else 1518.00)
            st_aud = "⚠️ Sem Salário" if sal_atual == 0.0 else ("❌ Abaixo CCT" if round(sal_atual, 2) < round(piso, 2) else "✅ Perfeito")
            return pd.Series([f"R$ {format_brl_number(piso)}", f"R$ {format_brl_number(sal_atual)}", st_aud])
        df_folha[['Salário Ideal (CCT)', 'Salário Atual', 'Status']] = df_folha.apply(calcular_auditoria, axis=1)
        st.dataframe(df_folha[~df_folha['Status'].str.contains("Demitido")][['id', 'nome', 'cargo', 'situacao', 'Salário Atual', 'Salário Ideal (CCT)', 'Status']], use_container_width=True, hide_index=True)
