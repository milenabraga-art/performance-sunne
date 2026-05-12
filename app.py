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

# ── 2. Paleta Sunne® e CSS Global ───────────────────────────────────────────
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
.sunne-card-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; color: #33001A; }
.sunne-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
.sunne-table th { text-align: left; padding: .6rem; background: #FBF5F0; color: #7A5060; border-bottom: 1px solid #EAD8D0; font-size: 11px; text-transform: uppercase; }
.sunne-table td { padding: .6rem; border-bottom: .5px solid #F0E4DC; color: #1A0A0F; }
.kpi-box { background: #FBF5F0; border-radius: 10px; padding: 1rem; flex: 1; min-width: 150px; }
.kpi-label { font-size: 11px; color: #7A5060; text-transform: uppercase; margin-bottom: 5px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: #33001A; }
.kpi-value.danger { color: #FF365E; }
</style>
"""

# ── 3. Constantes e Configurações de Usuário ─────────────────────────────────
USERS_FILE = "users.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        default = {"users": [{"name": "Admin", "email": "admin@sunne.com.br", "password": "admin123", "role": "admin"}]}
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

# ── 4. Utilitários de Dados (O Pulo do Gato) ──────────────────────────────────
def load_planilha(uploaded_file):
    if uploaded_file is None: return None
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, dtype=str, header=None, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file, sheet_name=0, dtype=str, header=None)
        
        found_header = False
        # Escaneia as primeiras 15 linhas para achar o cabeçalho real
        for i, row in df.head(15).iterrows():
            row_list = [str(cell).strip().lower() for cell in row]
            # Procura por termos-chave em qualquer célula da linha
            if any("uc nova/atual" in s or "número da uc" in s or "numero da uc" in s for s in row_list):
                df.columns = [str(cell).strip() for cell in row]
                df = df.iloc[i+1:].reset_index(drop=True)
                found_header = True
                break
        
        # Fallback: Se for extrato e não achou nome, assume que a primeira linha é o cabeçalho
        if not found_header:
            df.columns = [str(c).strip() for c in df.iloc[0]]
            df = df.iloc[1:].reset_index(drop=True)

        # Garante que nomes de colunas sejam strings e remove "lixo"
        df.columns = [str(c).strip() for c in df.columns]
        df = df.loc[:, [c for c in df.columns if c and c.lower() != "nan" and "unnamed" not in c.lower()]]
        return df.dropna(how='all').fillna("")
    except Exception as e:
        st.error(f"Erro ao ler {uploaded_file.name}: {e}"); return None

# ── 5. Lógica de Análise de Performance ──────────────────────────────────────
def analyze(df_rateio, df_extrato):
    # Identificar colunas no Rateio
    uc_r_col = next((c for c in df_rateio.columns if "UC Nova/Atual" in c), None)
    usina_r_col = next((c for c in df_rateio.columns if "Usina" in c), None)
    apelido_col = next((c for c in df_rateio.columns if "Apelido" in c), None)

    # Identificar colunas no Extrato (Com Fallback para a 1ª coluna)
    uc_e_col = next((c for c in df_extrato.columns if "Número da UC" in c or "Numero da UC" in c), None)
    if not uc_e_col: uc_e_col = df_extrato.columns[0] # Pega a primeira coluna (conforme imagem)
    
    comp_col = next((c for c in df_extrato.columns if "Competência" in c), None)
    leitura_col = next((c for c in df_extrato.columns if "Leitura Atual" in c), None)
    valor_col = next((c for c in df_extrato.columns if "Total a Pagar" in c), None)
    status_col = next((c for c in df_extrato.columns if "Status" in c), None)
    titular_col = next((c for c in df_extrato.columns if "Titular" in c), None)
    usina_e_col = next((c for c in df_extrato.columns if "Usina" in c), None)

    if not uc_r_col: return {"errors": ["Coluna 'UC Nova/Atual' não encontrada no Rateio."]}

    # Normalizar IDs de UC para comparação
    df_rateio[uc_r_col] = df_rateio[uc_r_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df_extrato[uc_e_col] = df_extrato[uc_e_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    ucs_rateio = df_rateio[uc_r_col].unique().tolist()
    
    # Mapear o que já existe no extrato
    extrato_pairs = set()
    comp_leitura = {}
    if comp_col:
        for _, row in df_extrato.iterrows():
            uc, comp = str(row[uc_e_col]), str(row[comp_col])
            extrato_pairs.add((uc, comp))
            if leitura_col and comp not in comp_leitura:
                comp_leitura[comp] = parse_date(row[leitura_col])

    # --- Cálculo de Captura (Faltantes) ---
    missing = {}
    if comp_col:
        competencias = [c for c in df_extrato[comp_col].unique() if c]
        for comp in competencias:
            leitura = comp_leitura.get(comp)
            # Regra dos 40 dias: Se hoje < leitura + 40, ainda está no prazo
            if leitura and TODAY <= (leitura + timedelta(days=DELAY_DAYS)): continue
            
            for uc in ucs_rateio:
                if (uc, comp) not in extrato_pairs:
                    row_r = df_rateio[df_rateio[uc_r_col] == uc]
                    if comp not in missing: missing[comp] = []
                    missing[comp].append({
                        "uc": uc, "comp": comp, 
                        "usina": row_r.iloc[0][usina_r_col] if usina_r_col else "—",
                        "apelido": row_r.iloc[0][apelido_col] if apelido_col else "—"
                    })

    # --- Cálculo de Inadimplência ---
    inadimplentes = {}; total_por_comp = {}
    if comp_col:
        for _, row in df_extrato.iterrows():
            comp = str(row[comp_col])
            try: valor = float(str(row[valor_col]).replace("R$", "").replace(".", "").replace(",", ".").strip())
            except: valor = 0.0
            
            total_por_comp[comp] = total_por_comp.get(comp, 0.0) + valor
            
            if status_col and "pago" not in str(row[status_col]).lower():
                if comp not in inadimplentes: inadimplentes[comp] = []
                inadimplentes[comp].append({
                    "uc": row[uc_e_col], "valor": valor, "status": row[status_col],
                    "titular": row[titular_col] if titular_col else "—",
                    "usina": row[usina_e_col] if usina_e_col else "—"
                })

    return {
        "errors": [], "missing": missing, "inadimplentes": inadimplentes, 
        "total_por_comp": total_por_comp, "n_ucs_rateio": len(ucs_rateio), "n_extrato": len(df_extrato)
    }

# ── 6. Interface Principal ───────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.markdown('<div class="login-wrap"><div class="login-mark">S</div><div class="login-title">Sunne Performance</div></div>', unsafe_allow_html=True)
        col_l, col_r = st.columns([1, 2])
        with col_r:
            with st.form("login"):
                e = st.text_input("E-mail"); s = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    u = authenticate(e, s)
                    if u: st.session_state["user"] = u; st.rerun()
                    else: st.error("Login inválido.")
        return

    user = st.session_state["user"]
    st.markdown(f'<div class="sunne-header"><div><span class="sunne-logo-mark">S</span><span class="sunne-header-title">Sunne Performance</span></div><div class="user-pill">{user["name"]}</div></div>', unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📂 Importar Dados", "🔍 Gestão de Captura", "💳 Inadimplência"])
    
    with t1:
        st.markdown('<div class="sunne-card"><div class="sunne-card-title">Upload de Planilhas</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_r = c1.file_uploader("Planilha de Rateio", type=["xlsx", "csv"])
        f_e = c2.file_uploader("Extrato Detalhado", type=["xlsx", "csv"])
        if f_r and f_e:
            if st.button("Analisar Performance", use_container_width=True):
                with st.spinner("Processando..."):
                    df_r = load_planilha(f_r)
                    df_e = load_planilha(f_e)
                    if df_r is not None and df_e is not None:
                        st.session_state["analysis"] = analyze(df_r, df_e)
                        st.success("✓ Análise concluída com sucesso!")
        st.markdown('</div>', unsafe_allow_html=True)

    res = st.session_state.get("analysis")
    if res:
        if res["errors"]: 
            for err in res["errors"]: st.error(err)
        else:
            with t2:
                miss = res["missing"]
                if not miss: st.success("✅ Todas as UCs foram capturadas dentro do prazo.")
                else:
                    for comp, items in miss.items():
                        with st.expander(f"⚠️ {comp} - {len(items)} faturas não encontradas"):
                            st.markdown(table_html(items, ["uc", "apelido", "usina"], ["Nº UC", "Apelido", "Usina"]), unsafe_allow_html=True)
            
            with t3:
                inad = res["inadimplentes"]
                if not inad: st.success("✅ Nenhuma inadimplência detectada.")
                else:
                    for comp, rows in inad.items():
                        total = sum(r["valor"] for r in rows)
                        with st.expander(f"💳 {comp} - Total em Aberto: R$ {total:,.2f}"):
                            st.markdown(table_html(rows, ["uc", "titular", "valor", "status"], ["UC", "Titular", "Valor", "Status"]), unsafe_allow_html=True)

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

if __name__ == "__main__": main()
