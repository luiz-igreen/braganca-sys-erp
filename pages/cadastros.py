import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    st.title("Gestão de Cadastros e Tabelas Base")
    st.markdown("Gerenciamento central da base de funcionários e dos domínios estruturais do sistema.")

    # Criação das 7 Abas
    tabs = st.tabs([
        "Consultar Base", 
        "Novo Colaborador", 
        "🏢 Gerenciar Obras", 
        "👔 Gerenciar Cargos", 
        "🏢 Departamentos", 
        "🏥 Situações eSocial", 
        "🏆 Tabela de Prêmios"
    ])

    tab_consultar, tab_novo, tab_obras, tab_cargos, tab_deptos, tab_situacoes, tab_premios = tabs

    # ==========================================
    # FUNÇÃO AUXILIAR GLOBAL
    # ==========================================
    def buscar_opcoes(query_sql, coluna_retorno, fallback_list):
        try:
            df = pd.read_sql(text(query_sql), con=engine)
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
            query_select = text("SELECT * FROM cadastro_geral_colaborador ORDER BY nome")
            df_colaboradores = pd.read_sql(query_select, con=engine)

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

            submit_button = st.form_submit_button("Salvar Colaborador", type="primary")

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
                        st.success(f"Colaborador {nome} cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # ==========================================
    # ABA 3: GERENCIAR OBRAS
    # ==========================================
    with tab_obras:
        st.subheader("Cadastro de Obras")
        with st.form("form_nova_obra", clear_on_submit=True):
            col1, col2 = st.columns(2)
            obra_id = col1.text_input("ID / Código da Obra")
            obra_nome = col2.text_input("Nome da Obra")
            
            col3, col4 = st.columns(2)
            obra_cnpj = col3.text_input("CNPJ (Opcional)")
            obra_cno = col4.text_input("CNO (Opcional)")
            
            if st.form_submit_button("Adicionar Obra"):
                if obra_id and obra_nome:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO cadastro_obras (id, nome, cnpj, cno) VALUES (:id, :nome, :cnpj, :cno)"), 
                                         {"id": obra_id, "nome": obra_nome, "cnpj": obra_cnpj, "cno": obra_cno})
                        st.success("Obra adicionada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Preencha o ID e o Nome.")
                    
        st.markdown("---")
        df_obras = pd.read_sql("SELECT * FROM cadastro_obras ORDER BY nome", engine)
        st.dataframe(df_obras, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 4: GERENCIAR CARGOS
    # ==========================================
    with tab_cargos:
        st.subheader("Cadastro de Cargos")
        with st.form("form_novo_cargo", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            cargo_cod = col1.number_input("Código", min_value=1, step=1)
            cargo_nome = col2.text_input("Nome do Cargo")
            cargo_cbo = col3.text_input("CBO 2002")
            
            if st.form_submit_button("Adicionar Cargo"):
                if cargo_nome:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO cadastro_cargos (codigo, nome, cbo_2002) VALUES (:cod, :nome, :cbo)"), 
                                         {"cod": cargo_cod, "nome": cargo_nome, "cbo": cargo_cbo})
                        st.success("Cargo adicionado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("O Nome do Cargo é obrigatório.")
                    
        st.markdown("---")
        df_cargos = pd.read_sql("SELECT * FROM cadastro_cargos ORDER BY nome", engine)
        st.dataframe(df_cargos, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 5: GERENCIAR DEPARTAMENTOS
    # ==========================================
    with tab_deptos:
        st.subheader("Cadastro de Departamentos")
        with st.form("form_novo_depto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            depto_id = col1.text_input("ID / Sigla do Departamento")
            depto_nome = col2.text_input("Nome do Departamento")
            
            if st.form_submit_button("Adicionar Departamento"):
                if depto_id and depto_nome:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO cadastro_departamentos (id, nome) VALUES (:id, :nome)"), 
                                         {"id": depto_id, "nome": depto_nome})
                        st.success("Departamento adicionado!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Preencha ID e Nome.")
                    
        st.markdown("---")
        df_deptos = pd.read_sql("SELECT * FROM cadastro_departamentos ORDER BY nome", engine)
        st.dataframe(df_deptos, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 6: SITUAÇÕES ESOCIAL
    # ==========================================
    with tab_situacoes:
        st.subheader("Cadastro de Situações (eSocial)")
        with st.form("form_nova_situacao", clear_on_submit=True):
            col1, col2 = st.columns([1, 3])
            sit_cod = col1.text_input("Código")
            sit_desc = col2.text_input("Descrição da Situação")
            
            if st.form_submit_button("Adicionar Situação"):
                if sit_cod and sit_desc:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO dominio_situacoes_esocial (codigo, descricao) VALUES (:cod, :desc)"), 
                                         {"cod": sit_cod, "desc": sit_desc})
                        st.success("Situação adicionada!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Preencha Código e Descrição.")
                    
        st.markdown("---")
        df_situacoes = pd.read_sql("SELECT * FROM dominio_situacoes_esocial ORDER BY codigo", engine)
        st.dataframe(df_situacoes, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 7: TABELA DE PRÊMIOS
    # ==========================================
    with tab_premios:
        st.subheader("Base de Descrições de Prêmios")
        with st.form("form_novo_premio", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 2, 2])
            prem_cod = col1.text_input("Código da Descrição")
            prem_nome = col2.text_input("Nome da Descrição")
            prem_obra = col3.text_input("Obra Vinculada (Opcional)")
            
            if st.form_submit_button("Adicionar Descrição"):
                if prem_cod and prem_nome:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO lista_descricoes_premios (codigo_descricao, nome_descricao, obra_vinculada) VALUES (:cod, :nome, :obra)"), 
                                         {"cod": prem_cod, "nome": prem_nome, "obra": prem_obra})
                        st.success("Descrição de prêmio adicionada!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Preencha Código e Nome da Descrição.")
                    
        st.markdown("---")
        df_premios = pd.read_sql("SELECT * FROM lista_descricoes_premios ORDER BY nome_descricao", engine)
        st.dataframe(df_premios, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption("🏗️ BRAGANÇA SYS | Módulo de Gestão Estrutural")
