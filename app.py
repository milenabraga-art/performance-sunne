import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io

# ── 1. CONFIGURAÇÃO DA PÁGINA ────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne Performance",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. CSS BACKOFFICE ────────────────────────────────────────────────────────
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

[data-testid="stSidebar"] {
    background-color: var(--rubi) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
}

[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important;
    border: none !important;
    color: white !important;
    padding: 0px !important;
    margin-bottom: 20px !important;
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
    text-align: left !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
    color: white !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    transition: 0.3s;
}

[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p {
    color: var(--laranja) !important;
    font-weight: 700 !important;
}

.stButton>button {
    background-color: var(--laranja) !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
}
</style>
"""

# ── 3. UTILITÁRIOS ───────────────────────────────────────────────────────────
def load_users():
    if not os.path.exists("users.json"):
        default = {"users": [{"name": "Milena", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]}
        with open("users.json", "w") as f: json.dump(default, f, indent=2)
    with open("users.json") as f: return json.load(f).get("users", [])

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

def color_rows(row):
    """Lógica de cores para a tabela de inadimplência"""
    dias = row['Dias de Atraso']
    if dias > 90:
        return ['background-color: #ffcccc; color: #990000; font-weight: bold'] * len(row)
    return ['background-color: #fff4cc; color: #856404'] * len(row)

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
    # Identificação de colunas
    uc_r_col = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    uc_e_col = next((c for c in df_e.columns if "Número da UC" in c), df_e.columns[0])
    comp_col = next((c for c in df_e.columns if "Competência" in c), None)
    status_col = next((c for c in df_e.columns if "Status" in c), None)
    valor_col = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular" in c), None)
    venc_col = next((c for c in df_e.columns if "Vencimento" in c), None)

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)
    
    # Conversão de data para cálculo
    if venc_col:
        df_e[venc_col] = pd.to_datetime(df_e[venc_col], errors='coerce', dayfirst=True)

    missing_res = {}; inad_res = {}; t_gerado = {}; t_pago = {}; t_vencido = {}
    hoje = datetime.now()

    for _, row in df_e.iterrows():
        comp = str(row[comp_col]) if comp_col else "Geral"
        status = str(row[status_col]).lower() if status_col else ""
        valor = clean_val(row[valor_col])
        vencimento = row[venc_col]

        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp, 0.0) + valor
        
        # REGRA: Status Vencido
        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp, 0.0) + valor
            
            # SUB-REGRA: Mais de 60 dias de atraso (Alerta para retirar do Rateio)
            if pd.notnull(vencimento):
                atraso = (hoje - vencimento).days
                if atraso > 60:
                    if comp not in inad_res: inad_res[comp] = []
                    inad_res[comp].append({
                        "titular": row[titular_col] if titular_col else "—",
                        "uc": row[uc_e_col], 
                        "vencimento": vencimento.strftime('%d/%m/%Y'),
                        "Dias de Atraso": atraso,
                        "valor": valor
                    })

    # Ordenar por criticidade (mais dias de atraso primeiro)
    for comp in inad_res:
        inad_res[comp] = sorted(inad_res[comp], key=lambda x: x['Dias de Atraso'], reverse=True)

    # Lógica de Faltantes
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
        if "page" not in st.session_state: st.session_state.page = "faturamento"
        if st.button("Faturamento"): st.session_state.page = "faturamento"
        if st.button("Sair"): del st.session_state["user"]; st.rerun()

    if st.session_state.page == "faturamento":
        st.title("💳 Gestão de Faturamento")
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência Crítica"])
        
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
                        csv_data = csv_from_list(items, ["uc", "apelido", "usina"], ["UC", "Apelido", "Usina"])
                        st.download_button(f"⬇️ Baixar Lista de Faltantes ({comp})", csv_data, f"faltantes_{comp.replace('/','-')}.csv", "text/csv")
                        st.table(pd.DataFrame(items))
            with t3:
                st.error("🚨 Clientes com status VENCIDO há mais de 60 dias (Atenção para saída do rateio)")
                for comp, rows in res["inad"].items():
                    gerado = res["t_gerado"].get(comp, 0.0)
                    vencido = res["t_vencido"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100) if gerado > 0 else 0
                    
                    st.markdown(f"### {comp}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Gerado", f"R$ {gerado:,.2f}")
                    c2.metric("Vencido Total", f"R$ {vencido:,.2f}")
                    c3.metric("Clientes Críticos", len(rows))
                    
                    if rows:
                        df_inad = pd.DataFrame(rows)
                        # Aplicar estilo de cores e exibir
                        st.dataframe(
                            df_inad.style.apply(color_rows, axis=1),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.success("Nenhum cliente com atraso crítico (>60 dias) nesta competência.")
                    st.write("---")

if __name__ == "__main__":
    main()
