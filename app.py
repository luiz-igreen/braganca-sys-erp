import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

# Conexão segura com o Banco de Dados
engine = create_engine(st.secrets["DATABASE_URL"])

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

# --- BLINDAGEM CONTRA AUTOFILL ---
st.markdown("""
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="(function(){
    setInterval(function(){
        document.querySelectorAll('input').forEach(function(el){
            el.setAttribute('autocomplete', 'new-password');
            el.setAttribute('autofill', 'off');
            el.setAttribute('name', 'input_' + Math.random().toString(36).substring(7));
        });
    }, 150);
})()" style="display:none;">
""", unsafe_allow_html=True)

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

# --- BARRA LATERAL DE NAVEGAÇÃO CENTRAL ---
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros"])

# --- 1. VISÃO GERAL ---
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    try:
        df = pd.read_sql("""
            SELECT id, nome, cpf, cargo, admissao, demissao, salario_mes_12_24, salario_hora 
            FROM cadastro_geral_colaborador 
            ORDER BY nome ASC
        """, engine)
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
                        "id": str(row[0]), 
                        "nome": str(row[1]),
                        "cpf": str(row[2]) if len(row) > 2 else None,
                        "cargo": str(row[3]) if len(row) > 3 else None,
                        "admissao": str(row[4]) if len(row) > 4 else None,
                        "demissao": str(row[5]) if len(row) > 5 else None,
                        "sal_mes": str(row[6]) if len(row) > 6 else None,
                        "sal_hora": str(row[7]) if len(row) > 7 else None
                    })
            st.success("Ingestão de dados executada com sucesso!")
        except Exception as e:
            st.error(f"Erro Crítico no mapeamento das colunas: {e}")

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

    # --- ABA: CONSULTAR, ALTERAR E EXCLUIR ---
    if sub_menu == "🔍 Consultar & Gerenciar":
        st.subheader("Consultar Ficha do Colaborador")
        
        termo = st.text_input("Digite o ID (Matrícula) ou parte do Nome:", key="k_term_busca")
        btn_buscar = st.button("Buscar Registro")
        
        if btn_buscar and termo:
            st.session_state['status_acao'] = None
            st.session_state['busca_selecionada_id'] = None
            
            try:
                with engine.connect() as conn:
                    # 1. Tenta Busca Exata por ID primeiro (Resolve o problema de listar vários)
                    sql_exact = "SELECT * FROM cadastro_geral_colaborador WHERE id = :t"
                    resultados = conn.execute(text(sql_exact), {"t": str(termo).strip()}).fetchall()
                    
                    # 2. Se não achar ID exato, busca por partes do nome ou da matrícula
                    if not resultados:
                        sql_like = "SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t OR id ILIKE :t ORDER BY nome ASC"
                        resultados = conn.execute(text(sql_like), {"t": f"%{termo.strip()}%"}).fetchall()
                    
                    if not resultados:
                        st.warning("Nenhum registro encontrado para o critério informado.")
                    elif len(resultados) == 1:
                        # Se encontrou exatamente um (ou pelo ID exato), abre a ficha na hora!
                        st.session_state['busca_selecionada_id'] = str(resultados[0].id)
                        st.rerun() # Força o recarregamento imediato para exibir a ficha
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
                    # 1. Busca Cadastro Geral
                    colab = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)}).fetchone()
                    
                    # 2. Busca Dados Bancários
                    df_fin = pd.read_sql(text("SELECT * FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), conn, params={"id": str(colab_id)})
                    fin_data = df_fin.iloc[0].to_dict() if not df_fin.empty else None
                    
                    # 3. Busca Histórico
                    df_hist = pd.read_sql(text("SELECT * FROM historico_premiacoes_e_folha WHERE id_colaborador = :id ORDER BY atualizado_em DESC"), conn, params={"id": str(colab_id)})
                
                if colab:
                    # --- BLOCO 1: DADOS GERAIS ---
                    st.markdown("### 📋 Ficha Completa do Colaborador")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown('<p class="field-label">ID / MATRÍCULA</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.id}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">CARGO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.cargo if colab.cargo else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-MÊS</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.salario_mes_12_24 if colab.salario_mes_12_24 else "Não Informado"}</p>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<p class="field-label">NOME COMPLETO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.nome}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE ADMISSÃO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.admissao if colab.admissao else "Não Informada"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">SALÁRIO-HORA</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.salario_hora if colab.salario_hora else "Não Informado"}</p>', unsafe_allow_html=True)
                    with c3:
                        st.markdown('<p class="field-label">CPF</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.cpf if colab.cpf else "Não Informado"}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="field-label">DATA DE DEMISSÃO</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-value">{colab.demissao if colab.demissao else "Ativo / Em Aberto"}</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # --- BLOCO 2: DADOS FINANCEIROS ---
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

                    # --- BLOCO 3: HISTÓRICO DE PRÊMIOS ---
                    st.markdown("### 💰 Histórico Mensal de Prêmios e Ajustes (CCT)")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    if not df_hist.empty:
                        cols_desejadas = ['competencia', 'tipo_lancamento', 'valor_lancamento', 'status_pagamento', 'retroativo_pago', 'data_pagamento']
                        cols_existentes = [c for c in cols_desejadas if c in df_hist.columns]
                        
                        df_view = df_hist[cols_existentes].copy()
                        mapa_colunas = {
                            'competencia': 'Competência',
                            'tipo_lancamento': 'Tipo',
                            'valor_lancamento': 'Valor (R$)',
                            'status_pagamento': 'Status',
                            'retroativo_pago': 'Foi Retroativo?',
                            'data_pagamento': 'Data Pagamento'
                        }
                        df_view.rename(columns=mapa_colunas, inplace=True)
                        st.dataframe(df_view, use_container_width=True)
                    else:
                        st.info("Nenhum histórico financeiro ou de premiações registrado.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # --- BOTÕES DE AÇÃO ---
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
                        st.warning(f"⚠️ **Deseja realmente excluir o colaborador {colab.nome} (ID: {colab.id})?**")
                        col_conf1, col_conf2 = st.columns(2)
                        if col_conf1.button("🔥 Sim, Quero Excluir", key="btn_conf_del"):
                            with engine.begin() as conn:
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

                    if st.session_state['status_acao'] == 'solicitou_alterar':
                        st.info("📝 Modo de Edição Ativo")
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_nome = st.text_input("Nome Completo", value=str(colab.nome), key="k_enome")
                            st.markdown('<label class="fake-label">Inscrição Cadastral Individual</label>', unsafe_allow_html=True)
                            edit_cpf = st.text_input(" ", value=str(colab.cpf) if colab.cpf else "", placeholder="Apenas dígitos", key="k_ecpf")
                            edit_adm = st.text_input("Data Admissão (AAAA-MM-DD)", value=str(colab.admissao) if colab.admissao else "", key="k_eadm")
                            edit_sal_mes = st.text_input("Salário-Mês Atual", value=str(colab.salario_mes_12_24) if colab.salario_mes_12_24 else "", key="k_esal_mes")
                        with col_e2:
                            edit_cargo = st.text_input("Cargo", value=str(colab.cargo) if colab.cargo else "", key="k_ecargo")
                            edit_dem = st.text_input("Data Demissão (AAAA-MM-DD)", value=str(colab.demissao) if colab.demissao else "", key="k_edem")
                            edit_pix = st.text_input("Chave PIX Principal", value=str(colab.chave_pix) if colab.chave_pix else "", key="k_epix")
                            edit_sal_hora = st.text_input("Salário-Hora Atual", value=str(colab.salario_hora) if colab.salario_hora else "", key="k_esal_hora")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Confirmar e Salvar Alterações", key="k_ebtn_salvar"):
                            if not edit_nome.strip():
                                st.error("O nome do colaborador não pode ficar vazio.")
                            else:
                                with engine.begin() as conn:
                                    conn.execute(text("""
                                        UPDATE cadastro_geral_colaborador 
                                        SET nome = :n, cpf = :c, cargo = :ca, admissao = :ad, demissao = :de,
                                            salario_mes_12_24 = :sm, salario_hora = :sh, chave_pix = :pix,
                                            atualizado_em = CURRENT_TIMESTAMP
                                        WHERE id = :id
                                    """), {
                                        "n": edit_nome, 
                                        "c": edit_cpf if edit_cpf.strip() else None,
                                        "ca": edit_cargo if edit_cargo.strip() else None,
                                        "ad": edit_adm if edit_adm.strip() else None,
                                        "de": edit_dem if edit_dem.strip() else None,
                                        "sm": edit_sal_mes if edit_sal_mes.strip() else None,
                                        "sh": edit_sal_hora if edit_sal_hora.strip() else None,
                                        "pix": edit_pix if edit_pix.strip() else None,
                                        "id": str(colab_id)
                                    })
                                st.success("Alterações gravadas com sucesso!")
                                st.session_state['status_acao'] = None
                                st.rerun()
                        
                        if st.button("Abandonar Edição", key="k_ebtn_abandonar"):
                            st.session_state['status_acao'] = None
                            st.rerun()
            except Exception as e:
                st.error(f"Falha operacional de leitura/escrita no banco: {e}")

    # --- ABA: NOVO CADASTRO ---
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
            n_id = st.text_input("Código ID / Matrícula (Ex: M0001 ou 1025)", key="k_nc_id")
            st.markdown('<label class="fake-label">Inscrição Cadastral Individual</label>', unsafe_allow_html=True)
            n_cpf = st.text_input(" ", placeholder="Digite apenas os 11 números", key="k_nc_cpf")
            n_admissao = st.text_input("Data de Admissão (Formatada AAAA-MM-DD)", key="k_nc_adm")
            n_sal_mes = st.text_input("Salário-Mês Atual", key="k_nc_sal_mes")
            
        with col_nc2:
            n_nome = st.text_input("Nome Completo", key="k_nc_nome")
            n_cargo = st.text_input("Cargo Ocupado", key="k_nc_cargo")
            n_demissao = st.text_input("Data de Demissão (Opcional - AAAA-MM-DD)", key="k_nc_dem")
            n_pix = st.text_input("Chave PIX", key="k_nc_pix")
            n_sal_hora = st.text_input("Salário-Hora Atual", key="k_nc_sal_hora")
            
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        submetido = st.button("💾 Salvar Registro no Sistema", key="k_nc_btn_salvar")
        if submetido:
            if not n_id.strip() or not n_nome.strip():
                st.error("⚠️ Os campos 'ID / Matrícula' e 'Nome Completo' são obrigatórios.")
            else:
                try:
                    with engine.begin() as conn: 
                        conn.execute(text("""
                            INSERT INTO cadastro_geral_colaborador 
                            (id, nome, cpf, cargo, admissao, demissao, salario_mes_12_24, salario_hora, chave_pix) 
                            VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :sm, :sh, :pix)
                        """), {
                            "id": str(n_id), 
                            "nome": str(n_nome),
                            "cpf": str(n_cpf) if n_cpf.strip() else None,
                            "cargo": str(n_cargo) if n_cargo.strip() else None,
                            "admissao": str(n_admissao) if n_admissao.strip() else None,
                            "demissao": str(n_demissao) if n_demissao.strip() else None,
                            "sm": str(n_sal_mes) if n_sal_mes.strip() else None,
                            "sh": str(n_sal_hora) if n_sal_hora.strip() else None,
                            "pix": str(n_pix) if n_pix.strip() else None
                        })
                    st.success(f"Colaborador {n_nome} inserido com sucesso!")
                    st.session_state['redirect_to_consulta'] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro de Integridade: Verifique se o ID digitado já pertence a outro cadastro. Detalhes: {e}")
