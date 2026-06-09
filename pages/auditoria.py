import streamlit as st
import pandas as pd

@st.cache_data(ttl=30)
def carregar_dados_auditoria(_engine):
    return pd.read_sql("SELECT id, nome, cargo, admissao, demissao, situacao, salario_mes_12_24 FROM cadastro_geral_colaborador", _engine)

def render(engine, clean_money_to_db, format_brl_number):
    st.title("🔎 Auditoria Automatizada da Folha")
    if st.button("🚀 Executar Varredura", type="primary"):
        with st.spinner("⏳ Executando auditoria, por favor aguarde..."):
            df_folha = carregar_dados_auditoria(engine)

            if df_folha.empty:
                st.warning("Nenhum colaborador encontrado na base de dados para auditoria.")
                return

            def calcular_auditoria(row):
                try:
                    if pd.notna(row['demissao']):
                        return pd.Series(["Demitido", "-", "Ok"])
                    sal_atual = float(clean_money_to_db(row['salario_mes_12_24']) or 0.0)
                    piso = 4068.99 if "MESTRE" in str(row['cargo']).upper() else (
                        2063.92 if any(x in str(row['cargo']).upper() for x in ["PEDREIRO", "CARPINTEIRO", "PINTOR", "ENCANADOR"])
                        else 1518.00
                    )
                    st_aud = (
                        "⚠️ Sem Salário" if sal_atual == 0.0
                        else ("❌ Abaixo CCT" if round(sal_atual, 2) < round(piso, 2)
                        else "✅ Perfeito")
                    )
                    return pd.Series([f"R$ {format_brl_number(piso)}", f"R$ {format_brl_number(sal_atual)}", st_aud])
                except:
                    return pd.Series(["Erro", "Erro", "Erro"])

            df_folha[['Salário Ideal (CCT)', 'Salário Atual', 'Status']] = df_folha.apply(calcular_auditoria, axis=1)
            df_resultado = df_folha[~df_folha['Status'].str.contains("Demitido|Ok", na=False)]

            if df_resultado.empty:
                st.success("🎉 Todos os colaboradores ativos estão com salários dentro da CCT!")
            else:
                st.dataframe(
                    df_resultado[['id', 'nome', 'cargo', 'situacao', 'Salário Atual', 'Salário Ideal (CCT)', 'Status']],
                    use_container_width=True,
                    hide_index=True
                )
