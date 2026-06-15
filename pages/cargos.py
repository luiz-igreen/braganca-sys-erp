import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    st.title("Cadastro de Cargos")
    st.markdown("Gerenciamento de cargos padronizado (Referência: Domínio Sistemas).")

    # Inicialização de estados da interface
    if 'cargo_modo' not in st.session_state:
        st.session_state.cargo_modo = 'novo'
    if 'cargo_codigo' not in st.session_state:
        st.session_state.cargo_codigo = ''
    if 'cargo_nome' not in st.session_state:
        st.session_state.cargo_nome = ''
    if 'cargo_cbo' not in st.session_state:
        st.session_state.cargo_cbo = ''

    def limpar_formulario():
        st.session_state.cargo_modo = 'novo'
        st.session_state.cargo_codigo = ''
        st.session_state.cargo_nome = ''
        st.session_state.cargo_cbo = ''

    # Layout principal: Formulário à esquerda, Botões à direita
    col_form, col_botoes = st.columns([3, 1])

    with col_form:
        st.subheader("Dados do Cargo")

        codigo_input = st.text_input(
            "Código:", 
            value=st.session_state.cargo_codigo, 
            disabled=(st.session_state.cargo_modo == 'editando')
        )

        nome_input = st.text_input(
            "Nome:", 
            value=st.session_state.cargo_nome,
            disabled=(st.session_state.cargo_modo == 'consultando')
        )

        cbo_input = st.text_input(
            "C.B.O. 2002:", 
            value=st.session_state.cargo_cbo,
            disabled=(st.session_state.cargo_modo == 'consultando')
        )

    with col_botoes:
        st.subheader("Ações")

        if st.button("Novo", use_container_width=True):
            limpar_formulario()
            st.rerun()

        if st.button("Consultar", use_container_width=True):
            if codigo_input:
                try:
                    query = text("SELECT codigo, nome, cbo FROM cadastro_cargos WHERE codigo = :codigo")
                    with engine.connect() as conn:
                        result = conn.execute(query, {"codigo": codigo_input}).fetchone()

                    if result:
                        st.session_state.cargo_modo = 'consultando'
                        st.session_state.cargo_codigo = str(result[0])
                        st.session_state.cargo_nome = result[1]
                        st.session_state.cargo_cbo = result[2]
                        st.rerun()
                    else:
                        st.warning("Cargo não encontrado.")
                except Exception as e:
                    st.error(f"Erro na consulta: {e}")
            else:
                st.warning("Informe o Código para consultar.")

        if st.button("Alterar", use_container_width=True):
            if st.session_state.cargo_modo == 'consultando':
                st.session_state.cargo_modo = 'editando'
                st.rerun()
            else:
                st.warning("Consulte um cargo primeiro para poder alterar.")

        if st.button("Salvar", type="primary", use_container_width=True):
            if not codigo_input or not nome_input:
                st.error("Código e Nome são obrigatórios.")
            else:
                try:
                    with engine.begin() as conn:
                        if st.session_state.cargo_modo == 'novo':
                            query = text("""
                                INSERT INTO cadastro_cargos (codigo, nome, cbo) 
                                VALUES (:codigo, :nome, :cbo)
                            """)
                        elif st.session_state.cargo_modo == 'editando':
                            query = text("""
                                UPDATE cadastro_cargos 
                                SET nome = :nome, cbo = :cbo 
                                WHERE codigo = :codigo
                            """)

                        conn.execute(query, {
                            "codigo": codigo_input,
                            "nome": nome_input.upper(),
                            "cbo": cbo_input
                        })

                    st.success("Registro salvo com sucesso.")
                    limpar_formulario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        if st.button("Excluir", use_container_width=True):
            if st.session_state.cargo_modo in ['consultando', 'editando'] and codigo_input:
                try:
                    query = text("DELETE FROM cadastro_cargos WHERE codigo = :codigo")
                    with engine.begin() as conn:
                        conn.execute(query, {"codigo": codigo_input})
                    st.success("Registro excluído com sucesso.")
                    limpar_formulario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
            else:
                st.warning("Consulte um cargo primeiro para poder excluir.")

    st.markdown("---")
    st.subheader("Listagem Geral de Cargos")

    try:
        # A conversão ::integer na ordenação garante que o código 2 venha antes do 10
        query_lista = text("SELECT codigo AS \"Código\", nome AS \"Nome\", cbo AS \"C.B.O. 2002\" FROM cadastro_cargos ORDER BY codigo::integer")
        df_cargos = pd.read_sql(query_lista, con=engine)
        st.dataframe(df_cargos, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar a listagem. Certifique-se de que a tabela 'cadastro_cargos' existe. Detalhe: {e}")

    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
