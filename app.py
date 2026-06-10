# Migração de dados de afastamento da tabela antiga para a nova, se necessário
try:
    with engine.begin() as conn:
        # Verifica se a tabela historico_afastamentos está vazia
        cnt_afastamentos = conn.execute(text("SELECT COUNT(*) FROM historico_afastamentos")).fetchone()[0]
        if cnt_afastamentos == 0:
            # Verifica se a tabela cadastro_geral_colaborador tem dados de afastamento para migrar
            df_colaboradores_com_afastamento = pd.read_sql_query("""
                SELECT id, admissao, status_esocial, data_afastamento, data_retorno
                FROM cadastro_geral_colaborador
                WHERE status_esocial IS NOT NULL AND status_esocial != '' AND status_esocial != '1 - Trabalhando'
            """, conn)

            if not df_colaboradores_com_afastamento.empty:
                for index, row in df_colaboradores_com_afastamento.iterrows():
                    id_colaborador = row['id']
                    data_inicio = row['data_afastamento'] if row['data_afastamento'] else row['admissao']
                    data_fim = row['data_retorno']
                    tipo_afastamento = row['status_esocial']

                    if data_inicio and tipo_afastamento:
                        conn.execute(text("""
                            INSERT INTO historico_afastamentos (id_colaborador, data_inicio, data_fim, tipo_afastamento)
                            VALUES (:id_colaborador, :data_inicio, :data_fim, :tipo_afastamento)
                        """), {
                            "id_colaborador": id_colaborador,
                            "data_inicio": data_inicio,
                            "data_fim": data_fim,
                            "tipo_afastamento": tipo_afastamento
                        })
                st.success("Dados de afastamento migrados para 'historico_afastamentos'.")
            else:
                st.info("Nenhum dado de afastamento para migrar.")
        else:
            st.info("Tabela 'historico_afastamentos' já contém dados, migração ignorada.")
except Exception as e:
    st.warning(f"Erro na migração de dados de afastamento: {e}")
