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

# --- MIGRAÇÃO AUTOMÁTICA DE BANCO DE DADOS (INSS E HISTÓRICOS) ---
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
except Exception as e:
    st.error(f"Erro ao inicializar tabelas de sistema: {e}")

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN data_afastamento VARCHAR(50);"))
except:
    pass 
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN data_retorno VARCHAR(50);"))
except:
    pass 

# --- ESTILIZAÇÃO VISUAL AVANÇADA (DARK PREMIUM GLASSMORPHISM) ---
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
    
    .fake-label {
        color: #f8fafc;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: -15px;
        display: block;
    }

    div[data-testid="stRadio"] > div {
        flex-direction: row;
        gap: 10px;
    }
    div[data-testid="stRadio"] label {
        background: rgba(30, 41, 59, 0.6);
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid rgba(51, 65, 85, 0.5);
        color: #94a3b8;
        cursor: pointer;
    }
    div[data-testid="stRadio"] label[data-testid="stWidgetSelected"] {
        background: #2563eb !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- INJEÇÃO DE JAVASCRIPT PROFISSIONAL (AUTOFILL + NAVEGAÇÃO ENTER CONTÍNUA) ---
components.html("""
<script>
const doc = window.parent.document;

setInterval(function(){
    doc.querySelectorAll('input').forEach(function(el){
        el.setAttribute('autocomplete', 'new-password');
        el.setAttribute('autofill', 'off');
        if (!el.hasAttribute('data-name-set')) {
            el.setAttribute('name', 'input_' + Math.random().toString(36).substring(7));
            el.setAttribute('data-name-set', 'true');
        }
    });
}, 150);

if (!window.parent.EnterToTabInjected) {
    window.parent.EnterToTabInjected = true;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            if (e.target.tagName === 'BUTTON') return;
            if (e.target.tagName === 'TEXTAREA') return;
            if (e.target.getAttribute('aria-expanded') === 'true') return;

            e.preventDefault();
            e.stopPropagation();
            
            var selectors = 'input:not([disabled]):not([type="hidden"]), button:not([disabled]), textarea:not([disabled]), [tabindex="0"]:not([disabled])';
            var focusable = Array.from(doc.querySelectorAll(selectors));
            focusable = focusable.filter(el => (el.offsetWidth > 0 || el.offsetHeight > 0) && el.style.display !== 'none' && el.style.visibility !== 'hidden');
            var index = focusable.indexOf(e.target);
            
            if (index > -1 && index < focusable.length - 1) {
                var nextEl = focusable[index + 1];
                nextEl.focus();
                if (nextEl.tagName === 'INPUT' && (nextEl.type === 'text' || nextEl.type === 'number')) {
                    setTimeout(() => nextEl.select(), 10);
                }
            }
        }
    }, true); 
}
</script>
""", height=0, width=0)

# --- LISTAS PADRÃO (CCT E PRÊMIOS) ---
LISTA_CARGOS = [
    "PEDREIRO", "SERVENTE", "AJUDANTE PRATICO", "CARPINTEIRO", "PINTOR", 
    "ENCANADOR", "MESTRE DE OBRAS", "ENCARREGADO", 
    "APRENDIZ LEGAL EM ARCO ADMINISTRATIVO", "ESTAGIÁRIO", 
    "OUTRO (DIGITAR MANUALMENTE)"
]

LISTA_SERVICOS_PREMIO = [
    "211 PRÊMIO META CRONOGRAMA",
    "212 PRÊMIO REVESTIMENTO EXTERNO",
    "213 PRÊMIO PINTURA",
    "215 PRÊMIO INSTALAÇÕES",
    "216 PRÊMIO REVESTIMENTO INTERNO",
    "225 PREMIO ESTRUTURA",
    "OUTRO (DIGITAR MANUALMENTE)"
]

# --- GERENCIADOR DE SESSÃO E ROTEAMENTO SPA ---
if 'busca_selecionada_id' not in st.session_state: st.session_state['busca_selecionada_id'] = None
if 'status_acao' not in st.session_state: st.session_state['status_acao'] = None
if 'zaut_acao' not in st.session_state: st.session_state['zaut_acao'] = None
if 'sub_menu_index' not in st.session_state: st.session_state['sub_menu_index'] = 0
if 'redirect_to_consulta' not in st.session_state: st.session_state['redirect_to_consulta'] = False

if st.session_state['redirect_to_consulta']:
    st.session_state['sub_menu_index'] = 0
    st.session_state['redirect_to_consulta'] = False
    st.rerun()

# --- FUNÇÕES INTELIGENTES DE FORMATAÇÃO E PARSING ---
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
    if '/' in s: return s
    digitos = re.sub(r'[^\d]', '', s)
    if len(digitos) == 6: return f"{digitos[:2]}/{digitos[2:]}"
    elif len(digitos) == 4: return f"{digitos[:2]}/20{digitos[2:]}"
    return s

# --- BARRA LATERAL DE NAVEGAÇÃO CENTRAL ---
menu = st.sidebar.radio("Navegação", [
    "👥 Visão Geral", 
    "📥 Importação Inteligente", 
    "🛠️ Gestão de Cadastros", 
    "🏆 Gestão de Prêmios (ZAUT)", 
    "🔎 Auditoria CCT (IA)"
])

# ==========================================
# 1. VISÃO GERAL
# ==========================================
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    try:
        df = pd.read_sql("""
            SELECT id, nome, cpf, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora 
            FROM cadastro_geral_colaborador 
            ORDER BY nome ASC
        """, engine)
        
        df['salario_mes_12_24'] = df['salario_mes_12_24'].apply(format_currency_brl)
        df['salario_hora'] = df['salario_hora'].apply(format_currency_brl)
        
        df.rename(columns={
            'data_afastamento': 'Afastamento (INSS)',
            'data_retorno': 'Retorno (INSS)'
        }, inplace=True)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados do painel: {e}")

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
                if arquivo.name.endswith('.xlsx'): df_bruto = pd.read_excel(arquivo, engine='openpyxl')
                else: df_bruto = pd.read_csv(arquivo)
                
                with engine.begin() as conn:
                    for _, row in df_bruto.iterrows():
                        try:
                            v_id = str(row.iloc[0]) if len(row) > 0 else None
                            if not v_id or v_id == 'nan': continue 
                                
                            conn.execute(text("""
                                INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, salario_mes_12_24, salario_hora) 
                                VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :sal_mes, :sal_hora)
                                ON CONFLICT (id) DO UPDATE SET 
                                    nome = EXCLUDED.nome, cpf = EXCLUDED.cpf, cargo = EXCLUDED.cargo, admissao = EXCLUDED.admissao,
                                    demissao = EXCLUDED.demissao, salario_mes_12_24 = EXCLUDED.salario_mes_12_24, salario_hora = EXCLUDED.salario_hora
                            """), {
                                "id": v_id, "nome": str(row.iloc[1]) if len(row) > 1 else None, "cpf": str(row.iloc[2]) if len(row) > 2 else None,
                                "cargo": str(row.iloc[3]) if len(row) > 3 else None, "admissao": str(row.iloc[4]) if len(row) > 4 else None,
                                "demissao": str(row.iloc[5]) if len(row) > 5 else None, "sal_mes": str(row.iloc[6]) if len(row) > 6 else None,
                                "sal_hora": str(row.iloc[7]) if len(row) > 7 else None
                            })
                        except Exception as inner_e: st.warning(f"Linha ignorada: {inner_e}")
                st.success("Ingestão executada com sucesso!")
            except Exception as e: st.error(f"Erro Crítico: {e}")

    with aba_imp2:
        st.subheader("Extração Inteligente de Matriz Salarial")
        st.markdown('<div style="background-color: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; padding: 15px; border-radius: 8px; margin-bottom: 20px;">', unsafe_allow_html=True)
        st.markdown("⚠️ **OPÇÃO NUCLEAR:** ZERAR completamente a tabela de histórico de salários do banco de dados.")
        if st.button("🧨 ESVAZIAR TODO O HISTÓRICO DO BANCO", type="primary"):
            try:
                with engine.begin() as conn: conn.execute(text("TRUNCATE TABLE historico_premiacoes_e_folha RESTART IDENTITY"))
                st.success("💥 BANCO DE HISTÓRICO ZERADO!")
            except Exception as e: st.error(f"Erro ao limpar: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
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
                        if match: return pd.Timestamp(year=2000 + int(match.group(2)), month=int(match.group(1)), day=1)
                        return None
                    def parse_str_date_old(d_str):
                        try: return pd.Timestamp(year=pd.to_datetime(d_str).year, month=pd.to_datetime(d_str).month, day=1)
                        except: return None

                    inserts_pendentes, linhas_processadas, recuperados_ia = [], 0, 0
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
                                recuperados_ia += 1

                            colab = db_dict[nome_xls]
                            dt_adm = parse_str_date_old(colab['admissao'])
                            dt_dem = parse_str_date_old(colab['demissao'])
                            
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
                                    existe = conn.execute(text("SELECT 1 FROM historico_premiacoes_e_folha WHERE id_colaborador = :id_colab AND competencia = :comp AND tipo_lancamento = :tipo"), item).fetchone()
                                    if not existe: conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_colab, :comp, :tipo, :valor, 'Pago')"), item)
                            st.success(f"✅ Lidos {linhas_processadas} colaboradores. Injetados {len(inserts_pendentes)} registros.")
                            if recuperados_ia > 0: st.warning(f"🤖 {recuperados_ia} recadastrados automaticamente.")
                        else: st.warning("Nenhum registro novo importado.")
                except Exception as e: st.error(f"Falha: {e}")

# ==========================================
# 3. GESTÃO DE CADASTROS
# ==========================================
elif menu == "🛠️ Gestão de Cadastros":
    st.title("🛠️ Gestão de Cadastros")
    
    opcoes_sub = ["🔍 Consultar & Gerenciar", "➕ Novo Cadastro"]
    sub_menu = st.radio("Menu de Operações", opcoes_sub, index=st.session_state['sub_menu_index'], label_visibility="collapsed")
    st.session_state['sub_menu_index'] = opcoes_sub.index(sub_menu)
    st.markdown("---")

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
                    df_evo_salarial = pd.read_sql(text("SELECT data_alteracao, motivo, salario_anterior, novo_salario FROM historico_salarial WHERE id_colaborador = :id ORDER BY data_alteracao DESC, id DESC"), conn, params={"id": str(colab_id)})
                
                if colab:
                    # O MOTOR DE AUTO-SINCRONIZAÇÃO APRIMORADO
                    sal_mestra_vazio = not colab.salario_mes_12_24 or str(colab.salario_mes_12_24).strip() == "" or str(colab.salario_mes_12_24).lower() in ["nan", "none"]
                    hist_salario = df_hist[df_hist['tipo_lancamento'].str.contains('Salário', na=False, case=False)] if not df_hist.empty else pd.DataFrame()
                    tem_hist = not hist_salario.empty
                    
                    val_atual_base = 0.0
                    
                    if sal_mestra_vazio and tem_hist:
                        ultimo_salario_hist = hist_salario.iloc[0]['valor_lancamento']
                        val_hora_calc = float(ultimo_salario_hist) / 220.0
                        with engine.begin() as conn_sync:
                            conn_sync.execute(text("UPDATE cadastro_geral_colaborador SET salario_mes_12_24 = :sm, salario_hora = :sh WHERE id = :id"), {"sm": str(ultimo_salario_hist), "sh": str(val_hora_calc), "id": str(colab_id)})
                        val_atual_base = float(ultimo_salario_hist)
                        salario_mes_display = format_currency_brl(val_atual_base)
                        salario_hora_display = format_currency_brl(val_hora_calc)
                        
                    elif not sal_mestra_vazio and not tem_hist:
                        sm_val = clean_money_to_db(str(colab.salario_mes_12_24))
                        if sm_val:
                            # AQUI ESTAVA O BLOQUEIO! Usamos a Data de Admissão para criar a base, assim não trava na Demissão.
                            if pd.notna(colab.admissao): comp_atual = pd.to_datetime(colab.admissao).strftime('%m/%Y')
                            elif pd.notna(colab.demissao): comp_atual = pd.to_datetime(colab.demissao).strftime('%m/%Y')
                            else: comp_atual = datetime.today().strftime('%m/%Y')
                            
                            try:
                                with engine.begin() as conn_sync:
                                    conn_sync.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": str(colab_id), "comp": comp_atual, "val": float(sm_val)})
                                df_hist = pd.read_sql(text("SELECT * FROM historico_premiacoes_e_folha WHERE id_colaborador = :id ORDER BY id DESC"), engine, params={"id": str(colab_id)})
                            except: pass
                                
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
                    
                    st.markdown("### 📋 Ficha Completa do Colaborador")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown('<p class="field-label">ID / MATRÍCULA</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.id}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">CARGO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.cargo if colab.cargo else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-MÊS ATUAL</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{salario_mes_display}</p>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<p class="field-label">NOME COMPLETO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.nome}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE ADMISSÃO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{format_date_br(colab.admissao) or "Não Informada"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-HORA ATUAL</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{salario_hora_display}</p>', unsafe_allow_html=True)
                    with c3:
                        st.markdown('<p class="field-label">CPF</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.cpf if colab.cpf else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE DEMISSÃO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{format_date_br(colab.demissao) or "Ativo / Em Aberto"}</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    v_afast = getattr(colab, 'data_afastamento', None)
                    v_ret = getattr(colab, 'data_retorno', None)
                    if v_afast:
                        st.markdown("### 🏥 Status de Afastamento (INSS)")
                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        ca1, ca2 = st.columns(2)
                        with ca1: st.markdown('<p class="field-label">AFASTAMENTO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value" style="color:#facc15;">{format_date_br(v_afast)}</p>', unsafe_allow_html=True)
                        with ca2: st.markdown('<p class="field-label">RETORNO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{format_date_br(v_ret) or "Ainda Afastado"}</p>', unsafe_allow_html=True)
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
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if not df_hist.empty:
                        cols_desejadas = ['competencia', 'tipo_lancamento', 'valor_lancamento', 'status_pagamento', 'retroativo_pago', 'data_pagamento']
                        cols_existentes = [c for c in cols_desejadas if c in df_hist.columns]
                        df_view = df_hist[cols_existentes].copy()
                        df_view['valor_lancamento'] = df_view['valor_lancamento'].apply(format_brl_number)
                        
                        if 'competencia' in df_view.columns:
                            df_view['competencia'] = df_view['competencia'].apply(format_competencia_smart)
                        
                        rename_dict = {'competencia': 'Competência', 'tipo_lancamento': 'Tipo', 'valor_lancamento': 'Valor (R$)', 'status_pagamento': 'Status', 'retroativo_pago': 'Foi Retroativo?', 'data_pagamento': 'Data Pagamento'}
                        df_view.rename(columns={k: v for k, v in rename_dict.items() if k in df_view.columns}, inplace=True)
                        st.dataframe(df_view, use_container_width=True, hide_index=True)
                    else: st.info("Nenhum histórico registrado na base de dados para este colaborador.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # --- BOTÕES DE AÇÃO ---
                    if st.session_state['status_acao'] is None:
                        cb1, cb2, cb3, cb4, cb5 = st.columns(5)
                        if cb1.button("✏️ Editar Ficha"): st.session_state['status_acao'] = 'solicitou_alterar'; st.rerun()
                        if cb2.button("➕ Lanç. Avulso"): st.session_state['status_acao'] = 'solicitou_lancamento_avulso'; st.rerun()
                        if cb3.button("🛠️ Corrigir Hist."): st.session_state['status_acao'] = 'solicitou_corrigir_historico'; st.rerun()
                        if cb4.button("❌ Excluir"): st.session_state['status_acao'] = 'solicitou_excluir'; st.rerun()
                        if cb5.button("🧹 Fechar"): st.session_state['busca_selecionada_id'] = None; st.session_state['status_acao'] = None; st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_excluir':
                        st.warning(f"⚠️ Deseja excluir {colab.nome}?")
                        cx1, cx2 = st.columns(2)
                        if cx1.button("🔥 Sim, Excluir"):
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM historico_salarial WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)})
                            st.success("Excluído!"); st.session_state['busca_selecionada_id'] = None; st.session_state['status_acao'] = None; st.rerun()
                        if cx2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_lancamento_avulso':
                        st.info("➕ **Inserção Avulsa (Com Validação Temporal):**")
                        c_av1, c_av2, c_av3 = st.columns(3)
                        
                        val_sugestao = format_brl_number(val_atual_base) if val_atual_base > 0 else ""
                        
                        with c_av1: av_comp = st.text_input("Competência (MM/AAAA)", placeholder="Ex: 092025 ou 09/2025")
                        with c_av2: av_tipo = st.selectbox("Tipo", ["Salário Mensal", "Prêmio ZAUT", "Férias", "Outros"])
                        with c_av3: av_valor = st.text_input("Valor (R$)", value=val_sugestao, placeholder="Digite o valor aqui")
                        c_bt1, c_bt2 = st.columns([1, 4])
                        
                        if c_bt1.button("💾 Salvar Lançamento"):
                            v_clean = clean_money_to_db(av_valor)
                            c_clean = format_competencia_smart(av_comp)
                            
                            if not c_clean or len(c_clean) < 6:
                                st.error("⚠️ A competência é inválida. Digite no formato MMAAAA ou MM/AAAA.")
                            elif not v_clean:
                                st.error("⚠️ O campo 'Valor' está vazio. Você precisa digitar um número.")
                            else:
                                try:
                                    m_c, y_c = map(int, c_clean.split('/'))
                                    dt_comp = date(y_c, m_c, 1)
                                    bloqueado = False
                                    msg_bloqueio = ""
                                    
                                    if pd.notna(colab.admissao):
                                        dt_a = pd.to_datetime(colab.admissao).date()
                                        if dt_comp < date(dt_a.year, dt_a.month, 1):
                                            bloqueado = True
                                            msg_bloqueio = f"Competência ({c_clean}) é anterior ao mês de admissão ({dt_a.strftime('%m/%Y')})."
                                            
                                    if not bloqueado and pd.notna(colab.demissao):
                                        dt_d = pd.to_datetime(colab.demissao).date()
                                        if dt_comp > date(dt_d.year, dt_d.month, 1):
                                            bloqueado = True
                                            msg_bloqueio = f"Colaborador demitido em {dt_d.strftime('%d/%m/%Y')}. Não é possível lançar para a competência {c_clean}."
                                            
                                    if bloqueado:
                                        st.error(f"🛑 **Lançamento Bloqueado:** {msg_bloqueio}")
                                    else:
                                        with engine.begin() as conn:
                                            conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, :tipo, :valor, 'Pago')"), {"id": str(colab_id), "comp": c_clean, "tipo": av_tipo, "valor": float(v_clean)})
                                        st.success(f"Mês {c_clean} salvo com sucesso!"); st.session_state['status_acao'] = None; st.rerun()
                                except Exception as e:
                                    st.error("Erro ao validar datas. Verifique se o mês digitado existe.")
                            
                        if c_bt2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_corrigir_historico':
                        st.info("🛠️ **Editor de Histórico:**")
                        if not df_hist.empty:
                            try:
                                opcoes_hist = {f"Comp: {format_competencia_smart(row['competencia'])} | Tipo: {row['tipo_lancamento']} | Val: R$ {format_brl_number(row['valor_lancamento'])}": row['id'] for _, row in df_hist.iterrows()}
                                id_alvo = opcoes_hist[st.selectbox("Selecione:", list(opcoes_hist.keys()))]
                                novo_val = st.text_input("Novo Valor", placeholder="Ex: 2354,90")
                                ch1, ch2, ch3 = st.columns(3)
                                if ch1.button("💾 Salvar"):
                                    vc = clean_money_to_db(novo_val)
                                    if vc:
                                        with engine.begin() as conn: conn.execute(text("UPDATE historico_premiacoes_e_folha SET valor_lancamento = :v WHERE id = :id"), {"v": float(vc), "id": id_alvo})
                                        st.success("Corrigido!"); st.session_state['status_acao'] = None; st.rerun()
                                    else:
                                        st.error("⚠️ O campo de novo valor está vazio ou inválido.")
                                if ch2.button("🗑️ Apagar"):
                                    with engine.begin() as conn: conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id = :id"), {"id": id_alvo})
                                    st.success("Apagado!"); st.session_state['status_acao'] = None; st.rerun()
                                if ch3.button("⬅️ Voltar / Cancelar"): st.session_state['status_acao'] = None; st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao carregar lista de histórico. ({e})")
                                if st.button("⬅️ Voltar / Cancelar (Modo de Segurança)"): st.session_state['status_acao'] = None; st.rerun()
                        else: 
                            st.warning("Nenhum histórico para corrigir.")
                            if st.button("⬅️ Voltar / Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_alterar':
                        st.info("📝 Modo de Edição Ativo")
                        cargo_idx = LISTA_CARGOS.index(str(colab.cargo).upper().strip()) if str(colab.cargo).upper().strip() in LISTA_CARGOS else (len(LISTA_CARGOS)-1)
                        
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            edit_id = st.text_input("ID / Matrícula", value=str(colab.id), key="k_eid")
                            edit_nome = st.text_input("Nome Completo", value=str(colab.nome), key="k_enome")
                            edit_cpf = st.text_input("CPF", value=str(colab.cpf) if colab.cpf else "", key="k_ecpf")
                            edit_adm = st.text_input("Data de Admissão (Sem barras)", value=format_date_br(colab.admissao), placeholder="Ex: 01072025")
                            edit_sal_mes = st.text_input("Salário-Mês Base", value=str(colab.salario_mes_12_24) if colab.salario_mes_12_24 else "", key="k_esal_mes")
                        with ce2:
                            sel_cargo = st.selectbox("Cargo", LISTA_CARGOS, index=cargo_idx)
                            edit_cargo = st.text_input("Digite o Cargo", value=str(colab.cargo) if cargo_idx == len(LISTA_CARGOS)-1 else "") if sel_cargo == "OUTRO (DIGITAR MANUALMENTE)" else sel_cargo
                            
                            ativo_ed = st.checkbox("✅ Colaborador Ativo (Ignorar Demissão)", value=(colab.demissao is None or pd.isna(colab.demissao)))
                            edit_dem = st.text_input("Data de Demissão (Sem barras)", value=format_date_br(colab.demissao), placeholder="Ex: 01072025", disabled=ativo_ed)
                            
                            edit_pix = st.text_input("Chave PIX", value=str(colab.chave_pix) if colab.chave_pix else "", key="k_epix")
                            edit_sal_hora = st.text_input("Salário-Hora Base (Calculado Pela IA)", value="Automático (Base / 220)", disabled=True, key="k_esal_hora")
                            
                        st.markdown("##### 🏥 INSS")
                        ci1, ci2 = st.columns(2)
                        with ci1: edit_afast = st.text_input("Afastamento (Deixe vazio se OK)", value=format_date_br(v_afast), placeholder="Ex: 01072025")
                        with ci2: edit_ret = st.text_input("Retorno (Deixe vazio se não voltou)", value=format_date_br(v_ret), placeholder="Ex: 01072025")
                        
                        if st.button("Confirmar e Salvar Alterações", key="k_ebtn_salvar"):
                            if not edit_id.strip() or not edit_nome.strip(): st.error("O ID/Matrícula e o Nome do colaborador não podem ficar vazios.")
                            else:
                                dt_a = parse_br_date_smart(edit_adm)
                                dt_d = parse_br_date_smart(edit_dem) if not ativo_ed else None
                                dt_af = parse_br_date_smart(edit_afast)
                                dt_r = parse_br_date_smart(edit_ret)
                                
                                adm_str = dt_a.strftime('%Y-%m-%d') if dt_a else None
                                dem_str = dt_d.strftime('%Y-%m-%d') if dt_d else None
                                af_str = dt_af.strftime('%Y-%m-%d') if dt_af else None
                                ret_str = dt_r.strftime('%Y-%m-%d') if dt_r else None
                                
                                sm_val = clean_money_to_db(edit_sal_mes)
                                sh_val = str(float(sm_val)/220.0) if sm_val is not None else None
                                
                                with engine.begin() as conn:
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET id=:nid, nome=:n, cpf=:c, cargo=:ca, admissao=:ad, demissao=:de, data_afastamento=:afast, data_retorno=:ret, chave_pix=:pix, salario_mes_12_24=:sm, salario_hora=:sh WHERE id=:oid"), {"nid": edit_id.strip(), "n": edit_nome, "c": edit_cpf, "ca": edit_cargo, "ad": adm_str, "de": dem_str, "afast": af_str, "ret": ret_str, "pix": edit_pix, "sm": sm_val, "sh": sh_val, "oid": str(colab_id)})
                                    if edit_id.strip() != str(colab_id):
                                        conn.execute(text("UPDATE historico_premiacoes_e_folha SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                    
                                    # CRIAR O PRIMEIRO HISTÓRICO CASO ELE ESTEJA VAZIO
                                    if sm_val:
                                        existe_hist = conn.execute(text("SELECT 1 FROM historico_premiacoes_e_folha WHERE id_colaborador = :id AND tipo_lancamento ILIKE '%Salário%'"), {"id": edit_id.strip()}).fetchone()
                                        if not existe_hist:
                                            comp_str = dt_a.strftime('%m/%Y') if dt_a else (dt_d.strftime('%m/%Y') if dt_d else datetime.today().strftime('%m/%Y'))
                                            conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": edit_id.strip(), "comp": comp_str, "val": float(sm_val)})
                                            
                                st.success("Salvo com Sucesso!"); st.session_state['busca_selecionada_id'] = edit_id.strip(); st.session_state['status_acao'] = None; st.rerun()
                        if st.button("Cancelar", key="k_ebtn_abandonar"): st.session_state['status_acao'] = None; st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

    elif sub_menu == "➕ Novo Cadastro":
        st.subheader("Inserir Novo Colaborador")
        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
        cn1, cn2 = st.columns(2)
        with cn1:
            n_id = st.text_input("ID / Matrícula")
            n_cpf = st.text_input("CPF")
            n_adm_str = st.text_input("Admissão (Pode digitar sem barras)", placeholder="Ex: 01072025")
            n_sal_mes = st.text_input("Salário-Mês")
            n_afast_str = st.text_input("Afastamento INSS (Opcional)", placeholder="Ex: 01072025")
        with cn2:
            n_nome = st.text_input("Nome Completo")
            s_c = st.selectbox("Cargo", LISTA_CARGOS)
            n_cargo = st.text_input("Digite o Cargo") if s_c == "OUTRO (DIGITAR MANUALMENTE)" else s_c
            a_nc = st.checkbox("✅ Colaborador Ativo", value=True)
            n_dem_str = st.text_input("Demissão (Sem barras)", placeholder="Ex: 01072025", disabled=a_nc)
            n_sal_hora = st.text_input("Salário-Hora Atual (Calculado pela IA)", value="Automático (Base / 220)", disabled=True)
            n_ret_str = st.text_input("Retorno INSS (Opcional)", placeholder="Ex: 01072025")
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("💾 Salvar Registro no Sistema"):
            dt_a = parse_br_date_smart(n_adm_str)
            dt_d = parse_br_date_smart(n_dem_str) if not a_nc else None
            dt_af = parse_br_date_smart(n_afast_str)
            dt_r = parse_br_date_smart(n_ret_str)
            
            sm_val = clean_money_to_db(n_sal_mes)
            sh_val = str(float(sm_val)/220.0) if sm_val is not None else None
            
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora) VALUES (:id, :n, :c, :ca, :ad, :de, :afast, :ret, :sm, :sh)"), {"id": str(n_id), "n": str(n_nome), "c": str(n_cpf), "ca": str(n_cargo), "ad": dt_a.strftime('%Y-%m-%d') if dt_a else None, "de": dt_d.strftime('%Y-%m-%d') if dt_d else None, "afast": dt_af.strftime('%Y-%m-%d') if dt_af else None, "ret": dt_r.strftime('%Y-%m-%d') if dt_r else None, "sm": sm_val, "sh": sh_val})
                
                # CRIA O PRIMEIRO HISTÓRICO AUTOMATICAMENTE NA GRAVAÇÃO
                if sm_val:
                    comp_str = dt_a.strftime('%m/%Y') if dt_a else (dt_d.strftime('%m/%Y') if dt_d else datetime.today().strftime('%m/%Y'))
                    conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": str(n_id), "comp": comp_str, "val": float(sm_val)})
                    
            st.success("Salvo!"); st.session_state['redirect_to_consulta'] = True; st.rerun()

# ==========================================
# 4. GESTÃO DE PRÊMIOS (ZAUT) - NOVO MÓDULO
# ==========================================
elif menu == "🏆 Gestão de Prêmios (ZAUT)":
    st.title("🏆 Lançamento de Prêmios (ZAUT)")
    st.markdown("Aponte as horas trabalhadas diretamente na grelha ou individualmente.")
    
    col_comp1, col_comp2 = st.columns([1, 3])
    with col_comp1:
        hoje = datetime.today()
        meses = [f"{str(m).zfill(2)}/{hoje.year}" for m in range(1, 13)] + [f"{str(m).zfill(2)}/{hoje.year+1}" for m in range(1, 13)]
        comp_sel = st.selectbox("Selecione a Competência:", meses, index=(hoje.month - 1))
    
    st.markdown("---")
    
    try:
        df_colabs = pd.read_sql("SELECT id, nome, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24 FROM cadastro_geral_colaborador ORDER BY nome ASC", engine)
        
        mes_comp = int(comp_sel.split('/')[0])
        ano_comp = int(comp_sel.split('/')[1])
        data_inicio_comp = pd.Timestamp(year=ano_comp, month=mes_comp, day=1)
        ultimo_dia = calendar.monthrange(ano_comp, mes_comp)[1]
        data_fim_comp = pd.Timestamp(year=ano_comp, month=mes_comp, day=ultimo_dia)
        
        colabs_elegiveis = []
        
        for _, row in df_colabs.iterrows():
            dt_dem = pd.to_datetime(row['demissao']) if pd.notna(row['demissao']) else None
            if dt_dem and dt_dem < data_inicio_comp: continue 
            
            dt_afast = pd.to_datetime(row['data_afastamento']) if pd.notna(row['data_afastamento']) else None
            dt_ret = pd.to_datetime(row['data_retorno']) if pd.notna(row['data_retorno']) else None
            if dt_afast and dt_afast < data_inicio_comp:
                if dt_ret is None or dt_ret > data_fim_comp: continue 
            
            sal_base_db = row['salario_mes_12_24']
            try:
                s_val = str(sal_base_db).upper().replace('R$', '').strip()
                s_val = s_val.replace('.', '').replace(',', '.') if '.' in s_val and ',' in s_val else s_val.replace(',', '.')
                sal_base_float = float(s_val)
            except: sal_base_float = 0.0
                
            if sal_base_float == 0.0:
                try:
                    with engine.connect() as conn2:
                        hs = conn2.execute(text("SELECT valor_lancamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id AND tipo_lancamento ILIKE '%Salário%' ORDER BY id DESC LIMIT 1"), {"id": str(row['id'])}).fetchone()
                        if hs: sal_base_float = float(hs[0])
                except: pass
                
            colabs_elegiveis.append({"id": str(row['id']), "nome": str(row['nome']), "sal_hora": sal_base_float / 220.0 if sal_base_float > 0 else 0.0})
            
        if not colabs_elegiveis:
            st.warning("Nenhum colaborador elegível (ativo) encontrado para esta competência.")
        else:
            aba_lote, aba_ind = st.tabs(["📊 Planilha de Lote Rápido", "👤 Lançamento Individual"])
            
            with aba_lote:
                st.markdown("Preencha as horas e selecione o serviço. Colaboradores com **0.00** serão ignorados na gravação.")
                df_lote = pd.DataFrame(colabs_elegiveis)
                df_lote['Horas Prêmio (HP)'] = 0.00
                df_lote['Descrição do Serviço'] = None
                
                edited_df = st.data_editor(
                    df_lote,
                    column_config={
                        "id": st.column_config.TextColumn("Matrícula", disabled=True),
                        "nome": st.column_config.TextColumn("Colaborador", disabled=True),
                        "sal_hora": st.column_config.NumberColumn("Valor Hora", format="R$ %.2f", disabled=True),
                        "Horas Prêmio (HP)": st.column_config.NumberColumn("Total HP", min_value=0.0, format="%.2f", step=1.0),
                        "Descrição do Serviço": st.column_config.SelectboxColumn("Serviço", options=LISTA_SERVICOS_PREMIO)
                    },
                    disabled=["id", "nome", "sal_hora"], hide_index=True, use_container_width=True, key="editor_lote_zaut"
                )
                
                c_btn_lt1, c_btn_lt2 = st.columns([1, 4])
                if c_btn_lt1.button("💾 Salvar Lote Inteiro", type="primary"):
                    lancamentos = edited_df[edited_df['Horas Prêmio (HP)'] > 0]
                    if lancamentos.empty: st.warning("Nenhuma hora prêmio preenchida na planilha.")
                    else:
                        sucessos, erros = 0, 0
                        with engine.begin() as conn:
                            for _, row_edit in lancamentos.iterrows():
                                hp = float(row_edit['Horas Prêmio (HP)'])
                                desc = row_edit['Descrição do Serviço'] or "PRÊMIO PRODUÇÃO (ZAUT)"
                                val_hora = float(row_edit['sal_hora'])
                                val_final = (val_hora * hp) + 1.00 
                                try:
                                    conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_c, :comp, :tipo, :val, 'Lançado')"), {"id_c": str(row_edit['id']), "comp": comp_sel, "tipo": f"Prêmio: {desc} (Horas: {hp})", "val": val_final})
                                    sucessos += 1
                                except: erros += 1
                        if sucessos > 0:
                            st.success(f"✅ {sucessos} recibos de prêmio gerados com a taxa ZAUT aplicada.")
                            if 'editor_lote_zaut' in st.session_state: del st.session_state['editor_lote_zaut']
                            st.rerun()
                        if erros > 0: st.error(f"Ocorreram {erros} erros.")

                if c_btn_lt2.button("❌ Cancelar / Limpar Planilha", key="btn_canc_lote"):
                    if 'editor_lote_zaut' in st.session_state: del st.session_state['editor_lote_zaut']
                    st.rerun()

            with aba_ind:
                opcoes_dropdown = {f"{c['nome']} (ID: {c['id']})": c for c in colabs_elegiveis}
                colab_escolhido = st.selectbox("Selecione o Colaborador:", list(opcoes_dropdown.keys()))
                dados_c = opcoes_dropdown[colab_escolhido]
                
                st.markdown(f"##### 📜 Lançamentos já realizados para {dados_c['nome']} em {comp_sel}:")
                try:
                    df_ja_lancado = pd.read_sql(text("SELECT tipo_lancamento, valor_lancamento, status_pagamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id_c AND competencia = :comp"), engine, params={"id_c": dados_c['id'], "comp": comp_sel})
                    if not df_ja_lancado.empty:
                        df_jl_view = df_ja_lancado.copy()
                        df_jl_view['valor_lancamento'] = df_jl_view['valor_lancamento'].apply(format_currency_brl)
                        df_jl_view.rename(columns={'tipo_lancamento': 'Descrição do Prêmio/Lançamento', 'valor_lancamento': 'Valor', 'status_pagamento': 'Status'}, inplace=True)
                        st.dataframe(df_jl_view, use_container_width=True, hide_index=True)
                    else: st.info(f"O colaborador ainda NÃO recebeu nenhum prêmio nesta competência ({comp_sel}). Lançamento livre!")
                except: pass
                st.markdown("---")
                
                if st.session_state.get('zaut_acao') != 'lancando':
                    if st.button(f"➕ Iniciar Lançamento para {dados_c['nome']}", type="primary"):
                        st.session_state['zaut_acao'] = 'lancando'
                        st.rerun()
                else:
                    st.markdown("#### 📝 Painel de Lançamento Ativo")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    
                    sal_hora_base = dados_c['sal_hora']
                    if sal_hora_base == 0.0:
                        st.warning("⚠️ Valor Hora Base zerado na Ficha e no Histórico. Digite o valor manualmente para prosseguir:")
                        sal_hora_manual = st.text_input("Valor Hora (R$)", key="k_sh_manual", placeholder="Ex: 9,38")
                        try: sal_hora_base = float(clean_money_to_db(sal_hora_manual)) if clean_money_to_db(sal_hora_manual) else 0.0
                        except: sal_hora_base = 0.0
                    else:
                        st.markdown(f"**Valor Hora Calculado pelo Sistema:** R$ {format_brl_number(sal_hora_base)}")
                    
                    cli1, cli2 = st.columns(2)
                    with cli1: hp_ind = st.text_input("Quantidade de Horas (Pressione ENTER)", key="k_hpi", placeholder="Ex: 47,00")
                    with cli2: 
                        desc_ind = st.selectbox("Descrição do Serviço", LISTA_SERVICOS_PREMIO, key="k_di")
                        desc_final_str = st.text_input("Especifique a Descrição:", key="k_d_outro") if desc_ind == "OUTRO (DIGITAR MANUALMENTE)" else desc_ind
                    
                    hp_ind_float = 0.0
                    try: hp_ind_float = float(clean_money_to_db(hp_ind)) if clean_money_to_db(hp_ind) else 0.0
                    except: pass
                    
                    val_final_ind = (sal_hora_base * hp_ind_float) + 1.00 if hp_ind_float > 0 else 0.00
                    
                    st.markdown('<p class="field-label">RECIBO FINAL A GRAVAR</p>', unsafe_allow_html=True)
                    if hp_ind_float > 0 and sal_hora_base > 0:
                        st.markdown(f'<p class="field-highlight">R$ {format_brl_number(val_final_ind)}</p>', unsafe_allow_html=True)
                        st.caption(f"(Inclui R$ 1,00 Taxa ZAUT)")
                    else: st.markdown(f'<p class="field-value">Aguardando Horas e Valor...</p>', unsafe_allow_html=True)
                    
                    c_btn_i1, c_btn_i2 = st.columns([1, 4])
                    if c_btn_i1.button("💾 Gravar Prêmio", type="primary", key="btn_ind_gravar"):
                        if hp_ind_float <= 0: st.error("⚠️ Digite horas válidas (pressione ENTER primeiro para calcular).")
                        elif sal_hora_base <= 0: st.error("⚠️ O valor da hora não pode ser zero.")
                        elif not desc_final_str.strip(): st.error("⚠️ Especifique o serviço.")
                        else:
                            try:
                                with engine.begin() as conn: conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_c, :comp, :tipo, :val, 'Lançado')"), {"id_c": dados_c['id'], "comp": comp_sel, "tipo": f"Prêmio: {desc_final_str} (Horas: {hp_ind_float})", "val": val_final_ind})
                                st.success("✅ Gravado com sucesso!")
                                for k in ['k_hpi', 'k_sh_manual', 'k_d_outro', 'zaut_acao']:
                                    if k in st.session_state: del st.session_state[k]
                                st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")
                            
                    if c_btn_i2.button("❌ Cancelar / Fechar Painel", key="btn_ind_fechar"):
                        for k in ['k_hpi', 'k_sh_manual', 'k_d_outro', 'zaut_acao']:
                            if k in st.session_state: del st.session_state[k]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erro operacional no filtro: {e}")

# ==========================================
# 5. AUDITORIA CCT (IA)
# ==========================================
elif menu == "🔎 Auditoria CCT (IA)":
    st.title("🔎 Auditoria Automatizada da Folha")
    
    if st.button("🚀 Executar Varredura Completa na Folha", type="primary"):
        with st.spinner("A cruzar salários atuais com as normas..."):
            try:
                df_folha = pd.read_sql("SELECT id, nome, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24 FROM cadastro_geral_colaborador", engine)
                hoje = pd.Timestamp.today()
                
                def calcular_auditoria(row):
                    cargo = str(row['cargo']).upper() if pd.notna(row['cargo']) else ""
                    sal_atual = float(clean_money_to_db(row['salario_mes_12_24']) or 0.0)
                    
                    if pd.notna(row['demissao']) and str(row['demissao']).strip() != "": return pd.Series(["Demitido", "-", "Ok"])
                    if pd.notna(row['data_afastamento']) and str(row['data_afastamento']).strip() != "" and pd.isna(row['data_retorno']): return pd.Series(["Afastado INSS", "-", "Ok"])
                    if "ESTAGIÁR" in cargo or "APRENDIZ" in cargo: return pd.Series(["N/A", "-", "Ok"])
                    
                    piso = 1518.00
                    if any(x in cargo for x in ["PEDREIRO", "CARPINTEIRO", "PINTOR", "ENCANADOR"]): piso = 2063.92
                    elif any(x in cargo for x in ["SERVENTE", "AJUDANTE"]): piso = 1548.00
                    elif "MESTRE" in cargo: piso = 4068.99
                        
                    try:
                        adm_dt = pd.to_datetime(row['admissao'])
                        ciclos = min(((hoje.year - adm_dt.year) * 12 + hoje.month - adm_dt.month) // 18, 3)
                    except: return pd.Series(["Erro Data", "-", "Pendente"])
                        
                    if "SERVENTE" in cargo: ciclos = 0
                    salario_ideal = piso * (1.05 ** ciclos)
                    
                    st_aud = "⚠️ Sem Salário" if sal_atual == 0.0 else ("❌ Abaixo CCT" if round(sal_atual, 2) < round(salario_ideal, 2) else "✅ Perfeito")
                    return pd.Series([f"R$ {format_brl_number(salario_ideal)}", f"R$ {format_brl_number(sal_atual)}", st_aud])

                df_folha[['Salário Ideal (CCT)', 'Salário Atual', 'Status']] = df_folha.apply(calcular_auditoria, axis=1)
                st.dataframe(df_folha[~df_folha['Status'].str.contains("Demitido")][['id', 'nome', 'cargo', 'Salário Atual', 'Salário Ideal (CCT)', 'Status']], use_container_width=True, hide_index=True)
            except Exception as e: st.error(f"Erro: {e}")    
