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
                focusable[index + 1].focus();
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
if 'busca_selecionada_id' not in st.session_state:
    st.session_state['busca_selecionada_id'] = None
if 'status_acao' not in st.session_state:
    st.session_state['status_acao'] = None
if 'sub_menu_index' not in st.session_state:
    st.session_state['sub_menu_index'] = 0
if 'redirect_to_consulta' not in st.session_state:
    st.session_state['redirect_to_consulta'] = False

if st.session_state['redirect_to_consulta']:
    st.session_state['sub_menu_index'] = 0
    st.session_state['redirect_to_consulta'] = False
    st.rerun()

# --- FUNÇÕES DE FORMATAÇÃO E LIMPEZA ---
def clean_money_to_db(val):
    if not val or str(val).strip() == "" or str(val).strip().lower() == "none": return None
    s = str(val).upper().replace('R$', '').strip()
    if '.' in s and ',' in s: 
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s: 
        s = s.replace(',', '.')
    try: return str(float(s))
    except: return None

def format_brl_number(val):
    try:
        if val is None or str(val).strip() == "" or str(val).lower() == "nan" or str(val).lower() == "none":
            return ""
        return f"{float(val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return val

def format_currency_brl(val):
    try:
        if val is None or str(val).strip() == "" or str(val).lower() == "nan" or str(val).lower() == "none":
            return ""
        return f"R$ {float(val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return val

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
                if arquivo.name.endswith('.xlsx'):
                    df_bruto = pd.read_excel(arquivo, engine='openpyxl')
                else:
                    df_bruto = pd.read_csv(arquivo)
                
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
                        except Exception as inner_e:
                            st.warning(f"Linha ignorada: {inner_e}")
                st.success("Ingestão executada com sucesso!")
            except Exception as e:
                st.error(f"Erro Crítico: {e}")

    with aba_imp2:
        st.subheader("Extração Inteligente de Matriz Salarial")
        st.markdown('<div style="background-color: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; padding: 15px; border-radius: 8px; margin-bottom: 20px;">', unsafe_allow_html=True)
        st.markdown("⚠️ **OPÇÃO NUCLEAR:** ZERAR completamente a tabela de histórico de salários do banco de dados.")
        if st.button("🧨 ESVAZIAR TODO O HISTÓRICO DO BANCO", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE historico_premiacoes_e_folha RESTART IDENTITY"))
                st.success("💥 BANCO DE HISTÓRICO ZERADO!")
            except Exception as e:
                st.error(f"Erro ao limpar: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        arquivo_hist = st.file_uploader("Selecione a matriz salarial (.xlsx)", type=["xlsx"], key="file_hist")
        
        if arquivo_hist and st.button("🚀 Processar e Injetar Histórico", type="primary"):
            with st.spinner("Analisando cruzamentos temporais..."):
                try:
                    df_excel = pd.read_excel(arquivo_hist, engine='openpyxl')
                    with engine.connect() as conn:
                        db_cols = conn.execute(text("SELECT id, nome, admissao, demissao FROM cadastro_geral_colaborador")).fetchall()
                    
                    db_dict = {str(r.nome).strip().upper(): {'id': str(r.id), 'admissao': str(r.admissao) if r.admissao else None, 'demissao': str(r.demissao) if r.demissao else None} for r in db_cols if r.nome}
                    lista_ids_numericos = [int(r.id) for r in db_cols if str(r.id).isdigit()]
                    proximo_id_livre = max(lista_ids_numericos) + 1 if lista_ids_numericos else 1000
                    
                    def get_comp_date(col_name):
                        match = re.search(r'(\d{2})/(\d{2})', str(col_name))
                        if match: return pd.Timestamp(year=2000 + int(match.group(2)), month=int(match.group(1)), day=1)
                        return None
                    def parse_str_date(d_str):
                        try:
                            dt = pd.to_datetime(d_str)
                            return pd.Timestamp(year=dt.year, month=dt.month, day=1)
                        except: return None

                    inserts_pendentes, linhas_processadas, recuperados_ia = [], 0, 0
                    coluna_nome = next((col for col in df_excel.columns if str(col).strip().upper() == 'NOME'), None)

                    if not coluna_nome:
                        st.error("Erro: A planilha não possui a coluna 'Nome'.")
                    else:
                        for _, row in df_excel.iterrows():
                            nome_xls = str(row[coluna_nome]).strip().upper()
                            if not nome_xls or nome_xls == 'NAN': continue
                                
                            if nome_xls not in db_dict:
                                novo_id = str(proximo_id_livre)
                                proximo_id_livre += 1
                                with engine.begin() as conn_recupera:
                                    conn_recupera.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome) ON CONFLICT (id) DO NOTHING"), {"id": novo_id, "nome": nome_xls})
                                db_dict[nome_xls] = {'id': novo_id, 'admissao': None, 'demissao': None}
                                recuperados_ia += 1

                            colab = db_dict[nome_xls]
                            dt_adm = parse_str_date(colab['admissao'])
                            dt_dem = parse_str_date(colab['demissao'])
                            
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
                                        
                                    if val_float > 0:
                                        inserts_pendentes.append({"id_colab": colab['id'], "comp": f"{dt_coluna.month:02d}/{dt_coluna.year}", "tipo": "Salário Mensal", "valor": val_float})
                            linhas_processadas += 1

                        if inserts_pendentes:
                            with engine.begin() as conn:
                                for item in inserts_pendentes:
                                    existe = conn.execute(text("SELECT 1 FROM historico_premiacoes_e_folha WHERE id_colaborador = :id_colab AND competencia = :comp AND tipo_lancamento = :tipo"), item).fetchone()
                                    if not existe:
                                        conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_colab, :comp, :tipo, :valor, 'Pago')"), item)
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
                    if not resultados:
                        resultados = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t ORDER BY nome ASC"), {"t": f"%{termo.strip()}%"}).fetchall()
                    if not resultados:
                        st.warning("Nenhum registro encontrado para o critério informado.")
                    elif len(resultados) == 1:
                        st.session_state['busca_selecionada_id'] = str(resultados[0].id)
                        st.rerun() 
                    else:
                        st.info("Múltiplos registros encontrados:")
                        opcoes_lista = {f"ID: {r.id} | Nome: {r.nome}": str(r.id) for r in resultados}
                        escolha = st.selectbox("Selecione:", list(opcoes_lista.keys()))
                        if st.button("Confirmar Seleção"):
                            st.session_state['busca_selecionada_id'] = opcoes_lista[escolha]
                            st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

        if st.session_state['busca_selecionada_id']:
            colab_id = st.session_state['busca_selecionada_id']
            try:
                with engine.connect() as conn:
                    colab = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)}).fetchone()
                    df_fin = pd.read_sql(text("SELECT * FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), conn, params={"id": str(colab_id)})
                    fin_data = df_fin.iloc[0].to_dict() if not df_fin.empty else None
                    df_hist = pd.read_sql(text("SELECT id as id_lancamento, competencia, tipo_lancamento, valor_lancamento, status_pagamento, retroativo_pago, data_pagamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id ORDER BY id DESC"), conn, params={"id": str(colab_id)})
                    df_evo_salarial = pd.read_sql(text("SELECT data_alteracao, motivo, salario_anterior, novo_salario FROM historico_salarial WHERE id_colaborador = :id ORDER BY data_alteracao DESC, id DESC"), conn, params={"id": str(colab_id)})
                
                if colab:
                    salario_mes_display, salario_hora_display, val_atual_base = "Não Informado", "Não Informado", 0.0
                    if colab.salario_mes_12_24 and str(colab.salario_mes_12_24).strip() != "" and str(colab.salario_mes_12_24).strip().lower() != "none":
                        try:
                            s_val = str(colab.salario_mes_12_24).upper().replace('R$', '').strip()
                            s_val = s_val.replace('.', '').replace(',', '.') if '.' in s_val and ',' in s_val else s_val.replace(',', '.')
                            val_m = float(s_val)
                            val_h = val_m / 220.0
                            val_atual_base = val_m
                            salario_mes_display = f"R$ {val_m:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            salario_hora_display = f"R$ {val_h:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        except:
                            salario_mes_display = str(colab.salario_mes_12_24)
                            salario_hora_display = str(colab.salario_hora) if colab.salario_hora else "Não Informado"
                            val_atual_base = -1.0 
                    
                    st.markdown("### 📋 Ficha Completa do Colaborador")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown('<p class="field-label">ID / MATRÍCULA</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.id}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">CARGO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.cargo if colab.cargo else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-MÊS ATUAL</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{salario_mes_display}</p>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<p class="field-label">NOME COMPLETO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.nome}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE ADMISSÃO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{pd.to_datetime(colab.admissao).strftime("%d/%m/%Y") if colab.admissao else "Não Informada"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-HORA ATUAL</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{salario_hora_display}</p>', unsafe_allow_html=True)
                    with c3:
                        st.markdown('<p class="field-label">CPF</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.cpf if colab.cpf else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE DEMISSÃO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{pd.to_datetime(colab.demissao).strftime("%d/%m/%Y") if colab.demissao else "Ativo / Em Aberto"}</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    v_afast = getattr(colab, 'data_afastamento', None)
                    v_ret = getattr(colab, 'data_retorno', None)
                    if v_afast:
                        st.markdown("### 🏥 Status de Afastamento (INSS)")
                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        ca1, ca2 = st.columns(2)
                        with ca1:
                            st.markdown('<p class="field-label">AFASTAMENTO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value" style="color:#facc15;">{pd.to_datetime(v_afast).strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)
                        with ca2:
                            st.markdown('<p class="field-label">RETORNO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{pd.to_datetime(v_ret).strftime("%d/%m/%Y") if v_ret else "Ainda Afastado"}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 🏦 Dados Bancários (PIX Principal)")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if fin_data or colab.chave_pix:
                        cf1, cf2 = st.columns(2)
                        with cf1:
                            st.markdown('<p class="field-label">BANCO</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{(fin_data.get("banco") if fin_data else "") or "Não Informado"}</p>', unsafe_allow_html=True)
                        with cf2:
                            st.markdown('<p class="field-label">CHAVE PIX</p>', unsafe_allow_html=True); st.markdown(f'<p class="field-value">{colab.chave_pix or (fin_data.get("chave_pix") if fin_data else "Não Informado")}</p>', unsafe_allow_html=True)
                    else: st.info("Nenhum dado bancário registrado.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 💰 Histórico Mensal de Prêmios e Folha")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if not df_hist.empty:
                        cols_desejadas = ['competencia', 'tipo_lancamento', 'valor_lancamento', 'status_pagamento']
                        df_view = df_hist[[c for c in cols_desejadas if c in df_hist.columns]].copy()
                        df_view['valor_lancamento'] = df_view['valor_lancamento'].apply(format_brl_number)
                        df_view.rename(columns={'competencia': 'Competência', 'tipo_lancamento': 'Tipo', 'valor_lancamento': 'Valor (R$)', 'status_pagamento': 'Status'}, inplace=True)
                        st.dataframe(df_view, use_container_width=True, hide_index=True)
                    else: st.info("Nenhum histórico registrado.")
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
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)})
                            st.success("Excluído!"); st.session_state['busca_selecionada_id'] = None; st.session_state['status_acao'] = None; st.rerun()
                        if cx2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_lancamento_avulso':
                        st.info("➕ **Inserção Avulsa:**")
                        c_av1, c_av2, c_av3 = st.columns(3)
                        with c_av1: av_comp = st.text_input("Competência (MM/AAAA)", placeholder="Ex: 09/2025")
                        with c_av2: av_tipo = st.selectbox("Tipo", ["Salário Mensal", "Prêmio ZAUT", "Férias", "Outros"])
                        with c_av3: av_valor = st.text_input("Valor", placeholder="2354,90")
                        c_bt1, c_bt2 = st.columns([1, 4])
                        if c_bt1.button("💾 Salvar"):
                            v_clean = clean_money_to_db(av_valor)
                            if v_clean:
                                with engine.begin() as conn:
                                    conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, :tipo, :valor, 'Pago')"), {"id": str(colab_id), "comp": av_comp.strip(), "tipo": av_tipo, "valor": float(v_clean)})
                                st.success("Salvo!"); st.session_state['status_acao'] = None; st.rerun()
                            else: st.error("Valor inválido.")
                        if c_bt2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_corrigir_historico':
                        st.info("🛠️ **Editor de Histórico:**")
                        if not df_hist.empty:
                            opcoes_hist = {f"Comp: {row['competencia']} | Tipo: {row['tipo_lancamento']} | Val: R$ {format_brl_number(row['valor_lancamento'])}": row['id_lancamento'] for _, row in df_hist.iterrows()}
                            id_alvo = opcoes_hist[st.selectbox("Selecione:", list(opcoes_hist.keys()))]
                            novo_val = st.text_input("Novo Valor", placeholder="Ex: 2354,90")
                            ch1, ch2, ch3 = st.columns(3)
                            if ch1.button("💾 Salvar"):
                                vc = clean_money_to_db(novo_val)
                                if vc:
                                    with engine.begin() as conn: conn.execute(text("UPDATE historico_premiacoes_e_folha SET valor_lancamento = :v WHERE id = :id"), {"v": float(vc), "id": id_alvo})
                                    st.success("Corrigido!"); st.session_state['status_acao'] = None; st.rerun()
                            if ch2.button("🗑️ Apagar"):
                                with engine.begin() as conn: conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id = :id"), {"id": id_alvo})
                                st.success("Apagado!"); st.session_state['status_acao'] = None; st.rerun()
                            if ch3.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_alterar':
                        st.info("📝 Modo de Edição Ativo")
                        try: dt_adm_val = pd.to_datetime(colab.admissao).date() if colab.admissao else None
                        except: dt_adm_val = None
                        try: dt_dem_val = pd.to_datetime(colab.demissao).date() if colab.demissao else None
                        except: dt_dem_val = None
                        try: dt_afast_val = pd.to_datetime(v_afast).date() if v_afast else None
                        except: dt_afast_val = None
                        try: dt_ret_val = pd.to_datetime(v_ret).date() if v_ret else None
                        except: dt_ret_val = None
                        
                        cargo_idx = LISTA_CARGOS.index(str(colab.cargo).upper().strip()) if str(colab.cargo).upper().strip() in LISTA_CARGOS else (len(LISTA_CARGOS)-1)
                        
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            edit_id = st.text_input("ID / Matrícula", value=str(colab.id), key="k_eid")
                            edit_nome = st.text_input("Nome Completo", value=str(colab.nome), key="k_enome")
                            edit_cpf = st.text_input("CPF", value=str(colab.cpf) if colab.cpf else "", key="k_ecpf")
                            edit_adm = st.date_input("Data de Admissão", value=dt_adm_val, format="DD/MM/YYYY")
                            edit_sal_mes = st.text_input("Salário-Mês Base", value=str(colab.salario_mes_12_24) if colab.salario_mes_12_24 else "", key="k_esal_mes")
                        with ce2:
                            sel_cargo = st.selectbox("Cargo", LISTA_CARGOS, index=cargo_idx)
                            edit_cargo = st.text_input("Digite o Cargo", value=str(colab.cargo) if cargo_idx == len(LISTA_CARGOS)-1 else "") if sel_cargo == "OUTRO (DIGITAR MANUALMENTE)" else sel_cargo
                            ativo_ed = st.checkbox("✅ Colaborador Ativo (Remove Demissão)", value=(dt_dem_val is None))
                            edit_dem = None if ativo_ed else st.date_input("Data de Demissão", value=dt_dem_val if dt_dem_val else datetime.today().date(), format="DD/MM/YYYY")
                            edit_pix = st.text_input("Chave PIX", value=str(colab.chave_pix) if colab.chave_pix else "", key="k_epix")
                            edit_sal_hora = st.text_input("Salário-Hora Base", value=str(colab.salario_hora) if colab.salario_hora else "", key="k_esal_hora")
                            
                        st.markdown("##### 🏥 INSS")
                        ci1, ci2 = st.columns(2)
                        with ci1: edit_afast = st.date_input("Afastamento (vazio=OK)", value=dt_afast_val, format="DD/MM/YYYY", key="k_eafast")
                        with ci2: edit_ret = st.date_input("Retorno (vazio=Não voltou)", value=dt_ret_val, format="DD/MM/YYYY", key="k_eret")
                        
                        if st.button("Confirmar e Salvar Alterações", key="k_ebtn_salvar"):
                            adm_str = edit_adm.strftime('%Y-%m-%d') if edit_adm else None
                            dem_str = edit_dem.strftime('%Y-%m-%d') if edit_dem else None
                            af_str = edit_afast.strftime('%Y-%m-%d') if edit_afast else None
                            ret_str = edit_ret.strftime('%Y-%m-%d') if edit_ret else None
                            with engine.begin() as conn:
                                conn.execute(text("UPDATE cadastro_geral_colaborador SET id=:nid, nome=:n, cpf=:c, cargo=:ca, admissao=:ad, demissao=:de, data_afastamento=:afast, data_retorno=:ret, chave_pix=:pix, salario_mes_12_24=:sm, salario_hora=:sh WHERE id=:oid"), {"nid": edit_id.strip(), "n": edit_nome, "c": edit_cpf, "ca": edit_cargo, "ad": adm_str, "de": dem_str, "afast": af_str, "ret": ret_str, "pix": edit_pix, "sm": clean_money_to_db(edit_sal_mes), "sh": clean_money_to_db(edit_sal_hora), "oid": str(colab_id)})
                                if edit_id.strip() != str(colab_id):
                                    conn.execute(text("UPDATE historico_premiacoes_e_folha SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                            st.success("Salvo!"); st.session_state['busca_selecionada_id'] = edit_id.strip(); st.session_state['status_acao'] = None; st.rerun()
                        if st.button("Cancelar", key="k_ebtn_abandonar"): st.session_state['status_acao'] = None; st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

    elif sub_menu == "➕ Novo Cadastro":
        st.subheader("Inserir Novo Colaborador")
        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
        cn1, cn2 = st.columns(2)
        with cn1:
            n_id = st.text_input("ID / Matrícula")
            n_cpf = st.text_input("CPF")
            n_adm = st.date_input("Admissão", value=None, format="DD/MM/YYYY")
            n_sal_mes = st.text_input("Salário-Mês")
            n_afast = st.date_input("Afastamento INSS (Opcional)", value=None, format="DD/MM/YYYY")
        with cn2:
            n_nome = st.text_input("Nome Completo")
            s_c =
