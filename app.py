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
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS data_afastamento VARCHAR(50);"))
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS data_retorno VARCHAR(50);"))
        conn.execute(text("ALTER TABLE cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS situacao VARCHAR(100) DEFAULT '1 - Trabalhando';"))
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

# --- AUTO-LIMPEZA DE FANTASMAS (HIGIENE DE BASE DE DADOS) ---
try:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM historico_situacoes WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
        conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id IS NULL OR TRIM(CAST(id AS TEXT)) = '' OR CAST(id AS TEXT) ILIKE 'nan' OR CAST(id AS TEXT) ILIKE 'none'"))
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
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; padding-left: 5px; padding-right: 5px; }
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
""", unsafe_allow_html=True)# --- INJEÇÃO DE JAVASCRIPT PROFISSIONAL ---
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
                let v = e.target.value.replace(/\\D/g, '');
                if(v.length > 11) v = v.substring(0, 11);
                let f = v;
                if(v.length > 9) f = v.replace(/(\\d{3})(\\d{3})(\\d{3})(\\d{1,2})/, "$1.$2.$3-$4");
                else if(v.length > 6) f = v.replace(/(\\d{3})(\\d{3})(\\d{1,3})/, "$1.$2.$3");
                else if(v.length > 3) f = v.replace(/(\\d{3})(\\d{1,3})/, "$1.$2");
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
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'TEXTAREA' || e.target.getAttribute('aria-expanded') === 'true' || e.target.closest('[data-testid="stDataFrame"]')) {
                return;
            }
            e.preventDefault(); 
            e.stopPropagation();
            var selectors = 'input:not([disabled]):not([type="hidden"]), button:not([disabled]), textarea:not([disabled]), [tabindex="0"]:not([disabled])';
            var focusable = Array.from(doc.querySelectorAll(selectors)).filter(el => (el.offsetWidth > 0 || el.offsetHeight > 0) && el.style.display !== 'none' && el.style.visibility !== 'hidden');
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
    raise ValueError(f"O arquivo não pode ser lido. Solução rápida: Abra o arquivo no Excel e salve como '.xlsx', depois tente de novo!")

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
    "39 - Ausência Justificada",
    "8136 - Licença Paternidade",
    "90 - Suspensão contratual decorrente de forca maior", "91 - Suspensão contratual para inquerito falta grave"
]

for k in ['busca_selecionada_id', 'status_acao', 'zaut_acao']:
    if k not in st.session_state: st.session_state[k] = None
if 'sub_menu_index' not in st.session_state: st.session_state['sub_menu_index'] = 0
if 'redirect_to_consulta' not in st.session_state: st.session_state['redirect_to_consulta'] = False# ==========================================
# 3. GESTÃO DE CADASTROS (Continuação e Conclusão)
# ==========================================
    # [Esta parte conecta-se à lógica iniciada na parte anterior]

                    # --- MÓDULO EXCLUSIVO DE LINHA DO TEMPO (ESOCIAL) ---
                    if st.session_state['status_acao'] == 'solicitou_hist_esocial':
                        injetar_autofoco(pular_busca=True, painel="esocial")
                        
                        st.info("⏳ **Editor da Linha do Tempo (eSocial):** Aperte ENTER para pular de campo. Use **CTRL + ENTER** para salvar rápido.")
                        aba_add, aba_del = st.tabs(["➕ Lançar Evento Retroativo", "🗑️ Apagar Evento"])
                        
                        with aba_add:
                            ce_dt, ce_sit = st.columns(2)
                            with ce_dt: nova_dt_esocial = st.text_input("Data do Evento (Sem barras)", placeholder="Ex: 09122025")
                            with ce_sit: nova_sit_esocial = st.selectbox("Selecione a Situação", LISTA_SITUACOES_ESOCIAL)
                            
                            if st.button("💾 Gravar no Histórico", type="primary"):
                                dt_limpa = parse_br_date_smart(nova_dt_esocial)
                                if not dt_limpa: st.error("Data inválida! Digite no formato correto (ex: 09122025).")
                                else:
                                    dt_str = dt_limpa.strftime('%Y-%m-%d')
                                    with engine.begin() as conn: conn.execute(text("INSERT INTO historico_situacoes (id_colaborador, data_evento, descricao) VALUES (:id, :dt, :desc)"), {"id": str(colab_id), "dt": dt_str, "desc": nova_sit_esocial})
                                    st.success("Evento gravado na Linha do Tempo!")
                                    st.session_state['status_acao'] = None; st.rerun()
                                    
                        with aba_del:
                            if not df_hist_sit.empty:
                                opcoes_sit = {f"Data: {pd.to_datetime(row['data_evento']).strftime('%d/%m/%Y')} | {row['descricao']}": row['id'] for _, row in df_hist_sit.iterrows()}
                                id_sit_alvo = opcoes_sit[st.selectbox("Selecione o evento a apagar:", list(opcoes_sit.keys()))]
                                if st.button("🗑️ Apagar Evento Selecionado", type="primary"):
                                    with engine.begin() as conn: conn.execute(text("DELETE FROM historico_situacoes WHERE id = :id"), {"id": id_sit_alvo})
                                    st.success("Evento apagado da linha do tempo!")
                                    st.session_state['status_acao'] = None; st.rerun()
                            else: st.warning("Nenhum histórico para apagar.")
                        if st.button("⬅️ Voltar / Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    # --- MÓDULO EXCLUSIVO DE DEMISSÃO ---
                    if st.session_state['status_acao'] == 'solicitou_demissao':
                        injetar_autofoco(pular_busca=True, painel="demissao")
                        
                        st.info("🛑 **Módulo de Desligamento e Correção de Demissão.** Use **CTRL + ENTER** para salvar rápido.")
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
                                    st.success("✅ Atualizado! Qualquer folha posterior a esta data será limpa ao recarregar a ficha."); st.session_state['status_acao'] = None; st.rerun()
                            except Exception as e: st.error(f"Erro ao salvar: {e}")
                        if c_bt2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                    # --- EXCLUIR ---
                    if st.session_state['status_acao'] == 'solicitou_excluir':
                        st.warning(f"⚠️ Deseja excluir definitivamente {colab.nome} e todo o seu histórico?")
                        cx1, cx2 = st.columns(2)
                        if cx1.button("🔥 Sim, Excluir Tudo", type="primary"):
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
                        injetar_autofoco(pular_busca=True, painel="avulso")
                        
                        st.info("➕ **Inserção Avulsa (Com Validação e Anti-Duplicidade).** Use **CTRL + ENTER** para salvar rápido.")
                        c_av1, c_av2, c_av3 = st.columns(3)
                        val_sugestao = format_brl_number(val_atual_base) if val_atual_base > 0 else ""
                        with c_av1: av_comp = st.text_input("Competência (MM/AAAA)", placeholder="Ex: 092025")
                        with c_av2: av_tipo = st.selectbox("Tipo", ["Salário Mensal", "Prêmio ZAUT", "Férias", "Outros"])
                        with c_av3: av_valor = st.text_input("Valor (R$)", value=val_sugestao, placeholder="Digite o valor")
                        c_bt1, c_bt2 = st.columns([1, 4])
                        
                        if c_bt1.button("💾 Salvar Lançamento", type="primary"):
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
                        injetar_autofoco(pular_busca=True, painel="corrigir")
                        
                        st.info("🛠️ **Editor de Histórico (Pagamentos).** Use **CTRL + ENTER** para salvar rápido.")
                        if not df_hist.empty:
                            try:
                                opcoes_hist = {f"ID: {row['id']} | Comp: {row['competencia']} | Tipo: {row['tipo_lancamento']} | Val: R$ {format_brl_number(row['valor_lancamento'])}": row['id'] for _, row in df_hist.iterrows()}
                                id_alvo = opcoes_hist[st.selectbox("Selecione o registo:", list(opcoes_hist.keys()))]
                                novo_val = st.text_input("Novo Valor", placeholder="Deixe vazio para deletar")
                                ch1, ch2 = st.columns([1, 4])
                                if ch1.button("💾 Salvar / Atualizar", type="primary"):
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
                        injetar_autofoco(pular_busca=True, painel="editar_ficha")
                        
                        st.info("📝 Modo de Edição Ativo. Aperte ENTER para pular campos. Use **CTRL + ENTER** para salvar rápido.")
                        cargo_idx = LISTA_CARGOS.index(str(colab.cargo).upper().strip()) if str(colab.cargo).upper().strip() in LISTA_CARGOS else (len(LISTA_CARGOS)-1)
                        sit_idx = LISTA_SITUACOES_ESOCIAL.index(v_sit_atual) if v_sit_atual in LISTA_SITUACOES_ESOCIAL else 0
                        
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            edit_id = st.text_input("ID / Matrícula", value=str(colab.id))
                            edit_nome = st.text_input("Nome Completo", value=str(colab.nome))
                            edit_cpf = st.text_input("CPF", value=format_cpf(colab.cpf) if colab.cpf else "")
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
                        
                        if st.button("Confirmar e Salvar Alterações", type="primary"):
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
                            except Exception as e:
                                error_msg = str(e).lower()
                                if "unique constraint" in error_msg or "duplicate key" in error_msg:
                                    st.error(f"⚠️ AÇÃO BLOQUEADA (DUPLICIDADE): O ID/Matrícula '{edit_id.strip()}' já pertence a outro colaborador no sistema! Como medida de segurança, não é possível ter duas pessoas com a mesma matrícula. Se está a tentar fundir cadastros, utilize o botão 'Mesclar'.")
                                else:
                                    st.error(f"Erro no banco de dados: {e}")
                        if st.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

            except Exception as e:
                st.error(f"Erro no processamento da ficha: {e}")

    elif sub_menu == "➕ Novo Cadastro":
        injetar_autofoco(painel="novo_cadastro")
        
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
        
        st.info("Aperte ENTER para pular campos. Use **CTRL + ENTER** para salvar direto no banco de dados.")
        if st.button("💾 Salvar Registro no Sistema", type="primary"):
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
            except Exception as e:
                error_msg = str(e).lower()
                if "unique constraint" in error_msg or "duplicate key" in error_msg:
                    st.error(f"⚠️ AÇÃO BLOQUEADA (DUPLICIDADE): O ID/Matrícula '{str(n_id).strip()}' já está registado para outro colaborador! Verifique se a pessoa já existe na base de dados pesquisando por esta matrícula.")
                else:
                    st.error(f"Erro ao salvar: {e}")

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
                    injetar_autofoco(pular_busca=False, painel="zaut_individual")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    sal_hora_base = dados_c['sal_hora']
                    if sal_hora_base == 0.0:
                        sal_hora_manual = st.text_input("Valor Hora (R$)", key="k_sh_manual", placeholder="Ex: 9,38")
                        try: sal_hora_base = float(clean_money_to_db(sal_hora_manual)) if clean_money_to_db(sal_hora_manual) else 0.0
                        except: sal_hora_base = 0.0
                    else: st.markdown(f"**Valor Hora Calculado:** R$ {format_brl_number(sal_hora_base)}")
                    
                    cli1, cli2 = st.columns(2)
                    with cli1: hp_ind = st.text_input("Horas", key="k_hpi")
                    with cli2: desc_final_str = st.text_input("Especificar:", key="k_d_outro") if (desc_ind := st.selectbox("Serviço", LISTA_SERVICOS_PREMIO, key="k_di")) == "OUTRO (DIGITAR MANUALMENTE)" else desc_ind
                    
                    try: hp_ind_float = float(clean_money_to_db(hp_ind)) if clean_money_to_db(hp_ind) else 0.0
                    except: hp_ind_float = 0.0
                    val_final_ind = (sal_hora_base * hp_ind_float) + 1.00 if hp_ind_float > 0 else 0.00
                    
                    if hp_ind_float > 0 and sal_hora_base > 0: st.markdown(f'<p class="field-highlight">R$ {format_brl_number(val_final_ind)}</p>', unsafe_allow_html=True)
                    
                    st.info("Aperte ENTER para pular campos. Use **CTRL + ENTER** para salvar rápido.")
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
