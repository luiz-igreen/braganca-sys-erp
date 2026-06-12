import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import json

@st.cache_data(ttl=30)
def carregar_dados_colaboradores_importacao(_engine):
    return _engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()

@st.cache_data(ttl=30)
def carregar_cpfs_atuais(_engine):
    return _engine.connect().execute(text("SELECT id, cpf FROM cadastro_geral_colaborador")).fetchall()

def render(engine, ler_planilha_inteligente, parse_br_date_smart, format_cpf, format_competencia_smart, LISTA_SITUACOES_ESOCIAL):
    st.title("📥 Central de Ingestão de Dados")

    aba_imp1, aba_imp2, aba_imp3, aba_imp4, aba_imp5, aba_imp6 = st.tabs([
        "📋 Carga Base", "💰 Motor ETL", "🔄 Sincronizar eSocial", "🪪 Injeção de CPFs", "🏆 Lançamento de Prêmios", "🤖 Leitor IA (Chat)"
    ])

    with aba_imp1:
        st.subheader("Importação de Cadastros Novos")
        arquivo = st.file_uploader("Selecione o arquivo de migração de colaboradores (.xlsx, .csv)", type=["xlsx", "csv"], key="up_cad_base")
        if arquivo and st.button("Executar Ingestão de Cadastros", key="btn_imp_cad", type="primary"):
            with st.spinner("⏳ Processando arquivo e inserindo cadastros..."):
                try:
                    df_bruto = ler_planilha_inteligente(arquivo)
                    df_temp = pd.DataFrame()
                    if df_bruto.shape[1] >= 7:
                        df_temp['id_colab'] = df_bruto.iloc[:, 1]
                        df_temp['nome_colab'] = df_bruto.iloc[:, 2]
                        df_temp['status_esocial_colab'] = df_bruto.iloc[:, 3]
                        df_temp['cpf_colab'] = df_bruto.iloc[:, 4]
                        df_temp['cargo_colab'] = df_bruto.iloc[:, 5]
                        df_temp['salario_mes_colab'] = df_bruto.iloc[:, 6]
                    else:
                        st.error("O arquivo CSV não possui o número esperado de colunas (mínimo 7).")
                        st.stop()

                    with engine.begin() as conn:
                        for _, row in df_temp.iterrows():
                            try:
                                v_id = str(row['id_colab']).strip()
                                v_nome = str(row['nome_colab']).strip() if pd.notna(row['nome_colab']) else None
                                v_cpf = str(row['cpf_colab']).strip() if pd.notna(row['cpf_colab']) else None
                                v_cargo = str(row['cargo_colab']).strip() if pd.notna(row['cargo_colab']) else None
                                v_status_esocial = str(row['status_esocial_colab']).strip() if pd.notna(row['status_esocial_colab']) else None

                                sal_mes_raw = str(row['salario_mes_colab']).replace('R$', '').replace('.', '').replace(',', '.').strip() if pd.notna(row['salario_mes_colab']) else '0'
                                try:
                                    v_sal_mes = float(sal_mes_raw)
                                except ValueError:
                                    v_sal_mes = 0.0

                                v_admissao = None
                                v_demissao = None
                                v_sal_hora = 0.0

                                if not v_id or v_id.lower() == 'nan': continue

                                conn.execute(text("""
                                    INSERT INTO cadastro_geral_colaborador
                                    (id, nome, cpf, cargo, admissao, demissao, status_esocial, salario_mes_12_24, salario_hora_12_24)
                                    VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :status_esocial, :sal_mes, :sal_hora)
                                    ON CONFLICT (id) DO UPDATE SET
                                    nome = EXCLUDED.nome, cpf = EXCLUDED.cpf, cargo = EXCLUDED.cargo,
                                    admissao = EXCLUDED.admissao, demissao = EXCLUDED.demissao,
                                    status_esocial = EXCLUDED.status_esocial,
                                    salario_mes_12_24 = EXCLUDED.salario_mes_12_24, salario_hora_12_24 = EXCLUDED.salario_hora_12_24
                                """), {
                                    "id": v_id, "nome": v_nome, "cpf": v_cpf, "cargo": v_cargo,
                                    "admissao": v_admissao, "demissao": v_demissao, "status_esocial": v_status_esocial,
                                    "sal_mes": v_sal_mes, "sal_hora": v_sal_hora
                                })
                            except Exception as inner_e:
                                st.warning(f"Linha ignorada (ID: {v_id if 'v_id' in locals() else 'N/A'}): {inner_e}")
                        st.cache_data.clear()
                        st.success("Ingestão executada com sucesso!")
                except Exception as e:
                    st.error(f"Erro Crítico: {e}")

    with aba_imp2:
        st.subheader("Extração Inteligente de Matriz Salarial")
        if st.button("🧨 ESVAZIAR TODO O HISTÓRICO DO BANCO", type="primary"):
            with st.spinner("⏳ Limpando histórico..."):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("TRUNCATE TABLE historico_premiacoes_e_folha RESTART IDENTITY"))
                    st.cache_data.clear()
                    st.success("💥 BANCO DE HISTÓRICO ZERADO!")
                except Exception as e:
                    st.error(f"Erro ao limpar: {e}")

        arquivo_hist = st.file_uploader("Selecione a matriz salarial (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="file_hist")
        if arquivo_hist and st.button("🚀 Processar e Injetar Histórico", type="primary"):
            st.info("Funcionalidade de injeção de histórico em desenvolvimento.")

    with aba_imp3:
        st.subheader("Sincronização de Situações eSocial")
        st.info("Módulo de sincronização do eSocial em desenvolvimento.")

    with aba_imp4:
        st.subheader("Injeção de CPFs")
        st.info("Módulo de injeção de CPFs em desenvolvimento.")

    with aba_imp5:
        st.subheader("🏆 Importação de Lançamento de Prêmios")

        st.markdown("---")
        st.warning("Saneamento de Banco de Dados: Utilize para apagar falhas de importação CSV.")
        if st.button("🧨 Zerar Tabela de Prêmios (Limpeza Total)", type="primary"):
            with st.spinner("Executando limpeza total no PostgreSQL..."):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("TRUNCATE TABLE premios_funcionarios RESTART IDENTITY"))
                    st.cache_data.clear()
                    st.success("Limpeza total concluída. A tabela de prêmios está 100% vazia e pronta para nova importação.")
                except Exception as e:
                    st.error(f"Falha na execução SQL: {e}")
        st.markdown("---")

        arquivo_premios = st.file_uploader("Selecione a Planilha de Prêmios (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="up_premios")
        if arquivo_premios and st.button("🚀 Executar Ingestão de Prêmios", key="btn_imp_premios", type="primary"):
            with st.spinner("⏳ Processando arquivo e inserindo prêmios..."):
                try:
                    if arquivo_premios.name.endswith('.csv'):
                        try:
                            df_premios = pd.read_csv(arquivo_premios, sep=';', encoding='utf-8')
                            if df_premios.shape[1] < 11:
                                arquivo_premios.seek(0)
                                df_premios = pd.read_csv(arquivo_premios, sep=',', encoding='utf-8')
                        except Exception:
                            arquivo_premios.seek(0)
                            df_premios = ler_planilha_inteligente(arquivo_premios)
                    else:
                        df_premios = ler_planilha_inteligente(arquivo_premios)

                    if df_premios is None or df_premios.shape[1] < 11:
                        st.error("O arquivo não possui as 11 colunas necessárias.")
                        st.stop()

                    df_temp = pd.DataFrame()
                    df_temp['matricula'] = df_premios.iloc[:, 0]
                    df_temp['competencia'] = df_premios.iloc[:, 1]
                    df_temp['nome'] = df_premios.iloc[:, 2]
                    df_temp['salario_mes'] = df_premios.iloc[:, 3]
                    df_temp['salario_hora'] = df_premios.iloc[:, 4]
                    df_temp['total_vlr'] = df_premios.iloc[:, 5]
                    df_temp['vlr_premio'] = df_premios.iloc[:, 6]
                    df_temp['valor_rs'] = df_premios.iloc[:, 7]
                    df_temp['descricao'] = df_premios.iloc[:, 8]
                    df_temp['pix'] = df_premios.iloc[:, 9]
                    df_temp['taxa_zaut'] = df_premios.iloc[:, 10]

                    inserts_count = 0

                    with engine.begin() as conn:
                        for _, row in df_temp.iterrows():
                            # Sanitização estrita: remove aspas, ponto e vírgula e espaços
                            v_matricula_raw = str(row['matricula'])
                            v_matricula = v_matricula_raw.replace('"', '').replace(';', '').replace('.0', '').strip()

                            # Bloqueio absoluto de lixo e cabeçalhos
                            if not v_matricula or v_matricula.lower() in ['nan', 'none', 'empty'] or 'id_colaborador' in v_matricula.lower() or 'matr' in v_matricula.lower(): 
                                continue

                            def limpa_valor(val):
                                try:
                                    if pd.isna(val): return 0.0
                                    v = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
                                    return round(float(v), 2)
                                except ValueError:
                                    return 0.0

                            v_salario_mes = limpa_valor(row['salario_mes'])
                            v_salario_hora = limpa_valor(row['salario_hora'])
                            v_total_vlr = limpa_valor(row['total_vlr'])
                            v_vlr_premio = limpa_valor(row['vlr_premio'])
                            v_valor_rs = limpa_valor(row['valor_rs'])
                            v_taxa_zaut = limpa_valor(row['taxa_zaut'])

                            v_comp = str(row['competencia']).strip()
                            v_comp = "" if v_comp.lower() == 'nan' else v_comp

                            v_nome = str(row['nome']).strip()
                            v_nome = "" if v_nome.lower() == 'nan' else v_nome

                            v_desc = str(row['descricao']).strip()
                            v_desc = "" if v_desc.lower() == 'nan' else v_desc

                            v_pix = str(row['pix']).strip()
                            v_pix = "" if v_pix.lower() == 'nan' else v_pix

                            conn.execute(text("""
                                INSERT INTO premios_funcionarios
                                (codigo_funcionario, competencia, nome_funcionario, salario_mes, salario_hora, 
                                total_vlr, valor_premio, valor_rs, descricao_servico, pix, taxa_zaut, data_lancamento, status_pagamento)
                                VALUES (:mat, :comp, :nome, :s_mes, :s_hora, :t_vlr, :v_premio, :v_rs, :desc, :pix, :taxa, :dt, :status)
                            """), {
                                "mat": v_matricula,
                                "comp": v_comp,
                                "nome": v_nome,
                                "s_mes": v_salario_mes,
                                "s_hora": v_salario_hora,
                                "t_vlr": v_total_vlr,
                                "v_premio": v_vlr_premio,
                                "v_rs": v_valor_rs,
                                "desc": v_desc,
                                "pix": v_pix,
                                "taxa": v_taxa_zaut,
                                "dt": datetime.now().date(),
                                "status": 'Pago'
                            })
                            inserts_count += 1
                    st.cache_data.clear()
                    st.success(f"Ingestão executada! {inserts_count} registros válidos inseridos.")
                except Exception as e:
                    st.error(f"Erro Crítico: {e}")

    with aba_imp6:
        st.subheader("🤖 Injeção Universal de Histórico via IA")
        pacote_ia = st.text_area("Pacote de Dados (JSON)", height=200)
        if st.button("🚀 Executar Injeção em Massa", type="primary"):
            with st.spinner("⏳ Injetando histórico em massa..."):
                if pacote_ia.strip():
                    try:
                        dados = json.loads(pacote_ia)
                        sucessos = 0
                        with engine.begin() as conn:
                            for colab in dados:
                                v_id = str(colab['id'])
                                conn.execute(text("DELETE FROM historico_afastamentos WHERE id_colaborador = :id"), {"id": v_id})
                                ultimo_status = "1 - Trabalhando"
                                ultima_data = None
                                for ev in colab['eventos']:
                                    data_ev = ev[0]
                                    desc_ev = ev[1]
                                    conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento) VALUES (:id, :dt, :desc)"), {"id": v_id, "dt": data_ev, "desc": desc_ev})
                                    ultimo_status = desc_ev
                                    ultima_data = data_ev
                                if ultimo_status.startswith("8 - "):
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit, demissao = :dt WHERE id = :id"), {"sit": ultimo_status, "dt": ultima_data, "id": v_id})
                                else:
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit WHERE id = :id"), {"sit": ultimo_status, "id": v_id})
                                sucessos += 1
                        st.cache_data.clear()
                        st.success(f"✅ Histórico de {sucessos} colaborador(es) reconstruído(s) com sucesso!")
                    except Exception as e:
                        st.error(f"Erro na interpretação do pacote: {e}")
                else:
                    st.warning("Cole o código gerado pela IA antes de clicar.")
