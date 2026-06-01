with aba1: # CONSULTAR
        st.subheader("Consultar")
        termo = st.text_input("Busca (ID ou Nome):", key="busca_consulta")
        if st.button("Buscar"):
            if termo:
                # Verifica se o termo é um número para fazer busca exata por ID
                if termo.isdigit():
                    sql = "SELECT * FROM cadastro_geral_colaborador WHERE id = :t"
                    params = {"t": int(termo)}
                # Caso contrário, faz a busca parcial por nome
                else:
                    sql = "SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t"
                    params = {"t": f"%{termo}%"}
                
                res = engine.connect().execute(text(sql), params).fetchall()
                if res:
                    for r in res: st.write(f"ID: {r.id} | Nome: {r.nome}")
                else:
                    st.warning("Nenhum registro encontrado para este critério.")    
