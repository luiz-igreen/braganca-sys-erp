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

    # Função interna para limpar estritamente as chaves desta aba
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

    st.markdown("#### 🔄 Registrar Nova Movimentação")
    
    if df_colaboradores.empty:
        st.info("⚠️ Nenhum colaborador cadastrado na base central (Mãe Construart).")
    else:
        # --- MOTOR DE BUSCA RÁPIDA ---
        c1, c2 = st.columns([1, 2])
        busca_colab = c1.text_input("Busca Rápida (Matrícula ou Nome):", key="busca_transf_rápida", autocomplete="off")
        
        lista_completa_colab = [f"{r['codigo']} | {r['nome']}" for _, r in df_colaboradores.iterrows()]
        busca_atual = str(busca_colab).strip()
        ultima_busca = st.session_state.get('last_busca_transf_rapida', '')

        filtrados = []
        if busca_atual:
            for op in lista_completa_colab:
                parts = op.split(" | ", 1)
                if len(parts) == 2:
                    id_part, nome_part = parts
                    if busca_atual.lower() == id_part.strip().lower() or busca_atual.lower() in nome_part.lower():
                        filtrados.append(op)

        if busca_atual != ultima_busca:
            st.session_state['last_busca_transf_rapida'] = busca_atual
            if busca_atual and filtrados:
                st.session_state['sel_transf_final'] = filtrados[0]

        if busca_atual:
            if not filtrados:
                st.warning("⚠️ Colaborador não encontrado na base.")
                opcoes_colab = []
            else:
                opcoes_colab = filtrados
        else:
            opcoes_colab = lista_completa_colab
            
        if opcoes_colab:
            selecao_colab = c2.selectbox("Colaborador Selecionado:", opcoes_colab, key="sel_transf_final")
            st.markdown("---")
            
            # --- FORMULÁRIO DE TRANSFERÊNCIA ---
            id_colab = selecao_colab.split(" | ")[0]
            row_colab = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
            
            obra_atual = str(row_colab['obra']) if pd.notna(row_colab['obra']) and str(row_colab['obra']).strip() else "Não Alocado"
            
            with st.form("form_transferencia_inteligente", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                # Preenchimento automático e travado
                col1.text_input(
                    "Obra de Origem (De onde foi transferido):", 
                    value=obra_atual, 
                    disabled=True, 
                    autocomplete="off"
                )
                
                # Destino: Remove a obra atual da lista de opções
                opcoes_destino = [o for o in lista_todas_obras if o != obra_atual]
                if not opcoes_destino:
                    opcoes_destino = lista_todas_obras
                
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
                        limpar_estado(['busca_transf_rápida', 'last_busca_transf_rapida', 'sel_transf_final'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar a transferência: {e}")
                        
                if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                    limpar_estado(['busca_transf_rápida', 'last_busca_transf_rapida', 'sel_transf_final'])
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
    except Exception:
        st.error("Erro ao carregar o log de auditoria de transferências.")

    st.markdown("---")
    st.caption("🏗️ BRAGANÇA SYS | Módulo de Gestão Estrutural")
