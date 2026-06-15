# pages/cargos.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- Inicialização do st.session_state ---
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'current_cargo' not in st.session_state:
    st.session_state.current_cargo = {}
if 'original_codigo' not in st.session_state:
    st.session_state.original_codigo = ""
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
if 'delete_codigo' not in st.session_state:
    st.session_state.delete_codigo = ""
if 'input_codigo_tab2_value' not in st.session_state:
    st.session_state.input_codigo_tab2_value = ""
if 'input_nome_tab2_value' not in st.session_state:
    st.session_state.input_nome_tab2_value = ""
if 'input_cbo_tab2_value' not in st.session_state:
    st.session_state.input_cbo_tab2_value = ""
# Nova chave para controlar a aba ativa
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Consultar Cargos" # Aba inicial

# --- Configuração do Banco de Dados (Supabase) ---
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

# --- Funções de Callback ---
def on_consultar_click():
    """Callback para o botão Consultar."""
    codigo_para_consultar = st.session_state.input_codigo_tab2_widget

    if codigo_para_consultar:
        cargo_encontrado = get_cargo_by_codigo(codigo_para_consultar)
        if cargo_encontrado is not None:
            st.session_state.edit_mode = True
            st.session_state.original_codigo = codigo_para_consultar
            st.session_state.input_codigo_tab2_value = cargo_encontrado['codigo']
            st.session_state.input_nome_tab2_value = cargo_encontrado['nome']
            st.session_state.input_cbo_tab2_value = cargo_encontrado['cbo']
            st.success(f"Cargo '{codigo_para_consultar}' encontrado. Preencha os campos para alterar.")
            st.session_state.active_tab = "Novo / Alterar Cargo" # Força a permanência na aba de edição
        else:
            st.warning(f"Cargo com código '{codigo_para_consultar}' não encontrado.")
            st.session_state.edit_mode = False
            st.session_state.current_cargo = {}
            st.session_state.original_codigo = ""
            st.session_state.input_codigo_tab2_value = ""
            st.session_state.input_nome_tab2_value = ""
            st.session_state.input_cbo_tab2_value = ""
            st.session_state.active_tab = "Novo / Alterar Cargo" # Permanece na aba de edição mesmo se não encontrar
    else:
        st.warning("Por favor, insira um Código para consultar.")
        st.session_state.active_tab = "Novo / Alterar Cargo" # Permanece na aba de edição

def on_novo_click():
    """Callback para o botão Novo."""
    st.session_state.edit_mode = False
    st.session_state.current_cargo = {}
    st.session_state.original_codigo = ""
    st.session_state.input_codigo_tab2_value = ""
    st.session_state.input_nome_tab2_value = ""
    st.session_state.input_cbo_tab2_value = ""
    st.info("Pronto para cadastrar um novo cargo.")
    st.session_state.active_tab = "Novo / Alterar Cargo" # Garante que a aba de edição esteja ativa

def on_cancelar_click():
    """Callback para o botão Cancelar."""
    st.session_state.edit_mode = False
    st.session_state.current_cargo = {}
    st.session_state.original_codigo = ""
    st.session_state.confirm_delete = False
    st.session_state.delete_codigo = ""
    st.session_state.input_codigo_tab2_value = ""
    st.session_state.input_nome_tab2_value = ""
    st.session_state.input_cbo_tab2_value = ""
    st.info("Operação cancelada.")
    st.session_state.active_tab = "Novo / Alterar Cargo" # Garante que a aba de edição esteja ativa

# --- Layout do Dashboard de Cargos ---

st.title("Dashboard de Cadastro de Cargos")

# Abas para Consultar e Gerenciar
# Usamos o st.session_state.active_tab para controlar qual aba está selecionada
selected_tab = st.tabs(["Consultar Cargos", "Novo / Alterar Cargo"], key="main_tabs", index=0 if st.session_state.active_tab == "Consultar Cargos" else 1)

# Renderiza o conteúdo da aba selecionada
if selected_tab[0] == "Consultar Cargos": # Conteúdo da primeira aba
    with st.container(): # Usa um container para garantir que o conteúdo esteja dentro da aba
        st.header("Consultar Cargos")
        df_cargos = get_all_cargos()

        if not df_cargos.empty:
            st.dataframe(df_cargos.set_index('codigo'), use_container_width=True)
        else:
            st.info("Nenhum cargo cadastrado ainda.")
elif selected_tab[0] == "Novo / Alterar Cargo": # Conteúdo da segunda aba
    with st.container(): # Usa um container para garantir que o conteúdo esteja dentro da aba
        st.header("Novo / Alterar Cargo")

        # Campos de entrada
        col_codigo, col_nome, col_cbo = st.columns([1, 2, 1])
        with col_codigo:
            input_codigo_widget = st.text_input(
                "Código do Cargo",
                value=st.session_state.input_codigo_tab2_value,
                key="input_codigo_tab2_widget",
                on_change=lambda: st.session_state.update(input_codigo_tab2_value=st.session_state.input_codigo_tab2_widget)
            )
        with col_nome:
            input_nome_widget = st.text_input(
                "Nome do Cargo",
                value=st.session_state.input_nome_tab2_value,
                key="input_nome_tab2_widget",
                on_change=lambda: st.session_state.update(input_nome_tab2_value=st.session_state.input_nome_tab2_widget)
            )
        with col_cbo:
            input_cbo_widget = st.text_input(
                "C.B.O. 2002",
                value=st.session_state.input_cbo_tab2_value,
                key="input_cbo_tab2_widget",
                on_change=lambda: st.session_state.update(input_cbo_tab2_value=st.session_state.input_cbo_tab2_widget)
            )

        # Botões de Ação
        col_botoes = st.columns(5)

        with col_botoes[0]:
            st.button("Consultar", key="btn_consultar_tab2", on_click=on_consultar_click)

        with col_botoes[1]:
            st.button("Novo", key="btn_novo_tab2", on_click=on_novo_click)

        with col_botoes[2]:
            if st.button("Salvar", key="btn_salvar_tab2"):
                if not st.session_state.input_codigo_tab2_value or not st.session_state.input_nome_tab2_value:
                    st.error("Código e Nome do Cargo são obrigatórios.")
                else:
                    if st.session_state.get("edit_mode", False) and st.session_state.get("original_codigo"):
                        if update_cargo(st.session_state.original_codigo, st.session_state.input_codigo_tab2_value, st.session_state.input_nome_tab2_value, st.session_state.input_cbo_tab2_value):
                            st.success(f"Cargo '{st.session_state.input_codigo_tab2_value}' atualizado com sucesso!")
                            on_cancelar_click()
                        else:
                            st.error("Falha ao atualizar cargo.")
                    else:
                        if insert_cargo(st.session_state.input_codigo_tab2_value, st.session_state.input_nome_tab2_value, st.session_state.input_cbo_tab2_value):
                            st.success(f"Cargo '{st.session_state.input_codigo_tab2_value}' cadastrado com sucesso!")
                            on_cancelar_click()
                        else:
                            st.error("Falha ao cadastrar cargo. O código pode já existir.")

        with col_botoes[3]:
            if st.button("Excluir", key="btn_excluir_tab2"):
                if st.session_state.input_codigo_tab2_value:
                    if st.session_state.get("confirm_delete", False) and st.session_state.get("delete_codigo") == st.session_state.input_codigo_tab2_value:
                        if delete_cargo(st.session_state.input_codigo_tab2_value):
                            st.success(f"Cargo '{st.session_state.input_codigo_tab2_value}' excluído com sucesso!")
                            on_cancelar_click()
                        else:
                            st.error("Falha ao excluir cargo. Verifique se há colaboradores associados a este cargo.")
                        st.session_state.confirm_delete = False
                        st.session_state.delete_codigo = ""
                    else:
                        st.warning(f"Tem certeza que deseja excluir o cargo '{st.session_state.input_codigo_tab2_value}'? Clique em Excluir novamente para confirmar.")
                        st.session_state.confirm_delete = True
                        st.session_state.delete_codigo = st.session_state.input_codigo_tab2_value
                else:
                    st.warning("Por favor, insira um Código para excluir.")

        with col_botoes[4]:
            st.button("Cancelar", key="btn_cancelar_tab2", on_click=on_cancelar_click)
