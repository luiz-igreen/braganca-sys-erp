import streamlit as st
import pandas as pd
from sqlalchemy import text
import datetime

# Motor de Cache de Alta Performance
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_dataframe(_engine, query, params=None):
    if params:
        return pd.read_sql(text(query), _engine, params=params)
    return pd.read_sql(text(query), _engine)

def render(engine, *args, **kwargs):
    st.title("Gestão de Transferências e Alocações")
    st.markdown("Módulo central para movimentação de colaboradores entre obras com registo de histórico para cálculo pró-rata.")

    # Função interna para limpar o estado das buscas e formulários
    def limpar_estado(chaves):
        get_cached_dataframe.clear()
        for chave in chaves:
            if chave in st.session_state:
                del st.session_state[chave]

    # 1. Carrega todos os colaboradores da base central (Mãe Construart)
    try:
        df_colaboradores = get_cached_dataframe(engine, "SELECT codigo, nome, cpf, obra, cargo FROM public.cadastro_geral_colaborador ORDER BY nome")
        lista_colaboradores = [f"{r['codigo']} | {r['nome']}" for _, r in df_colaboradores.iterrows()] if not df_colaboradores.empty else []
    except Exception:
        df_colaboradores = pd.DataFrame()
        lista_colaboradores = []

    # Carrega todas as obras cadastradas no sistema
    try:
        df_obras = get_cached_dataframe(engine, "SELECT nome FROM public.cadastro_obras ORDER BY nome")
        lista_todas_obras = df_obras['nome'].tolist() if not df_obras.empty else ["CONSTRUART"]
    except Exception:
        lista_todas_obras = ["CONSTRUART"]

    st.markdown("#### 🔄 Registrar Nova Movimentação")
    
    if not lista_colaboradores:
        st.info("⚠️ Nenhum colaborador cadastrado na base central (Mãe Construart).")
    else:
        # Campo 1: Lista completa de todos os colaboradores para busca imediata
        selecao_colab = st.selectbox(
            "Selecione o Colaborador (Listagem Geral Mãe):", 
            options=lista_colaboradores, 
            index=None, 
            placeholder="Digite o código ou nome para pesquisar...",
            key="busca_colab_transf"
        )
        st.markdown("---")
        
        if selecao_colab:
            id_colab = selecao_colab.split(" | ")[0]
            row_colab = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
            
            # Captura a obra onde ele se encontra alocado atualmente
            obra_atual = str(row_colab['obra']) if pd.notna(row_colab['obra']) and str(row_colab['obra']).strip() else "Não Alocado"
            
            with st.form("form_transferencia_inteligente", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                # Campo 2: Preenchido automaticamente com a lotação atual do funcionário
                col1.text_input(
                    "Obra de Origem (De onde foi transferido):", 
                    value=obra_atual, 
                    disabled=True, 
                    autocomplete="off"
                )
                
                # Remove apenas a obra atual para evitar transferências redundantes para o mesmo lugar
                opcoes_destino = [o for o in lista_todas_obras if o != obra_atual]
                if not opcoes_destino:
                    opcoes_destino = lista_todas_obras
                
                # Campo 3: Lista completa das obras do sistema para seleção do destino
                obra_destino = col2.selectbox(
                    "Obra de Destino (Para onde vai ser transferido):", 
                    options=opcoes_destino
                )
                
                st.markdown("##### Detalhes Contábeis da Operação")
                col_d, col_o = st.columns([1, 2])
                data_transf = col_d.date_input("Data Efetiva da Transferência", value=datetime.date.today())
                observacoes = col_o.text_input("Motivo / Observações:", autocomplete="off", key="obs_movimentacao")
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Confirmar Transferência", type="primary", use_container_width=True):
                    query_insert_hist = """
                        INSERT INTO public.historico_transferencias (codigo_colaborador, obra_origem, obra_destino, data_transferencia, observacoes)
                        VALUES (:codigo, :origem, :destino, :data_transf, :obs)
                    """
                    query_update_mae = """
                        UPDATE public.cadastro_geral_colaborador
                        SET obra = :destino
                        WHERE codigo = :codigo
                    """
                    try:
                        # Execução atómica unificada para manter a integridade dos dados
                        with engine.begin() as conn:
                            conn.execute(text(query_insert_hist), {
                                "codigo": id_colab, 
                                "origem": obra_atual, 
                                "destino": obra_destino, 
                                "data_transf": data_transf, 
                                "obs": observacoes
                            })
                            conn.execute(text(query_update_mae), {
                                "destino": obra_destino, 
                                "codigo": id_colab
                            })
                            
                        st.toast(f"✅ {row_colab['nome']} transferido para {obra_destino} com sucesso!")
                        limpar_estado(['busca_colab_transf'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar a transferência no banco de dados: {e}")
                        
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_colab_transf'])
                    st.rerun()

    st.markdown("---")
    st.markdown("#### 📜 Relatório de Movimentações Recentes")
    
    query_log = """
        SELECT 
            h.id,
            h.codigo_colaborador,
            c.nome,
            h.obra_origem,
            h.obra_destino,
            h.data_transferencia,
            h.observacoes
        FROM public.historico_transferencias h
        LEFT JOIN public.cadastro_geral_colaborador c ON h.codigo_colaborador = c.codigo
        ORDER BY h.data_registro DESC
        LIMIT 50
    """
    try:
        df_log = get_cached_dataframe(engine, query_log)
        if not df_log.empty:
            df_display = df_log.rename(columns={
                'codigo_colaborador': 'Matrícula',
                'nome': 'Nome do Colaborador',
                'obra_origem': 'Saiu de',
                'obra_destino': 'Foi para',
                'data_transferencia': 'Data Efetiva',
                'observacoes': 'Motivo/Obs'
            })
            
            st.dataframe(
                df_display[['Matrícula', 'Nome do Colaborador', 'Saiu de', 'Foi para', 'Data Efetiva', 'Motivo/Obs']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Matrícula": st.column_config.TextColumn(width="small"),
                    "Nome do Colaborador": st.column_config.TextColumn(width="medium"),
                    "Saiu de": st.column_config.TextColumn(width="medium"),
                    "Foi para": st.column_config.TextColumn(width="medium"),
                    "Data Efetiva": st.column_config.DateColumn(width="small", format="DD/MM/YYYY"),
                    "Motivo/Obs": st.column_config.TextColumn(width="large")
                }
            )
        else:
            st.info("Nenhuma transferência registrada no sistema até o momento.")
    except Exception:
        st.error("Erro ao carregar o log de auditoria de transferências.")

    st.markdown("---")
    st.caption("🏗️ BRAGANÇA SYS | Módulo de Gestão Estrutural")
