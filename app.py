import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import io

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne Performance",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Paleta Sunne® e CSS global (Design Claude ORIGINAL) ────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

/* Reset e base */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Esconde elementos padrão do Streamlit */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 1100px; }

/* Variáveis de cor Sunne® */
:root {
    --rubi:     #33001A;
    --dourado:  #FAB200;
    --magenta:  #FF365E;
    --laranja:  #FF6B1A;
    --turquesa: #69E0CF;
    --bege:     #F2C7A3;
    --bg:        #FDF8F5;
    --card-bg:  #FFFFFF;
    --muted:    #7A5060;
    --border:   #EAD8D0;
}

/* Header fixo */
.sunne-header {
    background: #33001A;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 1.5rem -1rem;
    border-radius: 0;
}
.sunne-logo-mark {
    width: 40px; height: 40px;
    background: #FAB200;
    border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px;
    color: #33001A; margin-right: 12px; vertical-align: middle;
}
.sunne-header-title {
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px;
    color: #FFFFFF; display: inline; vertical-align: middle;
}
.sunne-header-sub {
    font-size: 12px; color: rgba(255,255,255,0.55); margin-top: 2px;
}
.user-pill {
    background: rgba(255,255,255,0.12); border-radius: 8px;
    padding: 4px 12px; font-size: 12px; color: #FFFFFF; display: inline-block;
}

/* Cards */
.sunne-card {
    background: #FFFFFF;
    border: 1px solid #EAD8D0;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.sunne-card-title {
    font-family: 'Syne', sans-serif; font-weight: 700;
    font-size: 15px; color: #33001A; margin-bottom: 1rem;
}

/* KPI cards */
.kpi-row { display: flex; gap: 12px; margin-top: 1rem; flex-wrap: wrap; }
.kpi-box {
    background: #FBF5F0; border-radius: 10px;
    padding: .85rem 1.1rem; flex: 1; min-width: 150px;
}
.kpi-label { font-size: 11px; color: #7A5060; margin-bottom: 4px; text-transform: uppercase; letter-spacing: .05em; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: #33001A; }
.kpi-value.danger { color: #FF365E; }
.kpi-value.ok      { color: #0A8A7A; }

/* Badges */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 6px;
    font-size: 11px; font-weight: 600;
}
.badge-warn   { background: #FFF0F3; color: #CC1A3A; }
.badge-ok      { background: #F0FDFB; color: #0A7A6A; }
.badge-info   { background: #FFF8E6; color: #7A5010; }
.badge-orange { background: #FFF3EC; color: #C04010; }

/* Alert bar */
.alert-bar {
    background: #FFF0F3; border: 1px solid #FFCDD5;
    border-radius: 10px; padding: .75rem 1rem;
    font-size: 13px; color: #8B1530; margin-bottom: 1rem;
}

/* Upload boxes */
.upload-hint {
    background: #FBF5F0; border: 2px dashed #D4B5A8;
    border-radius: 12px; padding: 1.5rem; text-align: center;
    font-size: 13px; color: #7A5060;
}

/* Tabelas */
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sunne-table th {
    text-align: left; padding: .55rem .75rem;
    background: #FBF5F0; color: #7A5060;
    font-size: 11px; font-weight: 500;
    text-transform: uppercase; letter-spacing: .04em;
    border-bottom: 1px solid #EAD8D0;
}
.sunne-table td {
    padding: .55rem .75rem;
    border-bottom: .5px solid #F0E4DC;
    color: #1A0A0F;
}
.sunne-table tr:last-child td { border-bottom: none; }
.sunne-table tr:hover td { background: #FBF8F5; }
.uc-mono { font-family: monospace; font-size: 12.5px; }

/* Streamlit overrides */
.stButton > button {
    background: #FAB200 !important; color: #33001A !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 14px !important; padding: .7rem 1.8rem !important;
    cursor: pointer !important;
}
.stButton > button:hover { opacity: .88 !important; }

.stDownloadButton > button {
    background: transparent !important; color: #33001A !important;
    border: 1.5px solid #33001A !important; border-radius: 8px !important;
    font-size: 12px !important; font-weight: 600 !important;
    padding: .4rem .9rem !important;
}
.stDownloadButton > button:hover {
    background: #33001A !important; color: #FFFFFF !important;
}

/* Abas Streamlit */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px; border-bottom: 1.5px solid #EAD8D0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif !important; font-size: 13px !important;
    font-weight: 600 !important; color: #7A5060 !important;
    border-bottom: 2.5px solid transparent !important;
    background: transparent !important; border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #33001A !important;
    border-bottom-color: #FAB200 !important;
}

/* Login */
.login-wrap {
    max-width: 420px; margin: 6vh auto; padding: 3rem 2.5rem;
    background: #FFFFFF; border-radius: 20px;
    border: 1px solid #EAD8D0; text-align: center;
}
.login-mark {
    width: 60px; height: 60px; background: #33001A;
    border-radius: 14px; display: flex; align-items: center; justify-content: center;
    margin: 0 auto 1.2rem;
    font-family: 'Syne', sans-serif; font-weight: 700;
    font-size: 26px; color: #FAB200;
}
.login-title {
    font-family: 'Syne', sans-serif; font-weight: 700;
    font-size: 22px; color: #33001A; margin-bottom: .3rem;
}
.login-sub { font-size: 13px; color: #7A5060; margin-bottom: 1.5rem; }

div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
</style>
"""

# ── Constantes ────────────────────────────────────────────────────────────────
USERS_FILE = "users.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

# ── Utilitários ───────────────────────────────────────────────────────────────
def load_users() -> list:
    if not os.path.exists(USERS_FILE):
        default = {"users": [{"name": "Milena", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]}
        with open(USERS_FILE, "w") as f: json.dump(default, f, indent=2)
    with open(USERS_FILE) as f: return json.load(f).get("users", [])

def authenticate(email: str, password: str):
    for u in load_users():
        if u["email"].lower() == email.lower() and u["password"] == password: return u
    return None

def clean_val(v):
    """LIMPEZA PARA EVITAR BUG DE SOMA DE TEXTO"""
    if v is None or str(v).lower() in ("nan", ""): return 0.0
    s = str(v).replace("R$", "").replace(" ", "").strip()
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def to_excel(rows, cols, headers):
    """CONVERTER PARA EXCEL/SHEETS"""
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[cols]
        df.columns = headers
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sunne_Performance')
    return output.getvalue()

def normalize_col(df: pd.DataFrame, patterns: list) -> str | None:
    for p in patterns:
        for c in df.columns:
            if pd.Series([c]).str.contains(p, case=False, regex=True).any(): return c
    return None

def load_planilha(uploaded_file) -> pd.DataFrame | None:
    if uploaded_file is None: return None
    try:
        df = pd.read_excel(uploaded_file, dtype=str) if not uploaded_file.name.lower().endswith(".csv") else pd.read_csv(uploaded_file, dtype=str)
        df.columns = df.columns.str.strip()
        return df.fillna("")
    except: return None

def parse_date(v: str) -> datetime | None:
    if not v or v.strip() == "": return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try: return datetime.strptime(v.strip(), fmt)
        except: continue
    return None

# ── Lógica de análise ─────────────────────────────────────────────────────────
def analyze(df_rateio: pd.DataFrame, df_extrato: pd.DataFrame) -> dict:
    uc_r_col = normalize_col(df_rateio, [r"uc\s*(nova|atual)", r"número\s*da\s*uc"])
    uc_e_col = normalize_col(df_extrato, [r"uc\s*(nova|atual)", r"número\s*da\s*uc"])
    comp_col = normalize_col(df_extrato, [r"^competência$", r"^competencia$", r"competência\s*[-–]\s*extenso"])
    leitura_col = normalize_col(df_extrato, [r"leitura\s*atual"])
    valor_col = normalize_col(df_extrato, [r"total\s*a\s*pagar", r"total\s*pagar"])
    status_col = normalize_col(df_extrato, [r"status\s*de\s*pagamento", r"^status$"])
    venc_col = normalize_col(df_extrato, [r"vencimento"])
    
    if not uc_r_col or not uc_e_col: return {"errors": ["Colunas de UC não encontradas."]}

    # Normalizar UCs
    df_rateio[uc_r_col] = df_rateio[uc_r_col].str.strip().str.replace(r"\.0$", "", regex=True)
    df_extrato[uc_e_col] = df_extrato[uc_e_col].str.strip().str.replace(r"\.0$", "", regex=True)

    ucs_rateio = df_rateio[uc_r_col].unique().tolist()
    extrato_pairs = set()
    comp_leitura = {}
    
    for _, row in df_extrato.iterrows():
        extrato_pairs.add((row[uc_e_col], str(row[comp_col])))
        c = str(row[comp_col])
        if leitura_col and c not in comp_leitura:
            comp_leitura[c] = parse_date(row[leitura_col])

    # Faltantes e Inadimplência
    missing = {}; inadimplentes = {}; total_gerado_mes = {}

    for _, row in df_extrato.iterrows():
        comp = str(row[comp_col])
        valor = clean_val(row[valor_col])
        
        # SOMA MATEMÁTICA (FIM DO BUG DOS NÚMEROS LONGOS)
        total_gerado_mes[comp] = total_gerado_mes.get(comp, 0.0) + valor

        status = str(row[status_col]).lower()
        if "pago" not in status:
            if comp not in inadimplentes: inadimplentes[comp] = []
            inadimplentes[comp].append({
                "uc": row[uc_e_col], "titular": row.get("Titular", "—"), 
                "valor": valor, "status": row[status_col]
            })

    # Cruzamento de Captura
    for comp in df_extrato[comp_col].unique():
        if not comp: continue
        for uc in ucs_rateio:
            if (uc, str(comp)) not in extrato_pairs:
                if comp not in missing: missing[comp] = []
                missing[comp].append({"uc": uc, "comp": comp})

    return {
        "missing": missing, "inadimplentes": inadimplentes,
        "total_por_comp": total_gerado_mes, "errors": []
    }

# ── Interface (Design Claude) ─────────────────────────────────────────────────
def table_html(rows: list, cols: list, headers: list) -> str:
    html = '<table class="sunne-table"><thead><tr>'
    for h in headers: html += f"<th>{h}</th>"
    html += "</tr></thead><tbody>"
    for r in rows:
        html += "<tr>"
        for c in cols:
            val = r.get(c, "—")
            if c == "valor": val = f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            html += f"<td>{val}</td>"
        html += "</tr>"
    return html + "</tbody></table>"

def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.markdown('<div class="login-wrap"><div class="login-mark">S</div><div class="login-title">Sunne Performance</div></div>', unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail"); s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                u = authenticate(e, s)
                if u: st.session_state["user"] = u; st.rerun()
        return

    # Header
    st.markdown(f'<div class="sunne-header"><div><span class="sunne-logo-mark">S</span><span class="sunne-header-title">Sunne Performance</span></div><div class="user-pill">{st.session_state.user["name"]} 👋</div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["📂 Importar", "🔍 Gestão de Captura", "💳 Inadimplência"])

    with tabs[0]:
        st.markdown('<div class="sunne-card"><div class="sunne-card-title">Upload de Planilhas</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_r = c1.file_uploader("Rateio")
        f_e = c2.file_uploader("Extrato")
        if f_r and f_e and st.button("Analisar Performance"):
            st.session_state["analysis"] = analyze(load_planilha(f_r), load_planilha(f_e))
            st.success("Análise concluída!")
        st.markdown('</div>', unsafe_allow_html=True)

    res = st.session_state.get("analysis")
    if res:
        with tabs[1]:
            for comp, items in res["missing"].items():
                with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                    # BOTÃO EXPORTAR CAPTURA
                    excel_cap = to_excel(items, ["uc", "comp"], ["Nº UC", "Competência"])
                    st.download_button(f"📥 Baixar Lista {comp} (Excel)", excel_cap, f"captura_{comp}.xlsx")
                    st.markdown(table_html(items, ["uc", "comp"], ["Nº UC", "Competência"]), unsafe_allow_html=True)

        with tabs[2]:
            for comp, rows in res["inadimplentes"].items():
                total_inad = sum(r["valor"] for r in rows)
                total_mes = res["total_por_comp"].get(comp, 1.0)
                taxa = (total_inad / total_mes * 100)
                
                st.markdown(f'<div class="sunne-card"><div class="sunne-card-title">{comp}</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="kpi-row">
                    <div class="kpi-box"><div class="kpi-label">Total Vencido</div><div class="kpi-value danger">R$ {total_inad:,.2f}</div></div>
                    <div class="kpi-box"><div class="kpi-label">Total Gerado</div><div class="kpi-value">R$ {total_mes:,.2f}</div></div>
                    <div class="kpi-box"><div class="kpi-label">Taxa</div><div class="kpi-value danger">{taxa:.1f}%</div></div>
                </div>
                """, unsafe_allow_html=True)
                
                # BOTÃO EXPORTAR INADIMPLÊNCIA
                excel_inad = to_excel(rows, ["uc", "titular", "valor", "status"], ["Nº UC", "Titular", "Valor", "Status"])
                st.download_button(f"📥 Baixar Inadimplência {comp} (Excel)", excel_inad, f"inadimplencia_{comp}.xlsx")
                st.markdown(table_html(rows, ["uc", "titular", "valor"], ["UC", "Titular", "Valor"]), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
