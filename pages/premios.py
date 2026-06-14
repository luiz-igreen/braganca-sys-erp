import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, parse_br_date_smart, format_cpf, LISTA_SITUACOES_ESOCIAL):
    """
    Módulo Completo de Gestão de Prêmios (BRAGANÇA SYS).
    Substituição integral para garantir a integridade da interface e evitar TypeError.
    """
    st.title("Gestão de Prêmios")
    st.markdown("Módulo para análise e administração de prêmios dos colaboradores da Construart.")

    # Filtros de busca
    col1, col2 = st.columns(2)
    busca_nome = col1.text_input("Buscar por Nome do Colaborador")
    busca_competencia = col2.text_input("Competência", value="01/2026", help="Ex: 01/2026")

    # Consulta SQL buscando todas as colunas da tabela premios_funcionarios
    query = "SELECT * FROM premios_funcionarios WHERE 1=1"

    if busca_nome:
        query += f" AND nome ILIKE '%%{busca_nome}%%'"
    if busca_competencia:
        query += f" AND competencia = '{busca_competencia}'"

    try:
        df_premios = pd.read_sql(query, con=engine)

        if not df_premios.empty:
            # Identifica colunas que contêm valores monetários para formatação
            colunas_monetarias = [col for col in df_premios.columns if 'valor' in col.lower() or 'premio' in col.lower()]

            # Aplica a taxa de R$ 1,00 ao valor do prêmio, se a coluna existir
            coluna_base = 'valor' if 'valor' in df_premios.columns else ('valor_premio' if 'valor_premio' in df_premios.columns else None)

            if coluna_base:
                df_premios[coluna_base] = pd.to_numeric(df_premios[coluna_base], errors='coerce').fillna(0)
                df_premios['valor_total_com_taxa'] = df_premios[coluna_base] + 1.00
                if 'valor_total_com_taxa' not in colunas_monetarias:
                    colunas_monetarias.append('valor_total_com_taxa')

            # Formatação monetária no padrão brasileiro (ex: 1.234,56)
            for col in colunas_monetarias:
                if col in df_premios.columns:
                    df_premios[col] = pd.to_numeric(df_premios[col], errors='coerce')
                    df_premios[col] = df_premios[col].apply(
                        lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else ""
                    )

            st.dataframe(
                df_premios,
                hide_index=True,
                use_container_width=True
            )
            st.caption(f"Mostrando {len(df_premios)} registros de prêmios na Construart.")
        else:
            st.info("Nenhum registro de prêmio encontrado para os filtros aplicados.")

    except Exception as e:
        st.error(f"Erro ao carregar a tabela premios_funcionarios: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
