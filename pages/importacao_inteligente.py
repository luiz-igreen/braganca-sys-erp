import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import text

def render(engine, *args, **kwargs):
    """
    Módulo de Importação Inteligente de Prêmios via CSV.
    Processa o arquivo em memória e insere no banco de dados via Streamlit.
    """
    st.title("Importação Inteligente de Prêmios")
    st.markdown("Faça o upload da planilha CSV. O sistema formatará os cabeçalhos, limpará os valores e fará a importação direta para o banco de dados.")

    # Configurações de Importação
    col1, col2 = st.columns(2)
    competencia = col1.text_input("Competência (Mês/Ano)", value="01/2026")
    tabela_destino = col2.selectbox("Tabela de Destino", ["gestao_premios_zaut", "premios_funcionarios"])

    # Upload do Arquivo
    arquivo_csv = st.file_uploader("Anexar arquivo CSV (Excel)", type=['csv'])

    if arquivo_csv:
        try:
            # 1. Leitura do Arquivo
            df = pd.read_csv(arquivo_csv, sep=None, engine='python')

            # 2. Limpeza de colunas vazias
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(axis=1, how='all')

            # 3. Mapeamento de Cabeçalhos (De -> Para)
            df.columns = df.columns.str.strip()
            mapeamento = {
                'Código': 'codigo_colaborador',
                'Nome': 'nome_colaborador',
                'Salário MÊS': 'salario_mes',
                'Salário HORA': 'salario_hora',
                'Total HP': 'total_hp',
                'VLR PREMIO R$': 'valor_premio',
                'Valor R$': 'valor_total',
                'DESCRIÇÃO PREMIO': 'descricao',
                'PIX': 'pix'
            }
            df = df.rename(columns=mapeamento)

            # 4. Injeção de Dados Faltantes
            df['competencia_id'] = competencia
            df['competencia'] = competencia
            df['cpf'] = None
            df['cargo'] = None

            # 5. Tratamento de Valores Monetários (Conversão para formato de Banco de Dados)
            colunas_financeiras = ['salario_mes', 'salario_hora', 'total_hp', 'valor_premio', 'valor_total']
            for col in colunas_financeiras:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('R\$', '', regex=True)
                    df[col] = df[col].str.replace('.', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    df[col] = df[col].str.strip()
                    df[col] = df[col].replace(['', '-', 'nan', 'None'], '0')
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            st.subheader("Pré-visualização dos Dados Formatados")
            st.dataframe(df.head(10), use_container_width=True)

            # 6. Importação para o Banco de Dados
            if st.button("Executar Importação para o Banco de Dados", type="primary"):
                with st.spinner("Sincronizando com o banco de dados..."):

                    # Identificar colunas existentes na tabela de destino para evitar erro de UndefinedColumn
                    query_cols = f"SELECT * FROM {tabela_destino} LIMIT 0"
                    df_db_schema = pd.read_sql(query_cols, con=engine)
                    colunas_banco = df_db_schema.columns.tolist()

                    # Filtrar o dataframe apenas com as colunas que realmente existem na tabela
                    colunas_validas = [col for col in df.columns if col in colunas_banco]
                    df_final = df[colunas_validas]

                    if df_final.empty:
                        st.error("Nenhuma coluna do CSV corresponde às colunas da tabela no banco de dados.")
                    else:
                        # Inserção via Pandas/SQLAlchemy
                        df_final.to_sql(tabela_destino, con=engine, if_exists='append', index=False)
                        st.success(f"Importação concluída! {len(df_final)} registros inseridos na tabela '{tabela_destino}'.")

        except Exception as e:
            st.error(f"Falha no processamento: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
