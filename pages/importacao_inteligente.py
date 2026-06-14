import streamlit as st
import pandas as pd
import numpy as np

def render(engine, *args, **kwargs):
    """
    Módulo de Importação Inteligente de Prêmios (BRAGANÇA SYS).
    Lê o CSV bruto, padroniza cabeçalhos, limpa valores financeiros e insere no banco.
    """
    st.title("Importação Inteligente de Prêmios")
    st.markdown("Faça o upload da planilha CSV bruta. O sistema formatará os dados automaticamente para o padrão do banco de dados.")

    arquivo_csv = st.file_uploader("Selecione a planilha CSV", type=['csv'])

    if arquivo_csv is not None:
        try:
            # 1. Leitura do arquivo CSV
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

            # 4. Injeção de colunas obrigatórias
            # A coluna no banco de dados deve se chamar 'competencia' e ser do tipo 'text'
            df['competencia'] = '01/2026'
            df['cpf'] = np.nan
            df['cargo'] = np.nan

            # 5. Tratamento rigoroso de Valores Monetários
            colunas_financeiras = ['salario_mes', 'salario_hora', 'total_hp', 'valor_premio', 'valor_total']
            for col in colunas_financeiras:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('R\$', '', regex=True)
                    df[col] = df[col].str.replace('.', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    df[col] = df[col].str.strip()
                    df[col] = df[col].replace(['', '-', 'nan', 'None'], '0')
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            st.write("Pré-visualização dos dados formatados e prontos para inserção:")
            st.dataframe(df.head(10), use_container_width=True)

            # 6. Botão de Execução
            if st.button("Executar Importação para o Banco de Dados", type="primary"):
                with st.spinner("Processando e inserindo dados..."):
                    # Insere os dados formatados diretamente na tabela gestao_premios_zaut
                    df.to_sql('gestao_premios_zaut', con=engine, if_exists='append', index=False)
                    st.success("Importação realizada com sucesso! Os dados já estão no banco de dados.")

        except Exception as e:
            st.error(f"Falha no processamento: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
