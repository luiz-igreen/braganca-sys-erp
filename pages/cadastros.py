import streamlit as st
import pandas as pd
from sqlalchemy import text

# Motor de Cache para deixar o sistema ultrarrápido (Evita consultar o banco 7 vezes a cada clique)
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_dataframe(_engine, query):
    return pd.read_sql(text(query), _engine)

def render(engine, *args, **kwargs):
    st.title("Gestão de Cadastros e Tabelas Base")
    st.markdown("Gerenciamento central da base de funcionários e dos domínios estruturais do sistema.")

    # Função para limpar os campos após Salvar/Cancelar/Excluir
    def limpar_estado(chaves):
        get_cached_dataframe.clear() # Limpa a memória para forçar atualização
        for chave in chaves:
            if chave in st.session_state:
                del st.session_state[chave]

    tabs = st.tabs([
        "Consultar Base", 
        "Novo Colaborador", 
        "🏢 Obras", 
        "👔 Cargos", 
        "🏢 Departamentos", 
        "🏥 Situações eSocial", 
        "🏆 Prêmios"
    ])

    tab_consultar, tab_novo, tab_obras, tab_cargos, tab_deptos, tab_situacoes, tab_premios = tabs

    def buscar_opcoes(query_sql, coluna_retorno, fallback_list):
        try:
            df = get_cached_dataframe(engine, query_sql)
            if not df.empty and coluna_retorno in df.columns:
                opcoes = df[df[coluna_retorno].notna()][coluna_retorno].astype(str).str.strip().unique().tolist()
                opcoes = [op for op in opcoes if op]
                if opcoes:
                    return sorted(opcoes)
        except Exception:
            pass
        return fallback_list

    # ==========================================
    # ABA 1: CONSULTAR BASE DE DADOS
    # ==========================================
    with tab_consultar:
        st.subheader("Colaboradores Cadastrados")
        try:
            df_colaboradores = get_cached_dataframe(engine, "SELECT * FROM cadastro_geral_colaborador ORDER BY nome")
            if not df_colaboradores.empty:
                colunas_monetarias = ['salario_mes', 'salario_hora']
                for col in colunas_monetarias:
                    if col in df_colaboradores.columns:
                        df_colaboradores[col] = pd.to_numeric(df_colaboradores[col], errors='coerce')
                        df_colaboradores[col] = df_colaboradores[col].apply(
                            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else ""
                        )
                st.dataframe(df_colaboradores, use_container_width=True, hide_index=True)
                st.caption(f"Total de colaboradores registrados: {len(df_colaboradores)}")
            else:
                st.info("Nenhum colaborador encontrado na tabela.")
        except Exception as e:
            st.error(f"Erro ao carregar a base de colaboradores. Detalhe: {e}")

    # ==========================================
    # ABA 2: NOVO COLABORADOR
    # ==========================================
    with tab_novo:
        st.subheader("Adicionar Novo Colaborador")
        
        lista_departamentos = buscar_opcoes("SELECT nome FROM cadastro_departamentos", "nome", ["ADMINISTRAÇÃO CENTRAL"])
        lista_obras = buscar_opcoes("SELECT nome FROM cadastro_obras", "nome", ["CONSTRUART"])
        lista_cargos = buscar_opcoes("SELECT nome FROM cadastro_cargos", "nome", ["Pedreiro"])

        with st.form("form_novo_colaborador", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            codigo = col1.text_input("Código do Colaborador")
            nome = col2.text_input("Nome Completo")
            cpf = col3.text_input("CPF")

            col4, col5, col6 = st.columns(3)
            cargo = col4.selectbox("Cargo", options=lista_cargos)
            departamento = col5.selectbox("Departamento", options=lista_departamentos)
            obra = col6.selectbox("Obra", options=lista_obras)

            col7, col8, col9, col10 = st.columns(4)
            admissao = col7.date_input("Data de Admissão")
            salario_mes = col8.number_input("Salário Mês (R$)", min_value=0.0, format="%.2f")
            salario_hora = col9.number_input("Salário Hora (R$)", min_value=0.0, format="%.2f")
            status_esocial = col10.text_input("Status eSocial", value="Ativo", disabled=True)

            c_col1, c_col2 = st.columns(2)
            submit_button = c_col1.form_submit_button("💾 Salvar Colaborador", type="primary", use_container_width=True)
            cancel_button = c_col2.form_submit_button("❌ Cancelar", use_container_width=True)

            if submit_button:
                if not codigo or not nome:
                    st.error("Os campos 'Código' e 'Nome' são obrigatórios.")
                else:
                    query_insert = text("""
                        INSERT INTO cadastro_geral_colaborador (
                            codigo, nome, cpf, cargo, departamento, obra, admissao, 
                            salario_mes, salario_hora, status_esocial
                        ) VALUES (
                            :codigo, :nome, :cpf, :cargo, :departamento, :obra, :admissao, 
                            :salario_mes, :salario_hora, :status_esocial
                        )
                    """)
                    parametros = {
                        "codigo": codigo, "nome": nome, "cpf": cpf, "cargo": cargo,
                        "departamento": departamento, "obra": obra, "admissao": admissao, 
                        "salario_mes": salario_mes, "salario_hora": salario_hora, "status_esocial": "Ativo"
                    }
                    try:
                        with engine.begin() as conn:
                            conn.execute(query_insert, parametros)
                        st.toast(f"✅ Colaborador {nome} cadastrado com sucesso!")
                        get_cached_dataframe.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
            
            if cancel_button:
                st.rerun()

    # ==========================================
    # ABA 3: GERENCIAR OBRAS
    # ==========================================
    with tab_obras:
        st.subheader("Gestão de Obras")
        df_obras = get_cached_dataframe(engine, "SELECT * FROM cadastro_obras ORDER BY nome")
        
        st.markdown("#### 🔍 Consulta e Seleção")
        c1, c2 = st.columns([1, 2])
        busca_ob = c1.text_input("Busca Rápida (Digite ID ou Nome):", key="busca_ob")
        
        opcoes_obras = ["➕ Novo Registro (Criar)"] + [f"{r['id']} | {r['nome']}" for _, r in df_obras.iterrows()]
        if busca_ob:
            opcoes_obras = [op for op in opcoes_obras if busca_ob.lower() in str(op).lower() or "➕" in op]
            
        selecao_obra = c2.selectbox("Selecione o Registro abaixo:", opcoes_obras, key="sel_obra")
        st.markdown("---")
        
        if selecao_obra == "➕ Novo Registro (Criar)":
            with st.form("form_obra_novo", clear_on_submit=True):
                st.markdown("#### Criar Nova Obra")
                obra_id = st.text_input("ID / Código da Obra")
                obra_nome = st.text_input("Nome da Obra")
                col1, col2 = st.columns(2)
                obra_cnpj = col1.text_input("CNPJ (Opcional)")
                obra_cno = col2.text_input("CNO (Opcional)")
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Salvar Obra", type="primary", use_container_width=True):
                    if obra_id and obra_nome:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO cadastro_obras (id, nome, cnpj, cno) VALUES (:id, :nome, :cnpj, :cno)"), 
                                             {"id": obra_id, "nome": obra_nome, "cnpj": obra_cnpj, "cno": obra_cno})
                            st.toast("✅ Obra cadastrada com sucesso!")
                            limpar_estado(['busca_ob', 'sel_obra'])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        st.warning("ID e Nome são obrigatórios.")
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_ob', 'sel_obra'])
                    st.rerun()
        else:
            id_sel = selecao_obra.split(" | ")[0]
            row = df_obras[df_obras['id'].astype(str) == id_sel].iloc[0]
            
            with st.form(f"form_obra_editar_{id_sel}"):
                st.markdown("#### Alterar / Excluir Obra")
                obra_id = st.text_input("ID / Código (Inalterável)", value=row['id'], disabled=True)
                obra_nome = st.text_input("Nome da Obra", value=row['nome'])
                col1, col2 = st.columns(2)
                obra_cnpj = col1.text_input("CNPJ", value=str(row['cnpj']) if pd.notna(row['cnpj']) else "")
                obra_cno = col2.text_input("CNO", value=str(row['cno']) if pd.notna(row['cno']) else "")
                
                b1, b2, b3 = st.columns(3)
                if b1.form_submit_button("✏️ Alterar Obra", type="primary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE cadastro_obras SET nome=:nome, cnpj=:cnpj, cno=:cno WHERE id=:id"), 
                                         {"id": obra_id, "nome": obra_nome, "cnpj": obra_cnpj, "cno": obra_cno})
                        st.toast("✅ Obra atualizada!")
                        limpar_estado(['busca_ob', 'sel_obra'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b2.form_submit_button("🗑️ Excluir Obra", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM cadastro_obras WHERE id=:id"), {"id": obra_id})
                        st.toast("🗑️ Obra removida!")
                        limpar_estado(['busca_ob', 'sel_obra'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro (Pode estar em uso): {e}")
                if b3.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_ob', 'sel_obra'])
                    st.rerun()

        st.markdown("---")
        st.dataframe(df_obras, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 4: GERENCIAR CARGOS
    # ==========================================
    with tab_cargos:
        st.subheader("Gestão de Cargos")
        df_cargos = get_cached_dataframe(engine, "SELECT * FROM cadastro_cargos ORDER BY nome")
        
        st.markdown("#### 🔍 Consulta e Seleção")
        c1, c2 = st.columns([1, 2])
        busca_cg = c1.text_input("Busca Rápida (Digite ID ou Nome):", key="busca_cg")
        
        opcoes_cargos = ["➕ Novo Registro (Criar)"] + [f"{r['codigo']} | {r['nome']}" for _, r in df_cargos.iterrows()]
        if busca_cg:
            opcoes_cargos = [op for op in opcoes_cargos if busca_cg.lower() in str(op).lower() or "➕" in op]
            
        selecao_cargo = c2.selectbox("Selecione o Registro abaixo:", opcoes_cargos, key="sel_cg")
        st.markdown("---")
        
        if selecao_cargo == "➕ Novo Registro (Criar)":
            with st.form("form_cargo_novo", clear_on_submit=True):
                st.markdown("#### Criar Novo Cargo")
                col1, col2 = st.columns([1, 3])
                cg_cod = col1.number_input("Código", min_value=1, step=1)
                cg_nome = col2.text_input("Nome do Cargo")
                cg_cbo = st.text_input("CBO 2002")
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Salvar Cargo", type="primary", use_container_width=True):
                    if cg_nome:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO cadastro_cargos (codigo, nome, cbo_2002) VALUES (:cod, :nome, :cbo)"), 
                                             {"cod": cg_cod, "nome": cg_nome, "cbo": cg_cbo})
                            st.toast("✅ Cargo cadastrado!")
                            limpar_estado(['busca_cg', 'sel_cg'])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        st.warning("O Nome do Cargo é obrigatório.")
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_cg', 'sel_cg'])
                    st.rerun()
        else:
            id_sel = selecao_cargo.split(" | ")[0]
            row = df_cargos[df_cargos['codigo'].astype(str) == id_sel].iloc[0]
            
            with st.form(f"form_cargo_editar_{id_sel}"):
                st.markdown("#### Alterar / Excluir Cargo")
                col1, col2 = st.columns([1, 3])
                cg_cod = col1.number_input("Código (Inalterável)", value=int(row['codigo']), disabled=True)
                cg_nome = col2.text_input("Nome do Cargo", value=row['nome'])
                cg_cbo = st.text_input("CBO 2002", value=str(row['cbo_2002']) if pd.notna(row['cbo_2002']) else "")
                
                b1, b2, b3 = st.columns(3)
                if b1.form_submit_button("✏️ Alterar Cargo", type="primary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE cadastro_cargos SET nome=:nome, cbo_2002=:cbo WHERE codigo=:cod"), 
                                         {"cod": cg_cod, "nome": cg_nome, "cbo": cg_cbo})
                        st.toast("✅ Cargo atualizado!")
                        limpar_estado(['busca_cg', 'sel_cg'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b2.form_submit_button("🗑️ Excluir Cargo", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM cadastro_cargos WHERE codigo=:cod"), {"cod": cg_cod})
                        st.toast("🗑️ Cargo removido!")
                        limpar_estado(['busca_cg', 'sel_cg'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b3.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_cg', 'sel_cg'])
                    st.rerun()

        st.markdown("---")
        st.dataframe(df_cargos, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 5: GERENCIAR DEPARTAMENTOS
    # ==========================================
    with tab_deptos:
        st.subheader("Gestão de Departamentos")
        df_deptos = get_cached_dataframe(engine, "SELECT * FROM cadastro_departamentos ORDER BY nome")
        
        st.markdown("#### 🔍 Consulta e Seleção")
        c1, c2 = st.columns([1, 2])
        busca_dp = c1.text_input("Busca Rápida (Digite ID ou Nome):", key="busca_dp")
        
        opcoes_dp = ["➕ Novo Registro (Criar)"] + [f"{r['id']} | {r['nome']}" for _, r in df_deptos.iterrows()]
        if busca_dp:
            opcoes_dp = [op for op in opcoes_dp if busca_dp.lower() in str(op).lower() or "➕" in op]
            
        selecao_dp = c2.selectbox("Selecione o Registro abaixo:", opcoes_dp, key="sel_dp")
        st.markdown("---")
        
        if selecao_dp == "➕ Novo Registro (Criar)":
            with st.form("form_depto_novo", clear_on_submit=True):
                st.markdown("#### Criar Novo Departamento")
                dp_id = st.text_input("ID / Sigla do Departamento")
                dp_nome = st.text_input("Nome do Departamento")
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Salvar Departamento", type="primary", use_container_width=True):
                    if dp_id and dp_nome:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO cadastro_departamentos (id, nome) VALUES (:id, :nome)"), 
                                             {"id": dp_id, "nome": dp_nome})
                            st.toast("✅ Departamento cadastrado!")
                            limpar_estado(['busca_dp', 'sel_dp'])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        st.warning("ID e Nome são obrigatórios.")
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_dp', 'sel_dp'])
                    st.rerun()
        else:
            id_sel = selecao_dp.split(" | ")[0]
            row = df_deptos[df_deptos['id'].astype(str) == id_sel].iloc[0]
            
            with st.form(f"form_depto_editar_{id_sel}"):
                st.markdown("#### Alterar / Excluir Departamento")
                dp_id = st.text_input("ID / Sigla (Inalterável)", value=row['id'], disabled=True)
                dp_nome = st.text_input("Nome do Departamento", value=row['nome'])
                
                b1, b2, b3 = st.columns(3)
                if b1.form_submit_button("✏️ Alterar Depto", type="primary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE cadastro_departamentos SET nome=:nome WHERE id=:id"), 
                                         {"id": dp_id, "nome": dp_nome})
                        st.toast("✅ Departamento atualizado!")
                        limpar_estado(['busca_dp', 'sel_dp'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b2.form_submit_button("🗑️ Excluir Depto", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM cadastro_departamentos WHERE id=:id"), {"id": dp_id})
                        st.toast("🗑️ Departamento removido!")
                        limpar_estado(['busca_dp', 'sel_dp'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b3.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_dp', 'sel_dp'])
                    st.rerun()

        st.markdown("---")
        st.dataframe(df_deptos, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 6: SITUAÇÕES ESOCIAL
    # ==========================================
    with tab_situacoes:
        st.subheader("Gestão de Situações (eSocial)")
        df_sit = get_cached_dataframe(engine, "SELECT * FROM dominio_situacoes_esocial ORDER BY codigo")
        
        st.markdown("#### 🔍 Consulta e Seleção")
        c1, c2 = st.columns([1, 2])
        busca_sit = c1.text_input("Busca Rápida (Digite ID ou Nome):", key="busca_sit")
        
        opcoes_sit = ["➕ Novo Registro (Criar)"] + [f"{r['codigo']} | {r['descricao']}" for _, r in df_sit.iterrows()]
        if busca_sit:
            opcoes_sit = [op for op in opcoes_sit if busca_sit.lower() in str(op).lower() or "➕" in op]
            
        selecao_sit = c2.selectbox("Selecione o Registro abaixo:", opcoes_sit, key="sel_sit")
        st.markdown("---")
        
        if selecao_sit == "➕ Novo Registro (Criar)":
            with st.form("form_sit_novo", clear_on_submit=True):
                st.markdown("#### Criar Nova Situação")
                sit_cod = st.text_input("Código da Situação")
                sit_desc = st.text_input("Descrição da Situação")
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Salvar Situação", type="primary", use_container_width=True):
                    if sit_cod and sit_desc:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO dominio_situacoes_esocial (codigo, descricao) VALUES (:cod, :desc)"), 
                                             {"cod": sit_cod, "desc": sit_desc})
                            st.toast("✅ Situação salva!")
                            limpar_estado(['busca_sit', 'sel_sit'])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        st.warning("Código e Descrição são obrigatórios.")
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_sit', 'sel_sit'])
                    st.rerun()
        else:
            id_sel = selecao_sit.split(" | ")[0]
            row = df_sit[df_sit['codigo'].astype(str) == id_sel].iloc[0]
            
            with st.form(f"form_sit_editar_{id_sel}"):
                st.markdown("#### Alterar / Excluir Situação")
                sit_cod = st.text_input("Código (Inalterável)", value=row['codigo'], disabled=True)
                sit_desc = st.text_input("Descrição", value=row['descricao'])
                
                b1, b2, b3 = st.columns(3)
                if b1.form_submit_button("✏️ Alterar Situação", type="primary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE dominio_situacoes_esocial SET descricao=:desc WHERE codigo=:cod"), 
                                         {"cod": sit_cod, "desc": sit_desc})
                        st.toast("✅ Situação atualizada!")
                        limpar_estado(['busca_sit', 'sel_sit'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b2.form_submit_button("🗑️ Excluir Situação", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM dominio_situacoes_esocial WHERE codigo=:cod"), {"cod": sit_cod})
                        st.toast("🗑️ Situação removida!")
                        limpar_estado(['busca_sit', 'sel_sit'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b3.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_sit', 'sel_sit'])
                    st.rerun()

        st.markdown("---")
        st.dataframe(df_sit, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 7: TABELA DE PRÊMIOS
    # ==========================================
    with tab_premios:
        st.subheader("Base de Descrições de Prêmios")
        df_prem = get_cached_dataframe(engine, "SELECT * FROM lista_descricoes_premios ORDER BY nome_descricao")
        
        st.markdown("#### 🔍 Consulta e Seleção")
        c1, c2 = st.columns([1, 2])
        busca_pr = c1.text_input("Busca Rápida (Digite ID ou Nome):", key="busca_pr")
        
        opcoes_prem = ["➕ Novo Registro (Criar)"] + [f"{r['codigo_descricao']} | {r['nome_descricao']}" for _, r in df_prem.iterrows()]
        if busca_pr:
            opcoes_prem = [op for op in opcoes_prem if busca_pr.lower() in str(op).lower() or "➕" in op]
            
        selecao_prem = c2.selectbox("Selecione o Registro abaixo:", opcoes_prem, key="sel_pr")
        st.markdown("---")
        
        if selecao_prem == "➕ Novo Registro (Criar)":
            with st.form("form_premio_novo", clear_on_submit=True):
                st.markdown("#### Criar Nova Descrição de Prêmio")
                col1, col2 = st.columns([1, 2])
                pr_cod = col1.text_input("Código da Descrição")
                pr_nome = col2.text_input("Nome da Descrição")
                pr_obra = st.text_input("Obra Vinculada (Opcional)")
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Salvar Prêmio", type="primary", use_container_width=True):
                    if pr_cod and pr_nome:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO lista_descricoes_premios (codigo_descricao, nome_descricao, obra_vinculada) VALUES (:cod, :nome, :obra)"), 
                                             {"cod": pr_cod, "nome": pr_nome, "obra": pr_obra})
                            st.toast("✅ Descrição de prêmio cadastrada!")
                            limpar_estado(['busca_pr', 'sel_pr'])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        st.warning("Código e Nome da Descrição são obrigatórios.")
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_pr', 'sel_pr'])
                    st.rerun()
        else:
            id_sel = selecao_prem.split(" | ")[0]
            row = df_prem[df_prem['codigo_descricao'].astype(str) == id_sel].iloc[0]
            
            with st.form(f"form_premio_editar_{id_sel}"):
                st.markdown("#### Alterar / Excluir Descrição de Prêmio")
                col1, col2 = st.columns([1, 2])
                pr_cod = col1.text_input("Código (Inalterável)", value=row['codigo_descricao'], disabled=True)
                pr_nome = col2.text_input("Nome da Descrição", value=row['nome_descricao'])
                pr_obra = st.text_input("Obra Vinculada (Opcional)", value=str(row['obra_vinculada']) if pd.notna(row['obra_vinculada']) else "")
                
                b1, b2, b3 = st.columns(3)
                if b1.form_submit_button("✏️ Alterar Prêmio", type="primary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE lista_descricoes_premios SET nome_descricao=:nome, obra_vinculada=:obra WHERE codigo_descricao=:cod"), 
                                         {"cod": pr_cod, "nome": pr_nome, "obra": pr_obra})
                        st.toast("✅ Descrição de prêmio alterada!")
                        limpar_estado(['busca_pr', 'sel_pr'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b2.form_submit_button("🗑️ Excluir Prêmio", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM lista_descricoes_premios WHERE codigo_descricao=:cod"), {"cod": pr_cod})
                        st.toast("🗑️ Descrição de prêmio removida!")
                        limpar_estado(['busca_pr', 'sel_pr'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                if b3.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_pr', 'sel_pr'])
                    st.rerun()

        st.markdown("---")
        st.dataframe(df_prem, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption("🏗️ BRAGANÇA SYS | Módulo de Gestão Estrutural")
