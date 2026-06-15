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
# Estas chaves serão usadas para controlar o valor dos text_inputs
if 'input_codigo_tab2_value' not in st.session_state:
    st.session_state.input_codigo_tab2_value = ""
if 'input_nome_tab2_value' not in st.session_state:
    st.session_state.input_nome_tab2_value = ""
if 'input_cbo_tab2_value' not in st.session_state:
    st.session_state.input_cbo_tab2_value = ""
# Nova chave para controlar a aba ativa - Usaremos o nome da aba diretamente
if 'active_tab_name' not in st.session_state:
    st.session_state.active_tab_name = "Consultar Cargos" # Aba inicial

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

# --- Funções Auxiliares para Limpar/Resetar o Estado ---
def reset_form_state():
    """Reseta o estado do formulário para um novo cadastro ou após uma operação."""
    st.session_state.edit_mode = False
    st.session_state.current_cargo = {}
    st.session_state.original_codigo = ""
    st.session_state.confirm_delete = False
    st.session_state.delete_codigo = ""
    st.session_state.input_codigo_tab2_value = ""
    st.session_state.input_nome_tab2_value = ""
    st.session_state.input_cbo_tab2_value = ""

# --- Layout do Dashboard de Cargos ---

st.title("Dashboard de Cadastro de Cargos")

# Abas para Consultar e Gerenciar
# Usamos o st.session_state.active_tab_name para controlar qual aba está selecionada
# O parâmetro 'key' é importante para que o Streamlit possa gerenciar o estado das abas
tab_names = ["Consultar Cargos", "Novo / Alterar Cargo"]
selected_tab_index = tab_names.index(st.session_state.active_tab_name) if st.session_state.active_tab_name in tab_names else 0

tab1, tab2 = st.tabs(tab_names, key="main_tabs", index=selected_tab_index)

# Lógica para renderizar o conteúdo da aba selecionada
if st.session_state.main_tabs == "Consultar Cargos": # Verifica o valor da key "main_tabs"
    with tab1: # Garante que o conteúdo esteja dentro da aba correta
        st.header("Consultar Cargos")
        df_cargos = get_all_cargos()

        if not df_cargos.empty:
            st.dataframe(df_cargos.set_index('codigo'), use_container_width=True)
        else:
            st.info("Nenhum cargo cadastrado ainda.")

elif st.session_state.main_tabs == "Novo / Alterar Cargo": # Verifica o valor da key "main_tabs"
    with tab2: # Garante que o conteúdo esteja dentro da aba correta
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
            if st.button("Consultar", key="btn_consultar_tab2"):
                codigo_para_consultar = st.session_state.input_codigo_tab2_value

                if codigo_para_consultar:
                    cargo_encontrado = get_cargo_by_codigo(codigo_para_consultar)
                    if cargo_encontrado is not None:
                        st.session_state.edit_mode = True
                        st.session_state.original_codigo = codigo_para_consultar
                        st.session_state.input_codigo_tab2_value = cargo_encontrado['codigo']
                        st.session_state.input_nome_tab2_value = cargo_encontrado['nome']
                        st.session_state.input_cbo_tab2_value = cargo_encontrado['cbo']
                        st.success(f"Cargo '{codigo_para_consultar}' encontrado. Preencha os campos para alterar.")
                        # Não precisamos mais forçar active_tab_name aqui, pois o st.tabs já está vinculado
                    else:
                        st.warning(f"Cargo com código '{codigo_para_consultar}' não encontrado.")
                        reset_form_state()
                else:
                    st.warning("Por favor, insira um Código para consultar.")

        with col_botoes[1]:
            if st.button("Novo", key="btn_novo_tab2"):
                reset_form_state()
                st.info("Pronto para cadastrar um novo cargo.")

        with col_botoes[2]:
            if st.button("Salvar", key="btn_salvar_tab2"):
                if not st.session_state.input_codigo_tab2_value or not st.session_state.input_nome_tab2_value:
                    st.error("Código e Nome do Cargo são obrigatórios.")
                else:
                    if st.session_state.get("edit_mode", False) and st.session_state.get("original_codigo"):
                        if update_cargo(st.session_state.original_codigo, st.session_state.input_codigo_tab2_value, st.session_state.input_nome_tab2_value, st.session_state.input_cbo_tab2_value):
                            st.success(f"Cargo '{st.session_state.input_codigo_tab2_value}' atualizado com sucesso!")
                            reset_form_state()
                        else:
                            st.error("Falha ao atualizar cargo.")
                    else:
                        if insert_cargo(st.session_state.input_codigo_tab2_value, st.session_state.input_nome_tab2_value, st.session_state.input_cbo_tab2_value):
                            st.success(f"Cargo '{st.session_state.input_codigo_tab2_value}' cadastrado com sucesso!")
                            reset_form_state()
                        else:
                            st.error("Falha ao cadastrar cargo. O código pode já existir.")

        with col_botoes[3]:
            if st.button("Excluir", key="btn_excluir_tab2"):
                if st.session_state.input_codigo_tab2_value:
                    if st.session_state.get("confirm_delete", False) and st.session_state.get("delete_codigo") == st.session_state.input_codigo_tab2_value:
                        if delete_cargo(st.session_state.input_codigo_tab2_value):
                            st.success(f"Cargo '{st.session_state.input_codigo_tab2_value}' excluído com sucesso!")
                            reset_form_state()
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
            if st.button("Cancelar", key="btn_cancelar_tab2"):
                reset_form_state()
                st.info("Operação cancelada.")
