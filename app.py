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

# ── 2. CSS BACKOFFICE SUNNE (DESIGN RUBI E BOTÕES LARANJA) ───────────────────
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

/* Sidebar Rubi */
[data-testid="stSidebar"] {
    background-color: var(--rubi) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
}
[data-testid="stSidebar"] * { color: white !important; }

/* Botões da Sidebar Laranja */
.stButton>button {
    width: 100% !important;
    background-color: var(--laranja) !important;
    color: white !important;
    border: none !important;
    padding: 12px 20px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    margin-bottom: 10px !important;
}
.stButton>button:hover { background-color: #d65a1b !important; }

/* Top Header */
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

/* Tabelas e KPIs */
.kpi-box { background: white; border-radius: 12px; padding: 1rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-value { font-size: 20px; font-weight: 700; color: var(--rubi); }
.sunne-table { width: 100%; border-collapse: collapse; background: white; font-size: 13px; }
.sunne-table th { background: #F8F9FA; color: var(--rubi); padding: 10px; border-bottom: 2px solid #EEE; text-align: left; }
.sunne-table td { padding: 10px; border-bottom: 1px solid #EEE; }

/* Login */
.login-card {
    max-width: 380px; margin: 100px auto; padding: 40px;
    background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(51, 0, 26, 0.1);
    text-align: center; border: 1px solid #EAD8D0;
}
</style>
"""

# ── 3. UTILITÁRIOS DE LIMPEZA DE DADOS (CRUCIAL PARA VOLTAR A FUNCIONAR) ──────
def clean_val(v):
    if not v or str(v).lower() in ("nan", ""): return 0.0
    s = str(v).replace("R$", "").replace(" ", "").strip()
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def normalize_uc(val):
    """Garante que a UC seja apenas números e sem .0 no final"""
    if not val: return ""
    s = str(val).strip().split('.')[0] # Remove .0 se houver
    return "".join(filter(str.isdigit, s))

def load_planilha(file):
    if file is None: return None
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.csv') else pd.read_csv(file, header=None, sep=None, engine='python')
        # Procura cabeçalho
        for i, row in df.head(20).iterrows():
            row_l = [str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s or "numero da uc" in s for s in row_l):
                df.columns = [str(c).strip() for c in row]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

# ── 4. A LÓGICA DE ANÁLISE QUE ENCONTRA AS 63 FATURAS ─────────────────────────
def analyze_performance(df_r, df_e):
    # Identificar colunas no Rateio
    uc_r_col = next((c for c in df_r.columns if "UC Nova" in c), df_r.columns[0])
    usina_col = next((c for c in df_r.columns if "Usina" in c), None)
    apelido_col = next((c for c in df_r.columns if "Apelido" in c), None)

    # Identificar colunas no Extrato
    # Prioridade para a 1ª coluna conforme sua imagem
    uc_e_col = df_e.columns[0] 
    comp_col = next((c for c in df_e.columns if "Competência" in c), None)
    status_col = next((c for c in df_e.columns if "Status" in c), None)
    valor_col = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular" in c), None)

    # Normalizar UCs para comparação idêntica
    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    # 1. GESTÃO DE CAPTURA (QUEM ESTÁ FALTANDO)
    missing_results = {}
    if comp_col:
        competencias = df_e[comp_col].unique()
        for comp in competencias:
            if not comp: continue
            # UCs que aparecem no extrato para este mês
            extrato_no_mes = set(df_e[df_e[comp_col] == comp]['UC_NORM'])
            
            # Cruzamento: Quem está no Rateio mas não está no Extrato?
            faltantes = df_r[~df_r['UC_NORM'].isin(extrato_no_mes)]
            
            if not faltantes.empty:
                missing_results[comp] = []
                for _, row in faltantes.iterrows():
                    missing_results[comp].append({
                        "uc": row[uc_r_col],
                        "apelido": row[apelido_col] if apelido_col else "—",
                        "usina": row[usina_col] if usina_col else "—"
                    })

    # 2. INADIMPLÊNCIA (APENAS VENCIDOS)
    inad_results = {}
    totais_gerados = {}
    if status_col and valor_c:
        for comp in df_e[comp_col].unique():
            df_mes = df_e[df_e[comp_col] == comp].copy()
            df_mes['VALOR_NUM'] = df_mes[valor_c].apply(clean_val)
            
            totais_gerados[comp] = df_mes['VALOR_NUM'].sum()
            
            vencidos = df_mes[df_mes[status_col].astype(str).str.lower().str.contains("vencido")]
            if not vencidos.empty:
                inad_results[comp] = []
                for _, row in vencidos.iterrows():
                    inad_results[comp].append({
                        "uc": row[uc_e_col],
                        "titular": row[titular_col] if titular_col else "—",
                        "valor": row['VALOR_NUM'],
                        "status": "Vencido"
                    })

    return {
        "missing": missing_results,
        "inad": inad_results,
        "totais": totais_gerados
    }

# ── 5. INTERFACE DO APP ──────────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_THEME_CSS, unsafe_allow_html=True)
    
    # Login Simples
    if "user_data" not in st.session_state:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        with st.form("login"):
            e = st.text_input("E-mail", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar", use_container_width=True):
                if s == "sunne2026":
                    st.session_state["user_data"] = {"name": "Milena"}
                    st.rerun()
        return

    # Header Rubi
    st.markdown(f'<div class="top-header"><img src="https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png" height="30"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:60px"></div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        st.write(f"Olá, {st.session_state['user_data']['name']} 👋")
        st.write("---")
        if "page" not in st.session_state: st.session_state.page = "faturamento"
        
        if st.button("📊 Dashboard"): st.session_state.page = "dash"
        if st.button("📈 Rateio"): st.session_state.page = "rateio"
        if st.button("💳 Faturamento"): st.session_state.page = "faturamento"
        
        if st.button("🚪 Sair"):
            del st.session_state["user_data"]; st.rerun()

    # Conteúdo Faturamento
    if st.session_state.page == "faturamento":
        st.subheader("Gestão de Faturamento")
        t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])
        
        with t1:
            f_r = st.file_uploader("Upload Rateio")
            f_e = st.file_uploader("Upload Extrato")
            if f_r and f_e:
                if st.button("🔄 Executar Análise", use_container_width=True):
                    df_r = load_planilha(f_r)
                    df_e = load_planilha(f_e)
                    if df_r is not None and df_e is not None:
                        st.session_state["results"] = analyze_performance(df_r, df_e)
                        st.success("Análise concluída com sucesso!")

        res = st.session_state.get("results")
        if res:
            with t2:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faturas faltando"):
                        df_faltantes = pd.DataFrame(items)
                        st.table(df_faltantes)
            with t3:
                for comp, rows in res["inad"].items():
                    total_vencido = sum(r["valor"] for r in rows)
                    total_gerado = res["totais"].get(comp, 1.0)
                    taxa = (total_vencido / total_gerado) * 100
                    st.markdown(f"#### {comp}")
                    c1, c2 = st.columns(2)
                    c1.metric("Total Vencido", f"R$ {total_vencido:,.2f}")
                    c2.metric("Taxa de Inadimplência", f"{taxa:.1f}%")
                    st.table(pd.DataFrame(rows))

if __name__ == "__main__": main()
