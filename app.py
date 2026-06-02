import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import re
from datetime import datetime, date
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

# Injeção das colunas de INSS se não existirem
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN data_afastamento VARCHAR(50);"))
except:
    pass # A coluna já existe
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN data_retorno VARCHAR(50);"))
except:
    pass # A coluna já existe

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

# --- INJEÇÃO DE JAVASCRIPT PROFISSIONAL (AUTOFILL + ENTER = TAB) ---
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
        if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
            if (e.target.hasAttribute('aria-controls') || e.target.hasAttribute('aria-expanded')) {
                return; 
            }
            e.preventDefault();
            e.stopPropagation();
            
            var selectors = 'input:not([disabled]):not([type="hidden"]), button:not([disabled])';
            var focusable = Array.from(doc.querySelectorAll(selectors));
            focusable = focusable.filter(el => el.offsetWidth > 0 || el.offsetHeight > 0);
            var index = focusable.indexOf(e.target);
            
            if (index > -1 && index < focusable.length - 1) {
                focusable[index + 1].focus();
            }
        }
    }, true); 
}
</script>
""", height=0, width=0)

# --- LISTA PADRÃO DE CARGOS (CCT) ---
LISTA_CARGOS = [
    "PEDREIRO", "SERVENTE", "AJUDANTE PRATICO", "CARPINTEIRO", "PINTOR", 
    "ENCANADOR", "MESTRE DE OBRAS", "ENCARREGADO", 
    "APRENDIZ LEGAL EM ARCO ADMINISTRATIVO", "ESTAGIÁRIO", 
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
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros", "🔎 Auditoria CCT (IA)"])

# --- 1. VISÃO GERAL ---
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    try:
        # Puxa os dados incluindo as novas colunas
        df = pd.read_sql("""
            SELECT id, nome, cpf, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora 
            FROM cadastro_geral_colaborador 
            ORDER BY nome ASC
        """, engine)
        
        df['salario_mes_12_24'] = df['salario_mes_12_24'].apply(format_currency_brl)
        df['salario_hora'] = df['salario_hora'].apply(format_currency_brl)
        
        # Renomeia para ficar bonito na tela
        df.rename(columns={
            'data_afastamento': 'Afastamento (INSS)',
            'data_retorno': 'Retorno (INSS)'
        }, inplace=True)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados do painel: {e}")

# --- 2. IMPORTAÇÃO INTELIGENTE (COM MOTOR ETL E AUTO-RECUPERAÇÃO) ---
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
                            if not v_id or v_id == 'nan':
                                continue 
                                
                            conn.execute(text("""
                                INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, salario_mes_12_24, salario_hora) 
                                VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :sal_mes, :sal_hora)
                                ON CONFLICT (id) DO UPDATE SET 
                                    nome = EXCLUDED.nome,
                                    cpf = EXCLUDED.cpf,
                                    cargo = EXCLUDED.cargo,
                                    admissao = EXCLUDED.admissao,
                                    demissao = EXCLUDED.demissao,
                                    salario_mes_12_24 = EXCLUDED.salario_mes_12_24,
                                    salario_hora = EXCLUDED.salario_hora
                            """), {
                                "id": v_id, 
                                "nome": str(row.iloc[1]) if len(row) > 1 else None,
                                "cpf": str(row.iloc[2]) if len(row) > 2 else None,
                                "cargo": str(row.iloc[3]) if len(row) > 3 else None,
                                "admissao": str(row.iloc[4]) if len(row) > 4 else None,
                                "demissao": str(row.iloc[5]) if len(row) > 5 else None,
                                "sal_mes": str(row.iloc[6]) if len(row) > 6 else None,
                                "sal_hora": str(row.iloc[7]) if len(row) > 7 else None
                            })
                        except Exception as inner_e:
                            st.warning(f"Linha ignorada devido a formato incompatível. Detalhe: {inner_e}")
                            
                st.success("Ingestão de dados de cadastro executada com sucesso!")
            except Exception as e:
                st.error(f"Erro Crítico no mapeamento das colunas: {e}")

    with aba_imp2:
        st.subheader("Extração Inteligente de Matriz Salarial")
        st.markdown("""
        O sistema lerá os meses na planilha, aplicará a **Barreira de 12/2024** + **Janela de Admissão/Demissão** e irá **Recuperar Automaticamente** qualquer colaborador excluído por engano.
        """)
        
        st.markdown('<div style="background-color: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; padding: 15px; border-radius: 8px; margin-bottom: 20px;">', unsafe_allow_html=True)
        st.markdown("⚠️ **OPÇÃO NUCLEAR:** Este botão vai **ZERAR** completamente a tabela de histórico de salários do banco de dados para podermos começar do zero e sem erros.")
        
        if st.button("🧨 ESVAZIAR TODO O HISTÓRICO DO BANCO", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE historico_premiacoes_e_folha RESTART IDENTITY"))
                st.success("💥 BANCO DE HISTÓRICO ZERADO COM SUCESSO! Pode consultar qualquer ficha, os pagamentos sumiram. Faça a importação da planilha novamente.")
            except Exception as e:
                st.error(f"Erro ao limpar: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        arquivo_hist = st.file_uploader("Selecione a matriz salarial (.xlsx)", type=["xlsx"], key="file_hist")
        
        if arquivo_hist and st.button("🚀 Processar e Injetar Histórico", type="primary"):
            with st.spinner("Analisando cruzamentos de dados temporais e recuperando cadastros perdidos..."):
                try:
                    df_excel = pd.read_excel(arquivo_hist, engine='openpyxl')
                    
                    with engine.connect() as conn:
                        db_cols = conn.execute(text("SELECT id, nome, admissao, demissao FROM cadastro_geral_colaborador")).fetchall()
                    
                    db_dict = {}
                    lista_ids_numericos = []
                    
                    for r in db_cols:
                        if r.nome:
                            db_dict[str(r.nome).strip().upper()] = {
                                'id': str(r.id),
                                'admissao': str(r.admissao) if r.admissao else None,
                                'demissao': str(r.demissao) if r.demissao else None
                            }
                        if str(r.id).isdigit():
                            lista_ids_numericos.append(int(r.id))
                    
                    proximo_id_livre = max(lista_ids_numericos) + 1 if lista_ids_numericos else 1000
                    
                    def get_comp_date(col_name):
                        match = re.search(r'(\d{2})/(\d{2})', str(col_name))
                        if match:
                            m = int(match.group(1))
                            y = 2000 + int(match.group(2))
                            return pd.Timestamp(year=y, month=m, day=1)
                        return None
                        
                    def parse_str_date(d_str):
                        try:
                            dt = pd.to_datetime(d_str)
                            return pd.Timestamp(year=dt.year, month=dt.month, day=1)
                        except:
                            return None

                    inserts_pendentes = []
                    linhas_processadas = 0
                    recuperados_ia = 0
                    
                    coluna_nome = next((col for col in df_excel.columns if str(col).strip().upper() == 'NOME'), None)

                    if not coluna_nome:
                        st.error("Erro: A planilha enviada não possui uma coluna com o título 'Nome'.")
                    else:
                        for _, row in df_excel.iterrows():
                            nome_xls = str(row[coluna_nome]).strip().upper()
                            if not nome_xls or nome_xls == 'NAN':
                                continue
                                
                            if nome_xls not in db_dict:
                                novo_id = str(proximo_id_livre)
                                proximo_id_livre += 1
                                
                                with engine.begin() as conn_recupera:
                                    conn_recupera.execute(text("""
                                        INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome)
                                        ON CONFLICT (id) DO NOTHING
                                    """), {"id": novo_id, "nome": nome_xls})
                                
                                db_dict[nome_xls] = {
                                    'id': novo_id,
                                    'admissao': None,
                                    'demissao': None
                                }
                                recuperados_ia += 1

                            colab = db_dict[nome_xls]
                            dt_adm = parse_str_date(colab['admissao'])
                            dt_dem = parse_str_date(colab['demissao'])
                            
                            for col in df_excel.columns:
                                col_str = str(col).strip().upper()
                                if "SALÁRIO MÊS" in col_str or "SALARIO MES" in col_str:
                                    val = row[col]
                                    if pd.isna(val) or str(val).strip() == "":
                                        continue
                                        
                                    dt_coluna = get_comp_date(col_str)
                                    if not dt_coluna:
                                        continue
                                        
                                    if dt_coluna < pd.Timestamp(year=2024, month=12, day=1):
                                        continue
                                        
                                    if dt_adm and dt_coluna < dt_adm:
                                        continue
                                    if dt_dem and dt_coluna > dt_dem:
                                        continue
                                        
                                    try:
                                        if isinstance(val, str):
                                            val_limpo = val.upper().replace('R$', '').replace('.', '').replace(',', '.').strip()
                                            val_float = float(val_limpo)
                                        else:
                                            val_float = float(val)
                                    except:
                                        continue
                                        
                                    if val_float > 0:
                                        comp_str = f"{dt_coluna.month:02d}/{dt_coluna.year}"
                                        inserts_pendentes.append({
                                            "id_colab": colab['id'],
                                            "comp": comp_str,
                                            "tipo": "Salário Mensal",
                                            "valor": val_float
                                        })
                            linhas_processadas += 1

                        if inserts_pendentes:
                            with engine.begin() as conn:
                                for item in inserts_pendentes:
                                    existe = conn.execute(text("""
                                        SELECT 1 FROM historico_premiacoes_e_folha 
                                        WHERE id_colaborador = :id_colab 
                                        AND competencia = :comp 
                                        AND tipo_lancamento = :tipo
                                    """), item).fetchone()
                                    
                                    if not existe:
                                        conn.execute(text("""
                                            INSERT INTO historico_premiacoes_e_folha 
                                            (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) 
                                            VALUES (:id_colab, :comp, :tipo, :valor, 'Pago')
                                        """), item)
                            
                            st.success(f"✅ Ingestão Concluída! Lidos {linhas_processadas} colaboradores.")
                            st.info(f"💾 Foram injetados {len(inserts_pendentes)} registros de histórico salarial.")
                            if recuperados_ia > 0:
                                st.warning(f"🤖 **Auto-Recuperação IA:** {recuperados_ia} recadastrados automaticamente.")
                        else:
                            st.warning("Aviso: Nenhum registro novo importado.")

                except Exception as e:
                    st.error(f"Falha Operacional no Motor ETL: {e}")

# --- 3. GESTÃO DE CADASTROS ---
elif menu == "🛠️ Gestão de Cadastros":
    st.title("🛠️ Gestão de Cadastros")
    
    opcoes_sub = ["🔍 Consultar & Gerenciar", "➕ Novo Cadastro"]
    sub_menu = st.radio(
        label="Menu de Operações",
        options=opcoes_sub,
        index=st.session_state['sub_menu_index'],
        label_visibility="collapsed"
    )
    st.session_state['sub_menu_index'] = opcoes_sub.index(sub_menu)
    st.markdown("---")

    if sub_menu == "🔍 Consultar & Gerenciar":
        st.subheader("Consultar Ficha do Colaborador")
        
        termo = st.text_input("Digite o ID (Matrícula) ou parte do Nome:", key="k_term_busca")
        btn_buscar = st.button("Buscar Registro")
        
        if btn_buscar and termo:
            st.session_state['status_acao'] = None
            st.session_state['busca_selecionada_id'] = None
            
            try:
                with engine.connect() as conn:
                    sql_exact = "SELECT * FROM cadastro_geral_colaborador WHERE id = :t"
                    resultados = conn.execute(text(sql_exact), {"t": str(termo).strip()}).fetchall()
                    
                    if not resultados:
                        sql_like = "SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t ORDER BY nome ASC"
                        resultados = conn.execute(text(sql_like), {"t": f"%{termo.strip()}%"}).fetchall()
                    
                    if not resultados:
                        st.warning("Nenhum registro encontrado para o critério informado.")
                    elif len(resultados) == 1:
                        st.session_state['busca_selecionada_id'] = str(resultados[0].id)
                        st.rerun() 
                    else:
                        st.info("Múltiplos registros encontrados. Selecione o colaborador desejado abaixo:")
                        opcoes_lista = {f"ID: {r.id} | Nome: {r.nome}": str(r.id) for r in resultados}
                        escolha = st.selectbox("Selecione:", list(opcoes_lista.keys()))
                        if st.button("Confirmar Seleção"):
                            st.session_state['busca_selecionada_id'] = opcoes_lista[escolha]
                            st.rerun()
            except Exception as e:
                st.error(f"Erro ao pesquisar no banco: {e}")

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
                    salario_mes_display = "Não Informado"
                    salario_hora_display = "Não Informado"
                    val_atual_base = 0.0
                    
                    if colab.salario_mes_12_24 and str(colab.salario_mes_12_24).strip() != "" and str(colab.salario_mes_12_24).strip().lower() != "none":
                        try:
                            s_val = str(colab.salario_mes_12_24).upper().replace('R$', '').strip()
                            if '.' in s_val and ',' in s_val:
                                s_val = s_val.replace('.', '').replace(',', '.')
                            elif ',' in s_val:
                                s_val = s_val.replace(',', '.')
                            
                            val_m = float(s_val)
                            val_h = val_m / 220.0
                            val_atual_base = val_m
                            salario_mes_display = f"R$ {val_m:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            salario_hora_display = f"R$ {val_h:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        except:
                            salario_mes_display = str(colab.salario_mes_12_24)
                            salario_hora_display = str(colab.salario_hora) if colab.salario_hora else "Não Informado"
                            val_atual_base = -1.0 
                    
                    if val_atual_base == 0.0 and not df_hist.empty:
                        df_sal = df_hist[df_hist['tipo_lancamento'].str.contains('Salário', na=False, case=False)]
                        if not df_sal.empty:
                            val_m = float(df_sal.iloc[0]['valor_lancamento'])
                            val_h = val_m / 220.0
                            val_atual_base = val_m
                            salario_mes_display = f"R$ {val_m:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            salario_hora_display = f"R$ {val_h:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    
                    st.markdown("### 📋 Ficha Completa do Colaborador")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown('<p class="field-label">ID / MATRÍCULA</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.id}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">CARGO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.cargo if colab.cargo else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-MÊS ATUAL</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{salario_mes_display}</p>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<p class="field-label">NOME COMPLETO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.nome}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE ADMISSÃO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{pd.to_datetime(colab.admissao).strftime("%d/%m/%Y") if colab.admissao else "Não Informada"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-HORA ATUAL</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{salario_hora_display}</p>', unsafe_allow_html=True)
                    with c3:
                        st.markdown('<p class="field-label">CPF</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.cpf if colab.cpf else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE DEMISSÃO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{pd.to_datetime(colab.demissao).strftime("%d/%m/%Y") if colab.demissao else "Ativo / Em Aberto"}</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # --- NOVO PAINEL DE AFASTAMENTO INSS NA FICHA ---
                    v_afast = getattr(colab, 'data_afastamento', None)
                    v_ret = getattr(colab, 'data_retorno', None)
                    
                    if v_afast:
                        st.markdown("### 🏥 Status de Afastamento (INSS)")
                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        ca1, ca2 = st.columns(2)
                        with ca1:
                            st.markdown('<p class="field-label">AFASTAMENTO</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value" style="color:#facc15;">{pd.to_datetime(v_afast).strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)
                        with ca2:
                            st.markdown('<p class="field-label">RETORNO</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{pd.to_datetime(v_ret).strftime("%d/%m/%Y") if v_ret else "Ainda Afastado"}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 🏦 Dados Bancários (PIX Principal)")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if fin_data or colab.chave_pix:
                        cf1, cf2 = st.columns(2)
                        with cf1:
                            st.markdown('<p class="field-label">TIPO DE CHAVE</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{fin_data.get("tipo_chave_pix") if fin_data else "PIX Principal"}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">BANCO</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{(fin_data.get("banco") if fin_data else "") or "Não Informado"}</p>', unsafe_allow_html=True)
                        with cf2:
                            st.markdown('<p class="field-label">CHAVE PIX</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{colab.chave_pix or (fin_data.get("chave_pix") if fin_data else "Não Informado")}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">AGÊNCIA / CONTA</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{(fin_data.get("agencia") if fin_data else "-")} / {(fin_data.get("conta") if fin_data else "-")}</p>', unsafe_allow_html=True)
                    else:
                        st.info("Nenhum dado bancário ou PIX registrado para este colaborador. Utilize a edição para preencher.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 📈 Evolução e Alterações Salariais")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if not df_evo_salarial.empty:
                        df_evo_view = df_evo_salarial.copy()
                        df_evo_view['data_alteracao'] = pd.to_datetime(df_evo_view['data_alteracao']).dt.strftime('%d/%m/%Y')
                        df_evo_view['salario_anterior'] = df_evo_view['salario_anterior'].apply(format_currency_brl)
                        df_evo_view['novo_salario'] = df_evo_view['novo_salario'].apply(format_currency_brl)
                        df_evo_view.rename(columns={'data_alteracao': 'Data da Alteração', 'motivo': 'Motivo', 'salario_anterior': 'Salário Anterior', 'novo_salario': 'Novo Salário'}, inplace=True)
                        st.dataframe(df_evo_view, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma alteração salarial registrada no histórico deste colaborador.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("### 💰 Histórico Mensal de Prêmios e Ajustes (CCT)")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if not df_hist.empty:
                        cols_desejadas = ['competencia', 'tipo_lancamento', 'valor_lancamento', 'status_pagamento', 'retroativo_pago', 'data_pagamento']
                        cols_existentes = [c for c in cols_desejadas if c in df_hist.columns]
                        df_view = df_hist[cols_existentes].copy()
                        
                        df_view['valor_lancamento'] = df_view['valor_lancamento'].apply(format_brl_number)
                        
                        df_view.rename(columns={'competencia': 'Competência', 'tipo_lancamento': 'Tipo', 'valor_lancamento': 'Valor (R$)', 'status_pagamento': 'Status', 'retroativo_pago': 'Foi Retroativo?', 'data_pagamento': 'Data Pagamento'}, inplace=True)
                        st.dataframe(df_view, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum histórico financeiro ou de premiações registrado.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    if st.session_state['status_acao'] is None:
                        col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns([1, 1, 1, 1, 1, 1])
                        if col_b1.button("✏️ Editar Ficha"):
                            st.session_state['status_acao'] = 'solicitou_alterar'
                            st.rerun()
                        if col_b2.button("📈 Alterar Salário"):
                            st.session_state['status_acao'] = 'solicitou_alteracao_salarial'
                            st.rerun()
                        if col_b3.button("➕ Lanç. Avulso"):
                            st.session_state['status_acao'] = 'solicitou_lancamento_avulso'
                            st.rerun()
                        if col_b4.button("🛠️ Corrigir Hist."):
                            st.session_state['status_acao'] = 'solicitou_corrigir_historico'
                            st.rerun()
                        if col_b5.button("❌ Excluir"):
                            st.session_state['status_acao'] = 'solicitou_excluir'
                            st.rerun()
                        if col_b6.button("🧹 Fechar"):
                            st.session_state['busca_selecionada_id'] = None
                            st.session_state['status_acao'] = None
                            st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_excluir':
                        st.warning(f"⚠️ **Deseja realmente excluir o colaborador {colab.nome} (ID: {colab.id})?**")
                        col_conf1, col_conf2 = st.columns(2)
                        if col_conf1.button("🔥 Sim, Quero Excluir", key="btn_conf_del"):
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM historico_salarial WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)})
                            st.success("Registro excluído permanentemente de todas as bases.")
                            st.session_state['busca_selecionada_id'] = None
                            st.session_state['status_acao'] = None
                            st.rerun()
                        if col_conf2.button("Voltar / Cancelar", key="btn_canc_del"):
                            st.session_state['status_acao'] = None
                            st.rerun()
                            
                    if st.session_state['status_acao'] == 'solicitou_lancamento_avulso':
                        st.info("➕ **Inserção Avulsa no Histórico:** Adicione os meses que faltam diretamente no banco de dados.")
                        col_av1, col_av2, col_av3 = st.columns(3)
                        with col_av1:
                            av_comp = st.text_input("Competência (MM/AAAA)", placeholder="Ex: 09/2025")
                        with col_av2:
                            av_tipo = st.selectbox("Tipo de Lançamento", ["Salário Mensal", "Férias", "13º Salário", "Prêmio", "Outros"])
                        with col_av3:
                            av_valor = st.text_input("Valor Recebido", placeholder="Pode digitar com vírgula: 2354,90")
                            
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_bt1, col_bt2 = st.columns([1, 4])
                        if col_bt1.button("💾 Salvar Lançamento"):
                            if not av_comp.strip() or not av_valor.strip():
                                st.error("Competência e Valor são obrigatórios.")
                            else:
                                v_clean = clean_money_to_db(av_valor)
                                if v_clean is not None:
                                    with engine.begin() as conn:
                                        conn.execute(text("""
                                            INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) 
                                            VALUES (:id, :comp, :tipo, :valor, 'Pago')
                                        """), {"id": str(colab_id), "comp": av_comp.strip(), "tipo": av_tipo, "valor": float(v_clean)})
                                    st.success("Mês adicionado ao histórico com sucesso!")
                                    st.session_state['status_acao'] = None
                                    st.rerun()
                                else:
                                    st.error("Formato de valor inválido. Tente novamente.")
                        if col_bt2.button("Cancelar"):
                            st.session_state['status_acao'] = None
                            st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_corrigir_historico':
                        st.info("🛠️ **Editor de Histórico:** Corrija valores ou apague meses errados.")
                        
                        if df_hist.empty:
                            st.warning("Não há lançamentos no histórico deste colaborador para corrigir.")
                            if st.button("Voltar"):
                                st.session_state['status_acao'] = None
                                st.rerun()
                        else:
                            opcoes_hist = {f"Competência: {row['competencia']} | Tipo: {row['tipo_lancamento']} | Valor Atual: R$ {format_brl_number(row['valor_lancamento'])}": row['id_lancamento'] for _, row in df_hist.iterrows()}
                            st.markdown("<p class='field-label'>1. Selecione a linha do histórico:</p>", unsafe_allow_html=True)
                            sel_lbl = st.selectbox(" ", list(opcoes_hist.keys()), label_visibility="collapsed")
                            id_alvo = opcoes_hist[sel_lbl]
                            
                            col_ch1, col_ch2 = st.columns(2)
                            with col_ch1:
                                novo_val_hist = st.text_input("2. Digite o Valor Correto", placeholder="Ex: 2354,90 (O sistema formata sozinho)")
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                            
                            if col_btn1.button("💾 Salvar Novo Valor"):
                                v_clean = clean_money_to_db(novo_val_hist)
                                if v_clean is not None:
                                    with engine.begin() as conn:
                                        conn.execute(text("UPDATE historico_premiacoes_e_folha SET valor_lancamento = :v WHERE id = :id"), {"v": float(v_clean), "id": id_alvo})
                                    st.success("Tabela de Histórico corrigida com sucesso!")
                                    st.session_state['status_acao'] = None
                                    st.rerun()
                                else:
                                    st.error("Digite um valor numérico válido (ex: 2354,90).")
                                    
                            if col_btn2.button("🗑️ Apagar Mês Inteiro"):
                                with engine.begin() as conn:
                                    conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id = :id"), {"id": id_alvo})
                                st.success("Mês apagado!")
                                st.session_state['status_acao'] = None
                                st.rerun()
                                
                            if col_btn3.button("Cancelar Edição"):
                                st.session_state['status_acao'] = None
                                st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_alteracao_salarial':
                        st.info("📈 Modo de Alteração Salarial (Auditoria Ativa)")
                        col_as1, col_as2 = st.columns(2)
                        with col_as1:
                            as_sal_atual = st.text_input("Salário Atual Registrado", value=salario_mes_display, disabled=True)
                            as_data = st.date_input("Data Efetiva da Alteração", value=datetime.today().date(), format="DD/MM/YYYY")
                        with col_as2:
                            motivos_cct = ["MUDANÇA DE FUNÇÃO", "TEMPO DE SERVIÇO", "DISSÍDIO COLETIVO", "REAJUSTE ESPONTÂNEO", "AUMENTO DO SALÁRIO MÍNIMO", "READMISSÃO", "CORREÇÃO DE DADOS"]
                            as_motivo = st.selectbox("Motivo da Alteração", motivos_cct)
                            as_novo_sal = st.text_input("Novo Salário", placeholder="Pode digitar 2354,90 - o sistema formata")
                            
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_bs1, col_bs2 = st.columns([1, 1])
                        if col_bs1.button("💾 Gravar Alteração Salarial"):
                            if not as_novo_sal.strip():
                                st.error("O Novo Salário não pode ficar vazio.")
                            else:
                                v_clean = clean_money_to_db(as_novo_sal)
                                if v_clean is not None:
                                    try:
                                        val_float = float(v_clean)
                                        val_hora = val_float / 220.0
                                        val_str_formatado = f"{val_float:.2f}"
                                        val_hora_formatado = f"{val_hora:.2f}"
                                        val_atual_str = f"{val_atual_base:.2f}" if val_atual_base > 0 else (str(colab.salario_mes_12_24) if colab.salario_mes_12_24 else "0.00")
                                        
                                        with engine.begin() as conn:
                                            conn.execute(text("""
                                                INSERT INTO historico_salarial (id_colaborador, data_alteracao, motivo, salario_anterior, novo_salario)
                                                VALUES (:id, :dt, :motivo, :ant, :novo)
                                            """), {"id": str(colab_id), "dt": as_data, "motivo": as_motivo, "ant": val_atual_str, "novo": val_str_formatado})
                                            
                                            conn.execute(text("""
                                                UPDATE cadastro_geral_colaborador SET salario_mes_12_24 = :sm, salario_hora = :sh WHERE id = :id
                                            """), {"sm": val_str_formatado, "sh": val_hora_formatado, "id": str(colab_id)})
                                            
                                            comp_str = f"{as_data.month:02d}/{as_data.year}"
                                            conn.execute(text("""
                                                INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) 
                                                VALUES (:id, :comp, 'Salário Mensal', :valor, 'Pago')
                                            """), {"id": str(colab_id), "comp": comp_str, "valor": val_float})
                                            
                                        st.success(f"Alteração gravada! Evolução documentada.")
                                        st.session_state['status_acao'] = None
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Falha ao processar: {e}")
                                else:
                                    st.error("Formato inválido. Use vírgula ou ponto.")
                        if col_bs2.button("Cancelar"):
                            st.session_state['status_acao'] = None
                            st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_alterar':
                        st.info("📝 Modo de Edição Ativo - Utilize para corrigir dados mestres da ficha.")
                        
                        try: dt_adm_val = pd.to_datetime(colab.admissao).date() if colab.admissao else None
                        except: dt_adm_val = None
                        try: dt_dem_val = pd.to_datetime(colab.demissao).date() if colab.demissao else None
                        except: dt_dem_val = None
                        
                        # INSS Data
                        try: dt_afast_val = pd.to_datetime(v_afast).date() if v_afast else None
                        except: dt_afast_val = None
                        try: dt_ret_val = pd.to_datetime(v_ret).date() if v_ret else None
                        except: dt_ret_val = None
                        
                        cargo_atual = str(colab.cargo).upper().strip() if colab.cargo else ""
                        cargo_idx = LISTA_CARGOS.index(cargo_atual) if cargo_atual in LISTA_CARGOS else (len(LISTA_CARGOS)-1)
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_id = st.text_input("ID / Matrícula (Pode ser alterado)", value=str(colab.id), key="k_eid")
                            edit_nome = st.text_input("Nome Completo", value=str(colab.nome), key="k_enome")
                            st.markdown('<label class="fake-label">Inscrição Cadastral Individual</label>', unsafe_allow_html=True)
                            edit_cpf = st.text_input(" ", value=str(colab.cpf) if colab.cpf else "", placeholder="Apenas dígitos", key="k_ecpf")
                            edit_adm = st.date_input("Data de Admissão", value=dt_adm_val, format="DD/MM/YYYY")
                            edit_sal_mes = st.text_input("Correção: Salário-Mês Base (O sistema formata sozinho)", value=str(colab.salario_mes_12_24) if colab.salario_mes_12_24 else "", key="k_esal_mes")
                        
                        with col_e2:
                            sel_cargo = st.selectbox("Cargo Ocupado", LISTA_CARGOS, index=cargo_idx)
                            if sel_cargo == "OUTRO (DIGITAR MANUALMENTE)":
                                edit_cargo = st.text_input("Digite o Novo Cargo", value=cargo_atual if cargo_idx == len(LISTA_CARGOS)-1 else "")
                            else:
                                edit_cargo = sel_cargo
                                
                            ativo_ed = st.checkbox("✅ Colaborador Ativo (Remove a Demissão)", value=(dt_dem_val is None))
                            if ativo_ed:
                                edit_dem = None
                            else:
                                edit_dem = st.date_input("Data de Demissão", value=dt_dem_val if dt_dem_val else datetime.today().date(), format="DD/MM/YYYY")
                                
                            edit_pix = st.text_input("Chave PIX Principal", value=str(colab.chave_pix) if colab.chave_pix else "", key="k_epix")
                            edit_sal_hora = st.text_input("Correção: Salário-Hora Base", value=str(colab.salario_hora) if colab.salario_hora else "", key="k_esal_hora")
                            
                        st.markdown("##### 🏥 Dados de Afastamento (INSS)")
                        col_inss1, col_inss2 = st.columns(2)
                        with col_inss1:
                            edit_afast = st.date_input("Data de Afastamento (Deixe vazio se OK)", value=dt_afast_val, format="DD/MM/YYYY", key="k_eafast")
                        with col_inss2:
                            edit_ret = st.date_input("Data de Retorno (Deixe vazio se não retornou)", value=dt_ret_val, format="DD/MM/YYYY", key="k_eret")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Confirmar e Salvar Alterações", key="k_ebtn_salvar"):
                            if not edit_id.strip() or not edit_nome.strip():
                                st.error("O ID/Matrícula e o Nome do colaborador não podem ficar vazios.")
                            else:
                                adm_str = edit_adm.strftime('%Y-%m-%d') if edit_adm else None
                                dem_str = edit_dem.strftime('%Y-%m-%d') if edit_dem else None
                                afast_str = edit_afast.strftime('%Y-%m-%d') if edit_afast else None
                                ret_str = edit_ret.strftime('%Y-%m-%d') if edit_ret else None
                                
                                try:
                                    with engine.begin() as conn:
                                        if edit_id.strip() != str(colab_id):
                                            existe = conn.execute(text("SELECT 1 FROM cadastro_geral_colaborador WHERE id = :nid"), {"nid": edit_id.strip()}).fetchone()
                                            if existe:
                                                st.error(f"Erro Crítico: O ID '{edit_id.strip()}' já está sendo utilizado por outro colaborador!")
                                                raise Exception("ID duplicado")
                                        
                                        conn.execute(text("""
                                            UPDATE cadastro_geral_colaborador 
                                            SET id = :nid, nome = :n, cpf = :c, cargo = :ca, admissao = :ad, demissao = :de, 
                                                data_afastamento = :afast, data_retorno = :ret,
                                                chave_pix = :pix, salario_mes_12_24 = :sm, salario_hora = :sh
                                            WHERE id = :oid
                                        """), {
                                            "nid": edit_id.strip(), "n": edit_nome, "c": edit_cpf if edit_cpf.strip() else None, 
                                            "ca": edit_cargo if edit_cargo.strip() else None, "ad": adm_str, 
                                            "de": dem_str, "afast": afast_str, "ret": ret_str,
                                            "pix": edit_pix if edit_pix.strip() else None,
                                            "sm": clean_money_to_db(edit_sal_mes), "sh": clean_money_to_db(edit_sal_hora), 
                                            "oid": str(colab_id)
                                        })
                                        
                                        if edit_id.strip() != str(colab_id):
                                            conn.execute(text("UPDATE historico_premiacoes_e_folha SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                            conn.execute(text("UPDATE historico_salarial SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                            conn.execute(text("UPDATE cadastro_financeiro_colaborador SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                            
                                    st.success("Ficha Mestra corrigida com sucesso!")
                                    st.session_state['busca_selecionada_id'] = edit_id.strip()
                                    st.session_state['status_acao'] = None
                                    st.rerun()
                                    
                                except Exception as e:
                                    if "ID duplicado" not in str(e):
                                        try:
                                            with engine.begin() as conn2:
                                                conn2.execute(text("""
                                                    INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora, chave_pix)
                                                    VALUES (:nid, :n, :c, :ca, :ad, :de, :afast, :ret, :sm, :sh, :pix)
                                                """), {"nid": edit_id.strip(), "n": edit_nome, "c": edit_cpf if edit_cpf.strip() else None, "ca": edit_cargo if edit_cargo.strip() else None, "ad": adm_str, "de": dem_str, "afast": afast_str, "ret": ret_str, "sm": clean_money_to_db(edit_sal_mes), "sh": clean_money_to_db(edit_sal_hora), "pix": edit_pix if edit_pix.strip() else None})
                                                
                                                conn2.execute(text("UPDATE historico_premiacoes_e_folha SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                                conn2.execute(text("UPDATE historico_salarial SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                                conn2.execute(text("UPDATE cadastro_financeiro_colaborador SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                                conn2.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :oid"), {"oid": str(colab_id)})
                                                
                                            st.success("ID migrado e ficha corrigida com sucesso!")
                                            st.session_state['busca_selecionada_id'] = edit_id.strip()
                                            st.session_state['status_acao'] = None
                                            st.rerun()
                                        except Exception as inner_e:
                                            st.error(f"Falha Crítica ao migrar o ID: {inner_e}")
                        
                        if st.button("Abandonar Edição", key="k_ebtn_abandonar"):
                            st.session_state['status_acao'] = None
                            st.rerun()
            except Exception as e:
                st.error(f"Falha operacional de leitura/escrita no banco: {e}")

    elif sub_menu == "➕ Novo Cadastro":
        col_tit, col_can = st.columns([3, 1])
        with col_tit:
            st.subheader("Inserir Novo Colaborador")
        with col_can:
            if st.button("⬅️ Cancelar e Voltar", use_container_width=True, key="k_btn_canc_voltar"):
                st.session_state['redirect_to_consulta'] = True
                st.rerun()
        
        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
        col_nc1, col_nc2 = st.columns(2)
        with col_nc1:
            n_id = st.text_input("Código ID / Matrícula (Ex: 1025)", key="k_nc_id")
            st.markdown('<label class="fake-label">Inscrição Cadastral Individual</label>', unsafe_allow_html=True)
            n_cpf = st.text_input(" ", placeholder="Digite apenas os 11 números", key="k_nc_cpf")
            n_admissao = st.date_input("Data de Admissão", value=None, format="DD/MM/YYYY", key="k_nc_adm")
            n_sal_mes = st.text_input("Salário-Mês Atual", placeholder="O sistema formata sozinho", key="k_nc_sal_mes")
        with col_nc2:
            n_nome = st.text_input("Nome Completo", key="k_nc_nome")
            
            sel_nc_cargo = st.selectbox("Cargo Ocupado", LISTA_CARGOS)
            if sel_nc_cargo == "OUTRO (DIGITAR MANUALMENTE)":
                n_cargo = st.text_input("Digite o Cargo", key="k_nc_cargo_txt")
            else:
                n_cargo = sel_nc_cargo
                
            ativo_nc = st.checkbox("✅ Colaborador Ativo", value=True)
            if ativo_nc:
                n_demissao = None
            else:
                n_demissao = st.date_input("Data de Demissão", value=datetime.today().date(), format="DD/MM/YYYY", key="k_nc_dem")
                
            n_pix = st.text_input("Chave PIX", key="k_nc_pix")
            n_sal_hora = st.text_input("Salário-Hora Atual", key="k_nc_sal_hora")
            
        st.markdown("##### 🏥 Dados de Afastamento (INSS)")
        col_ninss1, col_ninss2 = st.columns(2)
        with col_ninss1:
            n_afast = st.date_input("Data de Afastamento (Opcional)", value=None, format="DD/MM/YYYY", key="k_n_afast")
        with col_ninss2:
            n_ret = st.date_input("Data de Retorno (Opcional)", value=None, format="DD/MM/YYYY", key="k_n_ret")
            
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        submetido = st.button("💾 Salvar Registro no Sistema", key="k_nc_btn_salvar")
        if submetido:
            if not n_id.strip() or not n_nome.strip():
                st.error("⚠️ Os campos 'ID / Matrícula' e 'Nome Completo' são obrigatórios.")
            else:
                adm_str = n_admissao.strftime('%Y-%m-%d') if n_admissao else None
                dem_str = n_demissao.strftime('%Y-%m-%d') if n_demissao else None
                afast_str = n_afast.strftime('%Y-%m-%d') if n_afast else None
                ret_str = n_ret.strftime('%Y-%m-%d') if n_ret else None
                
                try:
                    with engine.begin() as conn: 
                        conn.execute(text("""
                            INSERT INTO cadastro_geral_colaborador 
                            (id, nome, cpf, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora, chave_pix) 
                            VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :afast, :ret, :sm, :sh, :pix)
                        """), {"id": str(n_id), "nome": str(n_nome), "cpf": str(n_cpf) if n_cpf.strip() else None, "cargo": str(n_cargo) if n_cargo.strip() else None, "admissao": adm_str, "demissao": dem_str, "afast": afast_str, "ret": ret_str, "sm": clean_money_to_db(n_sal_mes), "sh": clean_money_to_db(n_sal_hora), "pix": str(n_pix) if n_pix.strip() else None})
                    st.success(f"Colaborador {n_nome} inserido com sucesso!")
                    st.session_state['redirect_to_consulta'] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro de Integridade: Verifique se o ID digitado já pertence a outro cadastro. Detalhes: {e}")

# --- 4. AUDITORIA CCT (IA) ---
elif menu == "🔎 Auditoria CCT (IA)":
    st.title("🔎 Auditoria Automatizada da Folha")
    st.markdown("""
    O Cérebro da Inteligência Artificial fará agora um Raio-X a toda a folha de pagamento cruzando:
    **Pisos da CCT + Regra de 5% (18/36/54 meses) + Exclusão de Aprendizes/Estagiários/Afastados**.
    """)
    
    st.info("Pisos Internos Ativos (CCT SINDTICMAL): Grupo E (Pedreiros/etc): R$ 2.063,92 | Grupo I (Servente): R$ 1.548,00 | Grupo A (Mestre): R$ 4.068,99 | Base Nacional Mínima: R$ 1.518,00.")
    
    if st.button("🚀 Executar Varredura Completa na Folha", type="primary"):
        with st.spinner("A cruzar salários atuais com as normas da convenção coletiva..."):
            try:
                # Agora puxamos também os dados de INSS para a IA entender
                df_folha = pd.read_sql("SELECT id, nome, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24 FROM cadastro_geral_colaborador", engine)
                hoje = pd.Timestamp.today()
                
                def converter_salario(val_str):
                    if not val_str or pd.isna(val_str) or str(val_str).strip() == "Não Informado" or str(val_str).strip() == "": return 0.0
                    s = str(val_str).upper().replace('R$', '').strip()
                    if '.' in s and ',' in s: s = s.replace('.', '').replace(',', '.')
                    elif ',' in s: s = s.replace(',', '.')
                    try: return float(s)
                    except: return 0.0
                
                def calcular_auditoria(row):
                    cargo = str(row['cargo']).upper() if pd.notna(row['cargo']) else ""
                    adm_str = row['admissao']
                    dem_str = row['demissao']
                    afast_str = row.get('data_afastamento', None)
                    ret_str = row.get('data_retorno', None)
                    sal_atual = converter_salario(row['salario_mes_12_24'])
                    
                    if pd.notna(dem_str) and str(dem_str).strip() != "" and str(dem_str).strip().lower() != "ativo / em aberto":
                        return pd.Series(["Demitido (Ignorado)", "-", "Ok"])
                        
                    # NOVA REGRA IA: Se está afastado e não voltou, o salário zero não é erro da empresa!
                    if pd.notna(afast_str) and str(afast_str).strip() != "" and (pd.isna(ret_str) or str(ret_str).strip() == ""):
                        return pd.Series(["Afastado INSS", "-", "Ok (Benefício INSS)"])
                    
                    if "ESTAGIÁR" in cargo or "ESTAGIAR" in cargo or "APRENDIZ" in cargo:
                        return pd.Series(["N/A (Jovem Aprendiz/Estagiário)", "-", "Ok (Contrato Especial)"])
                    
                    piso = 1518.00
                    if any(x in cargo for x in ["PEDREIRO", "CARPINTEIRO", "PINTOR", "ENCANADOR"]):
                        piso = 2063.92
                    elif any(x in cargo for x in ["SERVENTE", "AJUDANTE"]):
                        piso = 1548.00
                    elif "MESTRE" in cargo:
                        piso = 4068.99
                        
                    try:
                        adm_dt = pd.to_datetime(adm_str)
                        meses_casa = (hoje.year - adm_dt.year) * 12 + hoje.month - adm_dt.month
                    except:
                        return pd.Series(["Erro Data Admissão", "-", "Pendente (Verificar Data)"])
                        
                    ciclos = meses_casa // 18
                    if ciclos > 3: ciclos = 3
                    
                    if "SERVENTE" in cargo:
                        ciclos = 0
                        
                    salario_ideal = piso * (1.05 ** ciclos)
                    
                    sal_ideal_fmt = f"R$ {salario_ideal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    sal_atual_fmt = f"R$ {sal_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    
                    if sal_atual == 0.0:
                        status = "⚠️ Sem Salário Cadastrado"
                    elif round(sal_atual, 2) < round(salario_ideal, 2):
                        status = "❌ Defasagem! (Piso/Tempo Inferior)"
                    elif round(sal_atual, 2) == round(salario_ideal, 2):
                        status = "✅ Perfeito (Na Tabela Exata)"
                    else:
                        status = "⭐ Acima da CCT (Reajuste Espontâneo Ativo)"
                        
                    return pd.Series([sal_ideal_fmt, sal_atual_fmt, status])

                df_folha[['Salário Ideal (CCT)', 'Salário Atual (Banco)', 'Status da Auditoria']] = df_folha.apply(calcular_auditoria, axis=1)
                df_resultado = df_folha[~df_folha['Status da Auditoria'].str.contains("Demitido")].copy()
                df_resultado.rename(columns={'id': 'Matrícula', 'nome': 'Nome', 'cargo': 'Cargo Atual', 'admissao': 'Admissão'}, inplace=True)
                df_view = df_resultado[['Matrícula', 'Nome', 'Cargo Atual', 'Admissão', 'Salário Atual (Banco)', 'Salário Ideal (CCT)', 'Status da Auditoria']]
                
                total_analisados = len(df_view)
                erros = len(df_view[df_view['Status da Auditoria'].str.contains("❌")])
                
                col1, col2 = st.columns(2)
                col1.metric("Funcionários Ativos Analisados", total_analisados)
                col2.metric("Divergências Encontradas (Abaixo da CCT)", erros, delta_color="inverse")
                
                st.markdown("### Relatório Oficial de Divergências")
                st.dataframe(df_view, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"Erro durante a auditoria: {e}")
