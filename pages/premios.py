
import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import calendar

def render(engine, format_brl_number, format_currency_brl, clean_money_to_db, injetar_autofoco, LISTA_SERVICOS_PREMIO):
    st.title("🏆 Lançamento de Prêmios (ZAUT)")
    col_comp1, col_comp2 = st.columns([1, 3])
    with col_comp1:
        hoje = datetime.today()
        meses = [f"{str(m).zfill(2)}/{hoje.year}" for m in range(1, 13)] + [f"{str(m).zfill(2)}/{hoje.year+1}" for m in range(1, 13)]
        comp_sel = st.selectbox("Selecione a Competência:", meses, index=(hoje.month - 1))
    st.markdown("---")

    try:
        df_colabs = pd.read_sql("SELECT id, nome, cargo, admissao, demissao, data_afastamento, data_retorno, salario_mes_12_24, situacao FROM cadastro_geral_colaborador ORDER BY nome ASC", engine)
        data_inicio_comp = pd.Timestamp(year=int(comp_sel.split('/')[1]), month=int(comp_sel.split('/')[0]), day=1)
        data_fim_comp = pd.Timestamp(year=int(comp_sel.split('/')[1]), month=int(comp_sel.split('/')[0]), day=calendar.monthrange(int(comp_sel.split('/')[1]), int(comp_sel.split('/')[0]))[1])

        colabs_elegiveis = []
        for _, row in df_colabs.iterrows():
            if pd.notna(row['demissao']) and pd.to_datetime(row['demissao']) < data_inicio_comp: continue
            dt_afast = pd.to_datetime(row['data_afastamento']) if pd.notna(row['data_afastamento']) else None
            dt_ret = pd.to_datetime(row['data_retorno']) if pd.notna(row['data_retorno']) else None
            if dt_afast and dt_afast < data_inicio_comp and (dt_ret is None or dt_ret > data_fim_comp): continue
            try:
                sal_base_float = float(str(row['salario_mes_12_24']).upper().replace('R$', '').replace('.', '').replace(',', '.').strip()) if row['salario_mes_12_24'] else 0.0
            except:
                sal_base_float = 0.0
            if sal_base_float == 0.0:
                try:
                    with engine.connect() as conn2:
                        hs = conn2.execute(text("SELECT valor_lancamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id AND tipo_lancamento ILIKE '%Salário%' ORDER BY id DESC LIMIT 1"), {"id": str(row['id'])}).fetchone()
                        if hs: sal_base_float = float(hs[0])
                except: pass
            colabs_elegiveis.append({"id": str(row['id']), "nome": str(row['nome']), "sal_hora": sal_base_float / 220.0 if sal_base_float > 0 else 0.0})

        if not colabs_elegiveis:
            st.warning("Nenhum colaborador elegível para esta competência.")
        else:
            aba_lote, aba_ind = st.tabs(["📊 Planilha de Lote Rápido", "👤 Lançamento Individual"])

            with aba_lote:
                df_lote = pd.DataFrame(colabs_elegiveis)
                df_lote['Horas Prêmio (HP)'] = 0.00
                df_lote['Descrição do Serviço'] = None
                edited_df = st.data_editor(
                    df_lote,
                    column_config={
                        "id": st.column_config.TextColumn("Matrícula", disabled=True),
                        "nome": st.column_config.TextColumn("Colaborador", disabled=True),
                        "sal_hora": st.column_config.NumberColumn("Valor Hora", format="R$ %.2f", disabled=True),
                        "Horas Prêmio (HP)": st.column_config.NumberColumn("Total HP", min_value=0.0, format="%.2f", step=1.0),
                        "Descrição do Serviço": st.column_config.SelectboxColumn("Serviço", options=LISTA_SERVICOS_PREMIO)
                    },
                    disabled=["id", "nome", "sal_hora"],
                    hide_index=True,
                    use_container_width=True,
                    key="editor_lote_zaut"
                )
                c_btn_lt1, c_btn_lt2 = st.columns([1, 4])
                if c_btn_lt1.button("💾 Salvar Lote Inteiro", type="primary"):
                    lancamentos = edited_df[edited_df['Horas Prêmio (HP)'] > 0]
                    if lancamentos.empty:
                        st.warning("Nenhuma hora preenchida.")
                    else:
                        sucessos, erros = 0, 0
                        with engine.begin() as conn:
                            for _, r in lancamentos.iterrows():
                                try:
                                    conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_c, :comp, :tipo, :val, 'Lançado')"), {
                                        "id_c": str(r['id']),
                                        "comp": comp_sel,
                                        "tipo": f"Prêmio: {r['Descrição do Serviço'] or 'PRÊMIO PRODUÇÃO (ZAUT)'} (Horas: {r['Horas Prêmio (HP)']})",
                                        "val": (float(r['sal_hora']) * float(r['Horas Prêmio (HP)'])) + 1.00
                                    })
                                    sucessos += 1
                                except: erros += 1
                        if sucessos > 0:
                            st.success(f"✅ {sucessos} recibos gerados.")
                            del st.session_state['editor_lote_zaut']
                            st.rerun()
                        if erros > 0:
                            st.error(f"{erros} erros.")
                if c_btn_lt2.button("❌ Cancelar / Limpar Planilha", key="btn_canc_lote"):
                    del st.session_state['editor_lote_zaut']
                    st.rerun()

            with aba_ind:
                opcoes_dropdown = {f"{c['nome']} (ID: {c['id']})": c for c in colabs_elegiveis}
                colab_escolhido = st.selectbox("Selecione o Colaborador:", list(opcoes_dropdown.keys()))
                dados_c = opcoes_dropdown[colab_escolhido]
                try:
                    df_ja_lancado = pd.read_sql(text("SELECT tipo_lancamento, valor_lancamento, status_pagamento FROM historico_premiacoes_e_folha WHERE id_colaborador = :id_c AND competencia = :comp"), engine, params={"id_c": dados_c['id'], "comp": comp_sel})
                    if not df_ja_lancado.empty:
                        df_jl_view = df_ja_lancado.copy()
                        df_jl_view['valor_lancamento'] = df_jl_view['valor_lancamento'].apply(format_currency_brl)
                        st.dataframe(df_jl_view.rename(columns={'tipo_lancamento': 'Descrição do Prêmio', 'valor_lancamento': 'Valor', 'status_pagamento': 'Status'}), use_container_width=True, hide_index=True)
                except: pass

                if st.session_state.get('zaut_acao') != 'lancando':
                    if st.button(f"➕ Iniciar Lançamento para {dados_c['nome']}", type="primary"):
                        st.session_state['zaut_acao'] = 'lancando'
                        st.rerun()
                else:
                    injetar_autofoco(pular_busca=False, painel="zaut_individual")
                    st.markdown('<div class="panel-glass">', unsafe_allow_html=True)
                    sal_hora_base = dados_c['sal_hora']
                    if sal_hora_base == 0.0:
                        sal_hora_manual = st.text_input("Valor Hora (R$)", key="k_sh_manual", placeholder="Ex: 9,38")
                        try:
                            sal_hora_base = float(clean_money_to_db(sal_hora_manual)) if clean_money_to_db(sal_hora_manual) else 0.0
                        except:
                            sal_hora_base = 0.0
                    else:
                        st.markdown(f"**Valor Hora Calculado:** R$ {format_brl_number(sal_hora_base)}")

                    cli1, cli2 = st.columns(2)
                    with cli1:
                        hp_ind = st.text_input("Horas", key="k_hpi")
                    with cli2:
                        desc_ind = st.selectbox("Serviço", LISTA_SERVICOS_PREMIO, key="k_di")
                        desc_final_str = st.text_input("Especificar:", key="k_d_outro") if desc_ind == "OUTRO (DIGITAR MANUALMENTE)" else desc_ind

                    try:
                        hp_ind_float = float(clean_money_to_db(hp_ind)) if clean_money_to_db(hp_ind) else 0.0
                    except:
                        hp_ind_float = 0.0

                    val_final_ind = (sal_hora_base * hp_ind_float) + 1.00 if hp_ind_float > 0 else 0.00
                    if hp_ind_float > 0 and sal_hora_base > 0:
                        st.markdown(f'<p class="field-highlight">R$ {format_brl_number(val_final_ind)}</p>', unsafe_allow_html=True)

                    st.info("Aperte ENTER para pular campos. Use CTRL + ENTER para salvar rápido.")
                    c_btn_i1, c_btn_i2 = st.columns([1, 4])
                    if c_btn_i1.button("💾 Gravar", type="primary", key="btn_ind_gravar"):
                        if hp_ind_float <= 0 or sal_hora_base <= 0 or not desc_final_str.strip():
                            st.error("⚠️ Dados inválidos.")
                        else:
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO historico_premiacoes_e_folha (id_colaborador, competencia, tipo_lancamento, valor_lancamento, status_pagamento) VALUES (:id_c, :comp, :tipo, :val, 'Lançado')"), {
                                    "id_c": dados_c['id'],
                                    "comp": comp_sel,
                                    "tipo": f"Prêmio: {desc_final_str} (Horas: {hp_ind_float})",
                                    "val": val_final_ind
                                })
                            st.success("✅ Gravado!")
                            for k in ['k_hpi', 'k_sh_manual', 'k_d_outro', 'zaut_acao']:
                                st.session_state.pop(k, None)
                            st.rerun()
                    if c_btn_i2.button("❌ Cancelar", key="btn_ind_fechar"):
                        for k in ['k_hpi', 'k_sh_manual', 'k_d_outro', 'zaut_acao']:
                            st.session_state.pop(k, None)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro: {e}")
