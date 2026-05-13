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

# ── 2. CSS CUSTOMIZADO (DESIGN CLAUDE + SIDEBAR MINIMALISTA) ────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Reset e base */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

:root {
    --rubi: #33001A; --dourado: #FAB200; --magenta: #FF365E;
    --laranja: #F36E21; --bg: #FDF8F5; --card-bg: #FFFFFF; --border: #EAD8D0;
}

/* Sidebar Minimalista Rubi */
[data-testid="stSidebar"] {
    background-color: var(--rubi) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
}
[data-testid="stSidebar"] * { color: white !important; }

/* Botões da Sidebar como Texto */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important;
    border: none !important;
    padding: 0px !important;
    margin-bottom: 20px !important;
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
    font-size: 16px !important;
    font-weight: 500 !important;
    transition: 0.3s;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p {
    color: var(--laranja) !important;
    font-weight: 700 !important;
}

/* Header Estilo Claude */
.sunne-header {
    background: var(--rubi); padding: 1rem 2rem; display: flex;
    align-items: center; justify-content: space-between;
    margin: 0rem -1rem 1.5rem -1rem;
}
.sunne-logo-mark {
    width: 40px; height: 40px; background: var(--dourado); border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-weight: 700; color: var(--rubi); margin-right: 12px;
}
.sunne-header-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px; color: #FFFFFF; }

/* Cards e KPIs Claude Style */
.sunne-card {
    background: #FFFFFF; border: 1px solid var(--border);
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
}
.kpi-row { display: flex; gap: 12px; margin-top: 1rem; flex-wrap: wrap; }
.kpi-box {
    background: #FBF5F0; border-radius: 10px; padding: .85rem 1.1rem; flex: 1; min-width: 150px;
}
.kpi-label { font-size: 11px; color: #7A5060; text-transform: uppercase; font-weight: 600; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: var(--rubi); }
.kpi-value.danger { color: var(--magenta); }

/* Tabelas Claude Style */
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sunne-table th { text-align: left; padding: .6rem; background: #FBF5F0; color: #7A5060; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
.sunne-table td { padding: .6rem; border-bottom: .5px solid #F0E4DC; color: #1A0A0F; }

/* Login Claude Style */
.login-card {
    max-width: 400px; margin: 10vh auto; padding: 3rem; background: white;
    border-radius: 20px; border: 1px solid var(--border); text-align: center;
}
</style>
"""

# ── 3. UTILITÁRIOS E SEGURANÇA ────────────────────────────────────────────────
USERS_FILE = "users.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        default = {"users": [{"name": "Milena", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]}
        with open(USERS_FILE, "w") as f: json.dump(default, f, indent=2)
    with open(USERS_FILE) as f: return json.load(f).get("users", [])

def authenticate(email, password):
    for u in load_users():
        if u["email"].lower() == email.lower() and u["password"] == password: return u
    return None

def normalize_uc(val):
    if not val: return ""
    return "".join(filter(str.isdigit, str(val).split('.')[0]))

def clean_val(v):
    if not v: return 0.0
    s = str(v).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try: return float(s)
    except: return 0.0

def style_critical(row):
    dias = row['Dias de Atraso']
    if dias > 90: return ['background-color: #ffcccc; color: #990000; font-weight: bold'] * len(row)
    return ['background-color: #fff4cc; color: #856404; font-weight: bold'] * len(row)

# ── 4. LÓGICA DE ANÁLISE ROBUSTA ─────────────────────────────────────────────
def load_planilha(file):
    if file is None: return None
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.csv') else pd.read_csv(file, header=None, sep=None, engine='python')
        for i, row in df.head(20).iterrows():
            row_l = [str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s for s in row_l):
                df.columns = [str(c).strip() for c in row]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

def analyze_performance(df_r, df_e):
    # Identificação de Colunas
    uc_r_col = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    uc_e_col = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_col = next((c for c in df_e.columns if "Competência" in c), None)
    status_col = next((c for c in df_e.columns if "Status" in c), None)
    valor_col = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    venc_col = next((c for c in df_e.columns if "Vencimento" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular" in c), None)

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    # Processamento de Datas
    if venc_col:
        df_e[venc_col] = pd.to_datetime(df_e[venc_col], errors='coerce', dayfirst=True)

    missing_res = {}; inad_res = {}; t_gerado = {}; t_pago = {}; t_vencido = {}
    critical_inad = []

    for _, row in df_e.iterrows():
        uc = str(row['UC_NORM'])
        comp = str(row[comp_col]) if comp_col else "Geral"
        status = str(row[status_col]).lower() if status_col else ""
        valor = clean_val(row[valor_col])
        vencimento = row[venc_col] if venc_col else None

        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp, 0.0) + valor
        
        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp, 0.0) + valor
            item = {"uc": row[uc_e_col], "valor": valor, "titular": row[titular_col] if titular_col else "—", "status": "Vencido"}
            if comp not in inad_res: inad_res[comp] = []
            inad_res[comp].append(item)

            if pd.notnull(vencimento):
                atraso = (TODAY - vencimento).days
                if atraso > 60:
                    critical_inad.append({"Titular": item["titular"], "UC": item["uc"], "Vencimento": vencimento.strftime('%d/%m/%Y'), "Dias de Atraso": atraso, "Valor": valor, "Mês Ref": comp})

    # Cruzamento para faturas faltantes
    extrato_set = set(zip(df_e['UC_NORM'], df_e[comp_col].astype(str)))
    ucs_rateio = df_r['UC_NORM'].unique()
    for comp_ext in df_e[comp_col].unique():
        if not comp_ext or str(comp_ext).lower() == 'nan': continue
        for uc_norm in ucs_rateio:
            if (uc_norm, str(comp_ext)) not in extrato_set:
                r_orig = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if comp_ext not in missing_res: missing_res[comp_ext] = []
                missing_res[comp_ext].append({"uc": r_orig[uc_r_col], "apelido": r_orig.get("Apelido UC", "—"), "usina": r_orig.get("Usina", "—")})

    return {"missing": missing_res, "inad": inad_res, "t_gerado": t_gerado, "t_pago": t_pago, "t_vencido": t_vencido, "critical": critical_inad}

# ── 5. INTERFACE (DASHBOARD CLAUDE + LÓGICA CORRIGIDA) ──────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        st.markdown('<div class="kpi-value">Acesso Restrito</div>', unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar no Hub", use_container_width=True):
                u = authenticate(e, s)
                if u: st.session_state["user"] = u; st.rerun()
        return

    # Header Claude Style
    st.markdown(f"""
    <div class="sunne-header">
        <div>
            <span class="sunne-logo-mark">S</span>
            <span class="sunne-header-title">Sunne Performance</span>
        </div>
        <div class="user-pill">{st.session_state["user"]["name"]} 👋</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=100)
        st.write("---")
        menu = ["Gerenciamento", "Usinas", "Geradores", "Faturamento"]
        if "page" not in st.session_state: st.session_state.page = "Faturamento"
        for item in menu:
            if st.button(item): st.session_state.page = item
        if st.button("🚪 Sair"): del st.session_state["user"]; st.rerun()

    if st.session_state.page == "Faturamento":
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        
        with t1:
            st.markdown('<div class="sunne-card"><div class="kpi-label">Gestão de Arquivos</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Upload Rateio")
            f_e = c2.file_uploader("Upload Extrato")
            if f_r and f_e and st.button("🔄 Rodar Análise Completa", use_container_width=True):
                st.session_state["results"] = analyze_performance(load_planilha(f_r), load_planilha(f_e))
                st.success("✓ Processado!")
            st.markdown('</div>', unsafe_allow_html=True)

        res = st.session_state.get("results")
        if res:
            with t2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faturas faltando"):
                        st.table(pd.DataFrame(items))
            
            with t3:
                # Blocos Mensais
                for comp, rows in res["inad"].items():
                    gerado = res["t_gerado"].get(comp, 1.0)
                    vencido = res["t_vencido"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100)
                    
                    st.markdown(f"### Competência: {comp}")
                    st.markdown(f"""
                    <div class="kpi-row">
                        <div class="kpi-box"><div class="kpi-label">Gerado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>
                        <div class="kpi-box"><div class="kpi-label">Vencido</div><div class="kpi-value danger">R$ {vencido:,.2f}</div></div>
                        <div class="kpi-box"><div class="kpi-label">Taxa</div><div class="kpi-value danger">{taxa:.1f}%</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander(f"Lista de Clientes Vencidos ({comp})"):
                        st.table(pd.DataFrame(rows))
                
                # SEÇÃO CRÍTICA (REINSERIDA)
                st.write("---")
                st.markdown("## 🚨 Inadimplência Crítica (>60 dias)")
                if res["critical"]:
                    df_crit = pd.DataFrame(res["critical"])
                    st.dataframe(df_crit.style.apply(style_critical, axis=1), use_container_width=True, hide_index=True)
                else:
                    st.success("Tudo em dia! Nenhuma fatura com atraso crítico.")

    else:
        st.title(f"Aba {st.session_state.page}")

if __name__ == "__main__": main()
