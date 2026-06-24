import streamlit as st
import pandas as pd
from sqlalchemy import text
import datetime

# Cache de alta performance para não sobrecarregar o banco
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_dataframe(_engine, query, params=None):
    if params:
        return pd.read_sql(text(query), _engine, params=params)
    return pd.read_sql(text(query), _engine)

def render(engine, *args, **kwargs):
    st.title("Gestão de Transferências e Alocações")
    st.markdown("Módulo central para movimentar os colaboradores da Construart (Mãe) para as outras obras.")

    # 1. Carrega APENAS os colaboradores que estão na CONSTRUART (A Mãe)
    query_colab = """
        SELECT codigo, nome, cpf, obra, cargo 
        FROM public.cadastro_geral_colaborador 
        WHERE obra = 'CONSTRUART' 
        ORDER BY nome
    """
    try:
        df_colaboradores = get_cached_dataframe(engine, query_colab)
        if not df_colaboradores.empty:
            lista_colaboradores = [f"{row['codigo']} | {row['nome']}" for _, row in df_colaboradores.iterrows()]
        else:
            lista_colaboradores = []
    except Exception as e:
        st.error(f"Erro ao carregar colaboradores: {e}")
        df_colaboradores = pd.DataFrame()
        lista_colaboradores = []

    # 2. Carrega TODAS as obras cadastradas no sistema
    try:
        df_obras = get_cached_dataframe(engine, "SELECT nome FROM public.cadastro_obras ORDER BY nome")
        lista_todas_obras = df_obras['nome'].tolist() if not df_obras.empty else []
    except Exception as e:
        st.error(f"Erro ao carregar obras: {e}")
        lista_todas_obras = []

    st.markdown("#### 🔄 Registrar Nova Movimentação da Matriz")
    
    if not lista_colaboradores:
        st.info("⚠️ Não existem colaboradores atualmente alocados na CONSTRUART (Mãe).")
    else:
        # A LISTA APARECE AQUI! Sem rodeios.
        selecao_colab = st.selectbox(
            "1. Selecione o Colaborador (Listagem da Matriz Construart):",
            options=[""] + lista_colaboradores,
            index=0
        )

        st.markdown("---")

        if selecao_colab != "":
            id_colab = selecao_colab.split(" | ")[0]
            row_colab = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
            
            obra_atual = str(row_colab['obra']) if pd.notna(row_colab['obra']) else "CONSTRUART"
            
            st.markdown(f"**Colaborador Selecionado:** {row_colab['nome']} (Cargo: {row_colab['cargo']})")
            
            col1, col2 = st.columns(2)
            
            # ORIGEM
            col1.text_input("Obra de Origem (Atual):", value=obra_atual, disabled=True)
            
            # DESTINO (Remove a obra atual da lista para não transferir para o mesmo lugar)
            opcoes_destino = [o for o in lista_todas_obras if o != obra_atual]
            if not opcoes_destino:
                opcoes_destino = ["Nenhuma outra obra cadastrada"]
                
            obra_destino = col2.selectbox("2. Obra de Destino (Para onde vai?):", options=opcoes_destino)
            
            c_data, c_obs = st.columns([1, 2])
            data_transf = c_data.date_input("3. Data da Transferência:", value=datetime.date.today())
            observacoes = c_obs.text_input("4. Observações (Opcional):", autocomplete="off")
            
            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns([1, 1, 2])
            
            if b1.button("💾 Confirmar", type="primary", use_container_width=True):
                if obra_destino == "Nenhuma outra obra cadastrada":
                    st.error("Não é possível transferir. Tem de cadastrar as obras primeiro.")
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
                        st.success(f"✅ Transferência de {row_colab['nome']} para {obra_destino} realizada com sucesso!")
                        get_cached_dataframe.clear()
                        # Pequeno truque para forçar a tela a limpar e voltar ao início
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro no banco de dados: {e}")
                        
            if b2.button("❌ Cancelar", use_container_width=True):
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
            # Aplica formatação de datas
            df_log['Data'] = pd.to_datetime(df_log['Data']).dt.strftime('%d/%m/%Y')
            
            st.dataframe(df_log, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há transferências registadas.")
    except Exception as e:
        st.error(f"Erro ao carregar relatório: {e}")
