import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime

# FERRAMENTAS UTILIZADAS: Python e Streamlit

def formatar_data_universal(data_str):
    """Converte entradas manuais sem barra (ex: 21092021) para o formato de banco de dados."""
    if not data_str or pd.isna(data_str) or str(data_str).strip().lower() in ['nan', 'none', 'nat', '', 'não informada', 'nao informada']:
        return None

    data_str = str(data_str).strip()

    # Se o usuário digitou 8 números diretos sem barra (ex: 21092021)
    if data_str.isdigit() and len(data_str) == 8:
        data_str = f"{data_str[:2]}/{data_str[2:4]}/{data_str[4:]}"
    # Se digitou 6 números (ex: 210921)
    elif data_str.isdigit() and len(data_str) == 6:
        data_str = f"{data_str[:2]}/{data_str[2:4]}/20{data_str[4:]}"

    try:
        parsed = pd.to_datetime(data_str, dayfirst=True, errors='coerce')
        if pd.notna(parsed):
            return parsed.date()
    except Exception:
        pass
    return None

def render(engine, *args, **kwargs):
    st.title("Gestão de Cadastros")

    busca_id = st.text_input("Digite a Matrícula (ID) do Colaborador para buscar:")

    if st.button("Buscar Registro", type="primary") or busca_id:
        if busca_id:
            with engine.connect() as conn:
                # O ID é tratado estritamente como texto, conforme diretriz de arquitetura
                query = text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id")
                result = conn.execute(query, {"id": str(busca_id).strip()}).fetchone()

            if result:
                st.markdown("### 📄 Ficha Completa do Colaborador")

                col1, col2, col3 = st.columns(3)

                # Tratamento de valores monetários
                salario_mes_val = float(result.salario_mes or 0.0)

                # Lógica do Salário-Hora: Se não existir no banco, calcula base 220h
                salario_hora_val = getattr(result, 'salario_hora', 0.0)
                if not salario_hora_val or float(salario_hora_val) == 0.0:
                    salario_hora_val = salario_mes_val / 220.0 if salario_mes_val > 0 else 0.0

                with col1:
                    st.caption("ID / MATRÍCULA")
                    st.write(result.id)
                    st.caption("CARGO")
                    st.write(result.cargo if result.cargo else "Não Informado")
                    st.caption("SALÁRIO-MÊS ATUAL")
                    st.write(f"R$ {salario_mes_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if salario_mes_val > 0 else "R$ 0,00")

                with col2:
                    st.caption("NOME COMPLETO")
                    st.write(result.nome)
                    st.caption("SITUAÇÃO (eSocial)")
                    st.write(result.status_esocial if result.status_esocial else "Não Informado")
                    st.caption("SALÁRIO-HORA ATUAL")
                    st.write(f"R$ {salario_hora_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if salario_hora_val > 0 else "R$ 0,00")

                with col3:
                    st.caption("CPF")
                    cpf = getattr(result, 'cpf', "Não Informado")
                    st.write(cpf if cpf else "Não Informado")
                    st.caption("DATA DE ADMISSÃO")
                    admissao_atual = result.data_admissao.strftime('%d/%m/%Y') if result.data_admissao else "Não Informada"
                    st.write(admissao_atual)
                    st.caption("DATA DE DEMISSÃO")
                    demissao = getattr(result, 'data_demissao', None)
                    st.write(demissao.strftime('%d/%m/%Y') if demissao else "Ativo / Sem Demissão")

                st.markdown("---")

                with st.expander("✏️ Alterar Ficha (Editar Dados)"):
                    with st.form("form_editar_ficha"):
                        st.info("💡 Você pode digitar a data normalmente sem as barras (ex: 21092021). O sistema formatará automaticamente.")

                        novo_nome = st.text_input("Nome Completo", value=result.nome)
                        novo_cargo = st.text_input("Cargo", value=result.cargo if result.cargo else "")

                        # Campo de texto livre para permitir digitação rápida sem barras
                        nova_admissao_str = st.text_input("Data de Admissão", value=admissao_atual if admissao_atual != "Não Informada" else "")

                        novo_salario = st.number_input("Salário Mês (R$)", value=salario_mes_val, step=100.0)

                        if st.form_submit_button("Confirmar e Salvar Alterações", type="primary"):
                            # Aplica o motor de formatação automática antes de salvar
                            data_tratada = formatar_data_universal(nova_admissao_str)

                            with engine.begin() as conn_update:
                                conn_update.execute(text("""
                                    UPDATE cadastro_geral_colaborador 
                                    SET nome = :nome, 
                                        cargo = :cargo, 
                                        data_admissao = :admissao, 
                                        salario_mes = :salario
                                    WHERE id = :id
                                """), {
                                    "nome": novo_nome,
                                    "cargo": novo_cargo,
                                    "admissao": data_tratada,
                                    "salario": novo_salario,
                                    "id": result.id
                                })
                            st.success("Ficha atualizada com sucesso! O sistema formatou e salvou os dados corretamente.")
                            st.rerun()

                st.markdown("### 📜 Histórico de Situações (eSocial)")
                st.info("Nenhum histórico de situação registrado na base de dados para este colaborador.")

                st.markdown("### 🏦 Dados Bancários (PIX Principal)")
                st.info("Nenhum dado bancário registrado.")

                st.markdown("### 💰 Histórico Financeiro (Lançamentos)")
                st.info("Nenhum lançamento financeiro encontrado.")

            else:
                st.warning("Colaborador não encontrado. Verifique a matrícula digitada.")
