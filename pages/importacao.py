import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import calendar
import re
import json

@st.cache_data(ttl=30)
def carregar_colaboradores_importacao(_engine):
    # Esta função pode ser ajustada para carregar dados específicos se necessário
    # Por enquanto, retorna uma lista vazia ou dados mínimos para evitar erros
    return []

def render(engine, ler_planilha_inteligente, parse_br_date_smart, format_cpf, format_competencia_smart, LISTA_SITUACOES_ESOCIAL):
    st.title("📥 Central de Ingestão de Dados")

    aba_imp1, aba_imp2, aba_imp3, aba_imp4, aba_imp5 = st.tabs([
        "📋 Carga Base", "💰 Motor ETL", "🔄 Sincronizar eSocial", "🪪 Injeção de CPFs", "🤖 Leitor IA (Chat)"
    ])

    with aba_imp1:
        st.subheader("Importação de Cadastros Novos")
        arquivo = st.file_uploader("Selecione o arquivo de migração de colaboradores (.xlsx, .csv)", type=["xlsx", "csv"], key="up_cad_base")
        if arquivo and st.button("Executar Ingestão de Cadastros", key="btn_imp_cad", type="primary"):
            with st.spinner("⏳ Processando arquivo e inserindo cadastros..."):
                try:
                    df_bruto = ler_planilha_inteligente(arquivo)
                    with engine.begin() as conn:
                        for _, row in df_bruto.iterrows():
                            try:
                                v_id = str(row.iloc[0]) if len(row) > 0 else None
                                if not v_id or v_id == 'nan': continue
                                conn.execute(text("""
                                    INSERT INTO cadastro_geral_colaborador
                                    (id, nome, cpf, cargo, admissao, demissao, salario_mes_12_24, salario_hora)
                                    VALUES (:id, :nome, :cpf, :cargo, :admissao, :demissao, :sal_mes, :sal_hora)
                                    ON CONFLICT (id) DO UPDATE SET
                                    nome = EXCLUDED.nome, cpf = EXCLUDED.cpf, cargo = EXCLUDED.cargo,
                                    admissao = EXCLUDED.admissao, demissao = EXCLUDED.demissao,
                                    salario_mes_12_24 = EXCLUDED.salario_mes_12_24, salario_hora = EXCLUDED.salario_hora
                                """), {
                                    "id": v_id,
                                    "nome": str(row.iloc[1]) if len(row) > 1 else None,
                                    "cpf": str(row.iloc[2]) if len(row) > 2 else None,
                                    "cargo": str(row.iloc[3]) if len(row) > 3 else None,
                                    "admissao": str(row.iloc[4]) if len(row) > 4 else None,
                                    "demissao": str(row.iloc[5]) if len(row) > 5 else None,
                                    "sal_mes": str(row.iloc[6]) if len(row) > 6 else None,
                                    "sal_hora": str(row.iloc[7]) if len(row) > 7 else None
                                })
                        st.cache_data.clear() # Limpa o cache para que a Visão Geral seja atualizada
                        st.success("Ingestão executada com sucesso!")
                            except Exception as inner_e:
                                st.warning(f"Linha ignorada: {inner_e}")
                except Exception as e:
                    st.error(f"Erro Crítico: {e}")

    with aba_imp2:
        st.subheader("Extração Inteligente de Matriz Salarial")
        if st.button("🧨 ESVAZIAR TODO O HISTÓRICO DO BANCO", type="primary"):
            with st.spinner("⏳ Limpando histórico..."):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("TRUNCATE TABLE historico_premiacoes_e_folha RESTART IDENTITY"))
                    st.cache_data.clear() # Limpa o cache
                    st.success("💥 BANCO DE HISTÓRICO ZERADO!")
                except Exception as e:
                    st.error(f"Erro ao limpar: {e}")

        arquivo_hist = st.file_uploader("Selecione a matriz salarial (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="file_hist")
        if arquivo_hist and st.button("🚀 Processar e Injetar Histórico", type="primary"):
            with st.spinner("⏳ Analisando cruzamentos temporais e bloqueando previsões futuras..."):
                try:
                    df_excel = ler_planilha_inteligente(arquivo_hist)
                    with engine.connect() as conn:
                        db_cols = conn.execute(text("SELECT id, nome, admissao, demissao FROM cadastro_geral_colaborador")).fetchall()
                    db_dict = {
                        str(r.nome).strip().upper(): {
                            'id': str(r.id),
                            'admissao': str(r.admissao) if r.admissao else None,
                            'demissao': str(r.demissao) if r.demissao else None
                        } for r in db_cols if r.nome
                    }
                    lista_ids_numericos = [int(r.id) for r in db_cols if str(r.id).isdigit()]
                    proximo_id_livre = max(lista_ids_numericos) + 1 if lista_ids_numericos else 1000

                    def get_comp_date(col_name):
                        match = re.search(r'(\d{2})/(\d{2})', str(col_name))
                        return pd.Timestamp(year=2000 + int(match.group(2)), month=int(match.group(1)), day=1) if match else None

                    inserts_pendentes, linhas_processadas = [], 0
                    coluna_nome = next((col for col in df_excel.columns if str(col).strip().upper() == 'NOME'), None)
                    hoje = datetime.today()
                    limite_futuro = pd.Timestamp(year=hoje.year, month=hoje.month, day=calendar.monthrange(hoje.year, hoje.month)[1])

                    if not coluna_nome:
                        st.error("Erro: A planilha não possui a coluna 'Nome'.")
                    else:
                        for _, row in df_excel.iterrows():
                            nome_xls = str(row[coluna_nome]).strip().upper()
                            if not nome_xls or nome_xls == 'NAN': continue
                            if nome_xls not in db_dict:
                                novo_id = str(proximo_id_livre)
                                proximo_id_livre += 1
                                with engine.begin() as conn_recupera:
                                    conn_recupera.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome) ON CONFLICT (id) DO NOTHING"), {"id": novo_id, "nome": nome_xls})
                                db_dict[nome_xls] = {'id': novo_id, 'admissao': None, 'demissao': None}
                            colab = db_dict[nome_xls]
                            dt_adm = pd.Timestamp(year=pd.to_datetime(colab['admissao']).year, month=pd.to_datetime(colab['admissao']).month, day=1) if colab['admissao'] else None
                            dt_dem = pd.Timestamp(year=pd.to_datetime(colab['demissao']).year, month=pd.to_datetime(colab['demissao']).month, day=1) if colab['demissao'] else None
                            for col in df_excel.columns:
                                col_str = str(col).strip().upper()
                                if "SALÁRIO MÊS" in col_str or "SALARIO MES" in col_str:
                                    val = row[col]
                                    if pd.isna(val) or str(val).strip() == "": continue
                                    dt_coluna = get_comp_date(col_str)
                                    if not dt_coluna or dt_coluna < pd.Timestamp(year=2024, month=12, day=1): continue
                                    if dt_coluna > limite_futuro: continue
                                    if dt_adm and dt_coluna < dt_adm: continue
                                    if dt_dem and dt_coluna > dt_dem: continue
                                    try:
                                        val_float = float(val) if not isinstance(val, str) else float(val.upper().replace('R$', '').replace('.', '').replace(',', '.').strip())
                                    except: continue
                                    if val_float > 0:
                                        inserts_pendentes.append({"id_colab": colab['id'], "comp": f"{dt_coluna.month:02d}/{dt_coluna.year}", "tipo": "Salário Mensal", "valor": val_float})
                            linhas_processadas += 1

                        if inserts_pendentes:
                            with engine.begin() as conn:
                                for item in inserts_pendentes:
                                    if not conn.execute(text("SELECT 1 FROM historico_premiacoes_e_folha WHERE id_colaborador = :id_colab AND competencia = :comp AND tipo_lancamento = :tipo"), item).fetchone():
                                        conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_colab, :comp, :tipo, :valor, 'Pago')"), item)
                            st.cache_data.clear() # Limpa o cache
                            st.success(f"✅ Lidos {linhas_processadas} colaboradores. Injetados {len(inserts_pendentes)} registros reais.")
                        else:
                            st.warning("Nenhum registro novo importado.")
                except Exception as e:
                    st.error(f"Falha: {e}")

    with aba_imp3:
        st.subheader("🔄 Sincronização Automática de Afastamentos (eSocial)")
        st.info("Faça o upload do seu relatório da Domínio. O sistema vai ignorar falsos-excels, achar o cabeçalho e atualizar todo o histórico num piscar de olhos!")
        arquivo_st = st.file_uploader("Selecione a Relação de Empregados (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="up_st")
        if arquivo_st and st.button("🚀 Processar Situações (Varredura Massiva)", type="primary"):
            with st.spinner("⏳ Mapeando colunas e varrendo dados..."):
                try:
                    df_st = ler_planilha_inteligente(arquivo_st)
                    col_id = next((c for c in df_st.columns if str(c).strip().upper() in ['CÓDIGO', 'CODIGO', 'ID', 'MATRICULA', 'ID/MATRÍCULA']), None)
                    col_s = next((c for c in df_st.columns if str(c).strip().upper() in ['S', 'ST', 'SITUAÇÃO', 'SITUACAO']), None)
                    col_dt = next((c for c in df_st.columns if 'DATA ST' in str(c).strip().upper() or 'DATA' in str(c).strip().upper()), None)

                    if not col_id or not col_s or not col_dt:
                        st.error(f"⚠️ As colunas exatas não foram encontradas. Colunas que o sistema viu: {list(df_st.columns)}.")
                    else:
                        mapa_st = {str(item.split(' - ')[0]).strip(): item for item in LISTA_SITUACOES_ESOCIAL}
                        sucessos = 0
                        with engine.begin() as conn:
                            for _, row in df_st.iterrows():
                                v_id = str(row[col_id]).strip()
                                v_s = str(row[col_s]).strip().replace('.0', '')
                                v_dt_raw = row[col_dt]
                                if not v_id or v_id == 'nan' or not v_s or v_s == 'nan': continue
                                dt_st_obj = parse_br_date_smart(v_dt_raw)
                                dt_str = dt_st_obj.strftime('%Y-%m-%d') if dt_st_obj else None
                                sit_completa = mapa_st.get(v_s, "1 - Trabalhando")
                                existe = conn.execute(text("SELECT id FROM cadastro_geral_colaborador WHERE id = :id"), {"id": v_id}).fetchone()
                                if existe:
                                    if sit_completa.startswith('8'):
                                        conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = :sit, demissao = :dt WHERE id = :id"), {"sit": sit_completa, "dt": dt_str, "id": v_id})
                                    elif sit_completa.startswith('1 - '):
                                        conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = :sit, data_retorno = :dt WHERE id = :id"), {"sit": sit_completa, "dt": dt_str, "id": v_id})
                                    else:
                                        conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = :sit, data_afastamento = :dt, data_retorno = NULL WHERE id = :id"), {"sit": sit_completa, "dt": dt_str, "id": v_id})
                                    if dt_str:
                                        ja_tem = conn.execute(text("SELECT 1 FROM historico_afastamentos WHERE id_colaborador = :id AND data_inicio = :dt AND codigo_situacao = :desc"), {"id": v_id, "dt": dt_str, "desc": sit_completa}).fetchone()
                                        if not ja_tem:
                                            conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, codigo_situacao) VALUES (:id, :dt, :desc)"), {"id": v_id, "dt": dt_str, "desc": sit_completa})
                                            sucessos += 1
                        st.cache_data.clear() # Limpa o cache
                        st.success(f"✅ Missão Cumprida! A varredura analisou os dados e inseriu {sucessos} novos eventos na Linha do Tempo dos colaboradores.")
                except Exception as e:
                    st.error(f"Erro ao processar o ficheiro: {e}")

    with aba_imp4:
        st.subheader("🪪 Injeção Automática de CPFs")
        st.info("Envie a planilha. O robô vai formatar e corrigir os CPFs que perderam o zero à esquerda devido a falhas do Excel.")
        arquivo_cpf = st.file_uploader("Selecione a Planilha (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="up_cpf")
        if arquivo_cpf and st.button("🚀 Iniciar Varredura de CPFs", type="primary"):
            with st.spinner("⏳ Caçando cabeçalhos ocultos e processando..."):
                try:
                    df_preview = ler_planilha_inteligente(arquivo_cpf, nrows=15, header=None)
                    header_idx = 0
                    for idx, row in df_preview.iterrows():
                        row_str = ' '.join([str(v).upper() for v in row if pd.notna(v)])
                        if 'CPF' in row_str and ('MATR' in row_str or 'ID' in row_str or 'CÓD' in row_str or 'COD' in row_str):
                            header_idx = idx
                            break
                    arquivo_cpf.seek(0)
                    df_cpf = ler_planilha_inteligente(arquivo_cpf, header=header_idx)
                    col_id = next((c for c in df_cpf.columns if str(c).strip().upper() in ['CÓDIGO', 'CODIGO', 'ID', 'MATRÍCULA', 'MATRICULA', 'ID/MATRÍCULA']), None)
                    col_cpf = next((c for c in df_cpf.columns if 'CPF' in str(c).strip().upper()), None)
                    if not col_id or not col_cpf:
                        st.error(f"⚠️ Não consegui encontrar as colunas na linha {header_idx}. Tentei achar entre estas: {list(df_cpf.columns)}.")
                    else:
                        atualizados, ignorados = 0, 0
                        with engine.begin() as conn:
                            atuais = conn.execute(text("SELECT id, cpf FROM cadastro_geral_colaborador")).fetchall()
                            mapa_atuais = {str(r.id).strip(): format_cpf(str(r.cpf)) if r.cpf else "" for r in atuais}
                            for _, row in df_cpf.iterrows():
                                v_id = str(row[col_id]).strip().replace('.0', '')
                                raw_cpf = str(row[col_cpf]).strip()
                                if not v_id or v_id == 'nan' or raw_cpf.lower() == 'nan' or not raw_cpf: continue
                                cpf_planilha_formatado = format_cpf(raw_cpf)
                                if not cpf_planilha_formatado: continue
                                cpf_banco = mapa_atuais.get(v_id)
                                if cpf_banco is not None:
                                    if cpf_banco == cpf_planilha_formatado:
                                        ignorados += 1
                                    else:
                                        conn.execute(text("UPDATE cadastro_geral_colaborador SET cpf = :cpf WHERE id = :id"), {"cpf": cpf_planilha_formatado, "id": v_id})
                                        atualizados += 1
                        st.cache_data.clear() # Limpa o cache
                        st.success(f"✅ Varredura Concluída! {atualizados} CPFs corrigidos/atualizados. {ignorados} CPFs já estavam perfeitos.")
                except Exception as e:
                    st.error(f"Erro ao ler os CPFs: {e}")

    with aba_imp5:
        st.subheader("🤖 Injeção Universal de Histórico via IA")
        st.info("Cole na caixa abaixo o 'Pacote de Dados' (Código) gerado pelo seu Assistente de IA no chat.")
        pacote_ia = st.text_area("Pacote de Dados (JSON)", height=200, placeholder='Ex: [{"id": "9", "eventos": [["2022-06-14", "18 - Doenca..."], ...]}]')
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
                                    conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, codigo_situacao) VALUES (:id, :dt, :desc)"), {"id": v_id, "dt": data_ev, "desc": desc_ev})
                                    ultimo_status = desc_ev
                                    ultima_data = data_ev
                                if ultimo_status.startswith("8 - "):
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = :sit, demissao = :dt WHERE id = :id"), {"sit": ultimo_status, "dt": ultima_data, "id": v_id})
                                elif ultimo_status.startswith("1 - "):
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = :sit, data_retorno = :dt WHERE id = :id"), {"sit": ultimo_status, "dt": ultima_data, "id": v_id})
                                else:
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET situacao = :sit, data_afastamento = :dt, data_retorno = NULL WHERE id = :id"), {"sit": ultimo_status, "dt": ultima_data, "id": v_id})
                                sucessos += 1
                        st.cache_data.clear() # Limpa o cache
                        st.success(f"✅ Histórico de {sucessos} colaborador(es) reconstruído(s) com sucesso!")
                    except Exception as e:
                        st.error(f"Erro na interpretação do pacote. Tem a certeza que copiou o código inteiro? Erro: {e}")
                else:
                    st.warning("Cole o código gerado pela IA antes de clicar.")
