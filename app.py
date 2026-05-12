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
    initial_sidebar_state="collapsed",
)

# ── 2. CSS "BLINDADO" SUNNE (FOCO EM VISIBILIDADE) ───────────────────────────
SUNNE_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

/* Reset de Cores do Streamlit */
[data-testid="stAppViewContainer"] { background-color: #F8F9FA !important; }
[data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #33001A; }

/* ESCONDER ELEMENTOS NATIVOS */
#MainMenu, footer, header { visibility: hidden; }

/* TELA DE LOGIN CENTRALIZADA */
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    padding-top: 10vh;
}

.login-card {
    background: #FFFFFF !important;
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(51, 0, 26, 0.15) !important;
    width: 100%;
    max-width: 400px;
    text-align: center;
    border: 1px solid #EAD8D0 !important;
}

/* LOGO TIPO "S" */
.login-logo {
    width: 70px; height: 70px;
    background-color: #33001A !important;
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 1.5rem;
    font-size: 35px; font-weight: 700; color: #F36E21 !important;
}

/* LABELS DO FORMULÁRIO (EMAIL/SENHA) */
.stTextInput label {
    color: #33001A !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    margin-bottom: 8px !important;
}

/* BOTÃO LARANJA VIBRANTE */
.stButton>button {
    background-color: #F36E21 !important;
    color: white !important;
    border: none !important;
    width: 100% !important;
    padding: 12px !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    box-shadow: 0 4px 10px rgba(243, 110, 33, 0.3) !important;
}

/* SIDEBAR RUBI */
[data-testid="stSidebar"] { background-color: #33001A !important; }
[data-testid="stSidebar"] * { color: white !important; }

/* TABELAS E KPIS */
.kpi-box { background: white; border-radius: 12px; padding: 1rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-value { font-size: 20px; font-weight: 700; color: #33001A; }
.sunne-table { width: 100%; border-collapse: collapse; background: white; }
.sunne-table th { background: #F8F9FA; color: #33001A; padding: 10px; border-bottom: 2px solid #EEE; }
</style>
"""

# ── 3. UTILITÁRIOS E SEGURANÇA ────────────────────────────────────────────────
USERS_FILE = "users_db.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        initial = [{"name": "Milena", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]
        with open(USERS_FILE, "w") as f: json.dump(initial, f)
        return initial
    with open(USERS_FILE, "r") as f: return json.load(f)

def clean_val(v):
    if not v or str(v).lower() in ("nan", ""): return 0.0
    s = str(v).replace("R$", "").replace(" ", "").strip()
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def load_planilha(file):
    if file is None: return None
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.csv') else pd.read_csv(file, header=None, sep=None, engine='python')
        for i, row in df.head(20).iterrows():
            row_l = [str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s for s in row_l):
                df.columns = [str(c).strip() for c in df.columns]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

# ── 4. LÓGICA DE ANÁLISE (INTELIGÊNCIA) ──────────────────────────────────────
def analyze(df_r, df_e):
    uc_r = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    uc_e = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_c = next((c for c in df_e.columns if "Competência" in c), None)
    status_c = next((c for c in df_e.columns if "Status" in c), None)
    valor_c = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    leitura_c = next((c for c in df_e.columns if "Leitura Atual" in c), None)
    
    df_r[uc_r] = df_r[uc_r].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df_e[uc_e] = df_e[uc_e].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    missing = {}; inad_mes = {}; t_gerado = {}; t_pago = {}
    extrato_pairs = set(); comp_leitura = {}

    for _, row in df_e.iterrows():
        uc, comp = str(row[uc_e]), str(row[comp_c])
        status = str(row[status_c]).lower() if status_c else ""
        valor = clean_val(row[valor_c])

        extrato_pairs.add((uc, comp))
        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp, 0.0) + valor
        if "vencido" in status:
            if comp not in inad_mes: inad_mes[comp] = []
            inad_mes[comp].append({"uc": uc, "valor": valor, "status": "Vencido", "titular": str(row.get("Titular da Conta", "—"))})

        if comp not in comp_leitura and leitura_c:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try: 
                    comp_leitura[comp] = datetime.strptime(str(row[leitura_c]).strip(), fmt)
                    break
                except: comp_leitura[comp] = None

    ucs_r = df_r[uc_r].unique().tolist()
    for comp in df_e[comp_c].unique():
        if not comp: continue
        leitura = comp_leitura.get(comp)
        if leitura and TODAY <= (leitura + timedelta(days=DELAY_DAYS)): continue
        for uc in ucs_r:
            if (uc, comp) not in extrato_pairs:
                r_data = df_r[df_r[uc_r] == uc]
                if comp not in missing: missing[comp] = []
                missing[comp].append({"uc": uc, "apelido": r_data.iloc[0].get("Apelido UC", "—"), "usina": r_data.iloc[0].get("Usina", "—"), "comp": comp})

    return {"missing": missing, "inad": inad_mes, "t_gerado": t_gerado, "t_pago": t_pago}

# ── 5. INTERFACE DO APP ──────────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_THEME_CSS, unsafe_allow_html=True)
    
    if "user_data" not in st.session_state:
        # TELA DE LOGIN VISÍVEL
        st.markdown('<div class="login-container"><div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-logo">S</div>', unsafe_allow_html=True)
        st.markdown('<h2 style="color:#33001A; margin-bottom:5px;">Sunne Hub</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color:#7A5060; font-size:14px; margin-bottom:20px;">Performance & Faturamento</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            e = st.text_input("E-mail corporativo", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Sistema"):
                users = load_users()
                found = next((u for u in users if u["email"].lower() == e.lower() and u["password"] == s), None)
                if found:
                    st.session_state["user_data"] = found
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
        st.markdown('</div></div>', unsafe_allow_html=True)
        return

    # SESSÃO LOGADA
    user = st.session_state["user_data"]
    
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        if st.button("🚪 Sair do Sistema"):
            del st.session_state["user_data"]
            st.rerun()
        st.write("---")
        if "page" not in st.session_state: st.session_state.page = "perf"
        if st.button("📊 Performance"): st.session_state.page = "perf"
        if st.button("👥 Analistas"): st.session_state.page = "users"

    if st.session_state.page == "perf":
        st.subheader("📊 Análise de Performance")
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        
        with t1:
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Rateio")
            f_e = c2.file_uploader("Extrato")
            if f_r and f_e:
                if st.button("🔄 Rodar Análise Completa", use_container_width=True):
                    res = analyze(load_planilha(f_r), load_planilha(f_e))
                    st.session_state["analysis_result"] = res
                    st.success("✓ Pronto!")

        res = st.session_state.get("analysis_result")
        if res:
            with t2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        st.table(pd.DataFrame(items)[["uc", "apelido", "usina"]])
            with t3:
                for comp, rows in res["inad"].items():
                    vencido = sum(r["valor"] for r in rows)
                    gerado = res["t_gerado"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100) if gerado > 0 else 0
                    st.markdown(f"#### {comp}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Gerado", f"R$ {gerado:,.2f}")
                    c2.metric("Vencido", f"R$ {vencido:,.2f}")
                    c3.metric("Taxa", f"{taxa:.1f}%")

if __name__ == "__main__":
    main()
