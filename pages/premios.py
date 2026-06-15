import streamlit as st
import pandas as pd
from sqlalchemy import text

def render(engine, *args, **kwargs):
    st.title("Gestão de Prêmios Zaut")
    st.markdown("Módulo para lançamento manual, consulta, exclusão e transferência de colaboradores.")

    tab1, tab2, tab3 = st.tabs(["Lançar Prêmio (Salvar)", "Consultar / Excluir", "Transferência de Obra"])

    # ==========================================
    # ABA 1: LANÇAMENTO MANUAL (SALVAR)
    # ==========================================
    with tab1:
        st.subheader("Novo Lançamento de Prêmio")

        with st.form("form_lancamento_premio", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            codigo = col1.text_input("Código do Colaborador (Texto)")
            nome = col2.text_input("Nome Completo")
            cpf = col3.text_input("CPF")

            col4, col5, col6 = st.columns(3)
            cargo = col4.text_input("Cargo")
            obra = col5.text_input("Obra", value="Construart")
            competencia = col6.text_input("Competência (Mês/Ano)", value="01/2026")

            st.markdown("#### Dados Financeiros e Horas")
            col7, col8, col9 = st.columns(3)
            salario_mes = col7.number_input("Salário Mês (R$)", min_value=0.0, format="%.2f")
            salario_hora = col8.number_input("Salário Hora (R$)", min_value=0.0, format="%.2f")
            total_hp = col9.number_input("Total HP (Horas)", min_value=0.0, format="%.2f")

            col10, col11, col12 = st.columns(3)
            valor_hp_em_R = col10.number_input("Valor HP em R$ (Ex: 45.00)", min_value=0.0, format="%.2f")
            taxa_zaut = col11.number_input("Taxa Manutenção Zaut (R$)", value=1.00, format="%.2f")
            chave_pix = col12.text_input("Chave PIX")

            lista_descricao_premio = st.text_input("Descrição do Prêmio (Campo Digitável)")
            observacoes = st.text_area("Observações")

            submit_button = st.form_submit_button("Salvar Lançamento", type="primary")

            if submit_button:
                if not codigo or not nome:
                    st.error("Os campos 'Código' e 'Nome' são obrigatórios.")
                elif salario_hora <= 0 and valor_hp_em_R > 0:
                    st.error("Para converter 'Valor HP em R$', o 'Salário Hora' deve ser maior que zero.")
                else:
                    # Execução das Regras de Negócio (Cálculos)
                    total_hp_convertido = (valor_hp_em_R / salario_hora) if salario_hora > 0 else 0.0
                    soma_total_hp = total_hp + total_hp_convertido
                    valor_total_premio = (soma_total_hp * salario_hora) + taxa_zaut

                    # Preparação dos dados para inserção no Supabase
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
                        "lista_descricao_premio": lista_descricao_premio, "chave_pix": chave_pix,
                        "observacoes": observacoes, "competencia": competencia
                    }

                    try:
                        with engine.begin() as conn:
                            conn.execute(query_insert, parametros)
                        st.success(f"Lançamento salvo com sucesso para o colaborador: {nome}")
                        st.info(f"Cálculos aplicados: HP Convertido ({total_hp_convertido:.2f}) | Soma HP ({soma_total_hp:.2f}) | Prêmio Total (R$ {valor_total_premio:.2f})")
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados. Detalhe: {e}")

    # ==========================================
    # ABA 2: CONSULTAR E EXCLUIR
    # ==========================================
    with tab2:
        st.subheader("Consultar Colaborador")
        busca_codigo = st.text_input("Digite o Código do Colaborador para busca:")

        if st.button("Consultar"):
            if busca_codigo:
                try:
                    query_select = text("SELECT * FROM gestao_premios_zaut WHERE codigo = :codigo")
                    df_busca = pd.read_sql(query_select, con=engine, params={"codigo": str(busca_codigo)})

                    if not df_busca.empty:
                        # Formatação visual de moeda para 2 casas decimais
                        colunas_moeda = ['salario_mes', 'salario_hora', 'valor_hp_em_R$', 'valor_total_premio_R$', 'taxa_de_manutencao_zaut']
                        for col in colunas_moeda:
                            if col in df_busca.columns:
                                df_busca[col] = df_busca[col].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                        st.dataframe(df_busca, use_container_width=True)
                    else:
                        st.warning("Nenhum registro encontrado para este código.")
                except Exception as e:
                    st.error(f"Erro na consulta: {e}")
            else:
                st.warning("Informe um código para consultar.")

        st.markdown("---")
        st.subheader("Excluir Registro")
        codigo_exclusao = st.text_input("Código do Colaborador para exclusão:")
        competencia_exclusao = st.text_input("Competência do registro a excluir (ex: 01/2026):")

        # Trava de segurança exigida para exclusão
        confirmar_exclusao = st.checkbox("Confirmo que desejo excluir este registro permanentemente.")

        if st.button("Excluir Registro", type="primary"):
            if codigo_exclusao and competencia_exclusao:
                if confirmar_exclusao:
                    try:
                        query_delete = text("DELETE FROM gestao_premios_zaut WHERE codigo = :codigo AND competencia = :competencia")
                        with engine.begin() as conn:
                            result = conn.execute(query_delete, {"codigo": str(codigo_exclusao), "competencia": competencia_exclusao})
                            if result.rowcount > 0:
                                st.success("Registro excluído com sucesso.")
                            else:
                                st.warning("Nenhum registro encontrado com estes dados para exclusão.")
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                else:
                    st.error("Por favor, marque a caixa de confirmação antes de excluir.")
            else:
                st.warning("Informe o código e a competência para realizar a exclusão.")

    # ==========================================
    # ABA 3: TRANSFERÊNCIA DE OBRA
    # ==========================================
    with tab3:
        st.subheader("Transferir para Outra Obra")
        st.markdown("Atualiza a obra atual do colaborador e registra a origem nas observações.")

        transf_codigo = st.text_input("Código do Colaborador a ser transferido:")
        obra_origem = st.text_input("Obra de Origem (De onde foi transferido):")
        obra_destino = st.text_input("Obra de Destino (Para onde vai):")

        if st.button("Executar Transferência"):
            if transf_codigo and obra_origem and obra_destino:
                try:
                    nota_transferencia = f" [Transferido da obra {obra_origem} para {obra_destino}]"
                    query_update = text("""
                        UPDATE gestao_premios_zaut 
                        SET obra = :obra_destino, 
                            observacoes = COALESCE(observacoes, '') || :nota 
                        WHERE codigo = :codigo
                    """)
                    with engine.begin() as conn:
                        result = conn.execute(query_update, {
                            "obra_destino": obra_destino, 
                            "nota": nota_transferencia, 
                            "codigo": str(transf_codigo)
                        })
                        if result.rowcount > 0:
                            st.success(f"Colaborador transferido com sucesso para a obra {obra_destino}.")
                        else:
                            st.warning("Colaborador não encontrado.")
                except Exception as e:
                    st.error(f"Erro ao transferir: {e}")
            else:
                st.warning("Preencha todos os campos para realizar a transferência.")

    st.markdown("---")
    st.caption("BRAGANÇA SYS - Infraestrutura de Dados | Conexão: Supabase PostgreSQL")
