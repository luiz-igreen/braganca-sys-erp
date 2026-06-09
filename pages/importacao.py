    with aba_imp1:
        st.subheader("Importação de Cadastros Novos")
        arquivo = st.file_uploader("Selecione o arquivo de migração de colaboradores (.xlsx, .csv)", type=["xlsx", "csv"], key="up_cad_base")
        if arquivo and st.button("Executar Ingestão de Cadastros", key="btn_imp_cad", type="primary"):
            with st.spinner("⏳ Processando arquivo e inserindo cadastros..."):
                try:
                    df_bruto = ler_planilha_inteligente(arquivo)

                    # Mapeamento das colunas do CSV para as colunas do banco de dados
                    # As colunas do CSV são: 'Alertas do Sistema', 'id', 'nome', 'Status (eSocial)', 'cpf', 'cargo', 'salario_mes_12_24'

                    # Renomear colunas do DataFrame para facilitar o mapeamento
                    df_bruto.columns = [
                        'Alertas do Sistema', 'id_csv', 'nome_csv', 'status_esocial_csv', 
                        'cpf_csv', 'cargo_csv', 'salario_mes_12_24_csv'
                    ]

                    with engine.begin() as conn:
                        for _, row in df_bruto.iterrows():
                            try:
                                # Extraindo os valores das colunas do CSV
                                v_id = str(row['id_csv']).strip()
                                v_nome = str(row['nome_csv']).strip() if pd.notna(row['nome_csv']) else None
                                v_cpf = str(row['cpf_csv']).strip() if pd.notna(row['cpf_csv']) else None
                                v_cargo = str(row['cargo_csv']).strip() if pd.notna(row['cargo_csv']) else None
                                v_status_esocial = str(row['status_esocial_csv']).strip() if pd.notna(row['status_esocial_csv']) else None

                                # Limpar e converter salário
                                sal_mes_raw = str(row['salario_mes_12_24_csv']).replace('R$', '').replace('.', '').replace(',', '.').strip() if pd.notna(row['salario_mes_12_24_csv']) else '0'
                                try:
                                    v_sal_mes = float(sal_mes_raw)
                                except ValueError:
                                    v_sal_mes = 0.0

                                # Valores padrão para campos não presentes no CSV
                                v_admissao = None # CSV não tem data de admissão
                                v_demissao = None # CSV não tem data de demissão
                                v_sal_hora = 0.0 # CSV não tem salário por hora

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
