import streamlit as st
import pandas as pd
import numpy as np

def render(engine, *args, **kwargs):
    """
    Módulo de Importação Inteligente de Prêmios (BRAGANÇA SYS).
    Implementa as regras de negócio exatas da tabela gestao_premios_zaut.
    """
    st.title("Importação Inteligente de Prêmios")
    st.markdown("Faça o upload da planilha CSV. O sistema calculará automaticamente as conversões de HP e Prêmio Total.")

    col1, col2 = st.columns(2)
    competencia = col1.text_input("Competência (Mês/Ano)", value="01/2026")
    obra_padrao = col2.text_input("Obra Padrão", value="Construart")

    arquivo_csv = st.file_uploader("Selecione a planilha CSV", type=['csv'])

    if arquivo_csv is not None:
        try:
            # 1. Leitura bruta
            df_bruto = pd.read_csv(arquivo_csv, sep=None, engine='python', header=None)

            # 2. Localizar a linha real de cabeçalho
            header_idx = -1
            for i, row in df_bruto.iterrows():
                linha_texto = ' '.join([str(val).lower() for val in row.values])
                if 'nome' in linha_texto and ('código' in linha_texto or 'codigo' in linha_texto):
                    header_idx = i
                    break

            if header_idx == -1:
                st.error("Erro: Não foi possível encontrar a linha de cabeçalho contendo 'Código' e 'Nome'.")
                return

            # 3. Definir o cabeçalho correto
            df = df_bruto.iloc[header_idx + 1:].copy()
            df.columns = df_bruto.iloc[header_idx]
            df = df.reset_index(drop=True)

            # 4. Limpeza de colunas vazias
            df = df.loc[:, df.columns.notna()]
            df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed', case=False)]

            # 5. Mapeamento Dinâmico
            def mapear_coluna(col_name):
                nome_limpo = str(col_name).lower().strip()
                if 'código' in nome_limpo or 'codigo' in nome_limpo: return 'código'
                if 'nome' in nome_limpo: return 'nome'
                if 'salário mês' in nome_limpo or 'salario mes' in nome_limpo: return 'salario_mes'
                if 'salário hora' in nome_limpo or 'salario hora' in nome_limpo: return 'salario_hora'
                if 'total hp' in nome_limpo: return 'total_hp'
                if 'vlr premio' in nome_limpo or 'valor premio' in nome_limpo: return 'valor_hp_em_R$'
                if 'descrição' in nome_limpo or 'descricao' in nome_limpo: return 'lista_descricao_premio'
                if 'pix' in nome_limpo: return 'chave_pix'
                return None

            novas_colunas = {}
            for col in df.columns:
                novo_nome = mapear_coluna(col)
                if novo_nome:
                    novas_colunas[col] = novo_nome

            df = df.rename(columns=novas_colunas)
            colunas_validas = [col for col in df.columns if col in novas_colunas.values()]
            df = df[colunas_validas]

            # 6. Injeção de colunas estáticas
            df['competencia'] = competencia
            df['obra'] = obra_padrao
            df['cargo'] = ''
            df['cpf'] = ''
            df['taxa_de_manutencao_zaut'] = 1.00
            df['observacoes'] = ''

            # 7. Tratamento de Valores Monetários (Correção do SyntaxError com raw string r'R\$')
            colunas_financeiras = ['salario_mes', 'salario_hora', 'total_hp', 'valor_hp_em_R$']
            for col in colunas_financeiras:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'R\$', '', regex=True)
                    df[col] = df[col].str.replace('.', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    df[col] = df[col].str.strip()
                    df[col] = df[col].replace(['', '-', 'nan', 'None'], '0')
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                else:
                    df[col] = 0.0

            # 8. Regras de Negócio (Cálculos)
            df['total_hp_convertido'] = np.where(df['salario_hora'] > 0, df['valor_hp_em_R$'] / df['salario_hora'], 0.0)
            df['soma_total_hp'] = df['total_hp'] + df['total_hp_convertido']
            df['valor_total_premio_R$'] = (df['soma_total_hp'] * df['salario_hora']) + df['taxa_de_manutencao_zaut']

            # 9. Limpeza de registros inválidos
            if 'nome' in df.columns:
                df = df.dropna(subset=['nome'])
                df = df[df['nome'].astype(str).str.strip() != '']

            # 10. Ordenação para o banco de dados (ignorando 'ord' para auto-incremento do BD)
            colunas_finais = [
                'código', 'nome', 'cargo', 'cpf', 'obra', 'salario_mes', 'salario_hora', 
                'total_hp', 'total_hp_convertido', 'valor_hp_em_R$', 'soma_total_hp', 
                'valor_total_premio_R$', 'taxa_de_manutencao_zaut', 'lista_descricao_premio', 
                'chave_pix', 'observacoes', 'competencia'
            ]

            for col in colunas_finais:
                if col not in df.columns:
                    df[col] = None

            df_final = df[colunas_finais]

            st.write("Pré-visualização dos dados calculados:")
            st.dataframe(df_final.head(10), use_container_width=True)

            # 11. Execução da Importação
            if st.button("Executar Importação para o Banco de Dados", type="primary"):
                with st.spinner("Processando e inserindo dados..."):
                    df_final.to_sql('gestao_premios_zaut', con=engine, if_exists='append', index=False)
                    st.success(f"Importação realizada com sucesso! {len(df_final)} registros inseridos.")

        except Exception as e:
            st.error(f"Falha no processamento: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
