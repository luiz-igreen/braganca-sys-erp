import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

# Database ID: 1n-LpTzN9IiBF5TgcBqMW9vgQE_VYtrsKbiy73RP5kYI
engine = create_engine(st.secrets["DATABASE_URL"])

# --- ESTILIZAÇÃO VISUAL (DARK GLASSMORPHISM) ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .panel-glass { 
        background: rgba(30, 41, 59, 0.45); 
        border: 1px solid rgba(51, 65, 85, 0.7); 
        padding: 25px; 
        border-radius: 16px; 
        margin-bottom: 20px;
    }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .field-label { color: #94a3b8; font-size: 0.9rem; font-weight: bold; }
    .field-value { color: #f8fafc; font-size: 1.1rem; margin-bottom: 12px; background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }
    
    /* Abas customizadas premium via radio */
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

# --- CONTROLE DE ESTADOS DO FLUXO SPA ---
if 'busca_selecionada_id' not in st.session_state:
    st.session_state['busca_selecionada_id'] = None
if 'status_acao' not in st.session_state:
    st.session_state['status_acao'] = None
if 'sub_menu_cadastro' not in st.session_state:
    st.session_state['sub_menu_cadastro'] = "🔍 Consultar & Gerenciar"

# --- NAVEGAÇÃO CENTRAL ---
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros"])

# --- 1. VISÃO GERAL ---
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    try:
        df = pd.read_sql("SELECT id, nome, cpf, cargo, admissao, demissao FROM cadastro_geral_colaborador ORDER BY nome ASC", engine)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados do painel: {e}")

# --- 2. IMPORTAÇÃO INTELIGENTE ---
elif menu == "📥 Importação Inteligente":
    st.title("📥 Importação e Ingestão de Dados")
    arquivo = st.file_uploader("Selecione o arquivo de migração (.xlsx, .csv)", type=["xlsx", "csv"])
    
    if arquivo and st.button("Executar Ingestão Certificada"):
        try:
            if arquivo.name.endswith('.xlsx'):
                df_bruto = pd.read_excel(arquivo, engine='openpyxl')
            else:
                df_bruto = pd.read_csv(arquivo)
            
            with engine.begin() as conn:
                for _, row in df_bruto.iterrows():
                    conn.execute(text("""
                        INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao) 
                        VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao)
                        ON CONFLICT (id) DO UPDATE SET 
                            nome = EXCLUDED.nome,
                            cpf = EXCLUDED.cpf,
                            cargo = EXCLUDED.cargo,
                            admissao = EXCLUDED.admissao,
                            demissao = EXCLUDED.demissao
                    """), {
                        "id": str(row[0]), 
                        "nome": str(row[1]),
                        "cpf": str(row[2]) if len(row) > 2 else None,
                        "cargo": str(row[3]) if len(row) > 3 else None,
                        "admissao": str(row[4]) if len(row) > 4 else None,
                        "demissao": str(row[5]) if len(row) > 5 else None
                    })
            st.success("Ingestão resiliente executada com sucesso!")
        except Exception as e:
            st.error(f"Erro Crítico na estrutura ou codificação do arquivo: {e}")

# --- 3. GESTÃO DE CADASTROS ---
elif menu == "🛠️ Gestão de Cadastros":
    st.title("🛠️ Gestão de Cadastros")
    
    # Abas dinâmicas via Session State
    sub_menu = st.radio(
        label="Menu de Operações",
        options=["🔍 Consultar & Gerenciar", "➕ Novo Cadastro"],
        key="sub_menu_cadastro",
        label_visibility="collapsed"
    )
    
    st.markdown("---")

    # --- ABA: CONSULTAR, ALTERAR E EXCLUIR ---
    if sub_menu == "🔍 Consultar & Gerenciar":
        st.subheader("Consultar Ficha do Colaborador")
        
        termo = st.text_input("Digite o ID exato ou parte do Nome:", key="input_busca_central", autocomplete="new-password")
        btn_buscar = st.button("Buscar Registro")
        
        if btn_buscar and termo:
            st.session_state['status_acao'] = None
            st.session_state['busca_selecionada_id'] = None
            
            try:
                with engine.connect() as conn:
                    if termo.isdigit():
                        sql = "SELECT * FROM cadastro_geral_colaborador WHERE CAST(id AS TEXT) = :t"
                        params = {"t": str(termo)}
                    else:
                        sql = "SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t ORDER BY nome ASC"
                        params = {"t": f"%{termo}%"}
                    
                    resultados = conn.execute(text(sql), params).fetchall()
                    
                    if not resultados:
                        st.warning("Nenhum registro encontrado para o critério informado.")
                    elif len(resultados) == 1:
                        st.session_state['busca_selecionada_id'] = str(resultados[0].id)
                    else:
                        st.info("Múltiplos registros encontrados. Selecione o colaborador desejado abaixo:")
                        opcoes_lista = {f"{r.id} - {r.nome}": str(r.id) for r in resultados}
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
                    colab = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE CAST(id AS TEXT) = :id"), {"id": colab_id}).fetchone()
                
                if colab:
                    st.markdown("### 📋 Ficha Completa do Colaborador")
                    
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown('<p class="field-label">ID / MATRÍCULA</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.id}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">CARGO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.cargo if colab.cargo else "Não Informado"}</p>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<p class="field-label">NOME COMPLETO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.nome}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE ADMISSÃO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.admissao if colab.admissao else "Não Informada"}</p>', unsafe_allow_html=True)
                    with c3:
                        st.markdown('<p class="field-label">CPF</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.cpf if colab.cpf else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE DEMISSÃO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.demissao if colab.demissao else "Ativo / Em Aberto"}</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    if st.session_state['status_acao'] is None:
                        col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
                        if col_b1.button("✏️ Alterar Cadastro"):
                            st.session_state['status_acao'] = 'solicitou_alterar'
                            st.rerun()
                        if col_b2.button("❌ Excluir Colaborador"):
                            st.session_state['status_acao'] = 'solicitou_excluir'
                            st.rerun()
                        if col_b3.button("🧹 Limpar Consulta"):
                            st.session_state['busca_selecionada_id'] = None
                            st.session_state['status_acao'] = None
                            st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_excluir':
                        st.warning(f"⚠️ **PERGUNTA:** Deseja realmente excluir permanentemente o colaborador **{colab.nome}** (ID: {colab.id})?")
                        col_conf1, col_conf2 = st.columns(2)
                        if col_conf1.button("🔥 Sim, Quero Excluir", key="btn_conf_del"):
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE CAST(id AS TEXT) = :id"), {"id": colab_id})
                            st.success("Registro excluído permanentemente.")
                            st.session_state['busca_selecionada_id'] = None
                            st.session_state['status_acao'] = None
                            st.rerun()
                        if col_conf2.button("Voltar / Cancelar", key="btn_canc_del"):
                            st.session_state['status_acao'] = None
                            st.rerun()

                    if st.session_state['status_acao'] == 'solicitou_alterar':
                        st.info("📝 **Modo de Edição Active.** Modifique os dados desejados nos campos abaixo:")
                        
                        with st.form("form_edicao_direta"):
                            edit_nome = st.text_input("Nome Completo", value=str(colab.nome), autocomplete="new-password")
                            edit_cpf = st.text_input("CPF", value=str(colab.cpf) if colab.cpf else "", placeholder="00000000000", autocomplete="new-password")
                            edit_cargo = st.text_input("Cargo", value=str(colab.cargo) if colab.cargo else "", autocomplete="new-password")
                            edit_adm = st.text_input("Data Admissão (AAAA-MM-DD)", value=str(colab.admissao) if colab.admissao else "", autocomplete="new-password")
                            edit_dem = st.text_input("Data Demissão (AAAA-MM-DD)", value=str(colab.demissao) if colab.demissao else "", autocomplete="new-password")
                            
                            btn_salvar_alt = st.form_submit_button("Confirmar e Salvar Alterações")
                            
                            if btn_salvar_alt:
                                if not edit_nome.strip():
                                    st.error("O nome do colaborador não pode ficar vazio.")
                                else:
                                    with engine.begin() as conn:
                                        conn.execute(text("""
                                            UPDATE cadastro_geral_colaborador 
                                            SET nome = :n, cpf = :c, cargo = :ca, admissao = :ad, demissao = :de 
                                            WHERE CAST(id AS TEXT) = :id
                                        """), {
                                            "n": edit_nome, 
                                            "c": edit_cpf if edit_cpf.strip() else None,
                                            "ca": edit_cargo if edit_cargo.strip() else None,
                                            "ad": edit_adm if edit_adm.strip() else None,
                                            "de": edit_dem if edit_dem.strip() else None,
                                            "id": colab_id
                                        })
                                    st.success("Alterações gravadas perfeitamente no banco!")
                                    st.session_state['status_acao'] = None
                                    st.rerun()
                        
                        if st.button("Abandonar Edição"):
                            st.session_state['status_acao'] = None
                            st.rerun()
                            
                else:
                    st.error("Erro interno ao recuperar os dados atualizados deste ID.")
            except Exception as e:
                st.error(f"Falha de comunicação operacional: {e}")

    # --- ABA: NOVO CADASTRO ---
    elif sub_menu == "➕ Novo Cadastro":
        col_tit, col_can = st.columns([3, 1])
        with col_tit:
            st.subheader("Inserir Novo Colaborador")
        with col_can:
            if st.button("⬅️ Cancelar e Voltar", use_container_width=True):
                st.session_state['sub_menu_cadastro'] = "🔍 Consultar & Gerenciar"
                st.rerun()
                
        with st.form("form_novo_cadastro", clear_on_submit=True):
            n_id = st.text_input("Código ID / Matrícula (Ex: 1025)", autocomplete="new-password")
            n_nome = st.text_input("Nome Completo", autocomplete="new-password")
            
            # Blindagem absoluta contra vazamento e sugestão de cartões de crédito locais
            n_cpf = st.text_input("CPF (Apenas números)", placeholder="Ex: 00011122233", autocomplete="new-password")
            
            n_cargo = st.text_input("Cargo Ocupado", autocomplete="new-password")
            n_admissao = st.text_input("Data de Admissão (Formatada AAAA-MM-DD)", autocomplete="new-password")
            n_demissao = st.text_input("Data de Demissão (Opcional - AAAA-MM-DD)", autocomplete="new-password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_sb1, col_sb2 = st.columns([2, 2])
            
            with col_sb1:
                submetido = st.form_submit_button("💾 Salvar Registro no Sistema")
            with col_sb2:
                st.markdown("<p style='color:#94a3b8; font-size:0.85rem; margin-top:10px;'>Para sair sem salvar, clique no botão superior 'Cancelar e Voltar'.</p>", unsafe_allow_html=True)
            
            if submetido:
                if not n_id.strip() or not n_nome.strip():
                    st.error("⚠️ Os campos 'ID' e 'Nome Completo' são obrigatórios para a criação do cadastro.")
                else:
                    try:
                        with engine.begin() as conn: 
                            conn.execute(text("""
                                INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, demissao) 
                                VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao)
                            """), {
                                "id": str(n_id), 
                                "nome": str(n_nome),
                                "cpf": str(n_cpf) if n_cpf.strip() else None,
                                "cargo": str(n_cargo) if n_cargo.strip() else None,
                                "admissao": str(n_admissao) if n_admissao.strip() else None,
                                "demissao": str(n_demissao) if n_demissao.strip() else None
                            })
                        st.success(f"Colaborador {n_nome} inserido com total integridade!")
                        st.session_state['sub_menu_cadastro'] = "🔍 Consultar & Gerenciar"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro de Integridade: Verifique se o ID digitado já não pertence a outro cadastro. Detalhes: {e}")    
