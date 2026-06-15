# pages/cargos.py
import streamlit as st
import pandas as pd
from sqlalchemy import text

# -------------------------------------------------
# Configurações iniciais
# -------------------------------------------------
st.set_page_config(page_title="Cadastro de Cargos", layout="wide")
st.title("📋 Cadastro de Cargos (CBO)")

# -------------------------------------------------
# Estado da aplicação (session_state)
# -------------------------------------------------
if "cargo_modo" not in st.session_state:
    # modos: visualizando, novo, consultando, editando
    st.session_state.cargo_modo = "visualizando"

if "cargo_selecionado" not in st.session_state:
    st.session_state.cargo_selecionado = None

# -------------------------------------------------
# Funções auxiliares
# -------------------------------------------------
def limpar_formulario():
    """Reseta os campos e volta ao modo visualização."""
    st.session_state.codigo_input = ""
    st.session_state.nome_input = ""
    st.session_state.cbo_input = ""
    st.session_state.cargo_modo = "visualizando"
    st.session_state.cargo_selecionado = None

def buscar_cargo(codigo: str):
    """Retorna o registro do cargo com o código informado ou None."""
    try:
        with engine.connect() as conn:
            query = text(
                "SELECT codigo, nome, cbo FROM cadastro_cargos WHERE codigo = :codigo"
            )
            df = pd.read_sql(query, conn, params={"codigo": codigo})
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        st.error(f"Erro ao buscar cargo: {e}")
        return None

# -------------------------------------------------
# Layout – abas
# -------------------------------------------------
tab_consultar, tab_novo = st.tabs(["Consultar Cargos", "Novo / Alterar Cargo"])

# -------------------------------------------------
# Aba 1 – Consultar / Excluir
# -------------------------------------------------
with tab_consultar:
    st.subheader("📄 Lista de Cargos Cadastrados")
    try:
        with engine.connect() as conn:
            df_cargos = pd.read_sql(
                text(
                    """
                    SELECT codigo AS "Código",
                           nome   AS "Nome",
                           cbo    AS "C.B.O. 2002"
                    FROM cadastro_cargos
                    ORDER BY codigo::integer
                    """
                ),
                conn,
            )
        st.dataframe(df_cargos, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar a listagem: {e}")

    st.markdown("---")
    st.subheader("Operações")

    # Campos de ação
    col_codigo, col_consultar = st.columns([2, 1])
    with col_codigo:
        codigo_input = st.text_input("Código do Cargo", key="codigo_input")
    with col_consultar:
        if st.button("Consultar", use_container_width=True):
            if codigo_input:
                cargo = buscar_cargo(codigo_input)
                if cargo is not None:
                    st.session_state.cargo_selecionado = cargo
                    st.session_state.cargo_modo = "consultando"
                    st.success("Cargo encontrado – preencha os campos abaixo para alterar ou excluir.")
                else:
                    st.warning("Código não encontrado.")
            else:
                st.warning("Informe o código para consultar.")

# -------------------------------------------------
# Aba 2 – Novo / Alterar
# -------------------------------------------------
with tab_novo:
    st.subheader("🛠️ Formulário de Cargo")
    # Preenche campos caso esteja em modo de edição/consulta
    if st.session_state.cargo_modo in ["consultando", "editando"]:
        cargo = st.session_state.cargo_selecionado
        codigo_default = cargo["codigo"]
        nome_default = cargo["nome"]
        cbo_default = cargo["cbo"]
    else:
        codigo_default = ""
        nome_default = ""
        cbo_default = ""

    with st.form("form_cargo", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            codigo_input = st.text_input("Código", value=codigo_default, key="form_codigo")
        with col2:
            nome_input = st.text_input("Nome", value=nome_default, key="form_nome")
        with col3:
            cbo_input = st.text_input("C.B.O. 2002", value=cbo_default, key="form_cbo")

        # Botões de ação
        col_novo, col_alterar, col_salvar, col_excluir, col_cancel = st.columns([1, 1, 1, 1, 1])

        with col_novo:
            if st.form_submit_button("Novo", type="secondary"):
                limpar_formulario()
                st.session_state.cargo_modo = "novo"
                st.rerun()

        with col_alterar:
            if st.session_state.cargo_modo == "consultando":
                if st.form_submit_button("Alterar", type="secondary"):
                    st.session_state.cargo_modo = "editando"
                    st.rerun()

        with col_salvar:
            if st.form_submit_button("Salvar", type="primary"):
                if not codigo_input or not nome_input:
                    st.error("Código e Nome são obrigatórios.")
                else:
                    try:
                        with engine.begin() as conn:
                            if st.session_state.cargo_modo == "novo":
                                query = text(
                                    """
                                    INSERT INTO cadastro_cargos (codigo, nome, cbo)
                                    VALUES (:codigo, :nome, :cbo)
                                    """
                                )
                            elif st.session_state.cargo_modo == "editando":
                                query = text(
                                    """
                                    UPDATE cadastro_cargos
                                    SET nome = :nome,
                                        cbo  = :cbo
                                    WHERE codigo = :codigo
                                    """
                                )
                            else:
                                st.warning("Selecione Novo ou Alterar antes de salvar.")
                                st.stop()

                            conn.execute(
                                query,
                                {
                                    "codigo": codigo_input,
                                    "nome": nome_input.upper(),
                                    "cbo": cbo_input,
                                },
                            )
                        st.success("Registro salvo com sucesso.")
                        limpar_formulario()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        with col_excluir:
            if st.form_submit_button("Excluir", type="secondary"):
                if st.session_state.cargo_modo in ["consultando", "editando"] and codigo_input:
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("DELETE FROM cadastro_cargos WHERE codigo = :codigo"),
                                {"codigo": codigo_input},
                            )
                        st.success("Registro excluído com sucesso.")
                        limpar_formulario()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                else:
                    st.warning("Consulte um cargo antes de excluir.")

        with col_cancel:
            if st.form_submit_button("Cancelar", type="secondary"):
                limpar_formulario()
                st.rerun()

# -------------------------------------------------
# Rodapé
# -------------------------------------------------
st.markdown("---")
st.caption("BRAGANÇA SYS – Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
