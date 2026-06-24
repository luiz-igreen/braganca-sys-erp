import streamlit as st
import pandas as pd
from sqlalchemy import text
import datetime

# Cache de alta performance
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_dataframe(_engine, query, params=None):
    if params:
        return pd.read_sql(text(query), _engine, params=params)
    return pd.read_sql(text(query), _engine)

def render(engine, *args, **kwargs):
    # ==========================================
    # PADRÃO VISUAL: DARK PREMIUM & GLASSMORPHISM
    # ==========================================
    st.markdown("""
    <style>
        .glass-panel {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 20px;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔄 Gestão de Transferências")
    st.markdown("Módulo inteligente para movimentação de colaboradores entre canteiros de obras.")
    st.markdown("---")

    # 1. Carrega todas as obras para o filtro (busca nas obras cadastradas e nas já em uso)
    try:
        query_obras = """
            SELECT DISTINCT obra FROM public.cadastro_geral_colaborador 
            WHERE obra IS NOT NULL AND obra != ''
            UNION
            SELECT nome FROM public.cadastro_obras
            ORDER BY obra
        """
        df_obras = get_cached_dataframe(engine, query_obras)
        lista_obras = df_obras['obra'].tolist() if not df_obras.empty else ["CONSTRUART"]
    except Exception:
        lista_obras = ["CONSTRUART", "BRAGANÇA", "PÓVOA"] # Fallback de segurança

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown("#### 📍 1. Onde o colaborador está agora?")
    
    # FILTRO 1: Escolher a Obra de Origem
    obra_origem = st.selectbox(
        "Selecione a Obra de Origem para listar os funcionários:", 
        options=lista_obras,
        index=0
    )

    # 2. Carrega APENAS os colaboradores da obra selecionada
    query_colab = f"""
        SELECT id as codigo, nome, cpf, cargo 
        FROM public.cadastro_geral_colaborador 
        WHERE obra = '{obra_origem}' 
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

    st.markdown("</div>", unsafe_allow_html=True)

    if not lista_colaboradores:
        st.info(f"Nenhum colaborador lotado na obra **{obra_origem}** no momento.")
    else:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown("#### 👤 2. Quem vai ser transferido?")
        
        # FILTRO 2: Escolher o funcionário dentro daquela obra
        selecao_colab = st.selectbox(
            f"Colaboradores na obra {obra_origem}:",
            options=[""] + lista_colaboradores,
            index=0
        )

        if selecao_colab != "":
            id_colab = selecao_colab.split(" | ")[0]
            row_colab = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
            
            st.success(f"**Selecionado:** {row_colab['nome']} (Cargo: {row_colab['cargo']})")
            
            st.markdown("#### 🏗️ 3. Para onde ele vai?")
            
            # DESTINO (Remove a obra atual da lista de opções)
            opcoes_destino = [o for o in lista_obras if o != obra_origem]
            if not opcoes_destino:
                opcoes_destino = ["Nenhuma outra obra cadastrada"]
                
            col1, col2 = st.columns(2)
            obra_destino = col1.selectbox("Selecione a Nova Obra (Destino):", options=opcoes_destino)
            data_transf = col2.date_input("Data Efetiva da Transferência:", value=datetime.date.today())
            
            observacoes = st.text_input("Observações (Opcional):", autocomplete="off", placeholder="Motivo da transferência...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns([1, 1, 2])
            
            if b1.button("💾 Executar Transferência", type="primary", use_container_width=True):
                if obra_destino == "Nenhuma outra obra cadastrada":
                    st.error("Cadastre outras obras no sistema primeiro.")
                else:
                    query_hist = """
                        INSERT INTO public.historico_transferencias (codigo_colaborador, obra_origem, obra_destino, data_transferencia, observacoes)
                        VALUES (:codigo, :origem, :destino, :data_transf, :obs)
                    """
                    query_upd = """
                        UPDATE public.cadastro_geral_colaborador
                        SET obra = :destino
                        WHERE id = :codigo
                    """
                    try:
                        with engine.begin() as conn:
                            # 1. Grava no histórico
                            conn.execute(text(query_hist), {
                                "codigo": id_colab, "origem": obra_origem, "destino": obra_destino, 
                                "data_transf": data_transf, "obs": observacoes
                            })
                            # 2. Atualiza a tabela mãe (Atenção: usando 'id' em vez de 'codigo')
                            conn.execute(text(query_upd), {
                                "destino": obra_destino, "codigo": id_colab
                            })
                        st.toast(f"✅ Transferência realizada com sucesso!")
                        get_cached_dataframe.clear() # Limpa o cache para atualizar a tela na hora
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro no banco de dados: {e}")
                        
            if b2.button("❌ Cancelar", use_container_width=True):
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📜 Histórico de Movimentações (Auditoria)")
    
    query_log = """
        SELECT 
            h.codigo_colaborador as matricula,
            c.nome,
            h.obra_origem,
            h.obra_destino,
            h.data_transferencia,
            h.observacoes
        FROM public.historico_transferencias h
        LEFT JOIN public.cadastro_geral_colaborador c ON h.codigo_colaborador = c.id
        ORDER BY h.data_registro DESC
        LIMIT 20
    """
    try:
        df_log = get_cached_dataframe(engine, query_log)
        if not df_log.empty:
            df_log = df_log.rename(columns={
                'matricula': 'Matrícula',
                'nome': 'Colaborador',
                'obra_origem': 'Saiu de',
                'obra_destino': 'Foi para',
                'data_transferencia': 'Data',
                'observacoes': 'Motivo'
            })
            df_log['Data'] = pd.to_datetime(df_log['Data']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_log, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma transferência registrada no sistema até o momento.")
    except Exception as e:
        st.warning(f"O relatório de histórico está vazio ou houve um erro: {e}")
