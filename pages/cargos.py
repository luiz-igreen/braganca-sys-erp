import streamlit as st
import pandas as pd
from sqlalchemy import text

# Dicionário padrão de Cargos da Construção Civil e seus CBOs (Ministério do Trabalho)
CARGOS_CBO_MTE = {
    "ARMADOR DE ESTRUTURA DE CONCRETO": "7153-15",
    "APONTADOR DE OBRAS": "4122-05",
    "CARPINTEIRO": "7155-05",
    "ELETRICISTA DE INSTALAÇÕES": "7156-15",
    "ENCANADOR": "7110-05",
    "ENGENHEIRO CIVIL": "2142-05",
    "MESTRE DE OBRAS": "7102-05",
    "PEDREIRO": "7152-10",
    "PINTOR DE OBRAS": "7166-10",
    "SERVENTE DE OBRAS": "7170-20",
    "SOLDADOR": "7243-15",
    "TÉCNICO EM SEGURANÇA DO TRABALHO": "3516-05",
    "VIGIA": "5174-20"
}

def limpar_formulario():
    st.session_state.cargo_modo = 'novo'
    st.session_state.cargo_codigo = ""
    st.session_state.cargo_nome = list(CARGOS_CBO_MTE.keys())[0]
    st.session_state.cargo_cbo = CARGOS_CBO_MTE[list(CARGOS_CBO_MTE.keys())[0]]

def render(engine, *args, **kwargs):
    st.title("Gestão de Cargos e CBO")
    st.markdown("Cadastro e consulta de cargos padronizados (Restrito à lista oficial do MTE).")

    # Inicialização de variáveis de estado
    if 'cargo_modo' not in st.session_state:
        limpar_formulario()

    col_form, col_botoes = st.columns([3, 1])

    with col_form:
        st.subheader("Dados do Cargo")

        codigo_input = st.text_input(
            "Código:", 
            value=st.session_state.cargo_codigo, 
            disabled=(st.session_state.cargo_modo == 'editando')
        )

        # Se estiver consultando, mostra o valor salvo. Se for novo/editando, mostra a lista restrita.
        if st.session_state.cargo_modo == 'consultando':
            nome_input = st.text_input("Nome:", value=st.session_state.cargo_nome, disabled=True)
            cbo_input = st.text_input("C.B.O. 2002:", value=st.session_state.cargo_cbo, disabled=True)
        else:
            # Lista suspensa restrita aos cargos do dicionário
            opcoes_cargos = list(CARGOS_CBO_MTE.keys())

            # Tenta definir o index baseado no cargo atual, se existir na lista
            index_padrao = 0
            if st.session_state.cargo_nome in opcoes_cargos:
                index_padrao = opcoes_cargos.index(st.session_state.cargo_nome)

            nome_input = st.selectbox(
                "Nome (Selecione na lista oficial):", 
                options=opcoes_cargos,
                index=index_padrao
            )

            # Preenchimento automático do CBO baseado na seleção
            cbo_automatico = CARGOS_CBO_MTE.get(nome_input, "")
            cbo_input = st.text_input("C.B.O. 2002 (Automático):", value=cbo_automatico, disabled=True)

    with col_botoes:
        st.subheader("Ações")

        if st.button("Novo", use_container_width=True):
            limpar_formulario()
            st.rerun()

        if st.button("Consulta", use_container_width=True):
            if codigo_input:
                try:
                    query = text("SELECT codigo, nome, cbo FROM cadastro_cargos WHERE codigo = :codigo")
                    with engine.connect() as conn:
                        result = conn.execute(query, {"codigo": str(codigo_input)}).fetchone()

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
                            "codigo": str(codigo_input),
                            "nome": nome_input,
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
                        conn.execute(query, {"codigo": str(codigo_input)})
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
        query_lista = text("SELECT codigo AS \"Código\", nome AS \"Nome\", cbo AS \"C.B.O. 2002\" FROM cadastro_cargos ORDER BY codigo")
        df_cargos = pd.read_sql(query_lista, con=engine)
        st.dataframe(df_cargos, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar a listagem. Certifique-se de que a tabela 'cadastro_cargos' existe. Detalhe: {e}")

    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
