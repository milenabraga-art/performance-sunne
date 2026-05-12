import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import io

# ── 1. Configuração da Página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne Performance",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 2. Estilização Sunne® ──────────────────────────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 1100px; }
:root {
    --rubi: #33001A; --dourado: #FAB200; --magenta: #FF365E;
    --laranja: #FF6B1A; --turquesa: #69E0CF; --bege: #F2C7A3;
    --bg: #FDF8F5; --card-bg: #FFFFFF; --muted: #7A5060; --border: #EAD8D0;
}
.sunne-header {
    background: #33001A; padding: 1rem 2rem; display: flex;
    align-items: center; justify-content: space-between;
    margin: -1rem -1rem 1.5rem -1rem; border-radius: 0;
}
.sunne-logo-mark {
    width: 40px; height: 40px; background: #FAB200; border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px;
    color: #33001A; margin-right: 12px; vertical-align: middle;
}
.sunne-header-title {
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px;
    color: #FFFFFF; display: inline; vertical-align: middle;
}
.user-pill {
    background: rgba(255,255,255,0.12); border-radius: 8px;
    padding: 4px 12px; font-size: 12px; color: #FFFFFF;
}
.sunne-card {
    background: #FFFFFF; border: 1px solid #EAD8D0;
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
}
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
.sunne-table th { text-align: left; padding: .6rem; background: #FBF5F0; color: #7A5060; border-bottom: 1px solid #EAD8D0; font-size: 11px; text-transform: uppercase; }
.sunne-table td { padding: .6rem; border-bottom: .5px solid #F0E4DC; color: #1A0A0F; }
.kpi-row { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
.kpi-box { background: #FBF5F0; border-radius: 12px; padding: 1.2rem; flex: 1; min-width: 180px; border: 1px solid #EAD8D0; }
.kpi-label { font-size: 10px; color: #7A5060; text-transform: uppercase; margin-bottom: 5px; font-weight: 600; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: #33001A; }
.kpi-value.danger { color: #FF365E; }
.kpi-value.ok { color: #0A8A7A; }
</style>
"""

# ── 3. Constantes e Dados ──────────────────────────────────────────────────
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

def parse_date(v):
    if not v or str(v).lower() in ("nan", ""): return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try: return datetime.strptime(str(v).strip(), fmt)
        except: continue
    return None

def clean_val(v):
    """Limpa valores monetários de forma agressiva"""
    if not v: return 0.0
    s = str(v).replace("R$", "").strip()
    if not s or s.lower() == "nan": return 0.0
    # Se houver ponto e vírgula (formato BR), remove ponto (milhar) e troca vírgula por ponto (decimal)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
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

# ── 4. Processamento ─────────────────────────────────────────────────────────
def load_planilha(uploaded_file):
    if uploaded_file is None: return None
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file, dtype=str, header=None, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file, sheet_name=0, dtype=str, header=None)
        
        for i, row in df.head(15).iterrows():
            row_list = [str(cell).strip().lower() for cell in row]
            if any("uc nova/atual" in s or "número da uc" in s for s in row_list):
                df.columns = [str(cell).strip() for cell in row]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except Exception as e:
        st.error(f"Erro ao carregar: {e}"); return None

def analyze(df_r, df_e):
    # Colunas
    uc_r_col = next((c for c in df_r.columns if "UC Nova/Atual" in c), df_r.columns[0])
    usina_r_col = next((c for c in df_r.columns if "Usina" in c), None)
    apelido_col = next((c for c in df_r.columns if "Apelido" in c), None)

    uc_e_col = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_col = next((c for c in df_e.columns if "Competência" in c), None)
    leitura_col = next((c for c in df_e.columns if "Leitura Atual" in c), None)
    valor_col = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    status_col = next((c for c in df_e.columns if "Status" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular" in c), None)

    df_r[uc_r_col] = df_r[uc_r_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df_e[uc_e_col] = df_e[uc_e_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    ucs_rateio = df_r[uc_r_col].unique().tolist()
    extrato_pairs = set()
    comp_leitura = {}
    
    # Inadimplência stats
    inad_mes = {}; total_gerado_mes = {}; total_pago_mes = {}

    for _, row in df_e.iterrows():
        uc = str(row[uc_e_col])
        comp = str(row[comp_col])
        status = str(row[status_col]).lower() if status_col else ""
        valor = clean_val(row[valor_col]) if valor_col else 0.0

        extrato_pairs.add((uc, comp))
        if leitura_col and comp not in comp_leitura:
            comp_leitura[comp] = parse_date(row[leitura_col])

        # Cálculos Financeiros
        total_gerado_mes[comp] = total_gerado_mes.get(comp, 0.0) + valor
        if "pago" in status:
            total_pago_mes[comp] = total_pago_mes.get(comp, 0.0) + valor
        
        if "vencido" in status:
            if comp not in inad_mes: inad_mes[comp] = []
            inad_mes[comp].append({
                "uc": uc, "valor": valor, "status": "Vencido",
                "titular": row[titular_col] if titular_col else "—", "comp": comp
            })

    # Faltantes
    missing = {}
    for comp in df_e[comp_col].unique():
        if not comp: continue
        leitura = comp_leitura.get(str(comp))
        if leitura and TODAY <= (leitura + timedelta(days=DELAY_DAYS)): continue
        for uc in ucs_rateio:
            if (uc, str(comp)) not in extrato_pairs:
                r = df_r[df_r[uc_r_col] == uc]
                if comp not in missing: missing[comp] = []
                missing[comp].append({
                    "uc": uc, "usina": r.iloc[0][usina_r_col] if usina_r_col else "—",
                    "apelido": r.iloc[0][apelido_col] if apelido_col else "—", "comp": comp
                })

    return {
        "missing": missing, "inad": inad_mes, 
        "t_gerado": total_gerado_mes, "t_pago": total_pago_mes
    }

# ── 5. UI ──────────────────────────────────────────────────────────────────
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
    
    # Persistência de Login simples
    if "user" not in st.session_state:
        st.markdown('<div class="login-wrap"><div class="login-mark">S</div><div class="login-title">Sunne Performance</div></div>', unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail"); s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                u = authenticate(e, s)
                if u: st.session_state["user"] = u; st.rerun()
                else: st.error("Login inválido.")
        return

    st.markdown(f'<div class="sunne-header"><div><span class="sunne-logo-mark">S</span><span class="sunne-header-title">Sunne Performance</span></div><div class="user-pill">{st.session_state["user"]["name"]}</div></div>', unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
    
    with t1:
        st.markdown('<div class="sunne-card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2); f_r = c1.file_uploader("Planilha de Rateio"); f_e = c2.file_uploader("Extrato Detalhado")
        if f_r and f_e:
            if st.button("Analisar Performance", use_container_width=True):
                with st.spinner("Analisando..."):
                    st.session_state["analysis"] = analyze(load_planilha(f_r), load_planilha(f_e))
                    st.success("✓ Dados Processados!")
        st.markdown('</div>', unsafe_allow_html=True)

    res = st.session_state.get("analysis")
    if res:
        with t2:
            miss = res["missing"]
            if not miss: st.success("✅ Captura em dia.")
            else:
                for comp, items in miss.items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        csv = csv_from_list(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"])
                        st.download_button(f"⬇ Baixar CSV {comp}", csv, f"faltantes_{comp}.csv", "text/csv", key=f"dl_{comp}")
                        st.markdown(table_html(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"]), unsafe_allow_html=True)

        with t3:
            inad = res["inad"]
            for comp, rows in inad.items():
                vencido = sum(r["valor"] for r in rows)
                gerado = res["t_gerado"].get(comp, 0.0)
                pago = res["t_pago"].get(comp, 0.0)
                taxa = (vencido / gerado * 100) if gerado > 0 else 0
                
                st.markdown(f"#### Competência: {comp}")
                st.markdown(f'<div class="kpi-row">'
                            f'<div class="kpi-box"><div class="kpi-label">Total Gerado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>'
                            f'<div class="kpi-box"><div class="kpi-label">Total Pago</div><div class="kpi-value ok">R$ {pago:,.2f}</div></div>'
                            f'<div class="kpi-box"><div class="kpi-label">Total Vencido</div><div class="kpi-value danger">R$ {vencido:,.2f}</div></div>'
                            f'<div class="kpi-box"><div class="kpi-label">% Inadimplência</div><div class="kpi-value danger">{taxa:.1f}%</div></div>'
                            f'</div>', unsafe_allow_html=True)
                
                with st.expander(f"Lista de Vencidos - {comp}"):
                    st.markdown(table_html(rows, ["uc", "titular", "valor", "status"], ["UC", "Titular", "Valor", "Status"]), unsafe_allow_html=True)

if __name__ == "__main__": main()
