
import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, parse_br_date_smart, format_currency_brl, format_cpf, clean_money_to_db):
    st.title("📊 Painel Corporativo & Auditoria Cadastral")
    mostrar_alertas = st.checkbox("🚨 Mostrar Apenas Colaboradores com Alertas/Pendências", value=False)
    try:
        df = pd.read_sql("SELECT id, nome, cpf, cargo, situacao, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, salario_hora FROM cadastro_geral_colaborador ORDER BY nome ASC", engine)

        def verificar_alertas(row):
            alertas = []
            sit = str(row['situacao']) if pd.notna(row['situacao']) else ""
            dt_ret = parse_br_date_smart(row['data_retorno'])
            dt_afast = parse_br_date_smart(row['data_afastamento'])
            from datetime import datetime
            hoje = datetime.today().date()
            if sit not in ['1 - Trabalhando', '8 - Demitido'] and dt_ret and dt_ret <= hoje:
                alertas.append("Retorno Vencido (Abra a ficha)")
            if sit == '1 - Trabalhando' and dt_afast and not dt_ret:
                alertas.append("Afastamento em Aberto")
            v_id_check = str(row['id']).strip()
            if not v_id_check or v_id_check.lower() == 'none' or v_id_check.lower() == 'nan':
                alertas.append("FANTASMA (Exclua este registo)")
            elif pd.isna(row['cpf']) or str(row['cpf']).strip() == "":
                alertas.append("Falta CPF")
            sal = clean_money_to_db(row['salario_mes_12_24'])
            if not sal or float(sal) == 0:
                alertas.append("Sem Salário Base")
            return "⚠️ " + " / ".join(alertas) if alertas else "✅ Atualizado"

        df['Alertas do Sistema'] = df.apply(verificar_alertas, axis=1)
        df['salario_mes_12_24'] = df['salario_mes_12_24'].apply(format_currency_brl)
        df['salario_hora'] = df['salario_hora'].apply(format_currency_brl)
        df['cpf'] = df['cpf'].apply(format_cpf)
        df.rename(columns={'situacao': 'Status (eSocial)'}, inplace=True)
        cols_view = ['Alertas do Sistema', 'id', 'nome', 'Status (eSocial)', 'cpf', 'cargo', 'salario_mes_12_24']
        df_view = df[cols_view].copy()

        if mostrar_alertas:
            df_view = df_view[df_view['Alertas do Sistema'].str.contains('⚠️')]
            if df_view.empty:
                st.success("🎉 Parabéns! Todos os cadastros estão atualizados e sem pendências no momento.")

        st.dataframe(df_view, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🗑️ Exclusão Rápida de Inconsistências")
        st.info("Utilize este painel para apagar de forma definitiva linhas vazias, fantasmas ou qualquer outro registo listado acima, sem precisar de abrir a ficha.")

        opcoes_fantasma = {}
        for idx, r in df.iterrows():
            v_id = str(r['id']) if pd.notna(r['id']) and str(r['id']).strip() else "VAZIO"
            v_nome = str(r['nome']) if pd.notna(r['nome']) and str(r['nome']).strip() else "VAZIO"
            v_cpf = str(r['cpf']) if pd.notna(r['cpf']) and str(r['cpf']).strip() else "Sem CPF"
            label = f"Linha interna {idx} -> ID: {v_id} | Nome: {v_nome} | CPF: {v_cpf}"
            opcoes_fantasma[label] = v_id

        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            selecao_fantasma = st.selectbox("Selecione o registo problemático:", ["(Nenhum selecionado)"] + list(opcoes_fantasma.keys()))
        with col_f2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔥 Exterminar Registo", type="primary", use_container_width=True):
                if selecao_fantasma != "(Nenhum selecionado)":
                    id_alvo = opcoes_fantasma[selecao_fantasma]
                    try:
                        with engine.begin() as conn:
                            if id_alvo == "VAZIO" or id_alvo.lower() == "none" or id_alvo.lower() == "nan":
                                conn.execute(text("DELETE FROM historico_afastamentos WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
                                conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
                                conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador IS NULL OR TRIM(CAST(id_colaborador AS TEXT)) = '' OR CAST(id_colaborador AS TEXT) ILIKE 'nan' OR CAST(id_colaborador AS TEXT) ILIKE 'none'"))
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id IS NULL OR TRIM(CAST(id AS TEXT)) = '' OR CAST(id AS TEXT) ILIKE 'nan' OR CAST(id AS TEXT) ILIKE 'none'"))
                                st.success("🧹 Todos os Fantasmas sem ID foram exterminados da base de dados!")
                            else:
                                conn.execute(text("DELETE FROM historico_afastamentos WHERE id_colaborador = :id"), {"id": id_alvo})
                                conn.execute(text("DELETE FROM historico_salarial WHERE id_colaborador = :id"), {"id": id_alvo})
                                conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), {"id": id_alvo})
                                conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), {"id": id_alvo})
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_alvo})
                                st.success(f"✅ Matrícula {id_alvo} apagada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir o registo: {e}")
                else:
                    st.warning("Selecione um registo na lista ao lado primeiro.")

    except Exception as e:
        st.error(f"Erro ao carregar dados do painel: {e}")
