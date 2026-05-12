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

# ── 2. CSS BACKOFFICE (APENAS TEXTO - SEM BLOCOS) ────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --rubi: #33001A;
    --laranja: #F36E21;
    --bg: #FDF8F5;
}

[data-testid="stAppViewContainer"] { background-color: var(--bg); }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar Rubi */
[data-testid="stSidebar"] {
    background-color: var(--rubi) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
}

/* Remover estilo de botão e deixar apenas o texto */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important;
    border: none !important;
    color: white !important;
    padding: 0px !important;
    margin-bottom: 15px !important;
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
    text-align: left !important;
    box-shadow: none !important;
}

/* Estilo do texto da aba */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
    color: white !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    transition: 0.3s;
}

/* Efeito ao passar o mouse: a palavra fica laranja */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p {
    color: var(--laranja) !important;
    font-weight: 700 !important;
}

/* Elementos de login e KPIs */
.login-card { background: white; padding: 3rem; border-radius: 25px; box-shadow: 0 15px 35px rgba(51, 0, 26, 0.1); border: 1px solid #EAD8D0; max-width: 400px; margin: auto; text-align: center; }
.kpi-box { background: white; border-radius: 15px; padding: 1.2rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: var(--rubi); }
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
    s = str(val).strip().split('.')[0]
    return "".join(filter(str.isdigit, s))

def clean_val(v):
    if not v: return 0.0
    s = str(v).replace("R$", "").replace(" ", "").strip()
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

# ── 4. LÓGICA DE ANÁLISE ─────────────────────────────────────────────────────
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
    uc_r_col = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    uc_e_col = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_col = next((c for c in df_e.columns if "Competência" in c), None)
    status_col = next((c for c in df_e.columns if "Status" in c), None)
    valor_col = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular" in c), None)

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    missing_res = {}; inad_res = {}; t_gerado = {}; t_pago = {}; t_vencido = {}

    for _, row in df_e.iterrows():
        uc = str(row['UC_NORM'])
        comp = str(row[comp_col]) if comp_col else "Geral"
        status = str(row[status_col]).lower() if status_col else ""
        valor = clean_val(row[valor_col])

        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp, 0.0) + valor
        
        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp, 0.0) + valor
            if comp not in inad_res: inad_res[comp] = []
            inad_res[comp].append({
                "uc": row[uc_e_col], "valor": valor, "titular": row[titular_col] if titular_col else "—"
            })

    extrato_set = set(zip(df_e['UC_NORM'], df_e[comp_col].astype(str)))
    ucs_rateio = df_r['UC_NORM'].unique()
    
    for comp in df_e[comp_col].unique():
        if not comp or str(comp).lower() == 'nan': continue
        for uc_norm in ucs_rateio:
            if (uc_norm, str(comp)) not in extrato_set:
                r_orig = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if comp not in missing_res: missing_res[comp] = []
                missing_res[comp].append({
                    "uc": r_orig[uc_r_col], "apelido": r_orig.get("Apelido UC", "—"), "usina": r_orig.get("Usina", "—")
                })

    return {"missing": missing_res, "inad": inad_res, "t_gerado": t_gerado, "t_pago": t_pago, "t_vencido": t_vencido}

# ── 5. INTERFACE ─────────────────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        with st.form("login"):
            e = st.text_input("E-mail", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Hub", use_container_width=True):
                u = authenticate(e, s)
                if u: st.session_state["user"] = u; st.rerun()
        return

    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        st.write(f"Olá, {st.session_state['user']['name']} 👋")
        st.write("---")
        
        # NAVEGAÇÃO APENAS TEXTO
        if "page" not in st.session_state: st.session_state.page = "faturamento"
        if st.button("Dashboard"): st.session_state.page = "dash"
        if st.button("Usinas"): st.session_state.page = "usinas"
        if st.button("Geradores"): st.session_state.page = "geradores"
        if st.button("Rateio"): st.session_state.page = "rateio"
        if st.button("Faturamento"): st.session_state.page = "faturamento"
        
        st.write("---")
        if st.button("Sair"): del st.session_state["user"]; st.rerun()

    if st.session_state.page == "faturamento":
        st.title("💳 Gestão de Faturamento")
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        
        with t1:
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Rateio")
            f_e = c2.file_uploader("Extrato")
            if f_r and f_e and st.button("🔄 Rodar Análise"):
                st.session_state["results"] = analyze_performance(load_planilha(f_r), load_planilha(f_e))
                st.success("✓ Concluído!")

        res = st.session_state.get("results")
        if res:
            with t2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        st.table(pd.DataFrame(items))
            with t3:
                for comp, rows in res["inad"].items():
                    gerado = res["t_gerado"].get(comp, 0.0)
                    pago = res["t_pago"].get(comp, 0.0)
                    vencido = res["t_vencido"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100) if gerado > 0 else 0
                    
                    st.markdown(f"### Competência: {comp}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Gerado", f"R$ {gerado:,.2f}")
                    c2.metric("Pago", f"R$ {pago:,.2f}")
                    c3.metric("Vencido", f"R$ {vencido:,.2f}")
                    c4.metric("Inadimplência", f"{taxa:.1f}%")
                    with st.expander("Ver lista de clientes inadimplentes"):
                        st.table(pd.DataFrame(rows))
    else:
        st.title(f"Aba {st.session_state.page.capitalize()}")

if __name__ == "__main__":
    main()
