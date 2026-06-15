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
            st.error(f"Erro ao carregar a base de colaboradores. Verifique se a tabela existe no Supabase. Detalhe: {e}")

    # ==========================================
    # ABA 2: NOVO COLABORADOR (LANÇAMENTO MANUAL)
    # ==========================================
    with tab2:
        st.subheader("Adicionar Novo Colaborador")

        # Função robusta para buscar listas do banco de dados (com fallback para dados existentes)
        def buscar_opcoes(coluna_alvo, tabela_dominio):
            try:
                # Tenta buscar da tabela de domínio específica (ex: tabela 'cargos')
                query = text(f"SELECT nome FROM {tabela_dominio} ORDER BY nome")
                df = pd.read_sql(query, con=engine)
                if not df.empty:
                    return df['nome'].tolist()
            except Exception:
                pass

            try:
                # Fallback: busca os valores únicos já cadastrados na tabela principal
                query = text(f"SELECT DISTINCT {coluna_alvo} FROM cadastro_geral_colaborador WHERE {coluna_alvo} IS NOT NULL AND {coluna_alvo} != '' ORDER BY {coluna_alvo}")
                df = pd.read_sql(query, con=engine)
                if not df.empty:
                    return df[coluna_alvo].tolist()
            except Exception:
                pass

            return ["Adicione opções no banco de dados"]

        # Carregando as listas dinâmicas
        lista_cargos = buscar_opcoes('cargo', 'cargos')
        lista_departamentos = buscar_opcoes('departamento', 'departamentos')
        lista_obras = buscar_opcoes('obra', 'obras')

        with st.form("form_novo_colaborador", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            codigo = col1.text_input("Código do Colaborador (Identificador)")
            nome = col2.text_input("Nome Completo")
            cpf = col3.text_input("CPF")

            # Linha com as listas de seleção (Selectboxes)
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
                        "status_esocial": "Ativo" # Forçado no backend
                    }

                    try:
                        with engine.begin() as conn:
                            conn.execute(query_insert, parametros)
                        st.success(f"Colaborador {nome} cadastrado com sucesso na base geral!")
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados. Verifique se a coluna 'departamento' existe na tabela. Detalhe: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
