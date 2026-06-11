import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import calendar
import re
import json

@st.cache_data(ttl=30)
def carregar_dados_colaboradores_importacao(_engine):
    return _engine.connect().execute(text("SELECT id, nome, admissao, demissao FROM cadastro_geral_colaborador")).fetchall()

@st.cache_data(ttl=30)
def carregar_cpfs_atuais(_engine):
    return _engine.connect().execute(text("SELECT id, cpf FROM cadastro_geral_colaborador")).fetchall()

def render(engine, ler_planilha_inteligente, parse_br_date_smart, format_cpf, format_competencia_smart, LISTA_SITUACOES_ESOCIAL):
    st.title("📥 Central de Ingestão de Dados")

    # Adicionando uma nova aba para Prêmios, totalizando 6 abas
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

                    # As colunas do CSV são: 'Alertas do Sistema', 'id', 'nome', 'Status (eSocial)', 'cpf', 'cargo', 'salario_mes_12_24'
                    # Vamos garantir que o DataFrame tenha as colunas mapeadas pela posição, conforme o CSV que você enviou.

                    # Criar um DataFrame temporário com as colunas mapeadas pela posição
                    df_temp = pd.DataFrame()
                    # Verifica se o df_bruto tem colunas suficientes antes de tentar acessá-las
                    if df_bruto.shape[1] >= 7:
                        df_temp['id_colab'] = df_bruto.iloc[:, 1].astype(str) # Coluna 'id' do CSV
                        df_temp['nome_colab'] = df_bruto.iloc[:, 2].astype(str) # Coluna 'nome' do CSV
                        df_temp['status_esocial_colab'] = df_bruto.iloc[:, 3].astype(str) # Coluna 'Status (eSocial)' do CSV
                        df_temp['cpf_colab'] = df_bruto.iloc[:, 4].astype(str) # Coluna 'cpf' do CSV
                        df_temp['cargo_colab'] = df_bruto.iloc[:, 5].astype(str) # Coluna 'cargo' do CSV
                        df_temp['salario_mes_colab'] = df_bruto.iloc[:, 6] # Coluna 'salario_mes_12_24' do CSV
                    else:
                        st.error("O arquivo CSV não possui o número esperado de colunas (mínimo 7). Verifique o formato.")
                        return # Sai da função se o formato estiver incorreto

                    with engine.begin() as conn:
                        for _, row in df_temp.iterrows():
                            try:
                                # Extraindo os valores das colunas do DataFrame temporário
                                v_id = row['id_colab'].strip()
                                v_nome = row['nome_colab'].strip() if pd.notna(row['nome_colab']) else None
                                v_cpf = row['cpf_colab'].strip() if pd.notna(row['cpf_colab']) else None
                                v_cargo = row['cargo_colab'].strip() if pd.notna(row['cargo_colab']) else None
                                v_status_esocial = row['status_esocial_colab'].strip() if pd.notna(row['status_esocial_colab']) else None

                                # Limpar e converter salário
                                sal_mes_raw = str(row['salario_mes_colab']).replace('R$', '').replace('.', '').replace(',', '.').strip() if pd.notna(row['salario_mes_colab']) else '0'
                                try:
                                    v_sal_mes = float(sal_mes_raw)
                                except ValueError:
                                    v_sal_mes = 0.0

                                # Valores padrão para campos não presentes no CSV
                                v_admissao = None # CSV não tem data de admissão
                                v_demissao = None # CSV não tem data de demissão
                                v_sal_hora = 0.0 # CSV não tem salário por hora (usando salario_hora_12_24 na tabela)

                                if not v_id or v_id == 'nan': continue # Ignora linhas sem ID válido

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
                                    "id": v_id,
                                    "nome": v_nome,
                                    "cpf": v_cpf,
                                    "cargo": v_cargo,
                                    "admissao": v_admissao,
                                    "demissao": v_demissao,
                                    "status_esocial": v_status_esocial,
                                    "sal_mes": v_sal_mes,
                                    "sal_hora": v_sal_hora
                                })
                            except Exception as inner_e:
                                st.warning(f"Linha ignorada (ID: {v_id if 'v_id' in locals() else 'N/A'}): {inner_e}")
                        st.cache_data.clear() # Limpa o cache para que a Visão Geral seja atualizada
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
                    st.cache_data.clear() # Limpa o cache
                    st.success("💥 BANCO DE HISTÓRICO ZERADO!")
                except Exception as e:
                    st.error(f"Erro ao limpar: {e}")

        arquivo_hist = st.file_uploader("Selecione a matriz salarial (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="file_hist")
        if arquivo_hist and st.button("🚀 Processar e Injetar Histórico", type="primary"):
            with st.spinner("⏳ Analisando cruzamentos temporais e bloqueando previsões futuras..."):
                try:
                    df_excel = ler_planilha_inteligente(arquivo_hist)

                    db_cols = carregar_dados_colaboradores_importacao(engine)
                    db_dict = {
                        str(r.nome).strip().upper(): {
                            'id': str(r.id),
                            'admissao': str(r.admissao) if r.admissao else None,
                            'demissao': str(r.demissao) if r.demissao else None
                        } for r in db_cols if r.nome
                    }
                    # A lógica de proximo_id_livre pode precisar de ajuste se o ID for TEXT e não numérico sequencial
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
                                # Esta parte do código pode precisar de um gerador de ID TEXT se o ID não for numérico
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
                                        val_float = float(str(val).replace('.', '').replace(',', '.'))
                                    except ValueError:
                                        val_float = 0.0
                                    inserts_pendentes.append({
                                        "id_colaborador": colab['id'],
                                        "competencia": dt_coluna.strftime('%m/%Y'),
                                        "tipo_lancamento": "Salário Mensal",
                                        "valor_lancamento": val_float,
                                        "status_pagamento": "Pago",
                                        "retroativo_pago": 0.0,
                                        "data_pagamento": None
                                    })
                            linhas_processadas += 1
                        with engine.begin() as conn:
                            for insert_data in inserts_pendentes:
                                conn.execute(text("""
                                    INSERT INTO historico_premiacoes_e_folha
                                    (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento, retroativo_pago, data_pagamento)
                                    VALUES (:id_colaborador, :competencia, :tipo_lancamento, :valor_lancamento, :status_pagamento, :retroativo_pago, :data_pagamento)
                                    ON CONFLICT (id_colaborador, competencia, tipo_lancamento) DO UPDATE SET
                                    valor_lancamento = EXCLUDED.valor_lancamento,
                                    status_pagamento = EXCLUDED.status_pagamento,
                                    retroativo_pago = EXCLUDED.retroativo_pago,
                                    data_pagamento = EXCLUDED.data_pagamento
                                """), insert_data)
                        st.cache_data.clear() # Limpa o cache
                        st.success(f"🚀 {linhas_processadas} linhas processadas. Histórico injetado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao processar o ficheiro: {e}")

    with aba_imp3:
        st.subheader("🔄 Sincronização de Situações eSocial")
        st.info("Envie a planilha de histórico de situações do eSocial. O robô vai atualizar os status dos colaboradores e a linha do tempo de afastamentos.")
        arquivo_esocial = st.file_uploader("Selecione a Planilha (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="up_esocial")
        if arquivo_esocial and st.button("🚀 Iniciar Sincronização eSocial", type="primary"):
            with st.spinner("⏳ Analisando e sincronizando situações..."):
                try:
                    df_esocial = ler_planilha_inteligente(arquivo_esocial)
                    sucessos = 0
                    with engine.begin() as conn:
                        for _, row in df_esocial.iterrows():
                            v_id = str(row['id']).strip().replace('.0', '')
                            v_data = parse_br_date_smart(row['data'])
                            v_situacao = str(row['situacao']).strip()
                            if not v_id or not v_data or not v_situacao: continue
                            sit_completa = next((s for s in LISTA_SITUACOES_ESOCIAL if s.startswith(v_situacao.split(' ')[0])), v_situacao)
                            dt_str = v_data.strftime('%Y-%m-%d')
                            if sit_completa.startswith('8 - '):
                                conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit, demissao = :dt WHERE id = :id"), {"sit": sit_completa, "dt": dt_str, "id": v_id})
                            elif sit_completa.startswith('1 - '):
                                conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit WHERE id = :id"), {"sit": sit_completa, "id": v_id})
                                # data_retorno não existe mais na tabela, remover ou ajustar
                            else:
                                conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit WHERE id = :id"), {"sit": sit_completa, "id": v_id})
                                # data_afastamento e data_retorno não existem mais na tabela, remover ou ajustar
                            if dt_str:
                                # O campo 'codigo_situacao' na tabela historico_afastamentos é 'tipo_afastamento'
                                ja_tem = conn.execute(text("SELECT 1 FROM historico_afastamentos WHERE id_colaborador = :id AND data_inicio = :dt AND tipo_afastamento = :desc"), {"id": v_id, "dt": dt_str, "desc": sit_completa}).fetchone()
                                if not ja_tem:
                                    conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento) VALUES (:id, :dt, :desc)"), {"id": v_id, "dt": dt_str, "desc": sit_completa})
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
                    col_id = next((c for c in df_cpf.columns if str(c).strip().upper() in ['CÓDIGO', 'CODIGO', 'ID', 'MATRICULA', 'ID/MATRÍCULA']), None)
                    col_cpf = next((c for c in df_cpf.columns if 'CPF' in str(c).strip().upper()), None)
                    if not col_id or not col_cpf:
                        st.error(f"⚠️ Não consegui encontrar as colunas na linha {header_idx}. Tentei achar entre estas: {list(df_cpf.columns)}.")
                    else:
                        atualizados, ignorados = 0, 0
                        atuais = carregar_cpfs_atuais(engine)
                        mapa_atuais = {str(r.id).strip(): format_cpf(str(r.cpf)) if r.cpf else "" for r in atuais}
                        with engine.begin() as conn:
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

    with aba_imp5: # Nova aba para Lançamento de Prêmios
        st.subheader("🏆 Importação de Lançamento de Prêmios")
        st.info("Faça o upload da planilha de Lançamento de Prêmios. Os dados serão inseridos na tabela 'premios_funcionarios'.")
        arquivo_premios = st.file_uploader("Selecione a Planilha de Prêmios (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="up_premios")
        if arquivo_premios and st.button("🚀 Executar Ingestão de Prêmios", key="btn_imp_premios", type="primary"):
            with st.spinner("⏳ Processando arquivo e inserindo prêmios..."):
                try:
                    df_premios = ler_planilha_inteligente(arquivo_premios)

                    # Mapeamento das colunas do CSV para o DataFrame
                    # As colunas do CSV são: 'id', 'nome', 'sal_hora', 'Horas Prêmio (HP)', 'Descrição do Serviço'
                    df_temp_premios = pd.DataFrame()
                    if df_premios.shape[1] >= 5:
                        df_temp_premios['id_colaborador_csv'] = df_premios.iloc[:, 0].astype(str) # Coluna 'id' do CSV
                        df_temp_premios['nome_colaborador_csv'] = df_premios.iloc[:, 1].astype(str) # Coluna 'nome' do CSV
                        df_temp_premios['salario_hora_csv'] = df_premios.iloc[:, 2] # Coluna 'sal_hora' do CSV
                        df_temp_premios['horas_premio_csv'] = df_premios.iloc[:, 3] # Coluna 'Horas Prêmio (HP)' do CSV
                        df_temp_premios['descricao_servico_csv'] = df_premios.iloc[:, 4].astype(str) # Coluna 'Descrição do Serviço' do CSV
                    else:
                        st.error("O arquivo CSV de Prêmios não possui o número esperado de colunas (mínimo 5). Verifique o formato.")
                        return

                    inserts_count = 0
                    with engine.begin() as conn:
                        for _, row in df_temp_premios.iterrows():
                            try:
                                # --- USANDO OS NOMES DE COLUNAS DO SEU SUPABASE ---
                                v_codigo_funcionario = row['id_colaborador_csv'].strip()
                                v_nome_funcionario = row['nome_colaborador_csv'].strip() if pd.notna(row['nome_colaborador_csv']) else None

                                # Limpar e converter salario_hora
                                sal_hora_raw = str(row['salario_hora_csv']).replace('R$', '').replace('.', '').replace(',', '.').strip() if pd.notna(row['salario_hora_csv']) else '0'
                                try:
                                    v_salario_hora = round(float(sal_hora_raw), 2)
                                    if abs(v_salario_hora) >= 10**8:
                                        st.warning(f"Salário por hora ({v_salario_hora}) para ID {v_codigo_funcionario} é muito grande. Ajustando para 0.0.")
                                        v_salario_hora = 0.0
                                except ValueError:
                                    v_salario_hora = 0.0

                                # Limpar e converter horas_premio
                                horas_premio_raw = str(row['horas_premio_csv']).replace(',', '.').strip() if pd.notna(row['horas_premio_csv']) else '0'
                                try:
                                    v_horas_premio = round(float(horas_premio_raw), 2)
                                    if abs(v_horas_premio) >= 10**8:
                                        st.warning(f"Horas prêmio ({v_horas_premio}) para ID {v_codigo_funcionario} é muito grande. Ajustando para 0.0.")
                                        v_horas_premio = 0.0
                                except ValueError:
                                    v_horas_premio = 0.0

                                v_descricao_servico = row['descricao_servico_csv'].strip() if pd.notna(row['descricao_servico_csv']) else None
                                v_data_lancamento = datetime.now().date() # Data atual da importação

                                v_valor_total_premio = round(v_salario_hora * v_horas_premio, 2)
                                if abs(v_valor_total_premio) >= 10**8:
                                    st.warning(f"Valor total do prêmio ({v_valor_total_premio}) para ID {v_codigo_funcionario} é muito grande. Ajustando para 0.0.")
                                    v_valor_total_premio = 0.0

                                v_status_pagamento = 'Pago' # Padrão
                                v_cargo = 'N/A' # A coluna 'cargo' existe na sua tabela, mas não no CSV de prêmios. Usando um valor padrão.

                                if not v_codigo_funcionario or v_codigo_funcionario == 'nan': continue # Ignora linhas sem ID válido

                                # --- COMANDO SQL AJUSTADO PARA AS COLUNAS DO SEU SUPABASE ---
                                conn.execute(text("""
                                    INSERT INTO premios_funcionarios
                                    (codigo_funcionario, nome_funcionario, salario_hora, horas_premio, descricao_servico, data_lancamento, valor_total_premio, status_pagamento, cargo)
                                    VALUES (:codigo_funcionario, :nome_funcionario, :salario_hora, :horas_premio, :descricao_servico, :data_lancamento, :valor_total_premio, :status_pagamento, :cargo)
                                """), {
                                    "codigo_funcionario": v_codigo_funcionario,
                                    "nome_funcionario": v_nome_funcionario,
                                    "salario_hora": v_salario_hora,
                                    "horas_premio": v_horas_premio,
                                    "descricao_servico": v_descricao_servico,
                                    "data_lancamento": v_data_lancamento,
                                    "valor_total_premio": v_valor_total_premio,
                                    "status_pagamento": v_status_pagamento,
                                    "cargo": v_cargo
                                })
                                inserts_count += 1
                            except Exception as inner_e:
                                st.warning(f"Linha de prêmio ignorada (ID: {v_codigo_funcionario if 'v_codigo_funcionario' in locals() else 'N/A'}): {inner_e}")
                        st.cache_data.clear() # Limpa o cache
                        st.success(f"Ingestão de Prêmios executada com sucesso! {inserts_count} registros inseridos/atualizados.")
                except Exception as e:
                    st.error(f"Erro Crítico na importação de Prêmios: {e}")

    with aba_imp6: # A aba antiga 'aba_imp5' agora é aba_imp6
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
                                    # O campo 'codigo_situacao' na tabela historico_afastamentos é 'tipo_afastamento'
                                    conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento) VALUES (:id, :dt, :desc)"), {"id": v_id, "dt": data_ev, "desc": desc_ev})
                                    ultimo_status = desc_ev
                                    ultima_data = data_ev
                                # Atualizado para usar 'status_esocial' em vez de 'situacao'
                                if ultimo_status.startswith("8 - "):
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit, demissao = :dt WHERE id = :id"), {"sit": ultimo_status, "dt": ultima_data, "id": v_id})
                                elif ultimo_status.startswith("1 - "):
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit WHERE id = :id"), {"sit": ultimo_status, "id": v_id})
                                    # data_retorno não existe mais na tabela, remover ou ajustar
                                else:
                                    conn.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = :sit WHERE id = :id"), {"sit": ultimo_status, "id": v_id})
                                    # data_afastamento e data_retorno não existem mais na tabela, remover ou ajustar
                                sucessos += 1
                        st.cache_data.clear() # Limpa o cache
                        st.success(f"✅ Histórico de {sucessos} colaborador(es) reconstruído(s) com sucesso!")
                    except Exception as e:
                        st.error(f"Erro na interpretação do pacote. Tem a certeza que copiou o código inteiro? Erro: {e}")
                else:
                    st.warning("Cole o código gerado pela IA antes de clicar.")
