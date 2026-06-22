import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime

# ==========================================
# FUNÇÕES DE CACHE E BUSCA DE DADOS
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_iniciais(_engine):
    try:
        with _engine.connect() as conn:
            # 1. Colaboradores
            df_colab = pd.read_sql("SELECT id, nome, cpf, cargo, salario_mes_12_24 FROM cadastro_geral_colaborador ORDER BY nome", conn)
            
            # 2. Obras (Unidades de Negócio)
            try:
                df_obras = pd.read_sql("SELECT id, nome_unidade FROM unidade_negocio ORDER BY nome_unidade", conn)
                lista_obras = df_obras['nome_unidade'].tolist() if not df_obras.empty else ["Construart (Padrão)"]
            except:
                lista_obras = ["Construart (Padrão)"]
            
            # 3. Prêmios Base
            try:
                df_base_premios = pd.read_sql("SELECT id, descricao_premio, valor_padrao FROM premios_zaut ORDER BY descricao_premio", conn)
                dict_premios = dict(zip(df_base_premios['descricao_premio'], df_base_premios['valor_padrao'])) if not df_base_premios.empty else {"Prêmio Manual": 0.0}
            except:
                dict_premios = {"Prêmio Extra": 100.0, "Prêmio Assiduidade": 50.0, "Outro (Digitar Manual)": 0.0}
            
        return df_colab, lista_obras, dict_premios
    except Exception as e:
        st.error(f"Erro ao carregar bases: {e}")
        return pd.DataFrame(), ["Erro"], {"Erro": 0.0}

# ==========================================
# RENDERIZAÇÃO DA PÁGINA
# ==========================================
# Assinatura garantida para funcionar com a sua chamada em app.py
def render(engine, format_brl_number, format_currency_brl, clean_money_to_db, LISTA_SERVICOS_PREMIO):
    st.title("🏆 Gestão de Prêmios ZAUT")
    st.markdown("Módulo automatizado para lançamento, consulta e transferência de prêmios e obras.")

    tab1, tab2, tab3 = st.tabs(["Lançar Prêmio (Salvar)", "Consultar / Excluir", "Transferência de Obra"])

    df_colab, lista_obras, dict_premios = carregar_dados_iniciais(engine)

    opcoes_colab = ["Selecione um Colaborador..."]
    mapa_colab_dados = {}
    if not df_colab.empty:
        for _, row in df_colab.iterrows():
            linha_label = f"ID: {row['id']} | {row['nome']} | CPF: {row['cpf']}"
            opcoes_colab.append(linha_label)
            mapa_colab_dados[linha_label] = {
                "id": str(row['id']),
                "nome": str(row['nome']),
                "cpf": str(row['cpf']) if pd.notna(row['cpf']) else "",
                "cargo": str(row['cargo']) if pd.notna(row['cargo']) else "",
                "salario_mes": float(row['salario_mes_12_24']) if pd.notna(row['salario_mes_12_24']) else 0.0
            }

    # ==========================================
    # ABA 1: LANÇAMENTO AUTOMATIZADO
    # ==========================================
    with tab1:
        st.subheader("Novo Lançamento Inteligente")
        colaborador_selecionado = st.selectbox("Buscar Colaborador (ID, Nome ou CPF):", opcoes_colab)

        if colaborador_selecionado != "Selecione um Colaborador...":
            dados_c = mapa_colab_dados[colaborador_selecionado]
            sal_hora_auto = dados_c["salario_mes"] / 220.0 if dados_c["salario_mes"] > 0 else 0.0

            st.markdown("---")
            with st.form("form_lancamento_premio", clear_on_submit=True):
                st.markdown("#### 👤 Dados do Colaborador (Automático)")
                col1, col2, col3, col4 = st.columns(4)
                codigo = col1.text_input("Código", value=dados_c["id"], disabled=True)
                nome = col2.text_input("Nome", value=dados_c["nome"], disabled=True)
                cpf = col3.text_input("CPF", value=dados_c["cpf"], disabled=True)
                cargo = col4.text_input("Cargo", value=dados_c["cargo"], disabled=True)

                st.markdown("#### 🏢 Alocação e Classificação")
                col5, col6, col7 = st.columns(3)
                obra = col5.selectbox("Obra / Centro de Custo", lista_obras)
                competencia = col6.text_input("Competência (Mês/Ano)", value=datetime.today().strftime('%m/%Y'))
                
                lista_nome_premios = list(dict_premios.keys())
                premio_selecionado = col7.selectbox("Descrição do Prêmio ZAUT", lista_nome_premios)

                st.markdown("#### 💰 Financeiro")
                col8, col9, col10 = st.columns(3)
                salario_mes = col8.number_input("Salário Mês Base (R$)", value=dados_c["salario_mes"], min_value=0.0, format="%.2f")
                salario_hora = col9.number_input("Salário Hora Base (R$)", value=sal_hora_auto, min_value=0.0, format="%.2f")
                total_hp = col10.number_input("Total HP a adicionar", min_value=0.0, format="%.2f")

                col11, col12, col13 = st.columns(3)
                valor_padrao_premio = dict_premios.get(premio_selecionado, 0.0)
                valor_hp_em_R = col11.number_input("Prêmio Fixo em R$", value=float(valor_padrao_premio), min_value=0.0, format="%.2f")
                taxa_zaut = col12.number_input("Taxa Zaut (R$)", value=1.00, format="%.2f")
                chave_pix = col13.text_input("Chave PIX")

                observacoes = st.text_area("Observações")
                submit_button = st.form_submit_button("Salvar Lançamento ZAUT", type="primary", use_container_width=True)

                if submit_button:
                    if salario_hora <= 0 and valor_hp_em_R > 0:
                        st.error("Para converter prêmio em horas, o 'Salário Hora' precisa ser maior que zero.")
                    else:
                        total_hp_convertido = (valor_hp_em_R / salario_hora) if salario_hora > 0 else 0.0
                        soma_total_hp = total_hp + total_hp_convertido
                        valor_total_premio = (soma_total_hp * salario_hora) + taxa_zaut

                        query_insert = text("""
                            INSERT INTO gestao_premios_zaut (
                                codigo, nome, cargo, cpf, obra, salario_mes, salario_hora, 
                                total_hp, total_hp_convertido, "valor_hp_em_R$", soma_total_hp, 
                                "valor_total_premio_R$", taxa_de_manutencao_zaut, 
                                lista_descricao_premio, chave_pix, observacoes, competencia
                            ) VALUES (
                                :codigo, :nome, :cargo, :cpf, :obra, :salario_mes, :salario_hora, 
                                :total_hp, :total_hp_convertido, :valor_hp_em_R, :soma_total_hp, 
                                :valor_total_premio, :taxa_zaut, :lista_descricao_premio, 
                                :chave_pix, :observacoes, :competencia
                            )
                        """)

                        parametros = {
                            "codigo": str(codigo), "nome": nome, "cargo": cargo, "cpf": cpf, 
                            "obra": obra, "salario_mes": salario_mes, "salario_hora": salario_hora,
                            "total_hp": total_hp, "total_hp_convertido": total_hp_convertido,
                            "valor_hp_em_R": valor_hp_em_R, "soma_total_hp": soma_total_hp,
                            "valor_total_premio": valor_total_premio, "taxa_zaut": taxa_zaut,
                            "lista_descricao_premio": premio_selecionado, "chave_pix": chave_pix,
                            "observacoes": observacoes, "competencia": competencia
                        }

                        try:
                            with engine.begin() as conn:
                                conn.execute(query_insert, parametros)
                            st.success(f"Lançamento ZAUT salvo para: {nome}")
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")

    # ==========================================
    # ABA 2: CONSULTAR E EXCLUIR
    # ==========================================
    with tab2:
        st.subheader("Consultar Colaborador")
        busca_codigo = st.text_input("Digite o ID (Código) do Colaborador para busca:")

        if st.button("Consultar Lançamentos"):
            if busca_codigo:
                try:
                    query_select = text("SELECT * FROM gestao_premios_zaut WHERE codigo = :codigo")
                    df_busca = pd.read_sql(query_select, con=engine, params={"codigo": str(busca_codigo)})

                    if not df_busca.empty:
                        colunas_moeda = ['salario_mes', 'salario_hora', 'valor_hp_em_R$', 'valor_total_premio_R$', 'taxa_de_manutencao_zaut']
                        for col in colunas_moeda:
                            if col in df_busca.columns:
                                df_busca[col] = df_busca[col].apply(format_currency_brl)
                        st.dataframe(df_busca, use_container_width=True)
                    else:
                        st.warning("Nenhum prêmio encontrado para esta matrícula.")
                except Exception as e:
                    st.error(f"Erro na consulta: {e}")
            else:
                st.warning("Informe um código para consultar.")

        st.markdown("---")
        st.subheader("Excluir Registro de Prêmio")
        codigo_exclusao = st.text_input("Código do Colaborador para exclusão:")
        competencia_exclusao = st.text_input("Competência a excluir (ex: 06/2026):")
        confirmar_exclusao = st.checkbox("Confirmo a exclusão permanente deste prêmio.")

        if st.button("Excluir Registro", type="primary"):
            if codigo_exclusao and competencia_exclusao and confirmar_exclusao:
                try:
                    query_delete = text("DELETE FROM gestao_premios_zaut WHERE codigo = :codigo AND competencia = :competencia")
                    with engine.begin() as conn:
                        result = conn.execute(query_delete, {"codigo": str(codigo_exclusao), "competencia": competencia_exclusao})
                        if result.rowcount > 0:
                            st.success("Prêmio excluído.")
                        else:
                            st.warning("Prêmio não encontrado.")
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Preencha todos os campos e confirme a exclusão.")

    # ==========================================
    # ABA 3: TRANSFERÊNCIA DE OBRA
    # ==========================================
    with tab3:
        st.subheader("Transferir Obra do Colaborador")
        transf_codigo = st.selectbox("Selecione o Colaborador:", opcoes_colab, key="sel_transf")
        
        if transf_codigo != "Selecione um Colaborador...":
            id_transf_limpo = mapa_colab_dados[transf_codigo]["id"]
            obra_origem = st.selectbox("Obra de Origem:", lista_obras, key="obra_orig")
            obra_destino = st.selectbox("Nova Obra (Destino):", lista_obras, key="obra_dest")

            if st.button("Executar Transferência", type="primary"):
                if obra_origem != obra_destino:
                    try:
                        nota = f" [Transferido de {obra_origem} para {obra_destino} em {datetime.today().strftime('%d/%m/%Y')}]"
                        query_update = text("UPDATE gestao_premios_zaut SET obra = :obra_destino, observacoes = COALESCE(observacoes, '') || :nota WHERE codigo = :codigo")
                        with engine.begin() as conn:
                            res = conn.execute(query_update, {"obra_destino": obra_destino, "nota": nota, "codigo": id_transf_limpo})
                            if res.rowcount > 0:
                                st.success("Transferência concluída!")
                            else:
                                st.warning("Histórico não encontrado.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Obras de origem e destino devem ser diferentes.")    
