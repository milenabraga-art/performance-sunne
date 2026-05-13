import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import io

# ── 1. CONFIGURAÇÃO DA PÁGINA ────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne Performance",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. ESTILIZAÇÃO SUNNE® (BACKOFFICE RUBI) ──────────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; }

:root {
    --rubi: #33001A; --dourado: #FAB200; --laranja: #F36E21; --bg: #FDF8F5;
}

/* Sidebar Rubi */
[data-testid="stSidebar"] { background-color: var(--rubi) !important; border-right: 1px solid rgba(255,255,255,0.1); }
[data-testid="stSidebar"] * { color: white !important; }

/* Botões da Sidebar (Apenas texto) */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important; border: none !important; color: white !important;
    padding: 0px !important; margin-bottom: 20px !important; width: 100% !important;
    display: flex !important; justify-content: flex-start !important; text-align: left !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p { color: var(--laranja) !important; font-weight: 700; }

/* Kanban Cards */
.kanban-card {
    background: white; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
    border-left: 5px solid var(--laranja); box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.kanban-title { font-weight: 700; color: var(--rubi); font-size: 14px; margin-bottom: 4px; }
.kanban-sub { font-size: 11px; color: #7A5060; }

/* KPIs */
.kpi-box { background: white; border-radius: 15px; padding: 1.2rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: var(--rubi); }
</style>
"""

# ── 3. BANCO DE DADOS LOCAL (JSON) ───────────────────────────────────────────
DB_PATH = "database/"
if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

def save_data(data, filename):
    with open(os.path.join(DB_PATH, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data(filename):
    path = os.path.join(DB_PATH, filename)
    return json.load(open(path, 'r', encoding='utf-8')) if os.path.exists(path) else []

# ── 4. UTILITÁRIOS DE DADOS ──────────────────────────────────────────────────
def clean_val(v):
    if not v: return 0.0
    s = str(v).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try: return float(s)
    except: return 0.0

def normalize_uc(val):
    if not val: return ""
    return "".join(filter(str.isdigit, str(val).split('.')[0]))

def load_planilha(uploaded_file):
    if uploaded_file is None: return None
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    return df.fillna("")

# ── 5. LÓGICA DE ANÁLISE (A QUE ACHA AS 63 FATURAS) ──────────────────────────
def analyze_performance(df_r, df_e):
    # Identificar colunas (mesma lógica funcional anterior)
    uc_r_col = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    uc_e_col = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_col = next((c for c in df_e.columns if "Competência" in c), None)
    status_col = next((c for c in df_e.columns if "Status" in c), None)
    valor_col = next((c for c in df_e.columns if "Total a Pagar" in c), None)

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    missing_res = {}; inad_res = {}; t_gerado = {}

    competencias = df_e[comp_col].unique() if comp_col else ["Geral"]
    ucs_rateio = df_r['UC_NORM'].unique()
    extrato_set = set(zip(df_e['UC_NORM'], df_e[comp_col].astype(str)))

    for comp in competencias:
        if not comp or str(comp).lower() == 'nan': continue
        # Faltantes
        for uc_norm in ucs_rateio:
            if (uc_norm, str(comp)) not in extrato_set:
                r_orig = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if comp not in missing_res: missing_res[comp] = []
                missing_res[comp].append({"uc": r_orig[uc_r_col], "apelido": r_orig.get("Apelido UC", "—"), "usina": r_orig.get("Usina", "—")})
        
        # Inadimplência
        df_mes = df_e[df_e[comp_col] == comp]
        t_gerado[comp] = df_mes[valor_col].apply(clean_val).sum()
        vencidos = df_mes[df_mes[status_col].astype(str).str.lower().contains("vencido")]
        inad_res[comp] = vencidos.to_dict('records')

    return {"missing": missing_res, "inad": inad_res, "t_gerado": t_gerado}

# ── 6. INTERFACE PRINCIPAL ────────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        with st.form("login"):
            e = st.text_input("E-mail", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar no Hub"):
                if s == "sunne2026":
                    st.session_state["user"] = {"name": "Milena", "email": e}
                    st.rerun()
        return

    # SIDEBAR MINIMALISTA
    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=100)
        st.write(f"Olá, {st.session_state.user['name']} 👋")
        st.write("---")
        menu = ["Gerenciamento de Atividades", "Geradores", "Usinas", "Faturamento"]
        if "page" not in st.session_state: st.session_state.page = menu[3]
        for item in menu:
            if st.button(item): st.session_state.page = item
        if st.button("🚪 Sair"): 
            del st.session_state["user"]; st.rerun()

    # ── MÓDULO: GERADORES ──
    if st.session_state.page == "Geradores":
        st.title("📂 Carteira de Geradores")
        up = st.file_uploader("Importar Planilha de Geradores", type=["xlsx"])
        if up:
            df = load_planilha(up)
            # Filtro pela analista logada
            df_m = df[df['Analista'].str.contains(st.session_state.user['name'], na=False)]
            save_data(df_m.to_dict('records'), "geradores.json")
        
        data = load_data("geradores.json")
        if data: st.dataframe(pd.DataFrame(data), use_container_width=True)

    # ── MÓDULO: USINAS ──
    elif st.session_state.page == "Usinas":
        st.title("🌱 Gestão de Usinas")
        c1, c2 = st.columns(2)
        with c1: st.button("➕ Adicionar Usina Manual")
        with c2: 
            up_u = st.file_uploader("Importar Planilha de Usinas", type=["xlsx"])
            if up_u:
                df_u = load_planilha(up_u)
                save_data(df_u.to_dict('records'), "usinas.json")

        usinas = load_data("usinas.json")
        if usinas:
            for i, u in enumerate(usinas):
                col_a, col_b, col_c = st.columns([3, 1, 1])
                col_a.write(f"**{u['UFV']}** (UC: {u['UC']})")
                col_b.write(f"Analista: {u['Analista']}")
                if col_c.button("📝 Criar Atividade", key=f"at_{i}"):
                    st.session_state.nova_tarefa = u
            
            if "nova_tarefa" in st.session_state:
                with st.form("form_tarefa"):
                    st.subheader(f"Nova Tarefa: {st.session_state.nova_tarefa['UFV']}")
                    titulo = st.text_input("Título da Tarefa")
                    if st.form_submit_button("Criar"):
                        tasks = load_data("tasks.json")
                        tasks.append({
                            "id": len(tasks)+1, "titulo": titulo, 
                            "usina": st.session_state.nova_tarefa['UFV'], 
                            "status": "Em aberto", "data": datetime.now().strftime("%d/%m/%Y")
                        })
                        save_data(tasks, "tasks.json")
                        del st.session_state.nova_tarefa
                        st.success("Tarefa enviada ao Kanban!")
                        st.rerun()

    # ── MÓDULO: KANBAN ──
    elif st.session_state.page == "Gerenciamento de Atividades":
        st.title("📋 Kanban de Operações")
        tasks = load_data("tasks.json")
        cols = st.columns(5)
        status_list = ["Em aberto", "Em andamento", "Travado", "Concluido", "Cancelado"]
        
        for i, s in enumerate(status_list):
            with cols[i]:
                st.markdown(f"### {s}")
                for t in [x for x in tasks if x['status'] == s]:
                    with st.container():
                        st.markdown(f"""<div class="kanban-card">
                            <div class="kanban-title">{t['titulo']}</div>
                            <div class="kanban-sub">{t['usina']} · {t['data']}</div>
                        </div>""", unsafe_allow_html=True)
                        with st.popover("Mover"):
                            novo = st.selectbox("Status", status_list, index=i, key=f"sel_{t['id']}")
                            if novo != s:
                                for item in tasks:
                                    if item['id'] == t['id']: item['status'] = novo
                                save_data(tasks, "tasks.json")
                                st.rerun()

    # ── MÓDULO: FATURAMENTO ──
    elif st.session_state.page == "Faturamento":
        st.title("💳 Faturamento e Captura")
        c1, c2 = st.columns(2)
        f_r = c1.file_uploader("Rateio", type=["xlsx", "csv"])
        f_e = c2.file_uploader("Extrato", type=["xlsx", "csv"])
        if f_r and f_e and st.button("🔄 Analisar"):
            st.session_state.results = analyze_performance(load_planilha(f_r), load_planilha(f_e))
        
        if "results" in st.session_state:
            tab_cap, tab_ina = st.tabs(["🔍 Captura", "💳 Inadimplência"])
            with tab_cap:
                for comp, items in st.session_state.results['missing'].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        st.table(pd.DataFrame(items))
            with tab_ina:
                st.write("Relatório de faturas vencidas...")

if __name__ == "__main__": main()
