import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, parse_br_date_smart, format_cpf, LISTA_SITUACOES_ESOCIAL):
    """
    Módulo Completo de Gestão de Cadastros (BRAGANÇA SYS).
    Inclui formatação de salário no padrão Domínio Web e remoção de colunas obsoletas.
    """
    st.title("Gestão de Cadastros")
    st.markdown("Módulo central para administração de Obras, Departamentos e Colaboradores.")

    # Criação de abas para organizar o layout e manter todas as funcionalidades
    tab_obras, tab_dept, tab_colab = st.tabs([
        "🏢 Obras (Construart)", 
        "📁 Departamentos", 
        "👥 Colaboradores"
    ])

    # ==========================================
    # ABA 1: GESTÃO DE OBRAS
    # ==========================================
    with tab_obras:
        st.subheader("Dashboard de Obras")

        # Formulário para adicionar ou atualizar obras diretamente pela interface
        with st.expander("➕ Adicionar / Atualizar Obra", expanded=False):
            with st.form("form_obra", clear_on_submit=True):
                col1, col2 = st.columns(2)
                obra_id = col1.text_input("Código da Obra (ID) *", help="Identificador em formato de texto")
                obra_nome = col2.text_input("Nome da Obra *")
                obra_cnpj = col1.text_input("CNPJ")
                obra_cno = col2.text_input("CNO (Opcional)")

                submit_obra = st.form_submit_button("Salvar Registro")

                if submit_obra:
                    if obra_id and obra_nome:
                        try:
                            with engine.begin() as conn:
                                conn.execute(
                                    text("""
                                        INSERT INTO cadastro_obras (id, nome, cnpj, cno) 
                                        VALUES (:id, :nome, :cnpj, :cno)
                                        ON CONFLICT (id) DO UPDATE 
                                        SET nome = EXCLUDED.nome, cnpj = EXCLUDED.cnpj, cno = EXCLUDED.cno
                                    """),
                                    {"id": str(obra_id), "nome": obra_nome, "cnpj": obra_cnpj or None, "cno": obra_cno or None}
                                )
                            st.success(f"Obra '{obra_nome}' registrada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro no banco de dados: {e}")
                    else:
                        st.warning("Os campos Código e Nome são obrigatórios.")

        # Tabela de visualização de Obras
        try:
            df_obras = pd.read_sql("SELECT id, nome, cnpj, cno FROM cadastro_obras ORDER BY id::int", con=engine)
            st.dataframe(
                df_obras,
                column_config={
                    "id": st.column_config.TextColumn("Código", width="small"),
                    "nome": st.column_config.TextColumn("Nome da Obra", width="large"),
                    "cnpj": st.column_config.TextColumn("CNPJ", width="medium"),
                    "cno": st.column_config.TextColumn("CNO", width="medium")
                },
                hide_index=True,
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao carregar cadastro_obras: {e}")

    # ==========================================
    # ABA 2: GESTÃO DE DEPARTAMENTOS
    # ==========================================
    with tab_dept:
        st.subheader("Dashboard de Departamentos")

        with st.expander("➕ Adicionar / Atualizar Departamento", expanded=False):
            with st.form("form_dept", clear_on_submit=True):
                dept_id = st.text_input("Código do Departamento (ID) *")
                dept_nome = st.text_input("Nome do Departamento *")
                submit_dept = st.form_submit_button("Salvar Departamento")

                if submit_dept:
                    if dept_id and dept_nome:
                        try:
                            with engine.begin() as conn:
                                conn.execute(
                                    text("""
                                        INSERT INTO cadastro_departamentos (id, nome) 
                                        VALUES (:id, :nome)
                                        ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome
                                    """),
                                    {"id": str(dept_id), "nome": dept_nome}
                                )
                            st.success("Departamento salvo com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")

        try:
            df_dept = pd.read_sql("SELECT * FROM cadastro_departamentos ORDER BY id::int", con=engine)
            st.dataframe(df_dept, hide_index=True, use_container_width=True)
        except Exception as e:
            st.info("Nenhum departamento cadastrado ou erro de leitura.")

    # ==========================================
    # ABA 3: GESTÃO DE COLABORADORES
    # ==========================================
    with tab_colab:
        st.subheader("Dashboard de Colaboradores")
        st.markdown("Visão geral da tabela mãe (cadastro_geral_colaborador).")

        # Filtros básicos para a tabela de colaboradores
        col_f1, col_f2 = st.columns(2)
        busca_nome = col_f1.text_input("Buscar por Nome", key="busca_nome_colab")

        # Trava de segurança: ignora registros onde o nome é nulo ou 'nan'
        query_colab = "SELECT * FROM cadastro_geral_colaborador WHERE nome IS NOT NULL AND nome != 'nan'"

        if busca_nome:
            query_colab += f" AND nome ILIKE '%%{busca_nome}%%'"

        # Ordenação numérica crescente extraindo apenas os números do ID
        query_colab += " ORDER BY NULLIF(regexp_replace(id, '\D', '', 'g'), '')::int ASC NULLS LAST LIMIT 500"

        try:
            df_colab = pd.read_sql(query_colab, con=engine)

            # 1. Remoção das colunas obsoletas de salário da visualização
            colunas_remover = ['salario_mes_12_24', 'salario_hora_12_24']
            df_colab = df_colab.drop(columns=[col for col in colunas_remover if col in df_colab.columns])

            # 2. Formatação do salário para o padrão Domínio Web (ex: 9.726,00)
            colunas_salario = ['salario_mes', 'salario_mes_01_26']
            for col in colunas_salario:
                if col in df_colab.columns:
                    # Converte para numérico forçando erros a virarem NaN
                    df_colab[col] = pd.to_numeric(df_colab[col], errors='coerce')
                    # Aplica a formatação com 2 casas decimais, trocando ponto por vírgula e vírgula por ponto
                    df_colab[col] = df_colab[col].apply(
                        lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else ""
                    )

            st.dataframe(
                df_colab,
                hide_index=True,
                use_container_width=True
            )
            st.caption(f"Mostrando {len(df_colab)} registros válidos (Ordenados por ID).")
        except Exception as e:
            st.info(f"Tabela de colaboradores vazia ou aguardando carga de dados. Detalhe: {e}")

    # ==========================================
    # RODAPÉ
    # ==========================================
    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
