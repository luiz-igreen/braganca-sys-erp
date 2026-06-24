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

    # Carrega dados essenciais
    try:
        df_colaboradores = get_cached_dataframe(engine, "SELECT codigo, nome, cpf, obra, cargo FROM public.cadastro_geral_colaborador ORDER BY nome")
    except Exception:
        df_colaboradores = pd.DataFrame()

    try:
        df_obras = get_cached_dataframe(engine, "SELECT nome FROM public.cadastro_obras ORDER BY nome")
        lista_todas_obras = df_obras['nome'].tolist() if not df_obras.empty else ["CONSTRUART"]
    except Exception:
        lista_todas_obras = ["CONSTRUART"]

    st.markdown("#### 🔍 Seleção do Colaborador para Transferência")
    
    if df_colaboradores.empty:
        st.info("⚠️ Nenhum colaborador cadastrado na base central (Mãe).")
    else:
        c1, c2 = st.columns([1, 2])
        busca_transf = c1.text_input("Busca Rápida (Matrícula ou Nome):", key="busca_transf", autocomplete="off")
        
        lista_completa_colab = [f"{r['codigo']} | {r['nome']}" for _, r in df_colaboradores.iterrows()]
        busca_atual_transf = str(busca_transf).strip()
        ultima_busca_transf = st.session_state.get('last_busca_transf', '')

        filtrados_transf = []
        if busca_atual_transf:
            for op in lista_completa_colab:
                parts = op.split(" | ", 1)
                if len(parts) == 2:
                    id_part, nome_part = parts
                    if busca_atual_transf.lower() == id_part.strip().lower() or busca_atual_transf.lower() in nome_part.lower():
                        filtrados_transf.append(op)

        if busca_atual_transf != ultima_busca_transf:
            st.session_state['last_busca_transf'] = busca_atual_transf
            if busca_atual_transf and filtrados_transf:
                st.session_state['sel_colab_transf'] = filtrados_transf[0]

        if busca_atual_transf:
            if not filtrados_transf:
                st.warning("⚠️ Colaborador não encontrado na base.")
                opcoes_colab = []
            else:
                opcoes_colab = filtrados_transf
        else:
            opcoes_colab = lista_completa_colab
            
        if opcoes_colab:
            selecao_colab = c2.selectbox("Colaborador Localizado:", opcoes_colab, key="sel_colab_transf")
            st.markdown("---")
            
            id_colab = selecao_colab.split(" | ")[0]
            row_colab = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
            
            obra_atual = str(row_colab['obra']) if pd.notna(row_colab['obra']) and str(row_colab['obra']).strip() else "Não Alocado"
            
            with st.form("form_transferencia", clear_on_submit=True):
                st.markdown("##### 📍 Status Atual")
                c_c1, c_c2 = st.columns([2, 1])
                c_c1.text_input("Obra / Lotação Atual", value=obra_atual, disabled=True)
                c_c2.text_input("Cargo", value=row_colab['cargo'], disabled=True)
                
                st.markdown("##### 🔄 Dados da Nova Movimentação")
                col_d, col_o = st.columns([1, 2])
                data_transf = col_d.date_input("Data Efetiva da Transferência", value=datetime.date.today())
                
                # Remove a obra atual da lista de opções de destino
                opcoes_destino = [o for o in lista_todas_obras if o != obra_atual]
                if not opcoes_destino:
                    opcoes_destino = ["Nenhuma outra obra disponível"]
                    
                obra_destino = col_o.selectbox("Nova Obra / Lotação de Destino:", options=opcoes_destino)
                
                observacoes = st.text_input("Motivo / Observações (Opcional):", autocomplete="off", key="obs_transf")
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Confirmar Transferência", type="primary", use_container_width=True):
                    if obra_destino == "Nenhuma outra obra disponível":
                        st.error("Não é possível transferir. Crie novas obras no cadastro geral.")
                    else:
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
                            # Executa ambas as operações numa única transação atómica
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
                            limpar_estado(['busca_transf', 'sel_colab_transf', 'last_busca_transf'])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao processar transferência: {e}")
                            
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_transf', 'sel_colab_transf', 'last_busca_transf'])
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
            st.info("Nenhuma transferência registada no sistema até o momento.")
    except Exception as e:
        st.error("Erro ao carregar o log de transferências.")

    st.markdown("---")
    st.caption("🏗️ BRAGANÇA SYS | Módulo de Gestão Estrutural")
