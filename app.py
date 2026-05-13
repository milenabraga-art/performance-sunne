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

# ── 2. ESTILIZAÇÃO SUNNE® PREMIUM (DESIGN CLAUDE + SIDEBAR MINIMALISTA) ──────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

:root {
    --rubi: #33001A; --dourado: #FAB200; --magenta: #FF365E;
    --laranja: #F36E21; --bg: #FDF8F5; --card-bg: #FFFFFF; --border: #EAD8D0;
}

/* Sidebar Minimalista Rubi */
[data-testid="stSidebar"] { background-color: var(--rubi) !important; border-right: 1px solid rgba(255,255,255,0.1); }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important; border: none !important; padding: 0px !important;
    margin-bottom: 20px !important; width: 100% !important; display: flex !important; justify-content: flex-start !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p { font-size: 16px; transition: 0.3s; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p { color: var(--laranja) !important; font-weight: 700; }

/* Header Claude Style */
.sunne-header {
    background: var(--rubi); padding: 1rem 2rem; display: flex;
    align-items: center; justify-content: space-between; margin: 0rem -1rem 1.5rem -1rem;
}
.sunne-logo-mark {
    width: 40px; height: 40px; background: var(--dourado); border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-weight: 700; color: var(--rubi); margin-right: 12px;
}
.sunne-header-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px; color: #FFFFFF; }

/* Cards e KPIs Style Claude */
.sunne-card { background: #FFFFFF; border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; }
.kpi-row { display: flex; gap: 12px; margin-top: 1rem; flex-wrap: wrap; }
.kpi-box { background: #FBF5F0; border-radius: 10px; padding: .85rem 1.1rem; flex: 1; min-width: 150px; border: 1px solid var(--border); }
.kpi-label { font-size: 11px; color: #7A5060; text-transform: uppercase; font-weight: 600; margin-bottom: 5px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: var(--rubi); }
.kpi-value.danger { color: var(--magenta); }

/* Tabelas polidas */
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sunne-table th { text-align: left; padding: .6rem; background: #FBF5F0; color: #7A5060; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
.sunne-table td { padding: .6rem; border-bottom: .5px solid #F0E4DC; color: #1A0A0F; }

/* Kanban Cards */
.kanban-card { background: white; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border-left: 5px solid var(--laranja); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
</style>
"""

# ── 3. BANCO DE DADOS E UTILITÁRIOS ──────────────────────────────────────────
DB_PATH = "database/"
if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

def save_db(data, filename):
    with open(os.path.join(DB_PATH, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_db(filename):
    path = os.path.join(DB_PATH, filename)
    return json.load(open(path, 'r', encoding='utf-8')) if os.path.exists(path) else []

def normalize_uc(val):
    if not val: return ""
    return "".join(filter(str.isdigit, str(val).split('.')[0]))

def clean_val(v):
    if v is None or str(v).lower() in ("nan", ""): return 0.0
    s = str(v).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
    try: return float(s)
    except: return 0.0

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio_Sunne')
    return output.getvalue()

# ── 4. LÓGICA DE ANÁLISE ROBUSTA ─────────────────────────────────────────────
def analyze_data(df_r, df_e):
    def find_c(df, keys):
        for k in keys:
            for c in df.columns:
                if k.lower() in str(c).lower(): return c
        return df.columns[0]

    uc_r_col = find_c(df_r, ["UC Nova", "Atual"])
    uc_e_col = find_c(df_e, ["Número da UC", "Numero"])
    comp_col = find_c(df_e, ["Competência", "Mês"])
    status_col = find_c(df_e, ["Status"])
    valor_col = find_c(df_e, ["Total a Pagar", "Valor"])
    venc_col = find_c(df_e, ["Vencimento"])

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    if venc_col:
        df_e[venc_col] = pd.to_datetime(df_e[venc_col], errors='coerce', dayfirst=True)

    missing = {}; inad = {}; t_gerado = {}; t_vencido = {}; critical = []

    for _, row in df_e.iterrows():
        comp = str(row[comp_col])
        val = clean_val(row[valor_col])
        status = str(row[status_col]).lower()
        t_gerado[comp] = t_gerado.get(comp, 0.0) + val
        
        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp, 0.0) + val
            item = {"UC": row[uc_e_col], "Titular": row.get("Titular", "—"), "Valor": val}
            if comp not in inad: inad[comp] = []
            inad[comp].append(item)
            if venc_col and pd.notnull(row[venc_col]):
                atraso = (datetime.now() - row[venc_col]).days
                if atraso > 60: critical.append({"Titular": item["Titular"], "UC": item["UC"], "Dias": atraso, "Valor": val, "Mês": comp})

    extrato_set = set(zip(df_e['UC_NORM'], df_e[comp_col].astype(str)))
    ucs_rateio = df_r['UC_NORM'].unique()
    for c_mes in df_e[comp_col].unique():
        if not c_mes or str(c_mes) == "nan": continue
        for uc_norm in ucs_rateio:
            if (uc_norm, str(c_mes)) not in extrato_set:
                orig = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if c_mes not in missing: missing[c_mes] = []
                missing[c_mes].append({"UC": orig[uc_r_col], "Apelido": orig.get("Usina", "—")})

    return {"missing": missing, "inad": inad, "t_gerado": t_gerado, "t_vencido": t_vencido, "critical": critical}

# ── 5. INTERFACE DO HUB SUNNE ────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        st.markdown('<div style="max-width:400px; margin:10vh auto; text-align:center;" class="sunne-card">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        with st.form("login"):
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Hub") and s == "sunne2026":
                st.session_state.user = {"name": "Milena"}
                st.rerun()
        return

    # HEADER CLAUDE STYLE
    st.markdown(f'<div class="sunne-header"><div><span class="sunne-logo-mark">S</span><span class="sunne-header-title">Sunne Performance</span></div><div style="color:white">Olá, Milena 👋</div></div>', unsafe_allow_html=True)

    # SIDEBAR MINIMALISTA
    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=100)
        st.write("---")
        menu = ["Gerenciamento", "Geradores", "Usinas", "Faturamento"]
        if "page" not in st.session_state: st.session_state.page = "Faturamento"
        for item in menu:
            if st.button(item): st.session_state.page = item
        if st.button("🚪 Sair"): st.session_state.clear(); st.rerun()

    # PÁGINA: FATURAMENTO
    if st.session_state.page == "Faturamento":
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        with t1:
            st.markdown('<div class="sunne-card"><div class="kpi-label">Upload de Planilhas</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Rateio", type=["xlsx", "csv"])
            f_e = c2.file_uploader("Extrato", type=["xlsx", "csv"])
            if f_r and f_e and st.button("🔄 Analisar Performance"):
                df_r = pd.read_excel(f_r) if f_r.name.endswith('xlsx') else pd.read_csv(f_r)
                df_e = pd.read_excel(f_e) if f_e.name.endswith('xlsx') else pd.read_csv(f_e)
                st.session_state.results = analyze_data(df_r, df_e)
            st.markdown('</div>', unsafe_allow_html=True)

        res = st.session_state.get("results")
        if res:
            with t2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        df_m = pd.DataFrame(items)
                        st.download_button("📥 Exportar para Sheets", to_excel(df_m), f"faltantes_{comp}.xlsx")
                        st.table(df_m)
            with t3:
                for comp, rows in res["inad"].items():
                    gerado, vencido = res["t_gerado"].get(comp, 1.0), res["t_vencido"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100)
                    st.markdown(f"### {comp}")
                    st.markdown(f'<div class="kpi-row"><div class="kpi-box"><div class="kpi-label">Gerado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>'
                                f'<div class="kpi-box"><div class="kpi-label">Vencido</div><div class="kpi-value danger">R$ {vencido:,.2f}</div></div>'
                                f'<div class="kpi-box"><div class="kpi-label">Taxa</div><div class="kpi-value danger">{taxa:.1f}%</div></div></div>', unsafe_allow_html=True)
                    with st.expander("Ver lista e Exportar"):
                        df_i = pd.DataFrame(rows)
                        st.download_button("📥 Exportar para Sheets", to_excel(df_i), f"inadimplencia_{comp}.xlsx")
                        st.table(df_i)
                st.write("---")
                st.markdown("## 🚨 Inadimplência Crítica (>60 dias)")
                if res["critical"]:
                    df_c = pd.DataFrame(res["critical"])
                    st.dataframe(df_c.style.apply(lambda x: ['background-color: #ffcccc' if x.Dias > 90 else 'background-color: #fff4cc']*len(x), axis=1), use_container_width=True)

    # PÁGINA: GERADORES
    elif st.session_state.page == "Geradores":
        st.title("📂 Carteira de Geradores")
        up = st.file_uploader("Subir Geradores", type=["xlsx"])
        if up: 
            df = pd.read_excel(up)
            save_db(df.to_dict('records'), "geradores.json")
        data = load_db("geradores.json")
        if data: st.dataframe(pd.DataFrame(data), use_container_width=True)

    # PÁGINA: USINAS
    elif st.session_state.page == "Usinas":
        st.title("🌱 Gestão de Usinas")
        up_u = st.file_uploader("Subir Usinas", type=["xlsx"])
        if up_u: 
            df_u = pd.read_excel(up_u)
            save_db(df_u.to_dict('records'), "usinas.json")
        usinas = load_db("usinas.json")
        if usinas:
            for i, u in enumerate(usinas):
                c_a, c_b = st.columns([4, 1])
                c_a.write(f"**{u['UFV']}** (UC: {u['UC']})")
                if c_b.button("📝 Criar Atividade", key=f"at_{i}"):
                    st.session_state.nova_tarefa = u
            if "nova_tarefa" in st.session_state:
                with st.form("f_tarefa"):
                    st.subheader(f"Tarefa para {st.session_state.nova_tarefa['UFV']}")
                    titulo = st.text_input("O que precisa ser feito?")
                    if st.form_submit_button("Criar"):
                        tasks = load_db("tasks.json")
                        tasks.append({"id": len(tasks)+1, "titulo": titulo, "usina": st.session_state.nova_tarefa['UFV'], "status": "Em aberto", "data": datetime.now().strftime("%d/%m/%Y")})
                        save_db(tasks, "tasks.json")
                        del st.session_state.nova_tarefa; st.rerun()

    # PÁGINA: KANBAN
    elif st.session_state.page == "Gerenciamento":
        st.title("📋 Kanban de Operações")
        tasks = load_db("tasks.json")
        cols = st.columns(5)
        status_list = ["Em aberto", "Em andamento", "Travado", "Concluido", "Cancelado"]
        for i, s in enumerate(status_list):
            with cols[i]:
                st.markdown(f"**{s}**")
                for t in [x for x in tasks if x['status'] == s]:
                    with st.container():
                        st.markdown(f'<div class="kanban-card"><b>{t["titulo"]}</b><br/><small>{t["usina"]}</small></div>', unsafe_allow_html=True)
                        with st.popover("Mover"):
                            novo = st.selectbox("Novo Status", status_list, index=i, key=f"s_{t['id']}")
                            if novo != s:
                                for item in tasks:
                                    if item['id'] == t['id']: item['status'] = novo
                                save_db(tasks, "tasks.json"); st.rerun()

if __name__ == "__main__": main()
