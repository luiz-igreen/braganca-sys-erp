import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import json

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

    # ... (Abas 1 a 4 omitidas para brevidade, mantendo a estrutura original do seu sistema) ...

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

        arquivo_premios = st.file_uploader("Selecione a Planilha de Prêmios (.csv)", type=["csv"], key="up_premios")
        if arquivo_premios and st.button("🚀 Executar Ingestão de Prêmios", key="btn_imp_premios", type="primary"):
            # Lógica de importação de prêmios mantida conforme memorandos anteriores
            pass

    with aba_imp7:
        st.subheader("📅 Sincronização de Admissões e Novos Cadastros")
        st.markdown("Faça o upload da planilha contendo `id`, `nome`, `cargo`, `admissao` e `salario`.")

        arquivo_admissoes = st.file_uploader("Selecione a Planilha de Admissões (.csv)", type=["csv"], key="up_admissoes")

        if arquivo_admissoes and st.button("🔄 Sincronizar Base de Dados", type="primary"):
            with st.spinner("Processando atualizações e novos cadastros..."):
                try:
                    # Tenta ler com ponto e vírgula, faz fallback para vírgula
                    try:
                        df_adm = pd.read_csv(arquivo_admissoes, sep=';', encoding='utf-8')
                        if len(df_adm.columns) < 4:
                            arquivo_admissoes.seek(0)
                            df_adm = pd.read_csv(arquivo_admissoes, sep=',', encoding='utf-8')
                    except Exception:
                        st.error("Falha ao ler o arquivo CSV. Verifique a formatação.")
                        st.stop()

                    # Padroniza nomes das colunas para minúsculas
                    df_adm.columns = df_adm.columns.str.strip().str.lower()

                    inseridos = 0
                    atualizados = 0

                    with engine.begin() as conn:
                        for _, row in df_adm.iterrows():
                            v_id = str(row.get('id', '')).replace('.0', '').replace('"', '').replace(';', '').strip()

                            if not v_id or v_id.lower() == 'nan':
                                continue

                            v_nome = str(row.get('nome', '')).strip()
                            v_cargo = str(row.get('cargo', '')).strip()

                            # Tratamento de Data de Admissão (DD/MM/YYYY)
                            v_admissao_str = str(row.get('admissao', '')).strip()
                            v_admissao_date = None
                            if v_admissao_str and v_admissao_str.lower() != 'nan':
                                try:
                                    v_admissao_date = datetime.strptime(v_admissao_str, '%d/%m/%Y').date()
                                except ValueError:
                                    pass # Mantém None se a data for inválida

                            # Tratamento de Salário
                            def limpa_valor(val):
                                try:
                                    if pd.isna(val): return 0.0
                                    v = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
                                    return round(float(v), 2)
                                except ValueError:
                                    return 0.0

                            v_salario = limpa_valor(row.get('salario', 0))

                            # Verifica se o colaborador já existe no banco
                            existe = conn.execute(text("SELECT 1 FROM cadastro_geral_colaborador WHERE id = :id"), {"id": v_id}).scalar()

                            if existe:
                                # Atualiza registro existente
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
                                # Insere novo colaborador
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
                    st.error(f"Erro durante a sincronização: {e}")
