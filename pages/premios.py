import streamlit as st
import pandas as pd
from sqlalchemy import text
import datetime

# Motor de Cache de Alta Performance
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_dataframe(_engine, query, params=None):
    if params:
        return pd.read_sql(text(query), _engine, params=params)
    return pd.read_sql(text(query), _engine)

def render(engine, *args, **kwargs):
    # ==========================================
    # PADRÃO VISUAL E AUTO-CORREÇÃO
    # ==========================================
    st.markdown("""
    <style>
        .glass-panel {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 20px;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE public.cadastro_geral_colaborador ADD COLUMN IF NOT EXISTS obra TEXT DEFAULT 'CONSTRUART';"))
    except:
        pass

    st.title("Gestão de Prêmios e Lotação (ZAUT)")
    st.markdown("Módulo integrado para lançamento de Horas Prêmio (HP), conversão de valores variáveis e transferências entre obras.")

    def limpar_estado(chaves):
        get_cached_dataframe.clear()
        for chave in chaves:
            if chave in st.session_state:
                del st.session_state[chave]

    # ==========================================
    # CABEÇALHO GLOBAL (REFERÊNCIA)
    # ==========================================
    st.markdown("#### 🏢 Definição da Referência Operacional")
    col_ob, col_mes = st.columns([2, 1])
    
    try:
        df_obras = get_cached_dataframe(engine, "SELECT nome FROM public.cadastro_obras ORDER BY nome")
        lista_obras = df_obras['nome'].tolist() if not df_obras.empty else ["CONSTRUART"]
    except Exception:
        lista_obras = ["CONSTRUART"]
        
    obra_selecionada = col_ob.selectbox("Selecione a Obra de Trabalho:", options=lista_obras, key="filtro_obra_global")
    
    meses_ano = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    ano_corrente = datetime.datetime.now().year
    lista_anos = [ano_corrente, ano_corrente - 1, ano_corrente + 1]
    
    c_m, c_a = col_mes.columns(2)
    m_escolhido = c_m.selectbox("Mês:", meses_ano, index=datetime.datetime.now().month - 1)
    a_escolhido = c_a.selectbox("Ano:", lista_anos, index=0)
    mes_referencia = f"{meses_ano.index(m_escolhido)+1:02d}/{a_escolhido}"

    st.markdown("---")

    # ==========================================
    # CARREGAMENTO DOS DADOS GLOBAIS
    # ==========================================
    query_historico = """
        SELECT 
            l.id, l.codigo_colaborador, c.nome, c.cpf, c.cargo, c.salario_hora_12_24,
            l.total_hp, l.valor_hp, l.observacoes, l.data_cadastro
        FROM public.lancamento_premio_mensal l
        JOIN public.cadastro_geral_colaborador c ON l.codigo_colaborador = c.id
        WHERE l.obra_referencia = :obra AND l.mes_referencia = :mes
        ORDER BY c.nome
    """
    try:
        df_lancamentos = pd.read_sql(text(query_historico), engine, params={"obra": obra_selecionada, "mes": mes_referencia})
    except Exception:
        df_lancamentos = pd.DataFrame()

    query_colab_obra = """
        SELECT id as codigo, nome, cpf, cargo, salario_hora_12_24 
        FROM public.cadastro_geral_colaborador 
        WHERE obra = :obra 
        ORDER BY NULLIF(regexp_replace(id, '\D', '', 'g'), '')::numeric ASC
    """
    try:
        df_colaboradores = get_cached_dataframe(engine, query_colab_obra, params={"obra": obra_selecionada})
    except Exception:
        df_colaboradores = pd.DataFrame()

    # ==========================================
    # NAVEGAÇÃO POR ABAS (SPA)
    # ==========================================
    aba_premios, aba_transferencias = st.tabs(["💰 Lançamento de Prêmios (HP)", "🔄 Transferência de Obra"])

    # ---------------------------------------------------------
    # ABA 1: LANÇAMENTO DE PRÊMIOS
    # ---------------------------------------------------------
    with aba_premios:
        st.markdown("#### 🔍 Consulta e Lançamento de Colaborador")
        
        if df_colaboradores.empty:
            st.info(f"⚠️ Nenhum funcionário lotado na obra '{obra_selecionada}' no cadastro mãe.")
        else:
            c1, c2 = st.columns([1, 2])
            busca_colab = c1.text_input("Busca Rápida (Matrícula ou Nome):", key="busca_colab", autocomplete="off")
            
            lista_completa_colab = [f"{r['codigo']} | {r['nome']}" for _, r in df_colaboradores.iterrows()]
            busca_atual_colab = str(busca_colab).strip()
            ultima_busca_colab = st.session_state.get('last_busca_colab', '')

            filtrados_colab = []
            if busca_atual_colab:
                for op in lista_completa_colab:
                    parts = op.split(" | ", 1)
                    if len(parts) == 2:
                        id_part, nome_part = parts
                        if busca_atual_colab.lower() == id_part.strip().lower() or busca_atual_colab.lower() in nome_part.lower():
                            filtrados_colab.append(op)

            if busca_atual_colab != ultima_busca_colab:
                st.session_state['last_busca_colab'] = busca_atual_colab
                if busca_atual_colab and filtrados_colab:
                    st.session_state['sel_colab'] = filtrados_colab[0]

            if busca_atual_colab:
                if not filtrados_colab:
                    st.warning("⚠️ Colaborador não encontrado nesta obra.")
                    opcoes_colab = []
                else:
                    opcoes_colab = filtrados_colab
            else:
                opcoes_colab = lista_completa_colab
                
            if opcoes_colab:
                selecao_colab = c2.selectbox("Selecione o Colaborador:", opcoes_colab, key="sel_colab")
                st.markdown("---")
                
                id_colab = selecao_colab.split(" | ")[0]
                row_mae = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_colab].iloc[0]
                
                cargo_val = str(row_mae['cargo']) if pd.notna(row_mae['cargo']) and str(row_mae['cargo']).strip() else "Não Informado"
                cpf_val = str(row_mae['cpf']) if pd.notna(row_mae['cpf']) and str(row_mae['cpf']).strip() else "Não Informado"
                salario_hora_str = str(row_mae['salario_hora_12_24']).replace(',', '.') if pd.notna(row_mae['salario_hora_12_24']) else "0"
                
                try:
                    salario_hora = float(salario_hora_str)
                except ValueError:
                    salario_hora = 0.0
                
                tem_lancamento = not df_lancamentos.empty and id_colab in df_lancamentos['codigo_colaborador'].astype(str).values
                
                if not tem_lancamento:
                    with st.form("form_premio_novo", clear_on_submit=True):
                        st.markdown("##### ➕ Novo Lançamento")
                        c_c1, c_c2, c_c3 = st.columns(3)
                        c_c1.text_input("Cargo Atual", value=cargo_val, disabled=True, autocomplete="off")
                        c_c2.text_input("CPF", value=cpf_val, disabled=True, autocomplete="off")
                        c_c3.text_input("Salário/Hora Base", value=f"R$ {salario_hora:.2f}", disabled=True, autocomplete="off")
                        
                        st.markdown("##### Informações Operacionais (Digitação Manual)")
                        col_h, col_v, col_c = st.columns([1,1,2])
                        total_hp_digitado = col_h.number_input("Horas Extras Trabalhadas (HP)", min_value=0.0, format="%.2f", step=0.5)
                        valor_rs_digitado = col_v.number_input("Prêmio Extra em R$", min_value=0.0, format="%.2f", step=10.0)
                        
                        # A inteligência de conversão:
                        if salario_hora > 0:
                            horas_convertidas = valor_rs_digitado / salario_hora
                            total_geral_hp = total_hp_digitado + horas_convertidas
                        else:
                            horas_convertidas = 0.0
                            total_geral_hp = total_hp_digitado
                            
                        col_c.info(f"**Conversão Automática:**\nR$ {valor_rs_digitado:.2f} equivalem a **{horas_convertidas:.2f}h**.\n\nTotal a gravar: **{total_geral_hp:.2f} Horas**.")
                        
                        observacoes = st.text_input("Observações", autocomplete="off", key="obs_n")
                        
                        b1, b2 = st.columns(2)
                        if b1.form_submit_button("💾 Salvar Lançamento Integrado", type="primary", use_container_width=True):
                            if salario_hora <= 0 and valor_rs_digitado > 0:
                                st.error("Erro: Não é possível converter prêmio em dinheiro para horas porque o funcionário não tem Salário/Hora cadastrado na matriz.")
                            else:
                                query_ins = """
                                    INSERT INTO public.lancamento_premio_mensal (codigo_colaborador, obra_referencia, mes_referencia, total_hp, valor_hp, observacoes)
                                    VALUES (:codigo, :obra, :mes, :total_hp, :valor_hp, :observacoes)
                                """
                                try:
                                    with engine.begin() as conn:
                                        conn.execute(text(query_ins), {
                                            "codigo": id_colab, "obra": obra_selecionada, "mes": mes_referencia,
                                            "total_hp": total_geral_hp, "valor_hp": valor_rs_digitado, "observacoes": observacoes
                                        })
                                    st.toast("✅ Lançamento fixado no banco!")
                                    limpar_estado(['busca_colab', 'sel_colab', 'last_busca_colab'])
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {e}")
                                    
                        if b2.form_submit_button("❌ Cancelar", use_container_width=True):
                            limpar_estado(['busca_colab', 'sel_colab', 'last_busca_colab'])
                            st.rerun()
                else:
                    row_l = df_lancamentos[df_lancamentos['codigo_colaborador'].astype(str) == id_colab].iloc[0]
                    id_lanc = row_l['id']
                    
                    with st.form(f"form_premio_editar_{id_lanc}"):
                        st.markdown(f"##### ✏️ Modificar Prêmios Existente - {row_l['nome']}")
                        c_c1, c_c2, c_c3 = st.columns(3)
                        c_c1.text_input("Cargo", value=cargo_val, disabled=True, autocomplete="off")
                        c_c2.text_input("Referência", value=f"{mes_referencia}", disabled=True, autocomplete="off")
                        c_c3.text_input("Salário/Hora Base", value=f"R$ {salario_hora:.2f}", disabled=True, autocomplete="off")
                        
                        st.markdown("##### Ajuste de Lançamento")
                        col_h, col_v, col_c = st.columns([1,1,2])
                        total_hp_digitado = col_h.number_input("Ajustar Horas Trabalhadas", min_value=0.0, value=float(row_l['total_hp']), format="%.2f", step=0.5)
                        valor_rs_digitado = col_v.number_input("Ajustar Prêmio Extra (R$)", min_value=0.0, value=float(row_l['valor_hp']), format="%.2f", step=10.0)
                        
                        if salario_hora > 0:
                            horas_convertidas = valor_rs_digitado / salario_hora
                            total_geral_hp = total_hp_digitado + horas_convertidas
                        else:
                            horas_convertidas = 0.0
                            total_geral_hp = total_hp_digitado
                            
                        col_c.warning(f"**Revisão de Conversão:**\nR$ {valor_rs_digitado:.2f} = **{horas_convertidas:.2f}h**.\n\nNovo Total Final: **{total_geral_hp:.2f} Horas**.")
                        
                        obs_val = str(row_l['observacoes']) if pd.notna(row_l['observacoes']) and str(row_l['observacoes']).strip() != "None" else ""
                        observacoes = st.text_input("Observações", value=obs_val, autocomplete="off", key=f"obs_e_{id_lanc}")
                        
                        b1, b2, b3 = st.columns(3)
                        if b1.form_submit_button("✏️ Atualizar e Converter", type="primary", use_container_width=True):
                            query_upd = """
                                UPDATE public.lancamento_premio_mensal 
                                SET total_hp = :total_hp, valor_hp = :valor_hp, observacoes = :observacoes
                                WHERE id = :id
                            """
                            try:
                                with engine.begin() as conn:
                                    conn.execute(text(query_upd), {"total_hp": total_geral_hp, "valor_hp": valor_rs_digitado, "observacoes": observacoes, "id": id_lanc})
                                st.toast("✏️ Lançamento atualizado com sucesso!")
                                limpar_estado(['busca_colab', 'sel_colab', 'last_busca_colab'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                                
                        if b2.form_submit_button("🗑️ Excluir Lançamento", use_container_width=True):
                            try:
                                with engine.begin() as conn:
                                    conn.execute(text("DELETE FROM public.lancamento_premio_mensal WHERE id = :id"), {"id": id_lanc})
                                st.toast("🗑️ Registro de prêmio removido!")
                                limpar_estado(['busca_colab', 'sel_colab', 'last_busca_colab'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                                
                        if b3.form_submit_button("❌ Cancelar", use_container_width=True):
                            limpar_estado(['busca_colab', 'sel_colab', 'last_busca_colab'])
                            st.rerun()

        st.markdown("---")
        st.markdown(f"#### 📊 Rol de Prêmios - Período {mes_referencia}")
        
        if not df_lancamentos.empty:
            df_grid = df_lancamentos.copy()
            df_grid['valor_hp'] = pd.to_numeric(df_grid['valor_hp'], errors='coerce')
            df_grid['valor_hp'] = df_grid['valor_hp'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else ""
            )
            
            df_display = df_grid.rename(columns={
                'id': 'Cód. Lanç.',
                'codigo_colaborador': 'Cód. Func',
                'nome': 'Nome do Colaborador',
                'cpf': 'CPF',
                'cargo': 'Cargo',
                'total_hp': 'Total Final (HP)',
                'valor_hp': 'Valor Extra Injetado',
                'observacoes': 'Observações',
                'data_cadastro': 'Data Lançamento'
            })
            
            st.dataframe(
                df_display[['Cód. Lanç.', 'Cód. Func', 'Nome do Colaborador', 'Total Final (HP)', 'Valor Extra Injetado', 'Observações']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cód. Lanç.": st.column_config.NumberColumn(width="small"),
                    "Cód. Func": st.column_config.TextColumn(width="small"),
                    "Total Final (HP)": st.column_config.NumberColumn(width="medium", format="%.2f h"),
                    "Valor Extra Injetado": st.column_config.TextColumn(width="medium"),
                    "Nome do Colaborador": st.column_config.TextColumn(width="large"),
                    "Observações": st.column_config.TextColumn(width="large")
                }
            )
        else:
            st.info(f"Nenhum lançamento efetuado para a obra '{obra_selecionada}' em {mes_referencia}.")

    # ---------------------------------------------------------
    # ABA 2: TRANSFERÊNCIA DE OBRA (Filtro em Cascata Otimizado)
    # ---------------------------------------------------------
    with aba_transferencias:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f"#### 🔄 Transferir Colaborador da Obra: **{obra_selecionada}**")
        
        if df_colaboradores.empty:
            st.warning(f"Não há colaboradores alocados na obra '{obra_selecionada}' para serem transferidos.")
        else:
            lista_transferencia = [f"{r['codigo']} | {r['nome']}" for _, r in df_colaboradores.iterrows()]
            
            selecao_transf = st.selectbox(
                "1. Selecione quem deseja transferir:",
                options=[""] + lista_transferencia,
                index=0,
                key="sel_transf"
            )
            
            if selecao_transf != "":
                id_transf = selecao_transf.split(" | ")[0]
                row_t = df_colaboradores[df_colaboradores['codigo'].astype(str) == id_transf].iloc[0]
                
                opcoes_destino = [o for o in lista_obras if o != obra_selecionada]
                if not opcoes_destino:
                    opcoes_destino = ["Nenhuma outra obra cadastrada"]
                
                st.markdown("---")
                col_d, col_dat = st.columns(2)
                obra_destino = col_d.selectbox("2. Obra de Destino:", options=opcoes_destino)
                data_transf = col_dat.date_input("3. Data da Transferência:", value=datetime.date.today())
                
                obs_transf = st.text_input("4. Observações de Transferência (Opcional):", autocomplete="off")
                
                b_t1, b_t2, _ = st.columns([1,1,2])
                
                if b_t1.button("💾 Executar Transferência", type="primary", use_container_width=True):
                    if obra_destino == "Nenhuma outra obra cadastrada":
                        st.error("Cadastre outras obras no sistema primeiro.")
                    else:
                        query_hist = """
                            INSERT INTO public.historico_transferencias (codigo_colaborador, obra_origem, obra_destino, data_transferencia, observacoes)
                            VALUES (:codigo, :origem, :destino, :data_transf, :obs)
                        """
                        query_upd = """
                            UPDATE public.cadastro_geral_colaborador
                            SET obra = :destino
                            WHERE id = :codigo
                        """
                        try:
                            with engine.begin() as conn:
                                conn.execute(text(query_hist), {
                                    "codigo": id_transf, "origem": obra_selecionada, "destino": obra_destino, 
                                    "data_transf": data_transf, "obs": obs_transf
                                })
                                conn.execute(text(query_upd), {
                                    "destino": obra_destino, "codigo": id_transf
                                })
                            st.success(f"✅ {row_t['nome']} transferido para {obra_destino} com sucesso!")
                            limpar_estado(['filtro_obra_global', 'sel_transf'])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro no banco de dados: {e}")
                            
                if b_t2.button("❌ Cancelar", use_container_width=True):
                    st.rerun()
                    
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("🏗️ BRAGANÇA SYS | Módulo Operacional ZAUT")
