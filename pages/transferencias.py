import streamlit as st
import pandas as pd
from sqlalchemy import text
import datetime

# Cache de queries
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_dataframe(_engine, query, params=None):
    if params:
        return pd.read_sql(text(query), _engine, params=params)
    return pd.read_sql(text(query), _engine)

def render(engine, *args, **kwargs):
    st.title("Gestão de Transferências e Alocações")
    st.markdown("Módulo central para movimentação de colaboradores entre obras.")

    # 1. Carrega todos os colaboradores
    try:
        df_colaboradores = get_cached_dataframe(engine, "SELECT codigo, nome, cpf, obra, cargo FROM public.cadastro_geral_colaborador ORDER BY nome")
        # Cria a lista formatada "Código | Nome"
        lista_colaboradores = [f"{row['codigo']} | {row['nome']}" for _, row in df_colaboradores.iterrows()]
    except Exception as e:
        st.error(f"Erro ao carregar colaboradores: {e}")
        df_colaboradores = pd.DataFrame()
        lista_colaboradores = []

    # 2. Carrega todas as obras
    try:
        df_obras = get_cached_dataframe(engine, "SELECT nome FROM public.cadastro_obras ORDER BY nome")
        lista_todas_obras = df_obras['nome'].tolist()
    except Exception as e:
        st.error(f"Erro ao carregar obras: {e}")
        lista_todas_obras = ["CONSTRUART"]

    st.markdown("#### 🔄 Registrar Nova Movimentação")
    
    if not lista_colaboradores:
        st.warning("⚠️ Não há colaboradores cadastrados na base.")
        return

    # O SEGREDO ESTÁ AQUI: Um selectbox simples nativo do Streamlit. 
    # O utilizador pode clicar e escrever nele que ele filtra sozinho!
    selecao_colab = st.selectbox(
        "Selecione o Colaborador para Transferência:",
        options=[""] + lista_colaboradores, # Adiciona opção vazia no início
        index=0
    )

    if selecao_colab != "":
        # Extrai o código do colaborador selecionado
        id_colab = selecao_colab.split(" | ")[0]
        row_colab = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
        
        # Obra atual
        obra_atual = str(row_colab['obra']) if pd.notna(row_colab['obra']) else "Não Alocado"
        
        with st.form("form_transferencia", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            # Campo bloqueado com a obra atual
            col1.text_input("Obra Atual (Origem):", value=obra_atual, disabled=True)
            
            # Lista de destino (remove a obra atual da lista)
            opcoes_destino = [o for o in lista_todas_obras if o != obra_atual]
            if not opcoes_destino:
                opcoes_destino = ["Sem outras obras disponíveis"]
                
            obra_destino = col2.selectbox("Nova Obra (Destino):", options=opcoes_destino)
            
            st.markdown("##### Detalhes da Transferência")
            c_data, c_obs = st.columns([1, 2])
            data_transf = c_data.date_input("Data da Transferência", value=datetime.date.today())
            observacoes = c_obs.text_input("Observações:", autocomplete="off")
            
            b1, b2 = st.columns(2)
            submit = b1.form_submit_button("💾 Gravar Transferência", type="primary", use_container_width=True)
            cancel = b2.form_submit_button("❌ Limpar Seleção", use_container_width=True)
            
            if submit:
                if obra_destino == "Sem outras obras disponíveis":
                    st.error("Não pode transferir. Crie mais obras no sistema.")
                else:
                    query_hist = """
                        INSERT INTO public.historico_transferencias (codigo_colaborador, obra_origem, obra_destino, data_transferencia, observacoes)
                        VALUES (:codigo, :origem, :destino, :data_transf, :obs)
                    """
                    query_upd = """
                        UPDATE public.cadastro_geral_colaborador
                        SET obra = :destino
                        WHERE codigo = :codigo
                    """
                    try:
                        with engine.begin() as conn:
                            conn.execute(text(query_hist), {
                                "codigo": id_colab, "origem": obra_atual, "destino": obra_destino, 
                                "data_transf": data_transf, "obs": observacoes
                            })
                            conn.execute(text(query_upd), {
                                "destino": obra_destino, "codigo": id_colab
                            })
                        st.success(f"Transferência concluída para {obra_destino}!")
                        get_cached_dataframe.clear() # Limpa o cache para atualizar a tabela
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro no banco de dados: {e}")
                        
            if cancel:
                st.rerun()

    st.markdown("---")
    st.markdown("#### 📜 Relatório de Movimentações Recentes")
    
    query_log = """
        SELECT 
            h.codigo_colaborador,
            c.nome,
            h.obra_origem,
            h.obra_destino,
            h.data_transferencia,
            h.observacoes
        FROM public.historico_transferencias h
        LEFT JOIN public.cadastro_geral_colaborador c ON h.codigo_colaborador = c.codigo
        ORDER BY h.data_registro DESC
        LIMIT 20
    """
    try:
        df_log = get_cached_dataframe(engine, query_log)
        if not df_log.empty:
            df_log = df_log.rename(columns={
                'codigo_colaborador': 'Matrícula',
                'nome': 'Colaborador',
                'obra_origem': 'Saiu de',
                'obra_destino': 'Foi para',
                'data_transferencia': 'Data',
                'observacoes': 'Motivo'
            })
            st.dataframe(df_log, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há transferências registadas.")
    except Exception as e:
        st.error(f"Erro ao carregar relatório: {e}")
