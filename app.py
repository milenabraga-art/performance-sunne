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

# ── 2. CSS BACKOFFICE PREMIUM (RUBI & LARANJA) ──────────────────────────────
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
[data-testid="stSidebar"] * { color: white !important; }

/* Botões da Sidebar em Laranja */
.stSidebar .stButton > button {
    width: 100% !important;
    background-color: var(--laranja) !important;
    color: white !important;
    border: none !important;
    padding: 12px 20px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
    transition: 0.3s;
}
.stSidebar .stButton > button:hover {
    background-color: #d65a1b !important;
    transform: scale(1.02);
}

/* Card de Login */
.login-card {
    background: white; padding: 3rem; border-radius: 25px;
    box-shadow: 0 15px 35px rgba(51, 0, 26, 0.1);
    border: 1px solid #EAD8D0; max-width: 400px; margin: auto; text-align: center;
}

/* Estilo das Tabelas */
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; background: white; }
.sunne-table th { text-align: left; padding: 10px; background: #FBF5F0; color: #7A5060; border-bottom: 2px solid #EAD8D0; }
.sunne-table td { padding: 10px; border-bottom: 1px solid #F0E4DC; }

/* KPIs */
.kpi-box { background: white; border-radius: 15px; padding: 1.2rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: var(--rubi); }
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

def csv_from_list(rows, cols, headers):
    output = io.StringIO()
    df_temp = pd.DataFrame(rows)
    if not df_temp.empty:
        df_export = df_temp[cols]
        df_export.columns = headers
        df_export.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
    return output.getvalue().encode('utf-8-sig')

# ── 4. LÓGICA DE ANÁLISE (A QUE FUNCIONA 100%) ───────────────────────────────
def load_planilha(file):
    if file is None: return None
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.csv') else pd.read_csv(file, header=None, sep=None, engine='python')
        for i, row in df.head(20).iterrows():
            row_l = [str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s or "numero da uc" in s for s in row_l):
                df.columns = [str(c).strip() for c in row]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

def analyze_performance(df_r, df_e):
    # Localização de colunas
    uc_r_col = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    usina_col = next((c for c in df_r.columns if "Usina" in c), None)
    apelido_col = next((c for c in df_r.columns if "Apelido" in c), None)

    uc_e_col = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_col = next((c for c in df_e.columns if "Competência" in c), None)
    status_col = next((c for c in df_e.columns if "Status" in c), None)
    valor_col = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    leitura_col = next((c for c in df_e.columns if "Leitura Atual" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular" in c), None)

    # Normalização para matching perfeito
    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    missing_res = {}; inad_res = {}; t_gerado = {}; t_pago = {}
    extrato_pairs = set(); comp_leitura = {}

    # Processar Extrato
    for _, row in df_e.iterrows():
        uc = str(row['UC_NORM'])
        comp = str(row[comp_col]) if comp_col else "Geral"
        status = str(row[status_col]).lower() if status_col else ""
        valor = clean_val(row[valor_col]) if valor_col else 0.0

        extrato_pairs.add((uc, comp))
        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp, 0.0) + valor
        
        if "vencido" in status:
            if comp not in inad_res: inad_res[comp] = []
            inad_res[comp].append({
                "uc": row[uc_e_col], "valor": valor, "status": "Vencido",
                "titular": row[titular_col] if titular_col else "—", "comp": comp
            })
            
        if comp not in comp_leitura and leitura_col:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(str(row[leitura_col]).strip(), fmt)
                    comp_leitura[comp] = dt
                    break
                except: comp_leitura[comp] = None

    # Cruzamento de Faltantes (A Lógica dos 63)
    ucs_rateio = df_r['UC_NORM'].unique().tolist()
    competencias = df_e[comp_col].unique() if comp_col else ["Geral"]
    
    for comp in competencias:
        if not comp or str(comp).lower() == "nan": continue
        leitura = comp_leitura.get(comp)
        if leitura and TODAY <= (leitura + timedelta(days=DELAY_DAYS)): continue
        
        for uc_norm in ucs_rateio:
            if (uc_norm, str(comp)) not in extrato_pairs:
                r_orig = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if comp not in missing_res: missing_res[comp] = []
                missing_res[comp].append({
                    "uc": r_orig[uc_r_col],
                    "usina": r_orig[usina_col] if usina_col else "—",
                    "apelido": r_orig[apelido_col] if apelido_col else "—",
                    "comp": comp
                })

    return {"missing": missing_res, "inad": inad_res, "t_gerado": t_gerado, "t_pago": t_pago}

# ── 5. INTERFACE (HUB COM SIDEBAR) ───────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        with st.form("login"):
            e = st.text_input("E-mail corporativo", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Hub", use_container_width=True):
                u = authenticate(e, s)
                if u: st.session_state["user"] = u; st.rerun()
                else: st.error("Login inválido.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Sidebar Rubi com Botões Laranja
    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        st.write(f"Olá, **{st.session_state['user']['name']}** 👋")
        st.write("---")
        
        if "page" not in st.session_state: st.session_state.page = "faturamento"
        
        if st.button("📊 Dashboard"): st.session_state.page = "dash"
        if st.button("🌱 Usinas"): st.session_state.page = "usinas"
        if st.button("⚙️ Geradores"): st.session_state.page = "geradores"
        if st.button("📈 Rateio"): st.session_state.page = "rateio"
        if st.button("💳 Faturamento"): st.session_state.page = "faturamento"
        
        st.write("---")
        if st.button("🚪 Sair"):
            del st.session_state["user"]; st.rerun()

    # Roteamento de Páginas
    if st.session_state.page == "faturamento":
        st.title("💳 Gestão de Faturamento")
        tab1, tab2, tab3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        
        with tab1:
            st.markdown('<div class="kpi-box">Suba os arquivos para processar a performance</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Planilha de Rateio", type=["xlsx", "csv"])
            f_e = c2.file_uploader("Extrato Detalhado", type=["xlsx", "csv"])
            if f_r and f_e:
                if st.button("🔄 Rodar Análise Completa", use_container_width=True):
                    df_r = load_planilha(f_r)
                    df_e = load_planilha(f_e)
                    if df_r is not None and df_e is not None:
                        st.session_state["results"] = analyze_performance(df_r, df_e)
                        st.success("✓ Análise Concluída!")

        res = st.session_state.get("results")
        if res:
            with tab2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faturas não encontradas"):
                        csv = csv_from_list(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"])
                        st.download_button(f"⬇ Baixar Lista {comp}", csv, f"faltantes_{comp}.csv", "text/csv", key=f"dl_{comp}")
                        st.write(pd.DataFrame(items)[["uc", "apelido", "usina"]])
            
            with tab3:
                for comp, rows in res["inad"].items():
                    vencido = sum(r["valor"] for r in rows)
                    gerado = res["t_gerado"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100) if gerado > 0 else 0
                    st.markdown(f"#### {comp}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Gerado", f"R$ {gerado:,.2f}")
                    c2.metric("Vencido", f"R$ {vencido:,.2f}", delta=f"{taxa:.1f}% Inad.", delta_color="inverse")
                    st.table(pd.DataFrame(rows)[["uc", "titular", "valor"]])

    elif st.session_state.page == "dash": st.title("📊 Dashboard")
    elif st.session_state.page == "usinas": st.title("🌱 Usinas")
    elif st.session_state.page == "geradores": st.title("⚙️ Geradores")
    elif st.session_state.page == "rateio": st.title("📈 Rateio")

if __name__ == "__main__":
    main()
