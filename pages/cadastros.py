import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    st.title("Cadastro Geral de Colaboradores")
    st.markdown("Gerenciamento da base principal de funcionários da Construart.")

    tab1, tab2 = st.tabs(["Consultar Base de Dados", "Novo Colaborador"])

    # ==========================================
    # ABA 1: CONSULTAR BASE DE DADOS
    # ==========================================
    with tab1:
        st.subheader("Colaboradores Cadastrados")
        st.markdown("Analise as informações constantes no banco de dados para verificar se há necessidade de alterações.")

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
                st.info("Nenhum colaborador encontrado na tabela 'cadastro_geral_colaborador'.")

        except Exception as e:
            st.error(f"Erro ao carregar a base de colaboradores. Detalhe: {e}")

    # ==========================================
    # ABA 2: NOVO COLABORADOR (LANÇAMENTO MANUAL)
    # ==========================================
    with tab2:
        st.subheader("Adicionar Novo Colaborador")

        # Função robusta para buscar listas diretamente das tabelas do Supabase
        def buscar_opcoes(query_sql, coluna_retorno, fallback_list):
            try:
                df = pd.read_sql(text(query_sql), con=engine)
                if not df.empty and coluna_retorno in df.columns:
                    # Remove nulos, converte para texto e pega valores únicos
                    opcoes = df[df[coluna_retorno].notna()][coluna_retorno].astype(str).str.strip().unique().tolist()
                    opcoes = [op for op in opcoes if op] # Remove strings vazias
                    if opcoes:
                        return sorted(opcoes)
            except Exception:
                pass
            return fallback_list

        # Buscando dados reais das tabelas que você mostrou nos prints
        lista_departamentos = buscar_opcoes("SELECT nome FROM cadastro_departamentos", "nome", ["ADMINISTRAÇÃO CENTRAL", "CANTEIRO DE OBRA"])
        lista_obras = buscar_opcoes("SELECT nome FROM cadastro_obras", "nome", ["CONSTRUART", "LISBOA EMPREENDIMENTO"])

        # Como a tabela de cargos não apareceu no print, o sistema busca os cargos já existentes na tabela de colaboradores
        lista_cargos = buscar_opcoes("SELECT DISTINCT cargo FROM cadastro_geral_colaborador WHERE cargo IS NOT NULL", "cargo", ["Pedreiro", "Servente", "Mestre de Obras"])

        with st.form("form_novo_colaborador", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            codigo = col1.text_input("Código do Colaborador (Identificador)")
            nome = col2.text_input("Nome Completo")
            cpf = col3.text_input("CPF")

            # Linha com as listas de seleção (Selectboxes) puxando do banco
            col4, col5, col6 = st.columns(3)
            cargo = col4.selectbox("Cargo", options=lista_cargos)
            departamento = col5.selectbox("Departamento", options=lista_departamentos)
            obra = col6.selectbox("Obra", options=lista_obras)

            # Linha com dados financeiros e status fixo
            col7, col8, col9, col10 = st.columns(4)
            admissao = col7.date_input("Data de Admissão")
            salario_mes = col8.number_input("Salário Mês (R$)", min_value=0.0, format="%.2f")
            salario_hora = col9.number_input("Salário Hora (R$)", min_value=0.0, format="%.2f")

            # Status eSocial fixado como "Ativo" e desabilitado para edição
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
                        "codigo": codigo, 
                        "nome": nome, 
                        "cpf": cpf, 
                        "cargo": cargo,
                        "departamento": departamento,
                        "obra": obra, 
                        "admissao": admissao, 
                        "salario_mes": salario_mes,
                        "salario_hora": salario_hora, 
                        "status_esocial": "Ativo" # Forçado no backend para garantir a regra
                    }

                    try:
                        with engine.begin() as conn:
                            conn.execute(query_insert, parametros)
                        st.success(f"Colaborador {nome} cadastrado com sucesso na base geral!")
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados. Detalhe: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
