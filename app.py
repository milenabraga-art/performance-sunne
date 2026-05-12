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

# ── 2. CSS CUSTOMIZADO (VISIBILIDADE TOTAL & ESTILO SUNNE) ───────────────────
SUNNE_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

/* Cores Oficiais */
:root {
    --rubi: #33001A;
    --laranja: #F36E21;
    --texto: #1A0A0F;
}

/* Fundo da página levemente acinzentado para dar contraste com o card branco */
[data-testid="stAppViewContainer"] { background-color: #F4F4F9; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* TELA DE LOGIN - VISIBILIDADE MÁXIMA */
.login-box {
    max-width: 400px; 
    margin: 80px auto; 
    padding: 40px;
    background: white; 
    border-radius: 20px; 
    box-shadow: 0 10px 30px rgba(51, 0, 26, 0.1);
    text-align: center; 
    border: 1px solid #EAD8D0;
}

/* Garantir que os labels (E-mail/Senha) fiquem escuros */
.stTextInput label {
    color: var(--rubi) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* Botão de Acesso - LARANJA VIBRANTE */
.stButton>button {
    width: 100%;
    background-color: var(--laranja) !important;
    color: white !important;
    border: none !important;
    padding: 12px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    border-radius: 10px !important;
    margin-top: 10px;
}

/* TOP HEADER E SIDEBAR (ESTILO BACKOFFICE) */
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

[data-testid="stSidebar"] {
    background-color: var(--rubi) !important;
}
[data-testid="stSidebar"] * { color: white !important; }

/* KPIs E TABELAS */
.kpi-box { background: white; border-radius: 12px; padding: 1rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-label { font-size: 10px; color: #7A5060; text-transform: uppercase; font-weight: 700; }
.kpi-value { font-size: 20px; font-weight: 700; color: var(--rubi); }
.danger-text { color: #FF365E !important; }

.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; background: white; }
.sunne-table th { text-align: left; padding: 10px; background: #F8F9FA; color: #33001A; border-bottom: 2px solid #EEE; }
.sunne-table td { padding: 10px; border-bottom: 1px solid #F5F5F5; color: #1A0A0F; }
</style>
"""

# ── 3. UTILITÁRIOS, LOGIN E CÁLCULOS ─────────────────────────────────────────
USERS_FILE = "users_db.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        initial = [{"name": "Milena Braga", "email": "milena.braga@sunne.com.br", "password": "sunne2026", "role": "admin"}]
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

def csv_export(rows, cols, headers):
    output = io.StringIO()
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[cols]; df.columns = headers
        df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
    return output.getvalue().encode('utf-8-sig')

def load_planilha(file):
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.csv') else pd.read_csv(file, header=None, sep=None, engine='python')
        for i, row in df.head(20).iterrows():
            row_l = [str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s for s in row_l):
                df.columns = [str(c).strip() for c in df.columns]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

# ── 4. LÓGICA DE ANÁLISE DE PERFORMANCE ──────────────────────────────────────
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
        
        # FILTRO: Apenas VENCIDO para inadimplência
        if "vencido" in status:
            if comp not in inad_mes: inad_mes[comp] = []
            inad_mes[comp].append({"uc": uc, "valor": valor, "status": "Vencido", "titular": str(row.get("Titular da Conta", "—"))})

        if comp not in comp_leitura:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try: 
                    comp_leitura[comp] = datetime.strptime(str(row[leitura_c]).strip(), fmt)
                    break
                except: comp_leitura[comp] = None

    # Cruzamento para Captura Faltante
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

# ── 5. INTERFACE (CONTEÚDO E DASHBOARD) ──────────────────────────────────────
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
    st.markdown(SUNNE_THEME_CSS, unsafe_allow_html=True)
    
    # --- FLUXO DE LOGIN (VISÍVEL AGORA) ---
    if "user_data" not in st.session_state:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        # Fallback de imagem caso o link quebre
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        st.markdown("<h3 style='color:#33001A; margin-top:15px;'>Sunne Hub</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            e = st.text_input("E-mail corporativo", placeholder="analista@sunne.com.br")
            s = st.text_input("Senha", type="password", placeholder="••••••••")
            if st.form_submit_button("Acessar Sistema", use_container_width=True):
                users = load_users()
                found = next((u for u in users if u["email"] == e and u["password"] == s), None)
                if found:
                    st.session_state["user_data"] = found
                    st.rerun()
                else: st.error("E-mail ou senha incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    user = st.session_state["user_data"]

    # --- TOP BAR E SIDEBAR ---
    st.markdown(f'<div class="top-header"><img src="https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png" height="30"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:60px"></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=100)
        with st.popover(f"👤 {user['name']}", use_container_width=True):
            st.write(f"**{user['name']}**")
            st.caption(user['email'])
            if st.button("🚪 Sair do Sistema"):
                del st.session_state["user_data"]
                st.rerun()
        
        st.write("---")
        if "page" not in st.session_state: st.session_state.page = "perf"
        if st.button("📊 Faturamento"): st.session_state.page = "perf"
        if st.button("👥 Gerenciar Analistas"): st.session_state.page = "users"

    # --- ABA: PERFORMANCE ---
    if st.session_state.page == "perf":
        st.markdown("### 📊 Análise de Performance")
        
        # Filtros Superiores
        with st.expander("🔍 Filtros e Busca Avançada", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.text_input("Buscar pela UC")
            c2.selectbox("Competência", ["Todas"])
            c3.selectbox("Status", ["Todos"])
            st.button("Buscar", type="primary")

        t1, t2, t3 = st.tabs(["📂 Importar Planilhas", "🔍 Gestão de Captura", "💳 Inadimplência"])
        
        with t1:
            st.info("Suba os arquivos para realizar o cruzamento de dados.")
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Upload: Planilha de Rateio")
            f_e = c2.file_uploader("Upload: Extrato Detalhado")
            if f_r and f_e:
                if st.button("🔄 Rodar Análise Completa", use_container_width=True):
                    res = analyze(load_planilha(f_r), load_planilha(f_e))
                    st.session_state["analysis_result"] = res
                    st.success("✓ Análise concluída!")

        # MOSTRAR RESULTADOS
        res = st.session_state.get("analysis_result")
        if res:
            with t2:
                miss = res["missing"]
                if not miss: st.success("✅ Tudo capturado!")
                for comp, items in miss.items():
                    with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                        csv_cap = csv_export(items, ["uc", "apelido", "usina"], ["UC", "Nome", "Usina"])
                        st.download_button(f"⬇ Baixar CSV {comp}", csv_cap, f"captura_{comp}.csv", "text/csv")
                        st.markdown(table_html(items, ["uc", "apelido", "usina"], ["UC", "Nome", "Usina"]), unsafe_allow_html=True)
            
            with t3:
                inad = res["inad"]
                for comp, rows in inad.items():
                    vencido = sum(r["valor"] for r in rows)
                    gerado = res["t_gerado"].get(comp, 0.0)
                    taxa = (vencido / gerado * 100) if gerado > 0 else 0
                    st.markdown(f"#### Competência: {comp}")
                    st.markdown(f'<div style="display:flex; gap:15px; margin-bottom:15px;">'
                                f'<div class="kpi-box"><div class="kpi-label">Faturado</div><div class="kpi-value">R$ {gerado:,.2f}</div></div>'
                                f'<div class="kpi-box"><div class="kpi-label">Vencido</div><div class="kpi-value danger-text">R$ {vencido:,.2f}</div></div>'
                                f'<div class="kpi-box"><div class="kpi-label">% Inadimplência</div><div class="kpi-value danger-text">{taxa:.1f}%</div></div>'
                                f'</div>', unsafe_allow_html=True)
                    with st.expander(f"Exportar Vencidos - {comp}"):
                        csv_in = csv_export(rows, ["uc", "titular", "valor"], ["UC", "Titular", "Valor"])
                        st.download_button(f"⬇ Exportar Vencidos {comp}", csv_in, f"vencidos_{comp}.csv", "text/csv")
                        st.markdown(table_html(rows, ["uc", "titular", "valor", "status"], ["UC", "Titular", "Valor", "Status"]), unsafe_allow_html=True)

    elif st.session_state.page == "users":
        st.subheader("👥 Gestão de Analistas")
        # Interface de usuários

if __name__ == "__main__":
    main()
