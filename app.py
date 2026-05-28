import pandas as pd
import streamlit as st

# ... (restante do seu código de conexão)

if uploaded_file is not None:
    # 1. Ler o arquivo (suporta XLS ou CSV conforme o seu upload)
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("Planilha carregada com sucesso!")

        # 2. Mapeamento das colunas da planilha para o Banco de Dados
        # Ajustado conforme o arquivo Empregados-Bragança
        df_import = pd.DataFrame()
        
        # Mapeia as colunas (ajuste os nomes entre aspas se mudarem no Excel)
        df_import['nome'] = df['Nome']
        df_import['cargo'] = df.get('Cargo', 'Não Informado')
        df_import['pix'] = df.get('PIX', '')  # Se não houver PIX, fica vazio
        
        # Tratamento de Salário (remove pontos e vírgulas se necessário)
        if 'Salário' in df.columns:
            df_import['salario_base'] = pd.to_numeric(df['Salário'], errors='coerce')
        
        # Tratamento de Datas
        if 'Data Adm.' in df.columns:
            df_import['data_admissao'] = pd.to_datetime(df['Data Adm.'], errors='coerce').dt.date
        
        if 'Data Dem.' in df.columns:
            df_import['data_demissao'] = pd.to_datetime(df['Data Dem.'], errors='coerce').dt.date

        # 3. Botão para Confirmar Importação no Supabase
        if st.button("Confirmar Importação para o Banco de Dados"):
            try:
                # Conecta usando a sua DATABASE_URL das Secrets
                conn = st.connection("postgresql", type="sql")
                
                # Limpa a tabela antes de inserir os novos dados oficiais
                with conn.session as session:
                    session.execute("TRUNCATE TABLE public.pagamentos_premios;")
                    session.commit()

                # Insere os dados
                df_import.to_sql('pagamentos_premios', conn.engine, if_exists='append', index=False)
                st.balloons()
                st.success(f"Tudo pronto! {len(df_import)} colaboradores importados com sucesso.")
            except Exception as e:
                st.error(f"Erro ao salvar no banco: {e}")

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
