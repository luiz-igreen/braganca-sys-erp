import streamlit as st
import pandas as pd
from sqlalchemy import text
import re
from datetime import datetime, date

def render(engine, parse_br_date_smart, format_currency_brl, format_cpf, clean_money_to_db):
    # Importação interna e protegida para evitar erros de importação circular com o app.py
    from app import format_date_br, LISTA_SITUACOES_ESOCIAL

    st.subheader("👥 Visão Geral dos Colaboradores")

    # --- FILTROS ---
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_nome = st.text_input("Filtrar por Nome:", key="filtro_nome_visao_geral")
    with col2:
        filtro_cpf = st.text_input("Filtrar por CPF:", key="filtro_cpf_visao_geral")
    with col3:
        filtro_status = st.selectbox("Filtrar por Status eSocial:", ["Todos"] + LISTA_SITUACOES_ESOCIAL, key="filtro_status_visao_geral")

    # --- CARREGAR DADOS ---
    @st.cache_data(ttl=600) # Cache por 10 minutos
    def load_data():
        with engine.connect() as conn:
            df_colaboradores = pd.read_sql_query("SELECT * FROM cadastro_geral_colaborador", conn)
            df_afastamentos = pd.read_sql_query("SELECT * FROM historico_afastamentos", conn)
            df_financeiro = pd.read_sql_query("SELECT * FROM cadastro_financeiro_colaborador", conn)
            df_premiacoes = pd.read_sql_query("SELECT * FROM historico_premiacoes_e_folha", conn)
        return df_colaboradores, df_afastamentos, df_financeiro, df_premiacoes

    df_colaboradores, df_afastamentos, df_financeiro, df_premiacoes = load_data()

    # Aplicar filtros
    df_filtrado = df_colaboradores.copy()
    if filtro_nome:
        df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(filtro_nome, case=False, na=False)]
    if filtro_cpf:
        df_filtrado = df_filtrado[df_filtrado['cpf'].str.contains(filtro_cpf, case=False, na=False)]
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status_esocial'] == filtro_status]

    st.write(f"Total de colaboradores encontrados: **{len(df_filtrado)}**")

    # --- EXIBIR DADOS EM TABELA INTERATIVA ---
    if not df_filtrado.empty:
        df_display = df_filtrado.copy()
        df_display['cpf'] = df_display['cpf'].apply(format_cpf)
        df_display['admissao'] = df_display['admissao'].apply(lambda x: format_date_br(x) if pd.notna(x) else '-')
        df_display['demissao'] = df_display['demissao'].apply(lambda x: format_date_br(x) if pd.notna(x) else '-')
        df_display['salario_mes_12_24'] = df_display['salario_mes_12_24'].apply(format_currency_brl)
        df_display['salario_hora_12_24'] = df_display['salario_hora_12_24'].apply(format_currency_brl)

        st.dataframe(df_display[[
            'id', 'nome', 'cpf', 'cargo', 'admissao', 'demissao', 'status_esocial',
            'salario_mes_12_24', 'salario_hora_12_24'
        ]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum colaborador encontrado com os filtros aplicados.")

    st.markdown("---")
    st.subheader("🗑️ Exclusão Rápida de Inconsistências")
    st.info("Utilize este painel para apagar de forma definitiva linhas vazias, fantasmas ou qualquer outro registo listado acima, sem precisar de abrir a ficha.")

    # Identificar inconsistências (IDs nulos ou vazios)
    inconsistencias = df_colaboradores[
        df_colaboradores['id'].isna() |
        (df_colaboradores['id'].astype(str).str.strip() == '') |
        (df_colaboradores['id'].astype(str).str.lower() == 'nan') |
        (df_colaboradores['id'].astype(str).str.lower() == 'none')
    ]

    opcoes_fantasma = {}
    if not inconsistencias.empty:
        for idx, r in inconsistencias.iterrows():
            v_id = str(r['id']) if pd.notna(r['id']) and str(r['id']).strip() else "VAZIO"
            v_nome = str(r['nome']) if pd.notna(r['nome']) and str(r['nome']).strip() else "VAZIO"
            v_cpf = str(r['cpf']) if pd.notna(r['cpf']) and str(r['cpf']).strip() else "Sem CPF"
            label = f"Linha interna {idx} -> ID: {v_id} | Nome: {v_nome} | CPF: {v_cpf}"
            opcoes_fantasma[label] = v_id

    # Adicionar colaboradores com ID válido mas sem nome ou CPF (outras inconsistências)
    colaboradores_sem_nome_cpf = df_colaboradores[
        df_colaboradores['id'].notna() &
        (
            df_colaboradores['nome'].isna() | (df_colaboradores['nome'].astype(str).str.strip() == '') |
            df_colaboradores['cpf'].isna() | (df_colaboradores['cpf'].astype(str).str.strip() == '')
        )
    ]
    if not colaboradores_sem_nome_cpf.empty:
        for idx, r in colaboradores_sem_nome_cpf.iterrows():
            v_id = str(r['id'])
            v_nome = str(r['nome']) if pd.notna(r['nome']) and str(r['nome']).strip() else "VAZIO"
            v_cpf = str(r['cpf']) if pd.notna(r['cpf']) and str(r['cpf']).strip() else "Sem CPF"
            label = f"Linha interna {idx} -> ID: {v_id} | Nome: {v_nome} | CPF: {v_cpf} (Sem Nome/CPF)"
            opcoes_fantasma[label] = v_id

    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        selecao_fantasma = st.selectbox("Selecione o registo problemático:", ["(Nenhum selecionado)"] + list(opcoes_fantasma.keys()), key="selecao_fantasma_visao_geral")

    with col_f2:
        st.markdown("<br>", unsafe_allow_html=True)
        if selecao_fantasma != "(Nenhum selecionado)":
            with st.expander(f"⚠️ CONFIRMAR EXCLUSÃO DE: {selecao_fantasma.split('->')[1].strip()}?"):
                st.warning("Esta ação é IRREVERSÍVEL e apagará o registro e todo o seu histórico em todas as tabelas relacionadas.")
                if st.button("🔥 CONFIRMAR EXTERMINAR REGISTO", type="primary", use_container_width=True, key="btn_confirmar_exterminar"):
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
                                conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), {"id": id_alvo})
                                conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), {"id": id_alvo})
                                conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_alvo})
                                st.success(f"✅ Matrícula {id_alvo} apagada com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir o registo: {e}")
        else:
            st.button("🔥 Exterminar Registo", type="primary", use_container_width=True, disabled=True, key="btn_exterminar_disabled")
