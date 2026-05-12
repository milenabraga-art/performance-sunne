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

# ── 2. CSS PREMIUM SUNNE® (LOGIN COMPACTO & DASHBOARD) ───────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --rubi: #33001A; --dourado: #FAB200; --magenta: #FF365E;
    --laranja: #FF6B1A; --bg: #FDF8F5;
}

[data-testid="stAppViewContainer"] { background-color: var(--bg); }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Login Card - AGORA MAIS COMPACTO */
.login-wrap { 
    display: flex; justify-content: center; align-items: center; 
    padding-top: 10vh; /* Desceu um pouco para centralizar melhor */
}
.login-card {
    background: white; 
    padding: 2rem; /* Reduzido de 3.5rem */
    border-radius: 20px;
    box-shadow: 0 10px 25px rgba(51, 0, 26, 0.05); 
    border: 1px solid #EAD8D0;
    max-width: 360px; /* Reduzido de 420px */
    width: 100%; 
    text-align: center;
}
.login-logo-big {
    width: 60px; height: 60px; /* Reduzido de 80px */
    background: #33001A; color: #FAB200;
    font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    border-radius: 15px; margin: 0 auto 1rem; 
    box-shadow: 0 4px 12px rgba(250, 178, 0, 0.2);
}

/* Ajustes de formulário no login */
div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
.stTextInput > div > div > input { background-color: #FBF5F0 !important; border-radius: 8px !important; }

/* Dashboard e Sidebar */
[data-testid="stSidebar"] { background-color: #33001A; border-right: 1px solid rgba(255,255,255,0.1); }
[data-testid="stSidebar"] * { color: white !important; }

.sunne-card { background: #FFFFFF; border: 1px solid #EAD8D0; border-radius: 20px; padding: 1.5rem; margin-bottom: 1rem; }
.kpi-row { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
.kpi-box { background: #FBF5F0; border-radius: 12px; padding: 1rem; border: 1px solid #F0E4DC; flex: 1; min-width: 160px; text-align: center; }
.kpi-label { font-size: 10px; color: #7A5060; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 700; color: #33001A; }
.kpi-value.danger { color: #FF365E; }

.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sunne-table th { text-align: left; padding: 0.6rem; background: #FBF5F0; color: #7A5060; border-bottom: 2px solid #EAD8D0; font-size: 10px; text-transform: uppercase; }
.sunne-table td { padding: 0.6rem; border-bottom: 1px solid #F0E4DC; }

.main-header {
    background: white; padding: 0.8rem 1.5rem; border-radius: 12px;
    margin-bottom: 1rem; border: 1px solid #EAD8D0;
    display: flex; justify-content: space-between; align-items: center;
}
</style>
"""

# ── 3. UTILITÁRIOS E SEGURANÇA ────────────────────────────────────────────────
USERS_FILE = "users_db.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        initial = [{"name": "Milena", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]
        save_users(initial)
        return initial
    with open(USERS_FILE, "r") as f: return json.load(f)

def save_users(users_list):
    with open(USERS_FILE, "w") as f: json.dump(users_list, f, indent=4)

def authenticate(email, password):
    for u in load_users():
        if u["email"].lower() == email.lower() and u["password"] == password: return u
    return None

def clean_val(v):
    if not v or str(v).lower() in ("nan", ""): return 0.0
    s = str(v).replace("R$", "").replace(" ", "").strip()
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def csv_export(rows, cols, headers):
    output = io.StringIO()
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[cols]
        df.columns = headers
        df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
    return output.getvalue().encode('utf-8-sig')

# ── 4. LÓGICA DE PROCESSAMENTO ────────────────────────────────────────────────
def load_planilha(file):
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

def analyze(df_r, df_e):
    uc_r = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    uc_e = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_c = next((c for c in df_e.columns if "Competência" in c), None)
    leitura_c = next((c for c in df_e.columns if "Leitura Atual" in c), None)
    valor_c = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    status_c = next((c for c in df_e.columns if "Status" in c), None)
    
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

        if comp not in comp_leitura:
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
def table_html(rows, cols, headers):
    h = '<table class="sunne-table"><thead><tr>'
    for head in headers: h += f"<th>{head}</th>"
    h += "</tr></thead><tbody>"
    for r in rows:
        h += "<tr>"
        for c in cols:
            val = r.get(c, "—")
            if c == "valor": val = f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            h += f"<td>{val}</td>"
        h += "</tr>"
    return h + "</tbody></table>"

def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    
    if "user_data" not in st.session_state:
        st.markdown('<div class="login-wrap"><div class="login-card"><div class="login-logo-big">S</div>'
                    '<h4 style="color:#33001A; font-family:Syne; margin-bottom:0px;">Sunne Hub</h4>'
                    '<p style="font-size:12px; color:#7A5060; margin-bottom:15px;">Performance & Faturamento</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            e = st.text_input("E-mail corporativo")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                user = authenticate(e, s)
                if user: st.session_state["user_data"] = user; st.rerun()
                else: st.error("Incorreto.")
        st.markdown('</div></div>', unsafe_allow_html=True); return

    # SESSÃO LOGADA
    user = st.session_state["user_data"]
    
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.write("---")
        menu_opt = ["📊 Análise de Performance", "📋 Informações de Rateio"]
        if user["role"] == "admin": menu_opt.append("👥 Gerenciar Usuários")
        menu = st.radio("Menu", menu_opt)
        st.write("---")
        if st.button("🚪 Sair"):
            del st.session_state["user_data"]
            st.rerun()

    st.markdown(f'<div class="main-header"><span style="font-family:Syne; font-weight:700; color:#33001A;">Sunne Performance</span><span style="font-size:12px; color:#7A5060;">{user["name"]}</span></div>', unsafe_allow_html=True)

    # --- ABA: PERFORMANCE ---
    if menu == "📊 Análise de Performance":
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Gestão de Captura", "💳 Inadimplência"])
        with t1:
            st.markdown('<div class="sunne-card">', unsafe_allow_html=True)
            c1, c2 = st.columns(2); f_r = c1.file_uploader("Rateio"); f_e = c2.file_uploader("Extrato")
            if f_r and f_e:
                if st.button("Analisar Tudo", use_container_width=True):
                    st.session_state["analysis"] = analyze(load_planilha(f_r), load_planilha(f_e))
                    st.success("✓ Analisado!")
            st.markdown('</div>', unsafe_allow_html=True)

        res = st.session_state.get("analysis")
        if res:
            with t2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        csv = csv_export(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"])
                        st.download_button(f"⬇ Baixar CSV {comp}", csv, f"captura_{comp}.csv", "text/csv", key=f"cap_{comp}")
                        st.markdown(table_html(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"]), unsafe_allow_html=True)
            with t3:
                for comp, rows in res["inad"].items():
                    vencido = sum(r["valor"] for r in rows)
                    gerado = res["t_gerado"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100) if gerado > 0 else 0
                    st.markdown(f"#### {comp}")
                    st.markdown(f'<div class="kpi-row">'
                                f'<div class="kpi-box"><div class="kpi-label">Faturado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>'
                                f'<div class="kpi-box"><div class="kpi-label">Vencido</div><div class="kpi-value danger">R$ {vencido:,.2f}</div></div>'
                                f'<div class="kpi-box"><div class="kpi-label">Inadimplência</div><div class="kpi-value danger">{taxa:.1f}%</div></div>'
                                f'</div>', unsafe_allow_html=True)
                    with st.expander(f"Detalhes de Vencidos - {comp}"):
                        csv_in = csv_export(rows, ["uc", "titular", "valor"], ["UC", "Titular", "Valor"])
                        st.download_button(f"⬇ Exportar Vencidos {comp}", csv_in, f"vencidos_{comp}.csv", "text/csv", key=f"in_{comp}")
                        st.markdown(table_html(rows, ["uc", "titular", "valor", "status"], ["UC", "Titular", "Valor", "Status"]), unsafe_allow_html=True)

    # --- ABA: USUÁRIOS ---
    elif menu == "👥 Gerenciar Usuários":
        st.title("Gestão de Analistas")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Novo Cadastro")
            with st.form("new_u"):
                n = st.text_input("Nome"); em = st.text_input("E-mail"); p = st.text_input("Senha", type="password"); r = st.selectbox("Perfil", ["user", "admin"])
                if st.form_submit_button("Cadastrar"):
                    users = load_users()
                    users.append({"name": n, "email": em, "password": p, "role": r})
                    save_users(users); st.success("Cadastrado!")
        with c2:
            st.subheader("Equipe")
            st.table(pd.DataFrame(load_users())[["name", "email", "role"]])

    # --- ABA: RATEIO ---
    elif menu == "📋 Informações de Rateio":
        st.title("Base de Rateio")
        st.info("Utilize a aba de Importação para carregar dados aqui.")

if __name__ == "__main__": main()
