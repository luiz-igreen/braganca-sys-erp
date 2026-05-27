import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# Configuração da Página do Sistema
st.set_page_config(page_title="Gestão de Prémios - Construart", page_icon="🏆", layout="wide")

# URL de Conexão com o Supabase (Substitua [YOUR-PASSWORD] pela sua senha real)
URL_BANCO = "postgresql://postgres:[YOUR-PASSWORD]@db.iiiuyqlpnwshwxpmfdar.supabase.co:5432/postgres"

def conectar_supabase():
    return psycopg2.connect(URL_BANCO)

# Interface Principal do Painel
st.title("🏆 Painel Web de Gestão de Prémios — Obras Construart")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard de Custos", "🔍 Consultar Histórico", "➕ Lançar Novo Prémio", "⚙️ Alterar ou Excluir Lançamentos"])

# ==========================================
# SEPARADOR 1: DASHBOARD
# ==========================================
with tab1:
    st.subheader("Análise Financeira Operacional (Valores > R$ 0,00)")
    try:
        conn = conectar_supabase()
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
            st.info("Nenhum lançamento financeiro ativo encontrado para gerar os gráficos.")
    except Exception as e:
        st.error(f"Erro ao conectar ao Dashboard: {e}")

# ==========================================
# SEPARADOR 2: CONSULTAR
# ==========================================
with tab2:
    st.subheader("Filtro Geral de Colaboradores")
    nome_pesquisa = st.text_input("🔍 Procure por parte do nome do colaborador (Obra ou Escritório):")
    
    try:
        conn = conectar_supabase()
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
        pix_input = colB.text_input("Chave PIX para Pagamento")
        
        colC, colD, colE = st.columns(3)
        mes_input = colC.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
        ano_input = colD.number_input("Ano de Referência", min_value=2024, max_value=2030, value=2026)
        valor_input = colE.number_input("Valor Líquido do Prémio (R$) *", min_value=0.0, format="%.2f")
        
        btn_salvar = st.form_submit_button("💾 Salvar Registro na Nuvem")
        
        if btn_salvar:
            if nome_input:
                try:
                    conn = conectar_supabase()
                    cursor = conn.cursor()
                    mes_ano_str = f"{mes_input}/{ano_input}"
                    cursor.execute("""
                        INSERT INTO pagamentos_premios (mes_ano, mes, ano, nome, pix, valor_pago_rs)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (mes_ano_str, mes_input, ano_input, nome_input.upper().strip(), pix_input.strip(), valor_input))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"Sucesso! O prémio de R$ {valor_input} para {nome_input.upper()} foi computado no sistema.")
                except Exception as e:
                    st.error(f"Falha técnica ao salvar: {e}")
            else:
                st.warning("O preenchimento do Nome do Colaborador é obrigatório.")

# ==========================================
# SEPARADOR 4: ALTERAR / EXCLUIR
# ==========================================
with tab4:
    st.subheader("Modificação e Limpeza de Registos")
    nome_alvo = st.text_input("Digite o nome IDÊNTICO do funcionário para abrir edição:")
    
    if nome_alvo:
        try:
            conn = conectar_supabase()
            query = f"SELECT id, mes_ano, pix, valor_pago_rs FROM pagamentos_premios WHERE nome = '{nome_alvo.upper().strip()}'"
            df_edicao = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df_edicao.empty:
                for idx, row in df_edicao.iterrows():
                    with st.expander(f"Lançamento do Período: {row['mes_ano']} | Valor Atual: R$ {row['valor_pago_rs']}"):
                        with st.form(f"form_update_{row['id']}"):
                            novo_pix_edit = st.text_input("Atualizar Chave PIX", value=row['pix'])
                            novo_valor_edit = st.number_input("Corrigir Valor (R$)", value=float(row['valor_pago_rs']), format="%.2f")
                            
                            sub_col1, sub_col2 = st.columns(2)
                            act_alterar = sub_col1.form_submit_button("✏️ Confirmar Alteração")
                            act_excluir = sub_col2.form_submit_button("❌ Excluir Permanentemente")
                            
                            if act_alterar:
                                conn = conectar_supabase()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE pagamentos_premios SET pix=%s, valor_pago_rs=%s WHERE id=%s", (novo_pix_edit, novo_valor_edit, row['id']))
                                conn.commit()
                                cursor.close()
                                conn.close()
                                st.success("Registro modificado no Supabase! Atualize a página.")
                                
                            if act_excluir:
                                conn = conectar_supabase()
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM pagamentos_premios WHERE id=%s", (row['id'],))
                                conn.commit()
                                cursor.close()
                                conn.close()
                                st.error("Registro deletado com sucesso.")
            else:
                st.warning("Nenhum registro exato com esse nome encontrado. Verifique maiúsculas/minúsculas no separador de Consultas.")
        except Exception as e:
            st.error(f"Erro operacional: {e}")
