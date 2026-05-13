import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import io

# ── 1. Configuração da página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne Performance",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 2. Estilização Sunne® (Design Claude Original) ──────────────────────────
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
.sunne-header-sub { font-size: 12px; color: rgba(255,255,255,0.55); margin-top: 2px; }
.user-pill {
    background: rgba(255,255,255,0.12); border-radius: 8px;
    padding: 4px 12px; font-size: 12px; color: #FFFFFF;
}
.sunne-card {
    background: #FFFFFF; border: 1px solid #EAD8D0;
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
}
.sunne-card-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; color: #33001A; margin-bottom: 1rem; }
.kpi-row { display: flex; gap: 12px; margin-top: 1rem; flex-wrap: wrap; }
.kpi-box { background: #FBF5F0; border-radius: 10px; padding: .85rem 1.1rem; flex: 1; min-width: 150px; }
.kpi-label { font-size: 11px; color: #7A5060; margin-bottom: 4px; text-transform: uppercase; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: #33001A; }
.kpi-value.danger { color: #FF365E; }
.kpi-value.ok { color: #0A8A7A; }
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sunne-table th { text-align: left; padding: .55rem; background: #FBF5F0; color: #7A5060; border-bottom: 1px solid #EAD8D0; font-size: 11px; text-transform: uppercase; }
.sunne-table td { padding: .55rem; border-bottom: .5px solid #F0E4DC; color: #1A0A0F; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.badge-warn { background: #FFF0F3; color: #CC1A3A; }
.badge-info { background: #FFF8E6; color: #7A5010; }
.login-wrap { max-width: 420px; margin: 6vh auto; padding: 3rem 2.5rem; background: #FFFFFF; border-radius: 20px; border: 1px solid #EAD8D0; text-align: center; }
.login-mark { width: 60px; height: 60px; background: #33001A; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.2rem; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 26px; color: #FAB200; }
</style>
"""

# ── 3. Utilitários de Lógica (Recuperados do Código Funcional) ───────────────
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

# ── 4. Lógica de Análise (Focada em Faturamento e Inadimplência Crítica) ──────
def analyze(df_r, df_e):
    # Identificar colunas dinamicamente
    def find_col(df, keywords):
        for k in keywords:
            for c in df.columns:
                if k.lower() in str(c).lower(): return c
        return None

    uc_r_col = find_col(df_r, ["uc nova", "atual", "uc"])
    uc_e_col = find_col(df_e, ["número da uc", "numero da uc", "uc"])
    comp_col = find_col(df_e, ["competência", "mes", "mês"])
    status_col = find_col(df_e, ["status"])
    valor_col = find_col(df_e, ["total a pagar", "valor"])
    venc_col = find_col(df_e, ["vencimento"])
    titular_col = find_col(df_e, ["titular"])
    usina_col = find_col(df_r, ["usina"])
    apelido_col = find_col(df_r, ["apelido"])

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    if venc_col:
        df_e[venc_col] = pd.to_datetime(df_e[venc_col], errors='coerce', dayfirst=True)

    missing = {}; inadimplentes = {}; total_gerado_mes = {}; critical_inad = []

    for _, row in df_e.iterrows():
        comp = str(row[comp_col])
        valor = clean_val(row[valor_col])
        total_gerado_mes[comp] = total_gerado_mes.get(comp, 0.0) + valor

        status = str(row[status_col]).lower()
        if "vencido" in status:
            uc = row[uc_e_col]
            item = {"uc": uc, "titular": row.get(titular_col, "—"), "valor": valor, "status": status}
            if comp not in inadimplentes: inadimplentes[comp] = []
            inadimplentes[comp].append(item)

            if venc_col and pd.notnull(row[venc_col]):
                atraso = (TODAY - row[venc_col]).days
                if atraso > 60:
                    critical_inad.append({
                        "Titular": item["titular"], "UC": item["uc"], 
                        "Vencimento": row[venc_col].strftime('%d/%m/%Y'),
                        "Dias de Atraso": atraso, "Valor": valor, "Mês Ref": comp
                    })

    # Cruzamento de Captura
    extrato_set = set(zip(df_e['UC_NORM'], df_e[comp_col].astype(str)))
    ucs_rateio = df_r['UC_NORM'].unique()
    for comp_mes in df_e[comp_col].unique():
        if not comp_mes or str(comp_mes) == "nan": continue
        for uc_norm in ucs_rateio:
            if (uc_norm, str(comp_mes)) not in extrato_set:
                r_data = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if comp_mes not in missing: missing[comp_mes] = []
                missing[comp_mes].append({
                    "uc": r_data[uc_r_col], "usina": r_data.get(usina_col, "—"), 
                    "apelido": r_data.get(apelido_col, "—"), "comp": comp_mes
                })

    return {
        "missing": missing, "inadimplentes": inadimplentes,
        "total_gerado": total_gerado_mes, "critical": critical_inad,
        "n_ucs": len(ucs_rateio), "n_extrato": len(df_e)
    }

# ── 5. Componentes HTML e UI (Design Claude) ──────────────────────────────────
def render_header(user):
    st.markdown(f"""
    <div class="sunne-header">
        <div>
            <span class="sunne-logo-mark">S</span>
            <span class="sunne-header-title">Sunne Performance</span>
            <div class="sunne-header-sub" style="margin-left:52px">Gestão de Faturamento & Inadimplência</div>
        </div>
        <div class="user-pill">{user['name']} 👋</div>
    </div>
    """, unsafe_allow_html=True)

def table_html(rows, cols, headers):
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

# ── 6. Interface Principal ───────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.markdown('<div class="login-wrap"><div class="login-mark">S</div><div class="login-title">Sunne Performance</div></div>', unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail"); s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                u = authenticate(e, s)
                if u: st.session_state["user"] = u; st.rerun()
                else: st.error("Acesso negado.")
        return

    render_header(st.session_state["user"])

    with st.sidebar:
        st.write(f"**{st.session_state.user['name']}**")
        if st.button("🚪 Sair"):
            st.session_state.clear(); st.rerun()

    t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])

    with t1:
        st.markdown('<div class="sunne-card"><div class="sunne-card-title">Upload de Planilhas</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_r = c1.file_uploader("Rateio", type=["xlsx", "csv"])
        f_e = c2.file_uploader("Extrato", type=["xlsx", "csv"])
        if f_r and f_e:
            if st.button("Analisar Performance", use_container_width=True):
                df_r = pd.read_excel(f_r) if f_r.name.endswith('xlsx') else pd.read_csv(f_r)
                df_e = pd.read_excel(f_e) if f_e.name.endswith('xlsx') else pd.read_csv(f_e)
                st.session_state["analysis"] = analyze(df_r, df_e)
                st.success("Análise concluída!")
        st.markdown('</div>', unsafe_allow_html=True)

    res = st.session_state.get("analysis")
    if res:
        with t2:
            for comp, items in res["missing"].items():
                with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                    st.markdown(table_html(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"]), unsafe_allow_html=True)

        with t3:
            for comp, rows in res["inadimplentes"].items():
                vencido = sum(r["valor"] for r in rows)
                gerado = res["total_gerado"].get(comp, 1.0)
                taxa = (vencido / gerado * 100)
                st.markdown(f'<div class="sunne-card"><div class="sunne-card-title">{comp}</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="kpi-row">
                    <div class="kpi-box"><div class="kpi-label">Gerado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>
                    <div class="kpi-box"><div class="kpi-label">Vencido</div><div class="kpi-value danger">R$ {vencido:,.2f}</div></div>
                    <div class="kpi-box"><div class="kpi-label">Taxa</div><div class="kpi-value danger">{taxa:.1f}%</div></div>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("Ver lista de clientes"):
                    st.markdown(table_html(rows, ["uc", "titular", "valor"], ["UC", "Titular", "Valor"]), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.write("---")
            st.markdown("## 🚨 Inadimplência Crítica (>60 dias)")
            if res["critical"]:
                df_c = pd.DataFrame(res["critical"])
                st.dataframe(df_c.style.apply(style_critical, axis=1), use_container_width=True, hide_index=True)
            else:
                st.success("Nenhuma inadimplência crítica detectada.")

if __name__ == "__main__": main()
