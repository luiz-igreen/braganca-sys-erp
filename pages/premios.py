import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    """
    Módulo Completo de Gestão de Prêmios (BRAGANÇA SYS ERP)

    Este módulo permite a gestão de prêmios, exibindo dados relevantes e funcionalidades
    para análise e controle.

    Args:
        engine: Objeto de conexão do SQLAlchemy para interagir com o banco de dados.
        *args: Argumentos posicionais adicionais.
        **kwargs: Argumentos de palavra-chave adicionais.
    """
    try:
        # Carregar os dados dos prêmios
        # Consulta SQL para buscar dados de prêmios, incluindo nome, descrição, valor e status
        query_premios = text("""
            SELECT
                p.id,
                p.nome,
                p.descricao,
                p.valor,
                CASE
                    WHEN p.situacao = 1 THEN 'Ativo'
                    WHEN p.situacao = 0 THEN 'Inativo'
                    ELSE 'Desconhecido'
                END as situacao_desc
            FROM
                premios p
            WHERE p.ativo = 1
        """)
        df_premios = pd.read_sql(query_premios, engine)

        # Adicionar coluna de ações com botão para editar
        df_premios['Ações'] = df_premios.apply(
            lambda row: st.button("Editar", key=f"editar_premio_{row['id']}", on_click=lambda id=row['id']: set_editing_premio(id)), axis=1
        )

        # Exibir os prêmios em uma tabela interativa
        st.title("Gerenciamento de Prêmios")
        st.dataframe(df_premios.set_index('id'), use_container_width=True)

        # Funcionalidade para adicionar um novo prêmio
        if st.button("Adicionar Novo Prêmio"):
            st.session_state['editing_premio'] = None  # Limpa o estado de edição para adicionar um novo
            st.session_state['show_modal_premio'] = True

        # Modal para adicionar/editar prêmio
        if st.session_state.get('show_modal_premio', False):
            show_modal_add_edit_premio(engine)

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os prêmios: {e}")

def set_editing_premio(premio_id):
    """
    Define o ID do prêmio a ser editado e exibe o modal de edição.
    """
    st.session_state['editing_premio'] = premio_id
    st.session_state['show_modal_premio'] = True

def show_modal_add_edit_premio(engine):
    """
    Exibe o modal para adicionar ou editar um prêmio.
    """
    premio_id = st.session_state.get('editing_premio')

    if premio_id:
        # Carregar dados do prêmio para edição
        query_detalhes = text("SELECT id, nome, descricao, valor, situacao FROM premios WHERE id = :id")
        df_detalhes = pd.read_sql(query_detalhes, engine, params={'id': premio_id})
        if not df_detalhes.empty:
            premio_data = df_detalhes.iloc[0]
            nome = st.text_input("Nome do Prêmio", value=premio_data['nome'], key=f"edit_nome_{premio_id}")
            descricao = st.text_area("Descrição", value=premio_data['descricao'], key=f"edit_descricao_{premio_id}")
            valor = st.number_input("Valor", value=float(premio_data['valor']) if pd.notnull(premio_data['valor']) else 0.0, key=f"edit_valor_{premio_id}")
            situacao = st.selectbox("Situação", options=[('Ativo', 1), ('Inativo', 0)], format_func=lambda x: x[0], index=[0, 1].index(premio_data['situacao']) if premio_data['situacao'] in [0, 1] else 0, key=f"edit_situacao_{premio_id}")[1] # Pega o valor numérico da tupla
            update_button_key = f"update_premio_{premio_id}"
            cancel_button_key = f"cancel_edit_premio_{premio_id}"
        else:
            st.warning("Prêmio não encontrado para edição.")
            return
    else:
        # Campos para adicionar um novo prêmio
        nome = st.text_input("Nome do Prêmio", key="add_nome")
        descricao = st.text_area("Descrição", key="add_descricao")
        valor = st.number_input("Valor", value=0.0, key="add_valor")
        situacao = st.selectbox("Situação", options=[('Ativo', 1), ('Inativo', 0)], format_func=lambda x: x[0], key="add_situacao")[1] # Pega o valor numérico da tupla
        update_button_key = "add_premio_save"
        cancel_button_key = "cancel_add_premio"

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Salvar", key=update_button_key):
            try:
                cursor = engine.cursor()
                if premio_id:
                    # Atualizar prêmio existente
                    query_update = text("""
                        UPDATE premios
                        SET nome = :nome, descricao = :descricao, valor = :valor, situacao = :situacao
                        WHERE id = :id
                    """)
                    cursor.execute(query_update, {'nome': nome, 'descricao': descricao, 'valor': valor, 'situacao': situacao, 'id': premio_id})
                    engine.commit()
                    st.success("Prêmio atualizado com sucesso!")
                else:
                    # Adicionar novo prêmio
                    query_insert = text("""
                        INSERT INTO premios (nome, descricao, valor, situacao, ativo)
                        VALUES (:nome, :descricao, :valor, :situacao, 1)
                    """)
                    cursor.execute(query_insert, {'nome': nome, 'descricao': descricao, 'valor': valor, 'situacao': situacao})
                    engine.commit()
                    st.success("Prêmio adicionado com sucesso!")

                # Limpar estado e recarregar a página
                st.session_state['show_modal_premio'] = False
                st.session_state['editing_premio'] = None
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Erro ao salvar o prêmio: {e}")
            finally:
                cursor.close()

    with col2:
        if st.button("Cancelar", key=cancel_button_key):
            st.session_state['show_modal_premio'] = False
            st.session_state['editing_premio'] = None
            st.experimental_rerun()
