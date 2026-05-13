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

# ── 2. ESTILIZAÇÃO SUNNE® PREMIUM ──────────────────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

:root {
    --rubi: #33001A; --dourado: #FAB200; --magenta: #FF365E;
    --laranja: #F36E21; --bg: #FDF8F5; --card-bg: #FFFFFF; --border: #EAD8D0;
}

/* Sidebar Rubi Minimalista */
[data-testid="stSidebar"] { background-color: var(--rubi) !important; border-right: 1px solid rgba(255,255,255,0.1); }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important; border: none !important; padding: 0px !important;
    margin-bottom: 20px !important; width: 100% !important; display: flex !important; justify-content: flex-start !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p { font-size: 16px; transition: 0.3s; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p { color: var(--laranja) !important; font-weight: 700; }

/* Header */
.sunne-header {
    background: var(--rubi); padding: 1rem 2rem; display: flex;
    align-items: center; justify-content: space-between; margin: 0rem -1rem 1.5rem -1rem;
}
.sunne-logo-mark {
    width: 40px; height: 40px; background: var(--dourado); border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-weight: 700; color: var(--rubi); margin-right: 12px;
}
.sunne-header-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px; color: #FFFFFF; }

/* Cards e KPIs */
.sunne-card { background: #FFFFFF; border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; }
.kpi-row { display: flex; gap: 12px; margin-top: 1rem; flex-wrap: wrap; }
.kpi-box { background: #FBF5F0; border-radius: 10px; padding: .85rem 1.1rem; flex: 1; min-width: 150px; border: 1px solid var(--border); }
.kpi-label { font-size: 11px; color: #7A5060; text-transform: uppercase; font-weight: 600; margin-bottom: 5px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: var(--rubi); }
.kpi-value.danger { color: var(--magenta); }

/* Tabelas */
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sunne-table th { text-align: left; padding: .6rem; background: #FBF5F0; color: #7A5060; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
.sunne-table td { padding: .6rem; border-bottom: .5px solid #F0E4DC; color: #1A0A0F; }
</style>
"""

# ── 3. UTILITÁRIOS DE LÓGICA E EXPORTAÇÃO ───────────────────────────────────
def normalize_uc(val):
    if not val: return ""
    return "".join(filter(str.isdigit, str(val).split('.')[0]))

def clean_val(v):
    if v is None or str(v).lower() in ("nan", ""): return 0.0
    s = str(v).replace("R$", "").replace(" ", "").strip()
    # Corrige formato BR: 1.234,56 -> 1234.56
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    return output.getvalue()

# ── 4. LÓGICA DE ANÁLISE CORRIGIDA ──────────────────────────────────────────
def analyze_performance(df_r, df_e):
    # Encontrar colunas dinamicamente
    def find(df, keys):
        for k in keys:
            for c in df.columns:
                if k.lower() in str(c).lower(): return c
        return df.columns[0]

    uc_r_col = find(df_r, ["UC Nova", "Atual"])
    uc_e_col = find(df_e, ["Número da UC", "Numero"])
    comp_col = find(df_e, ["Competência", "Mês"])
    status_col = find(df_e, ["Status"])
    valor_col = find(df_e, ["Total a Pagar", "Valor"])
    venc_col = find(df_e, ["Vencimento"])
    titular_col = find(df_e, ["Titular"])

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    missing = {}; inad = {}; t_gerado = {}; t_vencido = {}; critical = []

    if venc_col:
        df_e[venc_col] = pd.to_datetime(df_e[venc_col], errors='coerce', dayfirst=True)

    for _, row in df_e.iterrows():
        comp = str(row[comp_col])
        valor = clean_val(row[valor_col])
        status = str(row[status_col]).lower()
        
        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        
        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp, 0.0) + valor
            item = {"UC": row[uc_e_col], "Titular": row.get(titular_col, "—"), "Valor": valor, "Status": "Vencido"}
            if comp not in inad: inad[comp] = []
            inad[comp].append(item)

            if venc_col and pd.notnull(row[venc_col]):
                dias = (datetime.now() - row[venc_col]).days
                if dias > 60:
                    critical.append({"Titular": item["Titular"], "UC": item["UC"], "Dias": dias, "Valor": valor, "Mês": comp})

    # Cruzamento de Captura
    extrato_set = set(zip(df_e['UC_NORM'], df_e[comp_col].astype(str)))
    ucs_rateio = df_r['UC_NORM'].unique()
    for c_mes in df_e[comp_col].unique():
        if not c_mes or str(c_mes) == "nan": continue
        for uc_norm in ucs_rateio:
            if (uc_norm, str(c_mes)) not in extrate_set:
                orig = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if c_mes not in missing: missing[c_mes] = []
                missing[c_mes].append({"UC": orig[uc_r_col], "Apelido": orig.get("Usina", "—"), "Mês": c_mes})

    return {"missing": missing, "inad": inad, "t_gerado": t_gerado, "t_vencido": t_vencido, "critical": critical}

# ── 5. INTERFACE PRINCIPAL ───────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        st.markdown('<div style="max-width:400px; margin:10vh auto; text-align:center;" class="sunne-card">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        with st.form("login"):
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar") and s == "sunne2026":
                st.session_state.user = "Milena"; st.rerun()
        return

    st.markdown(f'<div class="sunne-header"><div><span class="sunne-logo-mark">S</span><span class="sunne-header-title">Sunne Performance</span></div><div style="color:white">Olá, Milena 👋</div></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=100)
        st.write("---")
        menu = ["Gerenciamento", "Usinas", "Geradores", "Faturamento"]
        if "page" not in st.session_state: st.session_state.page = "Faturamento"
        for item in menu:
            if st.button(item): st.session_state.page = item
        if st.button("🚪 Sair"): st.session_state.clear(); st.rerun()

    if st.session_state.page == "Faturamento":
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        
        with t1:
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Rateio")
            f_e = c2.file_uploader("Extrato")
            if f_r and f_e and st.button("🔄 Rodar Análise"):
                df_r = pd.read_excel(f_r) if f_r.name.endswith('xlsx') else pd.read_csv(f_r)
                df_e = pd.read_excel(f_e) if f_e.name.endswith('xlsx') else pd.read_csv(f_e)
                st.session_state.results = analyze_performance(df_r, df_e)
                st.success("✓ Analisado!")

        res = st.session_state.get("results")
        if res:
            with t2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        df_miss = pd.DataFrame(items)
                        st.download_button("📥 Exportar para Excel", to_excel(df_miss), f"faltantes_{comp}.xlsx")
                        st.table(df_miss)
            
            with t3:
                for comp, rows in res["inad"].items():
                    gerado = res["t_gerado"].get(comp, 1.0)
                    vencido = res["t_vencido"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100)
                    st.markdown(f"### {comp}")
                    st.markdown(f"""<div class="kpi-row">
                        <div class="kpi-box"><div class="kpi-label">Gerado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>
                        <div class="kpi-box"><div class="kpi-label">Vencido</div><div class="kpi-value danger">R$ {vencido:,.2f}</div></div>
                        <div class="kpi-box"><div class="kpi-label">Taxa</div><div class="kpi-value danger">{taxa:.1f}%</div></div>
                    </div>""", unsafe_allow_html=True)
                    with st.expander("Ver lista e Exportar"):
                        df_inad = pd.DataFrame(rows)
                        st.download_button("📥 Exportar para Excel", to_excel(df_inad), f"inadimplencia_{comp}.xlsx")
                        st.table(df_inad)
    else:
        st.info(f"Módulo {st.session_state.page} em construção.")

if __name__ == "__main__": main()
