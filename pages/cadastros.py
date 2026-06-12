import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, date
import calendar
import re

@st.cache_data(ttl=30)
def carregar_dados_colaborador_cache(_engine, colab_id):
    with _engine.connect() as conn:
        colab = conn.execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)}).fetchone()
        df_fin = pd.read_sql(text("SELECT * FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), conn, params={"id": str(colab_id)})
        fin_data = df_fin.iloc[0].to_dict() if not df_fin.empty else None
        df_hist = pd.read_sql(text("SELECT * FROM historico_premiacoes_e_folha WHERE id_colaborador = :id ORDER BY id DESC"), conn, params={"id": str(colab_id)})
        df_hist_sit = pd.read_sql(text("SELECT id, data_inicio as data_evento, tipo_afastamento as descricao FROM historico_afastamentos WHERE id_colaborador = :id ORDER BY data_inicio DESC, id DESC"), conn, params={"id": str(colab_id)})
    return colab, fin_data, df_hist, df_hist_sit

@st.cache_data(ttl=30)
def buscar_colaboradores_cache(_engine, termo):
    with _engine.connect() as conn:
        resultados = conn.execute(text("SELECT id, nome FROM cadastro_geral_colaborador WHERE id = :t"), {"t": str(termo).strip()}).fetchall()
        if not resultados:
            resultados = conn.execute(text("SELECT id, nome FROM cadastro_geral_colaborador WHERE nome ILIKE :t ORDER BY nome ASC"), {"t": f"%{termo.strip()}%"}).fetchall()
    return resultados

def render(engine, parse_br_date_smart=None, format_cpf=None, LISTA_SITUACOES_ESOCIAL=None, *args, **kwargs):
    # --- INÍCIO DO BLOCO DE SEGURANÇA (FALLBACKS) ---
    if LISTA_SITUACOES_ESOCIAL is None:
        LISTA_SITUACOES_ESOCIAL = ["1 - Trabalhando", "2 - Afastamento Temporário - Doença", "3 - Afastamento Temporário - Acidente de Trabalho", "4 - Afastamento Temporário - Licença Maternidade", "5 - Afastamento Temporário - Serviço Militar", "6 - Afastamento Temporário - Outros", "7 - Afastamento Definitivo - Aposentadoria", "8 - Afastamento Definitivo - Demissão", "9 - Férias"]

    LISTA_CARGOS = ["VENDEDOR", "GERENTE", "DIRETOR", "OUTRO (DIGITAR MANUALMENTE)"]

    def injetar_autofoco(key): pass

    def format_date_br(d):
        try: return pd.to_datetime(d).strftime('%d/%m/%Y')
        except: return ""

    def format_currency_brl(v):
        try: return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except: return "R$ 0,00"

    def format_brl_number(v):
        try: return f"{float(v):.2f}".replace(".", ",")
        except: return "0,00"

    def format_competencia_smart(c):
        return str(c).strip() if pd.notna(c) else ""

    def clean_money_to_db(v):
        try:
            if pd.isna(v) or str(v).strip() == "": return None
            return str(float(str(v).replace("R$", "").replace(".", "").replace(",", ".").strip()))
        except: return None

    def sort_historico_chronological(df):
        return df

    if format_cpf is None:
        format_cpf = lambda x: str(x) if pd.notna(x) else ""

    if parse_br_date_smart is None:
        parse_br_date_smart = lambda x: pd.to_datetime(x, errors='coerce').date() if pd.notna(x) else None
    # --- FIM DO BLOCO DE SEGURANÇA ---

    opcoes_sub = ["🔍 Consultar & Gerenciar", "➕ Novo Cadastro"]
    if 'sub_menu_index' not in st.session_state:
        st.session_state['sub_menu_index'] = 0
    sub_menu = st.radio("Menu de Operações", opcoes_sub, index=st.session_state['sub_menu_index'], label_visibility="collapsed", horizontal=True)
    st.session_state['sub_menu_index'] = opcoes_sub.index(sub_menu)
    st.markdown("<br>", unsafe_allow_html=True)

    if sub_menu == "🔍 Consultar & Gerenciar":
        if 'busca_selecionada_id' not in st.session_state:
            st.session_state['busca_selecionada_id'] = None
        if 'status_acao' not in st.session_state:
            st.session_state['status_acao'] = None

        if not st.session_state['busca_selecionada_id']:
            injetar_autofoco("k_term_busca")

        termo = st.text_input("Digite o ID (Matrícula) ou parte do Nome:", key="k_term_busca")
        btn_buscar = st.button("Buscar Registro", type="primary")

        if btn_buscar and termo:
            st.session_state['status_acao'] = None
            st.session_state['busca_selecionada_id'] = None
            with st.spinner("⏳ Buscando registros..."):
                try:
                    resultados = buscar_colaboradores_cache(engine, termo)
                    if not resultados:
                        st.warning("Nenhum registro encontrado.")
                    elif len(resultados) == 1:
                        st.session_state['busca_selecionada_id'] = str(resultados[0].id)
                        st.rerun()
                    else:
                        st.info("Múltiplos registros encontrados:")
                        opcoes_lista = {f"ID: {r.id} | Nome: {r.nome}": str(r.id) for r in resultados}
                        escolha = st.selectbox("Selecione:", list(opcoes_lista.keys()))
                        if st.button("Confirmar Seleção", type="primary"):
                            st.session_state['busca_selecionada_id'] = opcoes_lista[escolha]
                            st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        if st.session_state['busca_selecionada_id']:
            colab_id = st.session_state['busca_selecionada_id']
            with st.spinner(f"⏳ Carregando ficha de {colab_id}..."):
                try:
                    colab, fin_data, df_hist, df_hist_sit = carregar_dados_colaborador_cache(engine, colab_id)

                    if colab:
                        if not df_hist.empty:
                            hoje = datetime.today().date()
                            max_date_allowed = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
                            if pd.notna(colab.demissao):
                                try:
                                    dt_dem_obj = pd.to_datetime(colab.demissao).date()
                                    max_dem_date = date(dt_dem_obj.year, dt_dem_obj.month, calendar.monthrange(dt_dem_obj.year, dt_dem_obj.month)[1])
                                    if max_dem_date < max_date_allowed: max_date_allowed = max_dem_date
                                except: pass

                            df_hist_clean = df_hist.copy()
                            df_hist_clean['temp_date'] = pd.to_datetime(df_hist_clean['competencia'], errors='coerce').dt.date
                            df_future = df_hist_clean[df_hist_clean['temp_date'] > max_date_allowed]

                            if not df_future.empty:
                                ids_to_del = tuple(df_future['id'].tolist())
                                with engine.begin() as conn_clean:
                                    if len(ids_to_del) == 1:
                                        conn_clean.execute(text(f"DELETE FROM historico_premiacoes_e_folha WHERE id = {ids_to_del[0]}"))
                                    else:
                                        conn_clean.execute(text(f"DELETE FROM historico_premiacoes_e_folha WHERE id IN {ids_to_del}"))
                                st.toast("🧹 Lançamentos posteriores ao mês de demissão/atual foram excluídos automaticamente!")
                                st.cache_data.clear() 
                                colab, fin_data, df_hist, df_hist_sit = carregar_dados_colaborador_cache(engine, colab_id) 

                        df_hist = sort_historico_chronological(df_hist)
                        sal_mestra_vazio = not colab.salario_mes_12_24 or str(colab.salario_mes_12_24).strip() == "" or str(colab.salario_mes_12_24).lower() in ["nan", "none"]
                        hist_salario = df_hist[df_hist['tipo_lancamento'].str.contains('Salário', na=False, case=False)] if not df_hist.empty else pd.DataFrame()
                        tem_hist = not hist_salario.empty
                        val_atual_base = 0.0

                        if sal_mestra_vazio and tem_hist:
                            ultimo_salario_hist = hist_salario.iloc[0]['valor_lancamento']
                            val_hora_calc = float(ultimo_salario_hist) / 220.0
                            with engine.begin() as conn_sync:
                                conn_sync.execute(text("UPDATE cadastro_geral_colaborador SET salario_mes_12_24 = :sm, salario_hora_12_24 = :sh WHERE id = :id"), {"sm": str(ultimo_salario_hist), "sh": str(val_hora_calc), "id": str(colab_id)})
                            val_atual_base = float(ultimo_salario_hist)
                            salario_mes_display = format_currency_brl(val_atual_base)
                            salario_hora_display = format_currency_brl(val_hora_calc)
                            st.cache_data.clear() 
                            colab, fin_data, df_hist, df_hist_sit = carregar_dados_colaborador_cache(engine, colab_id) 

                        elif not sal_mestra_vazio:
                            sm_val = clean_money_to_db(str(colab.salario_mes_12_24))
                            if sm_val:
                                val_atual_base = float(sm_val)
                                salario_mes_display = format_currency_brl(val_atual_base)
                                salario_hora_display = format_currency_brl(val_atual_base / 220.0)
                                comp_atual_dt = datetime.today()
                                comp_atual_str = comp_atual_dt.strftime('%m/%Y')
                                pode_sincronizar = True
                                if pd.notna(colab.demissao):
                                    dt_dem = pd.to_datetime(colab.demissao).date()
                                    if date(comp_atual_dt.year, comp_atual_dt.month, 1) > date(dt_dem.year, dt_dem.month, 1):
                                        pode_sincronizar = False
                                if pode_sincronizar:
                                    ja_tem_mes = False
                                    if not df_hist.empty:
                                        df_hist_mensal = df_hist[(df_hist['competencia'] == comp_atual_str) & (df_hist['tipo_lancamento'].str.contains('Salário', case=False, na=False))]
                                        if not df_hist_mensal.empty: ja_tem_mes = True
                                    if not ja_tem_mes:
                                        with engine.begin() as conn_sync:
                                            conn_sync.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": str(colab_id), "comp": comp_atual_str, "val": val_atual_base})
                                        st.toast(f"🗓️ O mês de {comp_atual_str} virou e o salário foi gerado automaticamente!")
                                        st.cache_data.clear() 
                                        colab, fin_data, df_hist, df_hist_sit = carregar_dados_colaborador_cache(engine, colab_id) 
                        else:
                            salario_mes_display = "Não Informado"
                            salario_hora_display = "Não Informado"

                        v_sit_atual = getattr(colab, "status_esocial", "1 - Trabalhando") or "1 - Trabalhando"

                        ultimo_afastamento = df_hist_sit.iloc[0] if not df_hist_sit.empty else None
                        v_afast_data = ultimo_afastamento['data_evento'] if ultimo_afastamento else None
                        v_afast_desc = ultimo_afastamento['descricao'] if ultimo_afastamento else None

                        if v_sit_atual not in ["1 - Trabalhando", "8 - Demitido"] and v_afast_data:
                            dt_afast_obj = parse_br_date_smart(v_afast_data)
                            if dt_afast_obj and dt_afast_obj < datetime.today().date():
                                if v_sit_atual != "1 - Trabalhando":
                                    with engine.begin() as conn_auto:
                                        conn_auto.execute(text("UPDATE cadastro_geral_colaborador SET status_esocial = '1 - Trabalhando' WHERE id = :id"), {"id": str(colab_id)})
                                        conn_auto.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento) VALUES (:id, :dt, '1 - Trabalhando')"), {"id": str(colab_id), "dt": datetime.today().strftime('%Y-%m-%d'), "desc": '1 - Trabalhando'})
                                    st.toast(f"🤖 Auto-Retorno: O sistema detetou que a data já passou e atualizou {colab.nome} para 'Trabalhando'!")
                                    st.cache_data.clear() 
                                    st.rerun()

                        sit_color = "#f8fafc"
                        if v_sit_atual.startswith("8"): sit_color = "#ef4444"
                        elif v_sit_atual.startswith("1"): sit_color = "#10b981"
                        elif v_sit_atual.startswith("9"): sit_color = "#3b82f6"
                        else: sit_color = "#facc15"

                        st.markdown("### 📋 Ficha Completa do Colaborador")
                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown('<p class="field-label">ID / MATRÍCULA</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{colab.id}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">CARGO</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{colab.cargo if colab.cargo else "Não Informado"}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">SALÁRIO-MÊS ATUAL</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{salario_mes_display}</p>', unsafe_allow_html=True)
                        with c2:
                            st.markdown('<p class="field-label">NOME COMPLETO</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{colab.nome}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">SITUAÇÃO (eSocial)</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value" style="color: {sit_color}; font-weight: bold;">{v_sit_atual}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">SALÁRIO-HORA ATUAL</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{salario_hora_display}</p>', unsafe_allow_html=True)
                        with c3:
                            st.markdown('<p class="field-label">CPF</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{format_cpf(colab.cpf) if colab.cpf else "Não Informado"}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">DATA DE ADMISSÃO</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value">{format_date_br(colab.admissao) or "Não Informada"}</p>', unsafe_allow_html=True)
                            st.markdown('<p class="field-label">DATA DE DEMISSÃO</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="field-value" style="color: #ef4444;">{format_date_br(colab.demissao) or "Ativo / Sem Demissão"}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        if ultimo_afastamento:
                            icon_afast, titulo_afast, alerta_color = "🕒", "🕒 Último Afastamento Registrado", "#94a3b8"
                            if v_afast_desc.startswith("8"):
                                titulo_afast = "🕒 Último Afastamento Antes da Demissão"
                            elif "Ferias" in v_afast_desc:
                                icon_afast, titulo_afast, alerta_color = "🏖️", f"🏖️ Afastamento Ativo: {v_afast_desc}", "#3b82f6"
                            elif v_afast_desc not in ["1 - Trabalhando", "8 - Demitido"]:
                                icon_afast, titulo_afast, alerta_color = "🏥", f"🏥 Afastamento Ativo: {v_afast_desc}", "#facc15"

                            st.markdown(f"### <span>{titulo_afast}</span>", unsafe_allow_html=True)
                            st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                            ca1, ca2 = st.columns(2)
                            with ca1:
                                st.markdown('<p class="field-label">DATA DE INÍCIO</p>', unsafe_allow_html=True)
                                st.markdown(f'<p class="field-value" style="color:{alerta_color}; font-weight: bold;">{format_date_br(v_afast_data) or "Pendente"}</p>', unsafe_allow_html=True)
                            with ca2:
                                st.markdown('<p class="field-label">DESCRIÇÃO DO AFASTAMENTO</p>', unsafe_allow_html=True)
                                st.markdown(f'<p class="field-value" style="color:{alerta_color};">{(v_afast_desc or "Não Informado")}</p>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown("### 📜 Histórico de Situações (eSocial)")
                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        if not df_hist_sit.empty:
                            df_hist_sit_view = df_hist_sit.copy()
                            df_hist_sit_view['data_evento'] = pd.to_datetime(df_hist_sit_view['data_evento']).dt.strftime('%d/%m/%Y')
                            df_hist_sit_view.rename(columns={'data_evento': 'Data do Evento', 'descricao': 'Descrição da Situação'}, inplace=True)
                            st.dataframe(df_hist_sit_view[['Data do Evento', 'Descrição da Situação']], use_container_width=True, hide_index=True)
                        else:
                            st.info("Nenhum histórico de situação registrado na base de dados para este colaborador.")
                        st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown("### 🏦 Dados Bancários (PIX Principal)")
                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        if fin_data or (colab and hasattr(colab, 'chave_pix') and colab.chave_pix):
                            cf1, cf2 = st.columns(2)
                            with cf1:
                                st.markdown('<p class="field-label">BANCO</p>', unsafe_allow_html=True)
                                st.markdown(f'<p class="field-value">{(fin_data.get("banco") if fin_data else "") or "Não Informado"}</p>', unsafe_allow_html=True)
                            with cf2:
                                st.markdown('<p class="field-label">CHAVE PIX</p>', unsafe_allow_html=True)
                                st.markdown(f'<p class="field-value">{(fin_data.get("chave_pix") if fin_data else "Não Informado")}</p>', unsafe_allow_html=True)
                        else:
                            st.info("Nenhum dado bancário registrado.")
                        st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown("### 💰 Histórico Mensal de Prêmios e Folha")
                        if not df_hist.empty:
                            duplicatas = df_hist.groupby(['competencia', 'tipo_lancamento']).size().reset_index(name='contagem')
                            duplicatas = duplicatas[duplicatas['contagem'] > 1]
                            if not duplicatas.empty:
                                st.markdown('<div style="background-color: rgba(220, 38, 38, 0.15); border: 1px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 20px;">🛑 ALERTA DE AUDITORIA INTERNA: DUPLICIDADE DETETADA! Utilize o botão Corrigir Hist. e apague o valor para limpar.</div>', unsafe_allow_html=True)

                        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                        if not df_hist.empty:
                            cols_desejadas = ['competencia', 'tipo_lancamento', 'valor_lancamento', 'status_pagamento', 'retroativo_pago', 'data_pagamento']
                            cols_existentes = [c for c in cols_desejadas if c in df_hist.columns]
                            df_view = df_hist[cols_existentes].copy()
                            df_view['valor_lancamento'] = df_view['valor_lancamento'].apply(format_brl_number)
                            df_view.rename(columns={'competencia': 'Competência', 'tipo_lancamento': 'Tipo', 'valor_lancamento': 'Valor (R$)', 'status_pagamento': 'Status'}, inplace=True)
                            st.dataframe(df_view, use_container_width=True, hide_index=True)
                        else:
                            st.info("Nenhum histórico registrado na base de dados para este colaborador.")
                        st.markdown('</div>', unsafe_allow_html=True)

                        if st.session_state['status_acao'] is None:
                            cb1, cb2, cb3, cb4, cb5, cb6, cb7, cb8 = st.columns(8)
                            if cb1.button("✏️ Editar"): st.session_state['status_acao'] = 'solicitou_alterar'; st.rerun()
                            if cb2.button("➕ Pagamento"): st.session_state['status_acao'] = 'solicitou_lancamento_avulso'; st.rerun()
                            if cb3.button("🛠️ Corrigir"): st.session_state['status_acao'] = 'solicitou_corrigir_historico'; st.rerun()
                            if cb4.button("⏳ eSocial"): st.session_state['status_acao'] = 'solicitou_hist_esocial'; st.rerun()
                            if cb5.button("🛑 Demitir"): st.session_state['status_acao'] = 'solicitou_demissao'; st.rerun()
                            if cb6.button("🔄 Mesclar"): st.session_state['status_acao'] = 'solicitou_mesclar'; st.rerun()
                            if cb7.button("❌ Excluir"): st.session_state['status_acao'] = 'solicitou_excluir'; st.rerun()
                            if cb8.button("🧹 Fechar"):
                                st.session_state['busca_selecionada_id'] = None
                                st.session_state['status_acao'] = None
                                st.rerun()

                        if st.session_state['status_acao'] == 'solicitou_demissao':
                            st.warning("🛑 Registrar Demissão")
                            ja_demitido = pd.notna(colab.demissao)
                            nova_dem = st.text_input("Data de Demissão (Sem barras)", value=format_date_br(colab.demissao) if ja_demitido else "")
                            reverter = st.checkbox("Reverter Demissão (Tornar Ativo)", value=not ja_demitido)
                            c_bt1, c_bt2 = st.columns([1, 4])
                            if c_bt1.button("💾 Gravar Demissão", type="primary"):
                                with st.spinner("⏳ Gravando demissão..."):
                                    try:
                                        dt_nova = None if reverter else parse_br_date_smart(nova_dem)
                                        if not reverter and not dt_nova:
                                            st.error("⚠️ Data de demissão inválida.")
                                        else:
                                            dem_str = dt_nova.strftime('%Y-%m-%d') if dt_nova else None
                                            novo_status = '1 - Trabalhando' if reverter else '8 - Demitido'
                                            dt_hist_evento = dt_nova.strftime('%Y-%m-%d') if dt_nova else datetime.today().strftime('%Y-%m-%d')
                                            with engine.begin() as conn:
                                                conn.execute(text("UPDATE cadastro_geral_colaborador SET demissao = :d, status_esocial = :sit WHERE id = :id"), {"d": dem_str, "sit": novo_status, "id": str(colab_id)})
                                                conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento) VALUES (:id, :dt, :desc)"), {"id": str(colab_id), "dt": dt_hist_evento, "desc": novo_status})
                                            st.success("✅ Atualizado!")
                                            st.cache_data.clear()
                                            st.session_state['status_acao'] = None; st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar: {e}")
                            if c_bt2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                        if st.session_state['status_acao'] == 'solicitou_excluir':
                            st.warning(f"⚠️ Deseja excluir definitivamente {colab.nome} e todo o seu histórico?")
                            cx1, cx2 = st.columns(2)
                            if cx1.button("🔥 Sim, Excluir Tudo", type="primary"):
                                with st.spinner("⏳ Excluindo registro..."):
                                    try:
                                        with engine.begin() as conn:
                                            conn.execute(text("DELETE FROM historico_afastamentos WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                            conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                            conn.execute(text("DELETE FROM cadastro_financeiro_colaborador WHERE id_colaborador = :id"), {"id": str(colab_id)})
                                            conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": str(colab_id)})
                                        st.success("Excluído!")
                                        st.session_state['busca_selecionada_id'] = None
                                        st.session_state['status_acao'] = None
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {e}")
                            if cx2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                        if st.session_state['status_acao'] == 'solicitou_lancamento_avulso':
                            injetar_autofoco("av_comp_input")
                            st.info("➕ Inserção Avulsa (Com Validação e Anti-Duplicidade). Use CTRL + ENTER para salvar rápido.")
                            c_av1, c_av2, c_av3 = st.columns(3)
                            val_sugestao = format_brl_number(val_atual_base) if val_atual_base > 0 else ""
                            with c_av1: av_comp = st.text_input("Competência (MM/AAAA)", placeholder="Ex: 092025", key="av_comp_input")
                            with c_av2: av_tipo = st.selectbox("Tipo", ["Salário Mensal", "Prêmio ZAUT", "Férias", "Outros"])
                            with c_av3: av_valor = st.text_input("Valor (R$)", value=val_sugestao, placeholder="Digite o valor")
                            c_bt1, c_bt2 = st.columns([1, 4])
                            if c_bt1.button("💾 Salvar Lançamento", type="primary"):
                                with st.spinner("⏳ Salvando lançamento..."):
                                    try:
                                        vc = clean_money_to_db(av_valor)
                                        c_clean = format_competencia_smart(av_comp)
                                        if not c_clean or len(c_clean) < 6:
                                            st.error("⚠️ Competência inválida.")
                                        elif not vc:
                                            st.error("⚠️ O campo 'Valor' está vazio.")
                                        else:
                                            m_c, y_c = map(int, c_clean.split('/'))
                                            dt_comp = date(y_c, m_c, 1)
                                            bloqueado, msg_bloqueio = False, ""
                                            if pd.notna(colab.admissao) and dt_comp < date(pd.to_datetime(colab.admissao).year, pd.to_datetime(colab.admissao).month, 1):
                                                bloqueado, msg_bloqueio = True, "Anterior à admissão."
                                            if not bloqueado and pd.notna(colab.demissao) and dt_comp > date(pd.to_datetime(colab.demissao).year, pd.to_datetime(colab.demissao).month, 1):
                                                bloqueado, msg_bloqueio = True, "Colaborador demitido."
                                            if not bloqueado:
                                                with engine.connect() as conn_check:
                                                    df_check = pd.read_sql(text("SELECT competencia, tipo_lancamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id"), conn_check, params={"id": str(colab_id)})
                                                    if not df_check.empty:
                                                        df_check['competencia'] = df_check['competencia'].apply(format_competencia_smart)
                                                        if not df_check[(df_check['competencia'] == c_clean) & (df_check['tipo_lancamento'].str.lower() == av_tipo.lower())].empty:
                                                            bloqueado, msg_bloqueio = True, f"Já existe '{av_tipo}' para {c_clean}."
                                            if bloqueado:
                                                st.error(f"🛑 {msg_bloqueio}")
                                            else:
                                                with engine.begin() as conn:
                                                    conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, :tipo, :val, 'Pago')"), {"id": str(colab_id), "comp": c_clean, "tipo": av_tipo, "val": float(vc)})
                                                st.success("Salvo!")
                                                st.cache_data.clear()
                                                st.session_state['status_acao'] = None; st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao validar datas: {e}")
                            if c_bt2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                        if st.session_state['status_acao'] == 'solicitou_corrigir_historico':
                            injetar_autofoco("novo_val_input")
                            st.info("🛠️ Editor de Histórico (Pagamentos). Use CTRL + ENTER para salvar rápido.")
                            if not df_hist.empty:
                                try:
                                    opcoes_hist = {f"ID: {row['id']} | Comp: {row['competencia']} | Tipo: {row['tipo_lancamento']} | Val: R$ {format_brl_number(row['valor_lancamento'])}": row['id'] for _, row in df_hist.iterrows()}
                                    id_alvo = opcoes_hist[st.selectbox("Selecione o registo:", list(opcoes_hist.keys()))]
                                    novo_val = st.text_input("Novo Valor", placeholder="Deixe vazio para deletar", key="novo_val_input")
                                    ch1, ch2 = st.columns([1, 4])
                                    if ch1.button("💾 Salvar / Atualizar", type="primary"):
                                        with st.spinner("⏳ Atualizando histórico..."):
                                            try:
                                                vc = clean_money_to_db(novo_val)
                                                with engine.begin() as conn:
                                                    if not vc or float(vc) == 0:
                                                        conn.execute(text("DELETE FROM historico_premiacoes_e_folha WHERE id = :id"), {"id": id_alvo})
                                                        st.success("Registo zerado e removido!")
                                                    else:
                                                        conn.execute(text("UPDATE historico_premiacoes_e_folha SET valor_lancamento = :v WHERE id = :id"), {"v": float(vc), "id": id_alvo})
                                                        st.success("Corrigido!")
                                                st.cache_data.clear()
                                                st.session_state['status_acao'] = None; st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro: {e}")
                                    if ch2.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao carregar lista: {e}")
                            else:
                                st.warning("Nenhum histórico para corrigir.")

                        if st.session_state['status_acao'] == 'solicitou_alterar':
                            injetar_autofoco("edit_id_input")
                            st.info("📝 Modo de Edição Ativo. Aperte ENTER para pular campos. Use CTRL + ENTER para salvar rápido.")
                            cargo_idx = LISTA_CARGOS.index(str(colab.cargo).upper().strip()) if str(colab.cargo).upper().strip() in LISTA_CARGOS else (len(LISTA_CARGOS)-1)
                            sit_idx = LISTA_SITUACOES_ESOCIAL.index(v_sit_atual) if v_sit_atual in LISTA_SITUACOES_ESOCIAL else 0
                            ce1, ce2 = st.columns(2)
                            with ce1:
                                edit_id = st.text_input("ID / Matrícula", value=str(colab.id), key="edit_id_input")
                                edit_nome = st.text_input("Nome Completo", value=str(colab.nome))
                                edit_cpf = st.text_input("CPF", value=format_cpf(colab.cpf) if colab.cpf else "")
                                edit_adm = st.text_input("Data de Admissão (Sem barras)", value=format_date_br(colab.admissao))
                                edit_sal_mes = st.text_input("Salário-Mês Base", value=str(colab.salario_mes_12_24) if colab.salario_mes_12_24 else "")
                            with ce2:
                                sel_cargo = st.selectbox("Cargo", LISTA_CARGOS, index=cargo_idx)
                                edit_cargo = st.text_input("Digite o Cargo", value=str(colab.cargo) if sel_cargo == "OUTRO (DIGITAR MANUALMENTE)" else sel_cargo)
                                sel_sit = st.selectbox("Situação (eSocial)", LISTA_SITUACOES_ESOCIAL, index=sit_idx)
                                edit_pix = st.text_input("Chave PIX", value=str(fin_data.get("chave_pix")) if fin_data and fin_data.get("chave_pix") else "")
                                edit_sal_hora = st.text_input("Salário-Hora Base", value="Automático (Base / 220)", disabled=True)
                            st.markdown("##### 📅 Datas da Situação Atual")
                            ci1, ci2 = st.columns(2)
                            st.info("A edição de datas de afastamento/retorno deve ser feita na seção 'Histórico de Situações (eSocial)'.")
                            if st.button("Confirmar e Salvar Alterações", type="primary"):
                                with st.spinner("⏳ Salvando alterações..."):
                                    try:
                                        if not edit_id.strip() or not edit_nome.strip():
                                            st.error("ID e Nome são obrigatórios.")
                                        else:
                                            dt_a = parse_br_date_smart(edit_adm)
                                            adm_str = dt_a.strftime('%Y-%m-%d') if dt_a else None
                                            sm_val = clean_money_to_db(edit_sal_mes)
                                            sh_val = str(float(sm_val)/220.0) if sm_val is not None else None
                                            with engine.begin() as conn:
                                                conn.execute(text("UPDATE cadastro_geral_colaborador SET id=:nid, nome=:n, cpf=:c, cargo=:ca, admissao=:ad, status_esocial=:sit, salario_mes_12_24=:sm, salario_hora_12_24=:sh WHERE id=:oid"), {"nid": edit_id.strip(), "n": edit_nome, "c": edit_cpf, "ca": edit_cargo, "ad": adm_str, "sit": sel_sit, "sm": sm_val, "sh": sh_val, "oid": str(colab_id)})

                                                if fin_data:
                                                    conn.execute(text("UPDATE cadastro_financeiro_colaborador SET chave_pix = :pix WHERE id_colaborador = :id"), {"pix": edit_pix, "id": edit_id.strip()})
                                                else:
                                                    conn.execute(text("INSERT INTO cadastro_financeiro_colaborador (id_colaborador, chave_pix) VALUES (:id, :pix)"), {"id": edit_id.strip(), "pix": edit_pix})

                                                if edit_id.strip() != str(colab_id):
                                                    conn.execute(text("UPDATE historico_premiacoes_e_folha SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})
                                                    conn.execute(text("UPDATE historico_afastamentos SET id_colaborador = :nid WHERE id_colaborador = :oid"), {"nid": edit_id.strip(), "oid": str(colab_id)})

                                                if sel_sit != v_sit_atual:
                                                    dt_hist_evento = datetime.today().date()
                                                    conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento) VALUES (:id, :dt, :desc)"), {"id": edit_id.strip(), "dt": dt_hist_evento.strftime('%Y-%m-%d'), "desc": sel_sit})

                                                if sm_val:
                                                    existe_hist = conn.execute(text("SELECT id FROM historico_premiacoes_e_folha WHERE id_colaborador = :id AND tipo_lancamento ILIKE '%Salário%' ORDER BY id DESC LIMIT 1"), {"id": edit_id.strip()}).fetchone()
                                                    if not existe_hist:
                                                        comp_str = dt_a.strftime('%m/%Y') if dt_a else datetime.today().strftime('%m/%Y')
                                                        conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": edit_id.strip(), "comp": comp_str, "val": float(sm_val)})
                                                    else:
                                                        conn.execute(text("UPDATE historico_premiacoes_e_folha SET valor_lancamento = :val WHERE id = :id_hist"), {"val": float(sm_val), "id_hist": existe_hist[0]})
                                            st.success("Salvo!")
                                            st.cache_data.clear()
                                            st.session_state['busca_selecionada_id'] = edit_id.strip()
                                            st.session_state['status_acao'] = None
                                            st.rerun()
                                    except Exception as e:
                                        error_msg = str(e).lower()
                                        if "unique constraint" in error_msg or "duplicate key" in error_msg:
                                            st.error(f"⚠️ AÇÃO BLOQUEADA (DUPLICIDADE): O ID/Matrícula '{edit_id.strip()}' já pertence a outro colaborador!")
                                        else:
                                            st.error(f"Erro no banco de dados: {e}")
                            if st.button("Cancelar"): st.session_state['status_acao'] = None; st.rerun()

                except Exception as e:
                    st.error(f"Erro no processamento da ficha: {e}")

    elif sub_menu == "➕ Novo Cadastro":
        injetar_autofoco("n_id_input")
        st.subheader("Inserir Novo Colaborador")
        st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
        cn1, cn2 = st.columns(2)
        with cn1:
            n_id = st.text_input("ID / Matrícula", key="n_id_input")
            n_cpf = st.text_input("CPF")
            n_adm_str = st.text_input("Admissão (Pode digitar sem barras)", placeholder="Ex: 01072025")
            n_sal_mes = st.text_input("Salário-Mês")
        with cn2:
            n_nome = st.text_input("Nome Completo")
            s_c = st.selectbox("Cargo", LISTA_CARGOS)
            n_cargo = st.text_input("Digite o Cargo") if s_c == "OUTRO (DIGITAR MANUALMENTE)" else s_c
            n_sit = st.selectbox("Situação Inicial", LISTA_SITUACOES_ESOCIAL, index=0)
            n_sal_hora = st.text_input("Salário-Hora", value="Automático (Base / 220)", disabled=True)
            n_chave_pix = st.text_input("Chave PIX (Opcional)")
        st.markdown('</div>', unsafe_allow_html=True)
        st.info("Aperte ENTER para pular campos. Use CTRL + ENTER para salvar direto no banco de dados.")
        if st.button("💾 Salvar Registro no Sistema", type="primary"):
            with st.spinner("⏳ Salvando novo registro..."):
                try:
                    dt_a = parse_br_date_smart(n_adm_str)
                    sm_val = clean_money_to_db(n_sal_mes)
                    sh_val = str(float(sm_val)/220.0) if sm_val is not None else None
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome, cpf, cargo, admissao, status_esocial, salario_mes_12_24, salario_hora_12_24) VALUES (:id, :n, :c, :ca, :ad, :sit, :sm, :sh)"), {"id": str(n_id), "n": str(n_nome), "c": str(n_cpf), "ca": str(n_cargo), "ad": dt_a.strftime('%Y-%m-%d') if dt_a else None, "sit": n_sit, "sm": sm_val, "sh": sh_val})

                        if n_chave_pix.strip():
                            conn.execute(text("INSERT INTO cadastro_financeiro_colaborador (id_colaborador, chave_pix) VALUES (:id, :pix)"), {"id": str(n_id), "pix": n_chave_pix.strip()})

                        dt_hist_evento = dt_a.strftime('%Y-%m-%d') if dt_a else datetime.today().strftime('%Y-%m-%d')
                        conn.execute(text("INSERT INTO historico_afastamentos (id_colaborador, data_inicio, tipo_afastamento) VALUES (:id, :dt, :desc)"), {"id": str(n_id), "dt": dt_hist_evento, "desc": n_sit})
                        if sm_val:
                            comp_str = dt_a.strftime('%m/%Y') if dt_a else datetime.today().strftime('%m/%Y')
                            conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id, :comp, 'Salário Mensal', :val, 'Pago')"), {"id": str(n_id), "comp": comp_str, "val": float(sm_val)})
                    st.success("Salvo!")
                    st.cache_data.clear()
                    st.session_state['redirect_to_consulta'] = True
                    st.rerun()
                except Exception as e:
                    error_msg = str(e).lower()
                    if "unique constraint" in error_msg or "duplicate key" in error_msg:
                        st.error(f"⚠️ AÇÃO BLOQUEADA (DUPLICIDADE): O ID/Matrícula '{str(n_id).strip()}' já está registado!")
                    else:
                        st.error(f"Erro ao salvar: {e}")
