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

# ── 2. CSS BACKOFFICE SUNNE (DESIGN RUBI E TEXTO BRANCO) ──────────────────────
SUNNE_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

:root {
    --rubi: #33001A;
    --laranja: #F36E21;
}

[data-testid="stAppViewContainer"] { background-color: #FDF8F5; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar Rubi com texto Branco */
[data-testid="stSidebar"] {
    background-color: var(--rubi) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
}
[data-testid="stSidebar"] * { 
    color: white !important; 
}

/* Botões da Sidebar (Abas) */
.stButton>button {
    width: 100%;
    background-color: transparent !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    text-align: left !important;
    padding: 10px !important;
    border-radius: 8px !important;
    margin-bottom: 5px;
}
.stButton>button:hover {
    background-color: var(--laranja) !important;
    border-color: var(--laranja) !important;
}

/* Header Superior Rubi */
.top-header {
    background-color: var(--rubi);
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 30px;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 999;
}

/* KPIs */
.kpi-box { background: white; border-radius: 12px; padding: 1rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-label { font-size: 10px; color: #7A5060; text-transform: uppercase; font-weight: 700; }
.kpi-value { font-size: 18px; font-weight: 700; color: var(--rubi); }
.danger-text { color: #FF365E !important; }

/* Login Box */
.login-card {
    max-width: 400px; margin: 80px auto; padding: 40px;
    background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    text-align: center; border: 1px solid #EAD8D0;
}
</style>
"""

# ── 3. UTILITÁRIOS E SEGURANÇA ────────────────────────────────────────────────
USERS_FILE = "users_db.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        initial = [{"name": "Milena Braga", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]
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
        # Lê o arquivo ignorando erros de cabeçalho iniciais
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

# ── 4. LÓGICA DE ANÁLISE (RECUPERADA E BLINDADA) ─────────────────────────────
def analyze(df_r, df_e):
    if df_r is None or df_e is None: return None
    
    # Busca inteligente de colunas
    uc_r = next((c for c in df_r.columns if "UC Nova" in c or "UC" == c), df_r.columns[0])
    uc_e = next((c for c in df_e.columns if "Número da UC" in c or "Número" in c), df_e.columns[0])
    comp_c = next((c for c in df_e.columns if "Competência" in c), None)
    leitura_c = next((c for c in df_e.columns if "Leitura Atual" in c), None)
    valor_c = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    status_c = next((c for c in df_e.columns if "Status" in c), None)
    
    # Normalização
    df_r[uc_r] = df_r[uc_r].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df_e[uc_e] = df_e[uc_e].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    missing = {}; inad_mes = {}; t_gerado = {}; t_pago = {}
    extrato_pairs = set(); comp_leitura = {}

    for _, row in df_e.iterrows():
        uc = str(row[uc_e])
        comp = str(row[comp_c]) if comp_c else "Sem Competência"
        status = str(row[status_c]).lower() if status_c else ""
        valor = clean_val(row[valor_c]) if valor_c else 0.0

        extrato_pairs.add((uc, comp))
        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp, 0.0) + valor
        
        if "vencido" in status:
            if comp not in inad_mes: inad_mes[comp] = []
            inad_mes[comp].append({
                "uc": uc, "valor": valor, "status": "Vencido",
                "titular": str(row.get("Titular da Conta", "—"))
            })

        if comp not in comp_leitura and leitura_c:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try: 
                    comp_leitura[comp] = datetime.strptime(str(row[leitura_c]).strip(), fmt)
                    break
                except: comp_leitura[comp] = None

    # Captura Faltante
    ucs_r = df_r[uc_r].unique().tolist()
    for comp in df_e[comp_c].unique() if comp_c else []:
        if not comp: continue
        leitura = comp_leitura.get(comp)
        if leitura and TODAY <= (leitura + timedelta(days=DELAY_DAYS)): continue
        for uc in ucs_r:
            if (uc, comp) not in extrato_pairs:
                r_data = df_r[df_r[uc_r] == uc]
                if comp not in missing: missing[comp] = []
                missing[comp].append({
                    "uc": uc, "apelido": r_data.iloc[0].get("Apelido UC", "—"), 
                    "usina": r_data.iloc[0].get("Usina", "—"), "comp": comp
                })

    return {"missing": missing, "inad": inad_mes, "t_gerado": t_gerado, "t_pago": t_pago}

# ── 5. INTERFACE (O VISUAL RUBI QUE FUNCIONA) ────────────────────────────────
def main():
    st.markdown(SUNNE_THEME_CSS, unsafe_allow_html=True)
    
    if "user_data" not in st.session_state:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        with st.form("login"):
            e = st.text_input("E-mail corporativo", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Sistema", use_container_width=True):
                users = load_users()
                found = next((u for u in users if u["email"].lower() == e.lower() and u["password"] == s), None)
                if found:
                    st.session_state["user_data"] = found
                    st.rerun()
                else: st.error("Login Inválido")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    user = st.session_state["user_data"]

    # Sidebar Rubi
    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        
        # Menu de Perfil
        with st.popover(f"👤 {user['name']}", use_container_width=True):
            st.write(user['email'])
            if st.button("🚪 Sair do Sistema"):
                del st.session_state["user_data"]
                st.rerun()
        
        st.write("---")
        if "page" not in st.session_state: st.session_state.page = "perf"
        if st.button("📊 Performance"): st.session_state.page = "perf"
        if st.button("👥 Gerenciar Analistas"): st.session_state.page = "users"

    # Conteúdo
    if st.session_state.page == "perf":
        st.subheader("📊 Análise de Performance")
        
        with st.expander("🔍 Busca Avançada", expanded=False):
            c1, c2 = st.columns(2)
            c1.text_input("UC")
            c2.selectbox("Mês", ["Todos"])

        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        
        with t1:
            st.info("Suba as planilhas para gerar os relatórios.")
            f_r = st.file_uploader("Upload Rateio")
            f_e = st.file_uploader("Upload Extrato")
            if f_r and f_e:
                if st.button("🔄 Rodar Análise Completa", use_container_width=True):
                    res = analyze(load_planilha(f_r), load_planilha(f_e))
                    st.session_state["analysis_res"] = res
                    st.success("✓ Análise Concluída!")

        # Mostrar Resultados
        res = st.session_state.get("analysis_res")
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
