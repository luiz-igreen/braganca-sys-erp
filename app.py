import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Dashboard Prêmios", layout="wide")

st.title("📊 Dashboard de Prêmios - CONSTRUART")

try:
    # Pega a string de conexão das Secrets
    DATABASE_URL = st.secrets["DATABASE_URL"]
    
    # Conecta ao banco
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Busca os dados da tabela
    cursor.execute("SELECT id, mes_ano, mes, ano, nome, pix, valor_pago_rs FROM public.pagamentos_premios ORDER BY ano DESC, mes DESC")
    dados = cursor.fetchall()
    
    # Pega os nomes das colunas
    colunas = ['ID', 'Mês/Ano', 'Mês', 'Ano', 'Nome', 'PIX', 'Valor (R$)']
    
    # Cria DataFrame
    df = pd.DataFrame(dados, columns=colunas)
    
    if len(df) > 0:
        st.success(f"✅ {len(df)} registros carregados!")
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total = df['Valor (R$)'].sum()
            st.metric("💰 Orçamento Consumido", f"R$ {total:,.2f}")
        
        with col2:
            quantidade = len(df)
            st.metric("📋 Quantidade de Lançamentos", quantidade)
        
        with col3:
            ticket_medio = df['Valor (R$)'].mean()
            st.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}")
        
        # Histórico mensal
        st.subheader("📈 Histórico Mensal")
        df_mensal = df.groupby('Mês/Ano')['Valor (R$)'].sum().reset_index()
        st.bar_chart(df_mensal.set_index('Mês/Ano'))
        
        # Tabela completa
        st.subheader("📋 Tabela Completa")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum registro encontrado na tabela!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    st.error(f"❌ Erro ao processar: {str(e)}")
    st.info("💡 Verifique se a DATABASE_URL nas Secrets está correta")
