import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# Configuração da Página do Sistema
st.set_page_config(page_title="Gestão de Prémios - Construart", page_icon="🏆", layout="wide")

# Função de Conexão utilizando estritamente st.secrets["DATABASE_URL"]
def conectar_supabase():
    try:
        # O psycopg2 faz o parse automático da URL de conexão segura
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro crítico de conexão: {e}")
        return None

# Interface Principal do Painel
st.title("🏆 Painel Web de Gestão de Prémios — Obras Construart")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard de Custos", "🔍 Consultar Histórico", "➕ Lançar Novo Prémio", "⚙️ Alterar ou Excluir Lançamentos"])

# ==========================================
# SEPARADOR 1: DASHBOARD
# ==========================================
with tab1:
    st.subheader("Análise Financeira Operacional (Valores > R$ 0,00)")
    conn = conectar_supabase()
    if conn:
        try:
            query = "SELECT * FROM pagamentos_premios WHERE valor_pago_rs > 0"
            df_dash = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df_dash.empty:
                total_pago = df_dash['valor_pago_rs'].sum()
                total_lancamentos = len(df_dash)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Orçamento Total Consumido", f"R$ {total_pago:,.2f}")
                c2.metric("Total de Prémios Efetivados", total_lancamentos)
                c3.metric("Ticket Médio por Prémio", f"R$ {(total_pago/total_lancamentos):,.2f}")
                
                st.markdown("### Histórico de Desembolso por Mês")
                resumo_mensal = df_dash.groupby('mes_ano')['valor_pago_rs'].sum().reset_index()
                fig = px.line(resumo_mensal, x='mes_ano', y='valor_pago_rs', markers=True)
                fig.update_traces(line_color="#10b981", marker=dict(size=8, color="#059669"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum lançamento financeiro ativo encontrado.")
        except Exception as e:
            st.error(f"Erro ao processar Dashboard: {e}")

# ==========================================
# SEPARADOR 2: CONSULTAR
# ==========================================
with tab2:
    st.subheader("Filtro Geral de Colaboradores")
    nome_pesquisa = st.text_input("🔍 Procure por parte do nome:")
    conn = conectar_supabase()
    if conn:
        try:
            if nome_pesquisa:
                query = f"SELECT mes_ano as \"Mês/Ano\", nome as \"Nome\", pix as \"Chave PIX\", valor_pago_rs as \"Valor R$\" FROM pagamentos_premios WHERE nome ILIKE '%{nome_pesquisa}%' ORDER BY ano DESC"
            else:
                query = "SELECT mes_ano as \"Mês/Ano\", nome as \"Nome\", pix as \"Chave PIX\", valor_pago_rs as \"Valor R$\" FROM pagamentos_premios ORDER BY id DESC LIMIT 200"
            
            df_busca = pd.read_sql_query(query, conn)
            conn.close()
            st.dataframe(df_busca, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro na consulta: {e}")

# ==========================================
# SEPARADOR 3: INCLUIR NOVO
# ==========================================
with tab3:
    st.subheader("Registrar Lançamento Extra")
    with st.form("novo_registro_form"):
        colA, colB = st.columns(2)
        nome_input = colA.text_input("Nome Completo do Colaborador *")
        pix_input = colB.text_input("Chave PIX")
        
        colC, colD, colE = st.columns(3)
        mes_input = colC.selectbox("Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
        ano_input = colD.number_input("Ano", min_value=2024, max_value=2030, value=2026)
        valor_input = colE.number_input("Valor Líquido (R$) *", min_value=0.0, format="%.2f")
        
        btn_salvar = st.form_submit_button("💾 Salvar Registro")
        
        if btn_salvar and nome_input:
            conn = conectar_supabase()
            if conn:
                try:
                    cursor = conn.cursor()
                    mes_ano_str = f"{mes_input}/{ano_input}"
                    cursor.execute("""
                        INSERT INTO pagamentos_premios (mes_ano, mes, ano, nome, pix, valor_pago_rs)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (mes_ano_str, mes_input, ano_input, nome_input.upper().strip(), pix_input.strip(), valor_input))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"Registro de {nome_input.upper()} salvo com sucesso.")
                except Exception as e:
                    st.error(f"Falha ao salvar: {e}")

# ==========================================
# SEPARADOR 4: ALTERAR / EXCLUIR
# ==========================================
with tab4:
    st.subheader("Modificação de Registos")
    nome_alvo = st.text_input("Digite o nome exato para editar:")
    if nome_alvo:
        conn = conectar_supabase()
        if conn:
            try:
                query = f"SELECT id, mes_ano, pix, valor_pago_rs FROM pagamentos_premios WHERE nome = '{nome_alvo.upper().strip()}'"
                df_edicao = pd.read_sql_query(query, conn)
                conn.close()
                
                if not df_edicao.empty:
                    for idx, row in df_edicao.iterrows():
                        with st.expander(f"Registro: {row['mes_ano']}"):
                            with st.form(f"edit_{row['id']}"):
                                n_pix = st.text_input("Chave PIX", value=row['pix'])
                                n_val = st.number_input("Valor", value=float(row['valor_pago_rs']))
                                if st.form_submit_button("Confirmar Alteração"):
                                    c = conectar_supabase()
                                    cur = c.cursor()
                                    cur.execute("UPDATE pagamentos_premios SET pix=%s, valor_pago_rs=%s WHERE id=%s", (n_pix, n_val, row['id']))
                                    c.commit()
                                    c.close()
                                    st.success("Alterado.")
                else:
                    st.warning("Nome não encontrado.")
            except Exception as e:
                st.error(f"Erro: {e}")
