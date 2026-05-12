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

# ── 2. CSS Sunne® (Login Bonito + KPIs Claros) ───────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

[data-testid="stAppViewContainer"] { background-color: #FDF8F5; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 1100px; }

:root {
    --rubi: #33001A; --dourado: #FAB200; --magenta: #FF365E;
    --laranja: #FF6B1A; --turquesa: #69E0CF; --bg: #FDF8F5;
}

.sunne-header {
    background: #33001A; padding: 1.2rem 2.5rem; display: flex;
    align-items: center; justify-content: space-between;
    margin: -1rem -1rem 2rem -1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.sunne-logo-mark {
    width: 42px; height: 42px; background: #FAB200; border-radius: 12px;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 20px;
    color: #33001A; margin-right: 15px; vertical-align: middle;
}
.sunne-header-title {
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 20px; color: #FFFFFF;
}
.user-pill { background: rgba(255,255,255,0.12); border-radius: 8px; padding: 4px 12px; font-size: 12px; color: #FFFFFF; }

/* Tela de Login */
.login-container { display: flex; justify-content: center; align-items: center; padding-top: 8vh; }
.login-card {
    background: #FFFFFF; padding: 3.5rem; border-radius: 30px;
    box-shadow: 0 20px 40px rgba(51, 0, 26, 0.08); border: 1px solid #EAD8D0;
    max-width: 420px; width: 100%; text-align: center;
}
.login-logo-big {
    width: 80px; height: 80px; background: #33001A; color: #FAB200;
    font-family: 'Syne', sans-serif; font-size: 38px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    border-radius: 22px; margin: 0 auto 1.5rem; box-shadow: 0 8px 20px rgba(250, 178, 0, 0.3);
}

/* KPIs e Tabelas */
.sunne-card { background: #FFFFFF; border: 1px solid #EAD8D0; border-radius: 20px; padding: 1.8rem; margin-bottom: 1rem; }
.kpi-row { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
.kpi-box { background: #FBF5F0; border-radius: 15px; padding: 1.2rem; border: 1px solid #F0E4DC; flex: 1; min-width: 180px; }
.kpi-label { font-size: 10px; color: #7A5060; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: #33001A; }
.kpi-value.danger { color: #FF365E; }
.kpi-value.ok { color: #0A8A7A; }
.sunne-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.sunne-table th { text-align: left; padding: 0.8rem; background: #FBF5F0; color: #7A5060; border-bottom: 2px solid #EAD8D0; font-size: 11px; text-transform: uppercase; }
.sunne-table td { padding: 0.8rem; border-bottom: 1px solid #F0E4DC; }
</style>
"""

# ── 3. Utilitários e Segurança ────────────────────────────────────────────────
USERS_FILE = "users.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        default = {"users": [{"name": "Milena", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]}
        with open(USERS_FILE, "w") as f: json.dump(default, f, indent=2)
    with open(USERS_FILE) as f: return json.load(f).get("users", [])

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

# ── 4. Lógica de Negócio ─────────────────────────────────────────────────────
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
    # Identificação de colunas
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
        valor = clean_val(row[valor_c]) if valor_c else 0.0

        extrato_pairs.add((uc, comp))
        if comp not in comp_leitura:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try: 
                    comp_leitura[comp] = datetime.strptime(str(row[leitura_c]).strip(), fmt)
                    break
                except: comp_leitura[comp] = None

        # Cálculos de Inadimplência
        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp, 0.0) + valor
        
        # FILTRO: Apenas status VENCIDO
        if "vencido" in status:
            if comp not in inad_mes: inad_mes[comp] = []
            inad_mes[comp].append({"uc": uc, "valor": valor, "status": "Vencido", "titular": str(row.get("Titular da Conta", "—"))})

    # Faltantes de Captura
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

# ── 5. Interface ─────────────────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    if "user" not in st.session_state:
        st.markdown('<div class="login-container"><div class="login-card"><div class="login-logo-big">S</div>'
                    '<h3>Sunne Performance</h3><p style="font-size:13px; color:#7A5060">Gestão de Performance</p>', unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail"); s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Sistema", use_container_width=True):
                if authenticate(e, s): st.session_state["user"] = e; st.rerun()
                else: st.error("Erro no login.")
        st.markdown('</div></div>', unsafe_allow_html=True); return

    st.markdown(f'<div class="sunne-header"><div><span class="sunne-logo-mark">S</span><span class="sunne-header-title">Sunne Performance</span></div></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
    
    with t1:
        st.markdown('<div class="sunne-card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2); f_r = c1.file_uploader("Rateio"); f_e = c2.file_uploader("Extrato")
        if f_r and f_e:
            if st.button("Analisar Tudo", use_container_width=True):
                st.session_state["analysis"] = analyze(load_planilha(f_r), load_planilha(f_e))
                st.success("✓ Pronto!")
        st.markdown('</div>', unsafe_allow_html=True)

    res = st.session_state.get("analysis")
    if res:
        with t2:
            for comp, items in res["missing"].items():
                with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                    csv = csv_export(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"])
                    st.download_button(f"⬇ Baixar Lista {comp}", csv, f"captura_{comp}.csv", "text/csv", key=f"cap_{comp}")
                    st.write(pd.DataFrame(items))
        with t3:
            for comp, rows in res["inad"].items():
                vencido = sum(r["valor"] for r in rows)
                gerado = res["t_gerado"].get(comp, 0.0)
                pago = res["t_pago"].get(comp, 0.0)
                taxa = (vencido / gerado * 100) if gerado > 0 else 0
                st.markdown(f"#### {comp}")
                st.markdown(f'<div class="kpi-row">'
                            f'<div class="kpi-box"><div class="kpi-label">Faturado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>'
                            f'<div class="kpi-box"><div class="kpi-label">Pago</div><div class="kpi-value ok">R$ {pago:,.2f}</div></div>'
                            f'<div class="kpi-box"><div class="kpi-label">Vencido</div><div class="kpi-value danger">R$ {vencido:,.2f}</div></div>'
                            f'<div class="kpi-box"><div class="kpi-label">% Inadimplência</div><div class="kpi-value danger">{taxa:.1f}%</div></div>'
                            f'</div>', unsafe_allow_html=True)
                with st.expander(f"Detalhes de Vencidos - {comp}"):
                    csv_inad = csv_export(rows, ["uc", "titular", "valor"], ["UC", "Titular", "Valor"])
                    st.download_button(f"⬇ Exportar Vencidos {comp}", csv_inad, f"inadimplencia_{comp}.csv", "text/csv", key=f"in_{comp}")
                    st.write(pd.DataFrame(rows))

if __name__ == "__main__": main()
