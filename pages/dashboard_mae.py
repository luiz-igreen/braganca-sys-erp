import streamlit as st
import pandas as pd
from sqlalchemy import text

# Cache de alta performance
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_dataframe(_engine, query, params=None):
    if params:
        return pd.read_sql(text(query), _engine, params=params)
    return pd.read_sql(text(query), _engine)

def render(engine, *args, **kwargs):
    # ==========================================
    # PREVENÇÃO DE ERROS (AUTO-CORREÇÃO DO BANCO)
    # ==========================================
    # Garante que a coluna 'obra' existe na tabela para evitar erros estruturais.
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE public.cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS obra TEXT DEFAULT 'CONSTRUART';"))
    except Exception:
        pass # Ignora silenciosamente caso não tenha permissões, o erro seria tratado na query

    # ==========================================
    # PADRÃO VISUAL: DARK PREMIUM & GLASSMORPHISM
    # ==========================================
    st.markdown("""
    <style>
        .glass-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            color: #f8fafc;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #38bdf8;
            margin-top: 8px;
            line-height: 1;
        }
        .metric-label {
            font-size: 1rem;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("🏢 Dashboard da Matriz (Construart Mãe)")
    st.markdown("Visão global e gerencial de todo o efetivo registrado na base central da empresa.")
    st.markdown("---")

    # ==========================================
    # MOTOR DE DADOS: BUSCA GERAL (ORDENAÇÃO CORRIGIDA)
    # ==========================================
    # O comando regexp_replace limpa letras e o CAST converte para INTEIRO, 
    # garantindo que 2 venha antes de 10.
    query_all = """
        SELECT id as codigo, nome, cpf, cargo, obra, admissao 
        FROM public.cadastro_geral_colaborador 
        ORDER BY CAST(NULLIF(regexp_replace(id, '\D', '', 'g'), '') AS INTEGER) ASC
    """
    
    try:
        df_all = get_cached_dataframe(engine, query_all)
    except Exception as e:
        st.error(f"Erro ao buscar os dados: {e}")
        df_all = pd.DataFrame()

    if not df_all.empty:
        # ==========================================
        # CÁLCULO DE INDICADORES (KPIs)
        # ==========================================
        total_geral = len(df_all)
        total_mae = len(df_all[df_all['obra'] == 'CONSTRUART'])
        total_obras = total_geral - total_mae

        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="glass-card">
                <div class="metric-label">Total de Efetivos (Geral)</div>
                <div class="metric-value">{total_geral}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="glass-card">
                <div class="metric-label">Lotados na Construart (Sede)</div>
                <div class="metric-value">{total_mae}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="glass-card">
                <div class="metric-label">Alocados em Outras Obras</div>
                <div class="metric-value">{total_obras}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📋 Relação Completa de Colaboradores (Master Data)")

        # ==========================================
        # TRATAMENTO E EXIBIÇÃO DA TABELA
        # ==========================================
        df_display = df_all.rename(columns={
            'codigo': 'Matrícula',
            'nome': 'Nome Completo',
            'cpf': 'CPF',
            'cargo': 'Cargo Atual',
            'obra': 'Lotação (Obra Atual)',
            'admissao': 'Data de Admissão'
        })

        if 'Data de Admissão' in df_display.columns:
            df_display['Data de Admissão'] = pd.to_datetime(df_display['Data de Admissão'], errors='coerce').dt.strftime('%d/%m/%Y')
            df_display['Data de Admissão'] = df_display['Data de Admissão'].fillna('Não informada')

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Matrícula": st.column_config.TextColumn(width="small"),
                "Nome Completo": st.column_config.TextColumn(width="large"),
                "CPF": st.column_config.TextColumn(width="medium"),
                "Cargo Atual": st.column_config.TextColumn(width="medium"),
                "Lotação (Obra Atual)": st.column_config.TextColumn(width="medium"),
                "Data de Admissão": st.column_config.TextColumn(width="small")
            }
        )
    else:
        st.info("Nenhum colaborador encontrado na base de dados matriz.")

    st.markdown("---")
    st.caption("🏗️ BRAGANÇA SYS | Painel Gerencial de Recursos Humanos")
