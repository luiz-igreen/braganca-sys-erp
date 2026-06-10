with engine.begin() as conn:
correcoes_esocial = {
"6 - Doença": "6 - Doenca periodo superior a 15 dias",
            "6 - Doenca periodo igual ou superior a 15 dias": "6 - Doenca periodo superior a 15 dias",
            "6 - Doenca periodo igual ou superior a 15 dias": "6 - Doenca periodo igual ou superior a 15 dias",
"18 - Doença": "18 - Doenca periodo igual ou inferior a 15 dias",
}
for errado, correto in correcoes_esocial.items():
conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :c WHERE status_esocial = :e"), {"c": correto, "e": errado})
conn.execute(text("UPDATE historico_afastamentos SET tipo_afastamento = :c WHERE tipo_afastamento = :e"), {"c": correto, "e": errado})
    # st.success("Situações eSocial corrigidas.") # Comentado para reduzir mensagens na inicialização
    st.success("Correções de situações eSocial aplicadas.")
except Exception as e:
    st.warning(f"Erro ao corrigir situações eSocial: {e}")
    st.warning(f"Erro ao aplicar correções de situações eSocial: {e}")

# Migração de dados de admissão/demissão para historico_afastamentos (se vazio)
# Adicionar colunas 'data_afastamento' e 'data_retorno' à tabela 'cadastro_geral_colaborador' se não existirem
try:
with engine.begin() as conn:
        cnt_hist_afast = conn.execute(text("SELECT COUNT(*) FROM historico_afastamentos")).fetchone()[0]
        if cnt_hist_afast == 0:
            conn.execute(text("""
                INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento)
                SELECT id, admissao, '1 - Trabalhando'
                FROM cadastro_geral_colaborador
                WHERE admissao IS NOT NULL
                ON CONFLICT DO NOTHING;
            """))
            conn.execute(text("""
                INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento)
                SELECT id, demissao, '8 - Demitido'
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
                WHERE demissao IS NOT NULL
                ON CONFLICT DO NOTHING;
            """))
            st.success("Dados de admissão/demissão migrados para histórico de afastamentos.")
                WHERE status_esocial IS NOT NULL AND status_esocial != '' AND status_esocial != '1 - Trabalhando'
            """, conn)

            if not df_colaboradores_com_afastamento.empty:
                for index, row in df_colaboradores_com_afastamento.iterrows():
                    id_colaborador = row['id']
                    data_inicio = row['data_afastamento'] if row['data_afastamento'] else row['admissao']
                    data_fim = row['data_retorno']
                    tipo_afastamento = row['status_esocial']

                    if data_inicio and tipo_afastamento:
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
    st.warning(f"Erro ao migrar dados para historico_afastamentos: {e}")
    st.warning(f"Erro na migração de dados de afastamento: {e}")

# Limpeza de registros fantasmas
# Limpeza de registros com ID nulo ou vazio em todas as tabelas
try:
with engine.begin() as conn:
conn.execute(text("DELETE FROM historico_afastamentos WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id IS NULL OR TRIM(CAST(id AS TEXT)) = '' OR CAST(id AS TEXT) ILIKE 'nan' OR CAST(id AS TEXT) ILIKE 'none'"))
    # st.success("Registros fantasmas limpos.") # Comentado para reduzir mensagens na inicialização
    st.success("Registros com ID nulo/vazio limpos em todas as tabelas.")
except Exception as e:
    st.warning(f"Erro ao limpar registros fantasmas: {e}")

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
setInterval(function() {
    doc.querySelectorAll('input').forEach(function(el) {
        el.setAttribute('autocomplete', 'new-password');
        el.setAttribute('autofill', 'off');
        if (!el.hasAttribute('data-name-set')) { el.setAttribute('name', 'input_' + Math.random().toString(36).substring(7)); el.setAttribute('data-name-set', 'true'); }
    });
    doc.querySelectorAll('input[aria-label="CPF"]').forEach(function(el) {
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
    st.warning(f"Erro ao limpar registros com ID nulo/vazio: {e}")

# --- FUNÇÕES AUXILIARES ---
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
        if val is None or str(val).strip() == "" or str(val).lower() in ["nan", "none"]: return ""
        return f"{float(val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return val
        if re.fullmatch(r'\d+\.?\d*', date_str):
            excel_date = float(date_str)
            return datetime.fromtimestamp((excel_date - 25569) * 86400).date() # Excel epoch is 1899-12-30
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

def format_cpf(cpf_str):
    if not cpf_str or str(cpf_str).strip().lower() in ["nan", "none", ""]: return ""
    s = str(cpf_str).strip()
    if s.endswith('.0'): s = s[:-2]
    v = re.sub(r'\D', '', s)
    if not v: return ""
    v = v.zfill(11)
    if len(v) == 11: return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
    return str(cpf_str)
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

# --- LISTAS DE OPÇÕES ---
LISTA_CARGOS = [
    "PEDREIRO", "SERVENTE", "AJUDANTE PRATICO", "CARPINTEIRO", "PINTOR", "ELETRICISTA",
    "ENCANADOR", "MESTRE DE OBRAS", "ENCARREGADO",
    "APRENDIZ LEGAL EM ARCO ADMINISTRATIVO", "ESTAGIÁRIO", "OUTRO (DIGITAR MANUALMENTE)"
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
    "211 PRÊMIO META CRONOGRAMA", "212 PRÊMIO REVESTIMENTO EXTERNO", "213 PRÊMIO PINTURA",
    "215 PRÊMIO INSTALAÇÕES", "216 PRÊMIO REVESTIMENTO INTERNO", "225 PREMIO ESTRUTURA", "OUTRO (DIGITAR MANUALMENTE)"
    "PRODUÇÃO", "QUALIDADE", "SEGURANÇA", "ASSIDUIDADE", "OUTROS"
]

LISTA_SITUACOES_ESOCIAL = [
    "1 - Trabalhando", "2 - Afastado Direitos Integrais",
    "3 - Acid. Trabalho periodo superior a 15 dias", "4 - Servico Militar",
    "5 - Licenca maternidade", "6 - Doenca periodo superior a 15 dias",
    "1 - Trabalhando", "2 - Acidente/Doença não relacionada ao trabalho",
    "3 - Acidente de trabalho", "4 - Doença relacionada ao trabalho",
    "5 - Licença maternidade", "6 - Doenca periodo superior a 15 dias",
"7 - Licenca sem Vencimento", "8 - Demitido", "8136 - Licença paternidade",
"8701 - Ausencia justificada", "9 - Ferias",
"10 - Novo afast. mesmo acid. trabalho",
