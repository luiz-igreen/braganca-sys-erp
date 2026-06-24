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
    st.markdown("Módulo para transferir colaboradores. **Busca Universal** em toda a base de dados.")
    st.markdown("---")

    # 1. Carrega TODOS os colaboradores do sistema, não importa a obra
    query_colab = """
        SELECT id as codigo, nome, cpf, cargo, obra 
        FROM public.cadastro_geral_colaborador 
        ORDER BY NULLIF(regexp_replace(id, '\D', '', 'g'), '')::numeric ASC
    """
    try:
        df_colaboradores = get_cached_dataframe(engine, query_colab)
        if not df_colaboradores.empty:
            lista_colaboradores = [f"{row['codigo']} | {row['nome']}" for _, row in df_colaboradores.iterrows()]
        else:
            lista_colaboradores = []
    except Exception as e:
        # Fallback se a ordenação numérica falhar
        try:
             query_fallback = "SELECT id as codigo, nome, cpf, cargo, obra FROM public.cadastro_geral_colaborador ORDER BY id ASC"
             df_colaboradores = get_cached_dataframe(engine, query_fallback)
             lista_colaboradores = [f"{row['codigo']} | {row['nome']}" for _, row in df_colaboradores.iterrows()] if not df_colaboradores.empty else []
        except Exception as e2:
             st.error(f"Erro crítico ao ler banco: {e2}")
             df_colaboradores = pd.DataFrame()
             lista_colaboradores = []

    # 2. Carrega as Obras (apenas para o destino)
    try:
        query_obras = """
            SELECT DISTINCT obra FROM public.cadastro_geral_colaborador WHERE obra IS NOT NULL AND obra != ''
            UNION SELECT nome FROM public.cadastro_obras
            ORDER BY obra
        """
        df_obras = get_cached_dataframe(engine, query_obras)
        lista_obras = df_obras['obra'].tolist() if not df_obras.empty else ["CONSTRUART", "BRAGANÇA", "PÓVOA"]
    except Exception:
        lista_obras = ["CONSTRUART", "BRAGANÇA", "PÓVOA"]

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    
    if not lista_colaboradores:
        st.warning("⚠️ Nenhum colaborador cadastrado no sistema inteiro.")
    else:
        st.markdown("#### 👤 1. Quem vai ser transferido?")
        
        # BUSCA UNIVERSAL: O utilizador pode digitar o nome aqui
        selecao_colab = st.selectbox(
            "Pesquise o colaborador por Matrícula ou Nome:",
            options=[""] + lista_colaboradores,
            index=0
        )

        if selecao_colab != "":
            id_colab = selecao_colab.split(" | ")[0]
            row_colab = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
            
            # Descobre onde ele está lotado agora
            obra_atual = str(row_colab['obra']).strip() if pd.notna(row_colab['obra']) else "Sem Lotação"
            
            st.success(f"**Selecionado:** {row_colab['nome']} | **Cargo:** {row_colab['cargo']} | **Lotação Atual:** {obra_atual}")
            
            st.markdown("#### 🏗️ 2. Para onde ele vai?")
            
            # DESTINO (Remove a obra atual da lista de opções)
            opcoes_destino = [o for o in lista_obras if o != obra_atual]
            if not opcoes_destino:
                opcoes_destino = ["Nenhuma outra obra disponível"]
                
            col1, col2 = st.columns(2)
            obra_destino = col1.selectbox("Selecione a Nova Obra (Destino):", options=opcoes_destino)
            data_transf = col2.date_input("Data da Transferência:", value=datetime.date.today())
            
            observacoes = st.text_input("Motivo / Observações:", autocomplete="off")
            
            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns([1, 1, 2])
            
            if b1.button("💾 Executar Transferência", type="primary", use_container_width=True):
                if obra_destino == "Nenhuma outra obra disponível":
                    st.error("Não é possível transferir. Crie outras obras no sistema.")
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
                            conn.execute(text(query_hist), {
                                "codigo": id_colab, "origem": obra_atual, "destino": obra_destino, 
                                "data_transf": data_transf, "obs": observacoes
                            })
                            conn.execute(text(query_upd), {
                                "destino": obra_destino, "codigo": id_colab
                            })
                        st.toast(f"✅ {row_colab['nome']} transferido(a) com sucesso!")
                        get_cached_dataframe.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
                        
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
                'obra_origem': 'Origem',
                'obra_destino': 'Destino',
                'data_transferencia': 'Data',
                'observacoes': 'Obs'
            })
            df_log['Data'] = pd.to_datetime(df_log['Data']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_log, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma transferência registada.")
    except Exception as e:
        pass
