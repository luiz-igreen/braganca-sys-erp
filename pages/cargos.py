# pages/cargos.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- Configuração do Banco de Dados (Supabase) ---
# É crucial que DATABASE_URL esteja configurada nas variáveis de ambiente
# ou em um arquivo de configuração seguro.
# Para o Streamlit Cloud, você pode usar os "Secrets".
try:
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        st.error("DATABASE_URL não configurada. Verifique as variáveis de ambiente ou Streamlit Secrets.")
        st.stop()
    engine = create_engine(DATABASE_URL)
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")
    st.stop()

# --- Funções de CRUD para Cargos ---

def get_all_cargos():
    """Retorna todos os cargos da tabela cadastro_cargos."""
    try:
        with engine.connect() as connection:
            query = text("SELECT codigo, nome, cbo FROM cadastro_cargos ORDER BY codigo")
            df = pd.read_sql(query, connection)
            return df
    except Exception as e:
        st.error(f"Erro ao buscar cargos: {e}")
        return pd.DataFrame()

def get_cargo_by_codigo(codigo):
    """Retorna um cargo específico pelo código."""
    try:
        with engine.connect() as connection:
            query = text("SELECT codigo, nome, cbo FROM cadastro_cargos WHERE codigo = :codigo")
            df = pd.read_sql(query, connection, params={"codigo": codigo})
            if not df.empty:
                return df.iloc[0]
            return None
    except Exception as e:
        st.error(f"Erro ao buscar cargo por código: {e}")
        return None

def insert_cargo(codigo, nome, cbo):
    """Insere um novo cargo na tabela cadastro_cargos."""
    try:
        with engine.connect() as connection:
            query = text("INSERT INTO cadastro_cargos (codigo, nome, cbo) VALUES (:codigo, :nome, :cbo)")
            connection.execute(query, {"codigo": codigo, "nome": nome, "cbo": cbo})
            connection.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir cargo: {e}")
        return False

def update_cargo(codigo_original, novo_codigo, novo_nome, novo_cbo):
    """Atualiza um cargo existente na tabela cadastro_cargos."""
    try:
        with engine.connect() as connection:
            query = text("UPDATE cadastro_cargos SET codigo = :novo_codigo, nome = :novo_nome, cbo = :novo_cbo WHERE codigo = :codigo_original")
            connection.execute(query, {
                "novo_codigo": novo_codigo,
                "novo_nome": novo_nome,
                "novo_cbo": novo_cbo,
                "codigo_original": codigo_original
            })
            connection.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar cargo: {e}")
        return False

def delete_cargo(codigo):
    """Exclui um cargo da tabela cadastro_cargos."""
    try:
        with engine.connect() as connection:
            query = text("DELETE FROM cadastro_cargos WHERE codigo = :codigo")
            connection.execute(query, {"codigo": codigo})
            connection.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir cargo: {e}")
        return False

# --- Layout do Dashboard de Cargos ---

st.title("Dashboard de Cadastro de Cargos")

# Abas para Consultar e Gerenciar
tab1, tab2 = st.tabs(["Consultar Cargos", "Novo / Alterar Cargo"])

with tab1:
    st.header("Consultar Cargos")
    df_cargos = get_all_cargos()

    if not df_cargos.empty:
        st.dataframe(df_cargos.set_index('codigo'), use_container_width=True)
    else:
        st.info("Nenhum cargo cadastrado ainda.")

with tab2:
    st.header("Novo / Alterar Cargo")

    # Campos de entrada
    col_codigo, col_nome, col_cbo = st.columns([1, 2, 1])
    with col_codigo:
        input_codigo = st.text_input("Código do Cargo", key="input_codigo_tab2")
    with col_nome:
        input_nome = st.text_input("Nome do Cargo", key="input_nome_tab2")
    with col_cbo:
        input_cbo = st.text_input("C.B.O. 2002", key="input_cbo_tab2")

    # Botões de Ação
    col_botoes = st.columns(5) # 5 colunas para os botões

    with col_botoes[0]:
        if st.button("Consultar", key="btn_consultar_tab2"):
            if input_codigo:
                cargo_encontrado = get_cargo_by_codigo(input_codigo)
                if cargo_encontrado is not None:
                    st.session_state.current_cargo = cargo_encontrado.to_dict()
                    st.session_state.edit_mode = True
                    st.session_state.original_codigo = input_codigo # Guarda o código original para atualização
                    st.success(f"Cargo '{input_codigo}' encontrado. Preencha os campos para alterar.")
                    # Atualiza os inputs para refletir o cargo encontrado
                    st.session_state.input_codigo_tab2 = cargo_encontrado['codigo']
                    st.session_state.input_nome_tab2 = cargo_encontrado['nome']
                    st.session_state.input_cbo_tab2 = cargo_encontrado['cbo']
                else:
                    st.warning(f"Cargo com código '{input_codigo}' não encontrado.")
                    st.session_state.edit_mode = False
                    st.session_state.current_cargo = {}
                    st.session_state.original_codigo = ""
            else:
                st.warning("Por favor, insira um Código para consultar.")

    with col_botoes[1]:
        if st.button("Novo", key="btn_novo_tab2"):
            st.session_state.edit_mode = False
            st.session_state.current_cargo = {}
            st.session_state.original_codigo = ""
            # Limpa os inputs
            st.session_state.input_codigo_tab2 = ""
            st.session_state.input_nome_tab2 = ""
            st.session_state.input_cbo_tab2 = ""
            st.info("Pronto para cadastrar um novo cargo.")

    with col_botoes[2]:
        if st.button("Salvar", key="btn_salvar_tab2"):
            # Validação de campos obrigatórios
            if not input_codigo or not input_nome:
                st.error("Código e Nome do Cargo são obrigatórios.")
            else:
                if st.session_state.get("edit_mode", False) and st.session_state.get("original_codigo"):
                    # Modo de Edição
                    if update_cargo(st.session_state.original_codigo, input_codigo, input_nome, input_cbo):
                        st.success(f"Cargo '{input_codigo}' atualizado com sucesso!")
                        st.session_state.edit_mode = False
                        st.session_state.current_cargo = {}
                        st.session_state.original_codigo = ""
                        # Limpa os inputs
                        st.session_state.input_codigo_tab2 = ""
                        st.session_state.input_nome_tab2 = ""
                        st.session_state.input_cbo_tab2 = ""
                    else:
                        st.error("Falha ao atualizar cargo.")
                else:
                    # Modo de Inserção
                    if insert_cargo(input_codigo, input_nome, input_cbo):
                        st.success(f"Cargo '{input_codigo}' cadastrado com sucesso!")
                        # Limpa os inputs
                        st.session_state.input_codigo_tab2 = ""
                        st.session_state.input_nome_tab2 = ""
                        st.session_state.input_cbo_tab2 = ""
                    else:
                        st.error("Falha ao cadastrar cargo. O código pode já existir.")

    with col_botoes[3]:
        if st.button("Excluir", key="btn_excluir_tab2"):
            if input_codigo:
                # Confirmação de exclusão
                if st.session_state.get("confirm_delete", False) and st.session_state.get("delete_codigo") == input_codigo:
                    if delete_cargo(input_codigo):
                        st.success(f"Cargo '{input_codigo}' excluído com sucesso!")
                        st.session_state.edit_mode = False
                        st.session_state.current_cargo = {}
                        st.session_state.original_codigo = ""
                        st.session_state.confirm_delete = False # Reseta a confirmação
                        st.session_state.delete_codigo = ""
                        # Limpa os inputs
                        st.session_state.input_codigo_tab2 = ""
                        st.session_state.input_nome_tab2 = ""
                        st.session_state.input_cbo_tab2 = ""
                    else:
                        st.error("Falha ao excluir cargo.")
                else:
                    st.warning(f"Tem certeza que deseja excluir o cargo '{input_codigo}'? Clique em Excluir novamente para confirmar.")
                    st.session_state.confirm_delete = True
                    st.session_state.delete_codigo = input_codigo
            else:
                st.warning("Por favor, insira um Código para excluir.")

    with col_botoes[4]:
        if st.button("Cancelar", key="btn_cancelar_tab2"):
            st.session_state.edit_mode = False
            st.session_state.current_cargo = {}
            st.session_state.original_codigo = ""
            st.session_state.confirm_delete = False
            st.session_state.delete_codigo = ""
            # Limpa os inputs
            st.session_state.input_codigo_tab2 = ""
            st.session_state.input_nome_tab2 = ""
            st.session_state.input_cbo_tab2 = ""
            st.info("Operação cancelada.")

    # Lógica para pré-preencher campos se estiver em modo de edição
    if st.session_state.get("edit_mode", False) and st.session_state.get("current_cargo"):
        # Garante que os inputs são atualizados apenas uma vez para evitar loops
        if st.session_state.input_codigo_tab2 != st.session_state.current_cargo.get('codigo', ''):
            st.session_state.input_codigo_tab2 = st.session_state.current_cargo.get('codigo', '')
        if st.session_state.input_nome_tab2 != st.session_state.current_cargo.get('nome', ''):
            st.session_state.input_nome_tab2 = st.session_state.current_cargo.get('nome', '')
        if st.session_state.input_cbo_tab2 != st.session_state.current_cargo.get('cbo', ''):
            st.session_state.input_cbo_tab2 = st.session_state.current_cargo.get('cbo', '')
