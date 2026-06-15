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
    # modos possíveis: "visualizando", "novo", "consultando", "editando"
    st.session_state.cargo_modo = "visualizando"

if "cargo_selecionado" not in st.session_state:
    st.session_state.cargo_selecionado = None

# -------------------------------------------------
# Funções auxiliares
# -------------------------------------------------
def limpar_formulario():
    """Reseta os campos do formulário e volta ao modo visualização."""
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
                           cbo    AS "C.B.O. 2002"
                    FROM cadastro_cargos
                    ORDER BY codigo::integer
                    """
                ),
                conn,
            )
        if df_cargos.empty:
            st.info("Nenhum cargo cadastrado ainda.")
        else:
            st.dataframe(df_cargos, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar a listagem de cargos: {e}")

    st.markdown("---")
    st.subheader("🔎 Consultar / Excluir um Cargo")

    col1, col2 = st.columns([2, 1])
    with col1:
        codigo_consulta = st.text_input(
            "Código do Cargo", placeholder="Informe o código para consulta"
        )
    with col2:
        if st.button("Consultar"):
            if codigo_consulta:
                cargo = buscar_cargo(codigo_consulta)
                if cargo is not None:
                    st.session_state.cargo_modo = "consultando"
                    st.session_state.cargo_selecionado = cargo
                    st.success("Cargo encontrado – agora você pode Alterar ou Excluir.")
                else:
                    st.warning("Cargo não encontrado.")
            else:
                st.warning("Informe um código para consultar.")

    if st.session_state.cargo_modo in ["consultando", "editando"]:
        cargo = st.session_state.cargo_selecionado
        st.info(
            f"**Código:** {cargo['codigo']}  |  **Nome:** {cargo['nome']}  |  **C.B.O.:** {cargo['cbo']}"
        )
        col_del, col_blank = st.columns([1, 1])
        with col_del:
            if st.button("Excluir", type="primary"):
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("DELETE FROM cadastro_cargos WHERE codigo = :codigo"),
                            {"codigo": cargo["codigo"]},
                        )
                    st.success("Cargo excluído com sucesso.")
                    limpar_formulario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir o cargo: {e}")

# -------------------------------------------------
# Aba 2 – Novo / Alterar
# -------------------------------------------------
with tab_novo:
    st.subheader("🆕 Novo Cargo / ✏️ Alterar Cargo")

    # Formulário (mantém valores entre reruns)
    with st.form("form_cargo", clear_on_submit=False):
        col_codigo, col_nome, col_cbo = st.columns([1, 2, 2])

        codigo_input = col_codigo.text_input(
            "Código",
            value=st.session_state.get("codigo_input", ""),
            key="codigo_input",
            disabled=st.session_state.cargo_modo == "editando",
        )
        nome_input = col_nome.text_input(
            "Nome do Cargo",
            value=st.session_state.get("nome_input", ""),
            key="nome_input",
        )
        cbo_input = col_cbo.text_input(
            "C.B.O. 2002",
            value=st.session_state.get("cbo_input", ""),
            key="cbo_input",
        )

        # Botões de ação
        col_novo, col_alterar, col_salvar, col_cancel = st.columns([1, 1, 1, 1])

        with col_novo:
            if st.form_submit_button("Novo", type="secondary"):
                limpar_formulario()
                st.session_state.cargo_modo = "novo"
                st.rerun()

        with col_alterar:
            if st.session_state.cargo_modo == "consultando":
                if st.form_submit_button("Alterar", type="secondary"):
                    # Carrega os dados do cargo selecionado no formulário
                    cargo = st.session_state.cargo_selecionado
                    st.session_state.codigo_input = cargo["codigo"]
                    st.session_state.nome_input = cargo["nome"]
                    st.session_state.cbo_input = cargo["cbo"]
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
                                st.warning("Nenhum modo de operação definido.")
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
                        st.error(f"Erro ao salvar o cargo: {e}")

        with col_cancel:
            if st.form_submit_button("Cancelar", type="secondary"):
                limpar_formulario()
                st.rerun()

# -------------------------------------------------
# Rodapé
# -------------------------------------------------
st.markdown("---")
st.caption(
    "BRAGANÇA SYS – Infraestrutura de Dados | Conexão: Supabase PostgreSQL"
)
