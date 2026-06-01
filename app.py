import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import io
import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="BRAGANÇA SYS", page_icon="🏗️", layout="wide")

# Conexão (preservada)
engine = create_engine(st.secrets["DATABASE_URL"])

# Inicialização de Estados (para controlar o Cancelar)
if 'id_edicao' not in st.session_state: st.session_state['id_edicao'] = None

# --- MENU LATERAL (Preservado) ---
menu = st.sidebar.radio("Navegação", ["👥 Visão Geral", "📥 Importação Inteligente", "🛠️ Gestão de Cadastros"])

# --- 1. VISÃO GERAL (Preservado) ---
if menu == "👥 Visão Geral":
    st.title("📊 Painel Corporativo")
    df = pd.read_sql("SELECT * FROM cadastro_geral_colaborador", engine)
    st.dataframe(df, use_container_width=True)

# --- 2. IMPORTAÇÃO INTELIGENTE (Restaurado e Funcional) ---
elif menu == "📥 Importação Inteligente":
    st.title("📥 Importação Inteligente")
    arquivo = st.file_uploader("Selecione o arquivo (.xlsx, .csv)", type=["xlsx", "csv"])
    
    if arquivo and st.button("Executar Ingestão Certificada"):
        try:
            # Lógica robusta de importação
            if arquivo.name.endswith('.xlsx'):
                df_bruto = pd.read_excel(arquivo, engine='openpyxl')
            else:
                df_bruto = pd.read_csv(arquivo)
            
            with engine.begin() as conn:
                for _, row in df_bruto.iterrows():
                    # Upsert básico
                    conn.execute(text("""
                        INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome)
                        ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome
                    """), {"id": str(row[0]), "nome": str(row[1])})
            st.success("Importação concluída com sucesso!")
        except Exception as e:
            st.error(f"Erro na importação: {e}")

# --- 3. GESTÃO DE CADASTROS (Corrigido com botões funcionais) ---
elif menu == "🛠️ Gestão de Cadastros":
    aba1, aba2, aba3, aba4 = st.tabs(["🔍 Consultar", "➕ Novo", "✏️ Alterar", "❌ Excluir"])

    with aba1:
        st.subheader("Consultar")
        termo = st.text_input("Busca:")
        if termo:
            res = engine.connect().execute(text("SELECT * FROM cadastro_geral_colaborador WHERE nome ILIKE :t"), {"t": f"%{termo}%"}).fetchall()
            for r in res: st.write(f"ID: {r.id} | Nome: {r.nome}")

    with aba2: # NOVO
        st.subheader("Novo Cadastro")
        # Botão de cancelar fora do form
        if st.button("Cancelar Inserção"): st.rerun()
        with st.form("form_novo"):
            i_id = st.text_input("ID")
            i_nome = st.text_input("Nome")
            if st.form_submit_button("Salvar Registro"):
                with engine.begin() as conn: conn.execute(text("INSERT INTO cadastro_geral_colaborador (id, nome) VALUES (:id, :nome)"), {"id": i_id, "nome": i_nome})
                st.success("Salvo!")
                st.rerun()

    with aba3: # ALTERAR
        st.subheader("Alterar Cadastro")
        if st.session_state['id_edicao'] is None:
            lista = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
            sel = st.selectbox("Selecione:", lista)
            if st.button("Carregar Ficha"): 
                st.session_state['id_edicao'] = sel.split(" - ")[0]
                st.rerun()
        else:
            id_alt = st.session_state['id_edicao']
            # Botão cancelar edição
            if st.button("Cancelar Edição"): 
                st.session_state['id_edicao'] = None
                st.rerun()
            
            dados = engine.connect().execute(text("SELECT * FROM cadastro_geral_colaborador WHERE id = :id"), {"id": id_alt}).fetchone()
            with st.form("form_alt"):
                n_nome = st.text_input("Nome", value=dados.nome)
                if st.form_submit_button("Salvar Alterações"):
                    with engine.begin() as conn: conn.execute(text("UPDATE cadastro_geral_colaborador SET nome = :n WHERE id = :id"), {"n": n_nome, "id": id_alt})
                    st.session_state['id_edicao'] = None
                    st.rerun()

    with aba4: # EXCLUIR
        st.subheader("Excluir Cadastro")
        lista_del = [f"{r.id} - {r.nome}" for r in engine.connect().execute(text("SELECT id, nome FROM cadastro_geral_colaborador")).fetchall()]
        sel_del = st.selectbox("Selecione para excluir:", lista_del)
        if st.button("Confirmar Exclusão"):
            with engine.begin() as conn: conn.execute(text("DELETE FROM cadastro_geral_colaborador WHERE id = :id"), {"id": sel_del.split(" - ")[0]})
            st.rerun()
