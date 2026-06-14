import streamlit as st
import pandas as pd
import numpy as np

def render(engine, *args, **kwargs):
    """
    Módulo de Importação Inteligente de Prêmios (BRAGANÇA SYS).
    Localiza cabeçalhos dinamicamente, aplica regras de negócio (cálculos de HP) e insere no banco.
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

            # 2. Localizar a linha real de cabeçalho com conversão segura de tipos (Correção do erro float/str)
            header_idx = -1
            for i, row in df_bruto.iterrows():
                linha_texto = ' '.join([str(val).lower() for val in row.values])
                if 'nome' in linha_texto and ('código' in linha_texto or 'codigo' in linha_texto):
                    header_idx = i
                    break

            if header_idx == -1:
                st.error("Erro: Não foi possível encontrar a linha de cabeçalho contendo 'Código' e 'Nome' no arquivo CSV.")
                return

            # 3. Definir o cabeçalho correto e descartar as linhas superiores
            df = df_bruto.iloc[header_idx + 1:].copy()
            df.columns = df_bruto.iloc[header_idx]
            df = df.reset_index(drop=True)

            # 4. Limpeza de colunas vazias
            df = df.loc[:, df.columns.notna()]
            df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed', case=False)]

            # 5. Mapeamento Dinâmico para a estrutura exata do Gestao_de_PremioZaut.txt
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

            # 6. Injeção de colunas estáticas e obrigatórias
            df['competencia'] = competencia
            df['obra'] = obra_padrao
            df['cargo'] = ''
            df['cpf'] = ''
            df['taxa_de_manutencao_zaut'] = 1.00
            df['observacoes'] = ''

            # 7. Tratamento rigoroso de Valores Monetários base
            colunas_financeiras = ['salario_mes', 'salario_hora', 'total_hp', 'valor_hp_em_R$']
            for col in colunas_financeiras:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('R\$', '', regex=True)
                    df[col] = df[col].str.replace('.', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    df[col] = df[col].str.strip()
                    df[col] = df[col].replace(['', '-', 'nan', 'None'], '0

