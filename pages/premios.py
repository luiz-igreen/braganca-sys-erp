import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    """
    Módulo Completo de Gestão de Prêmios (BRAGANÇA SYS).
    Solução Definitiva: Filtros transferidos para o Pandas para evitar UndefinedColumn no SQL.
    """
    st.title("Gestão de Prêmios")
    st.markdown("Módulo para análise e administração de prêmios dos colaboradores da Construart.")

    # Filtros de busca
    col1, col2 = st.columns(2)
    busca_nome = col1.text_input("Buscar por Nome do Colaborador")
    busca_competencia = col2.text_input("Competência", value="01/2026", help="Ex: 01/2026")

    # 1. Consulta SQL PURA (Sem WHERE dinâmico para evitar quebra no banco de dados)
    query = "SELECT * FROM premios_funcionarios"

    try:
        df_premios = pd.read_sql(query, con=engine)

        if not df_premios.empty:
            # 2. Padronização temporária de colunas para facilitar a busca dinâmica
            df_premios.columns = [str(c).lower().strip() for c in df_premios.columns]

            # 3. Filtro de Competência (em memória)
            if busca_competencia:
                col_comp = next((c for c in df_premios.columns if 'competencia' in c or 'mes' in c or 'mês' in c), None)
                if col_comp:
                    df_premios = df_premios[df_premios[col_comp].astype(str) == busca_competencia]

            # 4. Filtro de Nome (em memória - Blindado contra UndefinedColumn)
            if busca_nome:
                termos_nome = ['nome', 'colaborador', 'funcionario', 'empregado', 'profissional']
                col_nome = next((c for c in df_premios.columns if any(termo in c for termo in termos_nome)), None)

                if col_nome:
                    df_premios = df_premios[df_premios[col_nome].astype(str).str.contains(busca_nome, case=False, na=False)]
                else:
                    st.warning("Aviso: Coluna de identificação do colaborador não encontrada na tabela.")

            # 5. Processamento Financeiro (Taxa de R$ 1,00 e Formatação)
            colunas_monetarias = [col for col in df_premios.columns if 'valor' in col or 'premio' in col or 'prêmio' in col]
            coluna_base = next((c for c in df_premios.columns if c in ['valor', 'valor_premio', 'premio']), None)

            if coluna_base:
                df_premios[coluna_base] = pd.to_numeric(df_premios[coluna_base], errors='coerce').fillna(0)
                df_premios['valor_total_com_taxa'] = df_premios[coluna_base] + 1.00
                if 'valor_total_com_taxa' not in colunas_monetarias:
                    colunas_monetarias.append('valor_total_com_taxa')

            # Formatação padrão Domínio (ex: 1.234,56)
            for col in colunas_monetarias:
                if col in df_premios.columns:
                    df_premios[col] = pd.to_numeric(df_premios[col], errors='coerce')
                    df_premios[col] = df_premios[col].apply(
                        lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else ""
                    )

            # Capitaliza os nomes das colunas para exibição final no dashboard
            df_premios.columns = [str(c).title().replace('_', ' ') for c in df_premios.columns]

            st.dataframe(
                df_premios,
                hide_index=True,
                use_container_width=True
            )
            st.caption(f"Mostrando {len(df_premios)} registros de prêmios na Construart.")
        else:
            st.info("Nenhum registro de prêmio encontrado na base de dados.")

    except Exception as e:
        st.error(f"Erro crítico ao processar os dados: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
