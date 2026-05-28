import pandas as pd
import streamlit as st

# ... (restante do seu código)

if uploaded_file is not None:
    try:
        # 1. Ler o arquivo (XLS ou CSV)
        if uploaded_file.name.endswith('.csv'):
            # Pula as 4 primeiras linhas que são cabeçalho da empresa
            df = pd.read_csv(uploaded_file, skiprows=4)
        else:
            df = pd.read_excel(uploaded_file, skiprows=4)

        # Limpar espaços extras nos nomes das colunas
        df.columns = df.columns.str.strip()

        if 'Nome' in df.columns:
            st.success(f"Planilha reconhecida! {len(df)} linhas encontradas.")
            
            # 2. Mapeamento Inteligente
            df_import = pd.DataFrame()
            df_import['nome'] = df['Nome']
            df_import['cargo'] = df.get('Nome.1', 'Não Informado') # Na sua planilha o Cargo parece estar como Nome.1
            df_import['pix'] = df.get('PIX', '')
            
            # Tratamento de Salário
            if 'Demissão' in df.columns: # Na sua planilha o salário parece vir depois da demissão
                # Tenta pegar a coluna após 'Demissão' ou use o nome real se souber
                df_import['salario_base'] = 0 
            
            # Tratamento de Datas (Excel armazena datas como números às vezes)
            df_import['data_admissao'] = pd.to_datetime(df['Admissão'], errors='coerce').dt.date
            df_import['data_demissao'] = pd.to_datetime(df['Demissão'], errors='coerce').dt.date

            # 3. Botão de Confirmar
            if st.button("🚀 Confirmar Importação Oficial"):
                conn = st.connection("postgresql", type="sql")
                with conn.session as session:
                    session.execute("TRUNCATE TABLE public.pagamentos_premios;")
                    session.commit()
                
                df_import.to_sql('pagamentos_premios', conn.engine, if_exists='append', index=False)
                st.balloons()
                st.success("Dados importados com sucesso para o novo projeto!")
        else:
            st.error(f"Não achei a coluna 'Nome'. Colunas lidas: {list(df.columns)}")

    except Exception as e:
        st.error(f"Erro técnico: {e}")
