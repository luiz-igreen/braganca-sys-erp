import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    """
    Módulo de Cadastro Geral de Colaboradores (BRAGANÇA SYS).
    Permite a visualização da base atual e o cadastro manual de novos funcionários.
    """
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
            # Busca todos os registros da tabela principal
            query_select = text("SELECT * FROM cadastro_geral_colaborador ORDER BY nome")
            df_colaboradores = pd.read_sql(query_select, con=engine)

            if not df_colaboradores.empty:
                # Formatação de exibição para valores monetários
                colunas_monetarias = ['salario_mes', 'salario_hora']
                for col in colunas_monetarias:
                    if col in df_colaboradores.columns:
                        df_colaboradores[col] = pd.to_numeric(df_colaboradores[col], errors='coerce')
                        df_colaboradores[col] = df_colaboradores[col].apply(
                            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else ""
                        )

                # Exibe o dataframe completo
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

        with st.form("form_novo_colaborador", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            codigo = col1.text_input("Código do Colaborador (Identificador)")
            nome = col2.text_input("Nome Completo")
            cpf = col3.text_input("CPF")

            col4, col5, col6 = st.columns(3)
            cargo = col4.text_input("Cargo")
            obra = col5.text_input("Obra", value="Construart")
            admissao = col6.date_input("Data de Admissão")

            col7, col8, col9 = st.columns(3)
            salario_mes = col7.number_input("Salário Mês (R$)", min_value=0.0, format="%.2f")
            salario_hora = col8.number_input("Salário Hora (R$)", min_value=0.0, format="%.2f")
            status_esocial = col9.selectbox("Status eSocial", ["Ativo", "9 - Férias", "Afastado", "Desligado"])

            submit_button = st.form_submit_button("Salvar Colaborador", type="primary")

            if submit_button:
                if not codigo or not nome:
                    st.error("Os campos 'Código' e 'Nome' são obrigatórios.")
                else:
                    query_insert = text("""
                        INSERT INTO cadastro_geral_colaborador (
                            codigo, nome, cpf, cargo, obra, admissao, 
                            salario_mes, salario_hora, status_esocial
                        ) VALUES (
                            :codigo, :nome, :cpf, :cargo, :obra, :admissao, 
                            :salario_mes, :salario_hora, :status_esocial
                        )
                    """)

                    parametros = {
                        "codigo": codigo, "nome": nome, "cpf": cpf, "cargo": cargo,
                        "obra": obra, "admissao": admissao, "salario_mes": salario_mes,
                        "salario_hora": salario_hora, "status_esocial": status_esocial
                    }

                    try:
                        with engine.begin() as conn:
                            conn.execute(query_insert, parametros)
                        st.success(f"Colaborador {nome} cadastrado com sucesso na base geral!")
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados. Detalhe: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
