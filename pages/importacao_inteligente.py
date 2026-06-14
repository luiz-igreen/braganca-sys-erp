import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import json
import unicodedata

# FERRAMENTAS UTILIZADAS: Python e Streamlit

@st.cache_data(ttl=30)
def carregar_dados_colaboradores_importacao(_engine):
    return _engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()

def render(engine, *args, **kwargs):
    st.title("📥 Central de Ingestão de Dados")

    aba_imp1, aba_imp2, aba_imp3, aba_imp4, aba_imp5, aba_imp6, aba_imp7 = st.tabs([
        "Importar CSV (Upload)", 
        "Importar CSV (Colar)", 
        "Importar CSV (URL)", 
        "Ajustes Detalhados", 
        "🏆 Lançamento de Prêmios", 
        "Injeção de Histórico",
        "📅 Sincronizar Admissões"
    ])

    with aba_imp1:
        st.subheader("Importar CSV (Upload)")
        st.info("Módulo aguardando restauração da lógica original de importação geral. Caso possua o backup, insira o código neste bloco.")

    with aba_imp2:
        st.subheader("Importar CSV (Colar)")
        st.info("Módulo aguardando restauração da lógica original.")

    with aba_imp3:
        st.subheader("Importar CSV (URL)")
        st.info("Módulo aguardando restauração da lógica original.")

    with aba_imp4:
        st.subheader("Ajustes Detalhados")
        st.info("Módulo aguardando restauração da lógica original.")

    with aba_imp5:
        st.subheader("🏆 Importação de Lançamento de Prêmios")
        st.markdown("---")
        st.warning("Saneamento de Banco de Dados: Utilize para apagar falhas de importação CSV.")
        if st.button("🧨 Zerar Tabela de Prêmios (Limpeza Total)", type="primary"):
            with st.spinner("Executando limpeza total no PostgreSQL..."):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM gestao_premios_zaut"))
                    st.cache_data.clear()
                    st.success("Limpeza total concluída. A tabela de prêmios está 100% vazia.")
                except Exception as e:
                    st.error(f"Falha na execução SQL: {e}")
        st.markdown("---")
        st.info("Módulo de importação de prêmios em reestruturação para o novo formato manual.")

    with aba_imp6:
        st.subheader("Injeção de Histórico")
        st.info("Módulo aguardando restauração da lógica original.")

    with aba_imp7:
        st.subheader("📅 Sincronização de Admissões e Novos Cadastros")
        st.markdown("Faça o upload da planilha contendo `id`, `nome`, `cargo`, `admissao` e `salario`.")

        arquivo_admissoes = st.file_uploader("Selecione a Planilha de Admissões (.csv)", type=["csv"], key="up_admissoes")

        if arquivo_admissoes:
            try:
                try:
                    df_adm = pd.read_csv(arquivo_admissoes, sep=';', encoding='utf-8')
                    if len(df_adm.columns) < 4:
                        arquivo_admissoes.seek(0)
                        df_adm = pd.read_csv(arquivo_admissoes, sep=',', encoding='utf-8')
                except Exception:
                    st.error("Falha ao ler o arquivo CSV. Verifique a formatação.")
                    st.stop()

                # BLINDAGEM DE CABEÇALHOS
                df_adm.columns = [unicodedata.normalize('NFKD', str(c)).encode('ASCII', 'ignore').decode('utf-8').strip().lower() for c in df_adm.columns]

                st.write("🔍 **Auditoria de Colunas Identificadas:**", df_adm.columns.tolist())
                st.write("🔍 **Auditoria de Dados Brutos (3 primeiras linhas):**")
                st.dataframe(df_adm.head(3))

                if st.button("🔄 Executar Sincronização no Banco de Dados", type="primary"):
                    with st.spinner("Processando atualizações e novos cadastros..."):
                        inseridos = 0
                        atualizados = 0

                        with engine.begin() as conn:
                            for _, row in df_adm.iterrows():
                                col_id = next((c for c in df_adm.columns if 'id' in c or 'matr' in c or 'cod' in c), 'id')
                                col_nome = next((c for c in df_adm.columns if 'nome' in c), 'nome')
                                col_cargo = next((c for c in df_adm.columns if 'cargo' in c or 'func' in c), 'cargo')
                                col_admissao = next((c for c in df_adm.columns if 'admiss' in c or 'data' in c), 'admissao')
                                col_salario = next((c for c in df_adm.columns if 'salar' in c or 'remun' in c), 'salario')

                                v_id = str(row.get(col_id, '')).replace('.0', '').replace('"', '').replace(';', '').strip()

                                if not v_id or v_id.lower() == 'nan':
                                    continue

                                v_nome = str(row.get(col_nome, '')).strip()
                                v_cargo = str(row.get(col_cargo, '')).strip()

                                # MOTOR AVANÇADO DE DATAS (Inclui conversão de número de série do Excel)
                                v_admissao_str = str(row.get(col_admissao, '')).strip()
                                v_admissao_date = None
                                if v_admissao_str and v_admissao_str.lower() not in ['nan', 'none', 'nat', '', 'não informada', 'nao informada']:
                                    try:
                                        if v_admissao_str.replace('.', '', 1).isdigit():
                                            # Converte número de série do Excel para Data
                                            parsed_date = pd.to_datetime('1899-12-30') + pd.to_timedelta(float(v_admissao_str), unit='D')
                                            v_admissao_date = parsed_date.date()
                                        else:
                                            # Converte string de data padrão
                                            parsed_date = pd.to_datetime(v_admissao_str, dayfirst=True, errors='coerce')
                                            if pd.notna(parsed_date):
                                                v_admissao_date = parsed_date.date()
                                    except Exception:
                                        pass

                                def limpa_valor(val):
                                    try:
                                        if pd.isna(val): return 0.0
                                        v = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
                                        return round(float(v), 2)
                                    except ValueError:
                                        return 0.0

                                v_salario = limpa_valor(row.get(col_salario, 0))

                                existe = conn.execute(text("SELECT 1 FROM cadastro_geral_colaborador WHERE id = :id"), {"id": v_id}).scalar()

                                if existe:
                                    conn.execute(text("""
                                        UPDATE cadastro_geral_colaborador 
                                        SET data_admissao = COALESCE(:admissao, data_admissao),
                                            cargo = COALESCE(NULLIF(:cargo, ''), cargo),
                                            salario_mes = CASE WHEN :salario > 0 THEN :salario ELSE salario_mes END
                                        WHERE id = :id
                                    """), {
                                        "admissao": v_admissao_date,
                                        "cargo": v_cargo,
                                        "salario": v_salario,
                                        "id": v_id
                                    })
                                    atualizados += 1
                                else:
                                    conn.execute(text("""
                                        INSERT INTO cadastro_geral_colaborador (id, nome, cargo, data_admissao, salario_mes, status_esocial) 
                                        VALUES (:id, :nome, :cargo, :admissao, :salario, '1 - Trabalhando')
                                    """), {
                                        "id": v_id,
                                        "nome": v_nome,
                                        "cargo": v_cargo,
                                        "admissao": v_admissao_date,
                                        "salario": v_salario
                                    })
                                    inseridos += 1

                        st.cache_data.clear()
                        st.success(f"Sincronização concluída! {atualizados} registros atualizados e {inseridos} novos colaboradores inseridos.")

            except Exception as e:
                st.error(f"Erro durante a leitura do arquivo: {e}")
