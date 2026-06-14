import streamlit as st
import pandas as pd
import numpy as np

def render(engine, *args, **kwargs):
    """
    Módulo de Importação Inteligente de Prêmios (BRAGANÇA SYS).
    Lê o CSV bruto, localiza o cabeçalho real, padroniza para a tabela gestao_premios_zaut e insere no banco.
    """
    st.title("Importação Inteligente de Prêmios")
    st.markdown("Faça o upload da planilha CSV. O sistema localizará os dados, formatará os cabeçalhos para o padrão da tabela **gestao_premios_zaut** e fará a inserção.")

    col1, col2 = st.columns(2)
    competencia = col1.text_input("Competência (Mês/Ano)", value="01/2026")
    obra_padrao = col2.text_input("Obra Padrão", value="Construart")

    arquivo_csv = st.file_uploader("Selecione a planilha CSV", type=['csv'])

    if arquivo_csv is not None:
        try:
            # 1. Leitura bruta sem assumir a primeira linha como cabeçalho
            df_bruto = pd.read_csv(arquivo_csv, sep=None, engine='python', header=None)

            # 2. Localizar a linha real de cabeçalho (que contém 'Nome' e 'Código')
            header_idx = -1
            for i, row in df_bruto.iterrows():
                linha_texto = ' '.join(row.astype(str).str.lower())
                if 'nome' in linha_texto and ('código' in linha_texto or 'codigo' in linha_texto):
                    header_idx = i
                    break

            if header_idx == -1:
                st.error("Erro: Não foi possível encontrar a linha de cabeçalho contendo 'Código' e 'Nome' no arquivo CSV.")
                return

            # 3. Definir o cabeçalho correto e descartar as linhas "sujas" do topo
            df = df_bruto.iloc[header_idx + 1:].copy()
            df.columns = df_bruto.iloc[header_idx]
            df = df.reset_index(drop=True)

            # 4. Limpeza de colunas vazias (Unnamed)
            df = df.loc[:, df.columns.notna()]
            df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed', case=False)]

            # 5. Mapeamento Dinâmico para a estrutura da tabela gestao_premios_zaut
            def mapear_coluna(col_name):
                nome_limpo = str(col_name).lower().strip()
                if 'código' in nome_limpo or 'codigo' in nome_limpo: return 'codigo_colaborador'
                if 'nome' in nome_limpo: return 'nome_colaborador'
                if 'salário mês' in nome_limpo or 'salario mes' in nome_limpo: return 'salario_mes'
                if 'salário hora' in nome_limpo or 'salario hora' in nome_limpo: return 'salario_hora'
                if 'total hp' in nome_limpo: return 'total_hp'
                if 'vlr premio' in nome_limpo or 'valor premio' in nome_limpo: return 'valor_hp_em_R$'
                if 'valor r$' in nome_limpo or 'valor total' in nome_limpo: return 'valor_total_premio_R$'
                if 'descrição' in nome_limpo or 'descricao' in nome_limpo: return 'lista_descricao_premio'
                if 'pix' in nome_limpo: return 'chave_pix'
                return None

            novas_colunas = {}
            for col in df.columns:
                novo_nome = mapear_coluna(col)
                if novo_nome:
                    novas_colunas[col] = novo_nome

            # Renomeia as colunas encontradas e descarta as que não interessam
            df = df.rename(columns=novas_colunas)
            colunas_validas = [col for col in df.columns if col in novas_colunas.values()]
            df = df[colunas_validas]

            # 6. Injeção de colunas obrigatórias da tabela gestao_premios_zaut
            df['competencia_id'] = competencia
            df['obra'] = obra_padrao
            df['cargo'] = ''
            df['cpf'] = ''
            df['total_hp_convertido'] = 0.0
            df['soma_total_hp'] = 0.0
            df['taxa_de_manutencao_zaut'] = 1.00
            df['observacoes'] = ''

            # 7. Tratamento rigoroso de Valores Monetários
            colunas_financeiras = ['salario_mes', 'salario_hora', 'total_hp', 'valor_hp_em_R$', 'valor_total_premio_R$']
            for col in colunas_financeiras:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('R\$', '', regex=True)
                    df[col] = df[col].str.replace('.', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    df[col] = df[col].str.strip()
                    df[col] = df[col].replace(['', '-', 'nan', 'None'], '0')
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Remove linhas onde o nome do colaborador está vazio
            df = df.dropna(subset=['nome_colaborador'])
            df = df[df['nome_colaborador'].str.strip() != '']

            st.write("Pré-visualização dos dados mapeados para a tabela `gestao_premios_zaut`:")
            st.dataframe(df.head(10), use_container_width=True)

            # 8. Botão de Execução
            if st.button("Executar Importação para o Banco de Dados", type="primary"):
                with st.spinner("Processando e inserindo dados..."):
                    # Insere os dados formatados diretamente na tabela
                    df.to_sql('gestao_premios_zaut', con=engine, if_exists='append', index=False)
                    st.success(f"Importação realizada com sucesso! {len(df)} registros inseridos na tabela gestao_premios_zaut.")

        except Exception as e:
            st.error(f"Falha no processamento: {e}")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
