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

# ── Paleta Sunne® e CSS global ────────────────────────────────────────────────
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
    --bg:       #FDF8F5;
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
.kpi-value.ok     { color: #0A8A7A; }

/* Badges */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 6px;
    font-size: 11px; font-weight: 600;
}
.badge-warn   { background: #FFF0F3; color: #CC1A3A; }
.badge-ok     { background: #F0FDFB; color: #0A7A6A; }
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
DELAY_DAYS = 40  # 1 mês (30d) + 10 dias de captura


# ── Utilitários de usuário ────────────────────────────────────────────────────
def load_users() -> list:
    if not os.path.exists(USERS_FILE):
        default = {"users": [{"name": "Admin", "email": "admin@sunne.com.br", "password": "admin123", "role": "admin"}]}
        with open(USERS_FILE, "w") as f:
            json.dump(default, f, indent=2)
    with open(USERS_FILE) as f:
        return json.load(f).get("users", [])


def save_users(users: list):
    with open(USERS_FILE, "w") as f:
        json.dump({"users": users}, f, indent=2, ensure_ascii=False)


def authenticate(email: str, password: str):
    for u in load_users():
        if u["email"].lower() == email.lower() and u["password"] == password:
            return u
    return None


# ── Utilitários de dados ──────────────────────────────────────────────────────
def normalize_col(df: pd.DataFrame, patterns: list) -> str | None:
    for p in patterns:
        for c in df.columns:
            if pd.Series([c]).astype(str).str.contains(p, case=False, regex=True).any():
                return c
    return None

def load_planilha(uploaded_file) -> pd.DataFrame | None:
    if uploaded_file is None:
        return None
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            # Lê a primeira aba do Excel
            df = pd.read_excel(uploaded_file, sheet_name=0, dtype=str, header=None)
            
            # Procura a linha que contém "UC Nova/Atual" para ser o cabeçalho real
            found_header = False
            for i, row in df.iterrows():
                row_str = [str(cell).strip() for cell in row]
                if "UC Nova/Atual" in row_str:
                    df.columns = row_str
                    df = df.iloc[i+1:].reset_index(drop=True)
                    found_header = True
                    break
            
            # Se não achou por "UC Nova/Atual", tenta pela primeira linha que tenha o símbolo "#"
            if not found_header:
                for i, row in df.iterrows():
                    if any(str(cell).strip() == "#" for cell in row):
                        df.columns = [str(c).strip() for c in row]
                        df = df.iloc[i+1:].reset_index(drop=True)
                        break
        
        df.columns = df.columns.str.strip()
        # Remove colunas e linhas totalmente vazias que o Excel às vezes cria
        df = df.loc[:, df.columns.notnull()]
        df = df.dropna(how='all').fillna("")
        return df
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

def parse_date(v: str) -> datetime | None:
    if not v or str(v).strip() == "" or str(v).lower() == "nan":
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(v).strip(), fmt)
        except ValueError:
            continue
    return None

def get_uc_col(df: pd.DataFrame) -> str | None:
    return normalize_col(df, [
        r"uc\s*(nova|atual)", r"número\s*da\s*uc", r"numero\s*da\s*uc",
        r"num.*uc", r"^uc$", r"^uc\b"
    ])

# ── Lógica de análise ─────────────────────────────────────────────────────────
def analyze(df_rateio: pd.DataFrame, df_extrato: pd.DataFrame) -> dict:
    # ---- Mapeamento de Colunas (Nomes Exatos da Sunne) ----------------------
    uc_r_col = "UC Nova/Atual" if "UC Nova/Atual" in df_rateio.columns else get_uc_col(df_rateio)
    usina_r_col = "Usina" if "Usina" in df_rateio.columns else normalize_col(df_rateio, [r"usina"])
    apelido_col = "Apelido UC" if "Apelido UC" in df_rateio.columns else normalize_col(df_rateio, [r"apelido"])

    uc_e_col = "Número da UC" if "Número da UC" in df_extrato.columns else get_uc_col(df_extrato)
    titular_col = "Titular da Conta" if "Titular da Conta" in df_extrato.columns else normalize_col(df_extrato, [r"titular"])
    
    comp_ext_col = "Competência - extenso" if "Competência - extenso" in df_extrato.columns else normalize_col(df_extrato, [r"competência\s*[-–]\s*extenso"])
    comp_col = "Competência" if "Competência" in df_extrato.columns else normalize_col(df_extrato, [r"^competência$"])
    
    leitura_col = "Leitura Atual" if "Leitura Atual" in df_extrato.columns else normalize_col(df_extrato, [r"leitura\s*atual"])
    valor_col = "Total a Pagar Boleto Sunne" if "Total a Pagar Boleto Sunne" in df_extrato.columns else normalize_col(df_extrato, [r"total\s*a\s*pagar"])
    status_col = "Status de Pagamento" if "Status de Pagamento" in df_extrato.columns else normalize_col(df_extrato, [r"status\s*de\s*pagamento"])
    usina_e_col = "Usina" if "Usina" in df_extrato.columns else normalize_col(df_extrato, [r"usina"])

    errors = []
    if not uc_r_col: 
        cols_found = ", ".join(list(df_rateio.columns[:5]))
        errors.append(f"Coluna 'UC Nova/Atual' não encontrada no Rateio. Colunas detectadas: {cols_found}")
    if not uc_e_col: 
        errors.append("Coluna 'Número da UC' não encontrada no Extrato.")
    
    if errors:
        return {"errors": errors}

    # Normalizar IDs de UC para comparação (Texto limpo)
    df_rateio = df_rateio.copy()
    df_extrato = df_extrato.copy()
    df_rateio[uc_r_col] = df_rateio[uc_r_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df_extrato[uc_e_col] = df_extrato[uc_e_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    ucs_rateio = df_rateio[uc_r_col].unique().tolist()
    comp_key = comp_ext_col or comp_col

    # Criar registro de faturas existentes
    extrato_pairs = set()
    if comp_key:
        for _, row in df_extrato.iterrows():
            extrato_pairs.add((str(row[uc_e_col]), str(row[comp_key])))

    # Calcular prazos por competência
    comp_leitura = {}
    if comp_key and leitura_col:
        for _, row in df_extrato.iterrows():
            c = str(row[comp_key])
            l = parse_date(str(row[leitura_col]))
            if l and c not in comp_leitura:
                comp_leitura[c] = l

    # ---- Identificar Falhas de Captura ----
    missing: dict[str, list] = {}
    if comp_key:
        competencias = [c for c in df_extrato[comp_key].unique() if c]
        for comp in competencias:
            leitura = comp_leitura.get(comp)
            if leitura:
                limite = leitura + timedelta(days=DELAY_DAYS)
                if TODAY <= limite:
                    continue 

            for uc in ucs_rateio:
                if (str(uc), str(comp)) not in extrato_pairs:
                    row_r = df_rateio[df_rateio[uc_r_col] == uc]
                    usina = row_r.iloc[0][usina_r_col] if usina_r_col else "—"
                    apelido = row_r.iloc[0][apelido_col] if apelido_col else "—"

                    if comp not in missing:
                        missing[comp] = []
                    missing[comp].append({
                        "uc": uc,
                        "usina": usina,
                        "apelido": apelido,
                        "comp": comp,
                        "leitura": leitura,
                        "limite": leitura + timedelta(days=DELAY_DAYS) if leitura else None,
                    })

    # ---- Identificar Inadimplência ----
    inadimplentes: dict[str, list] = {}
    total_por_comp: dict[str, float] = {}

    if comp_key:
        for _, row in df_extrato.iterrows():
            comp = str(row[comp_key])
            
            v_raw = str(row[valor_col]) if valor_col else "0"
            try:
                valor = float(v_raw.replace("R$", "").replace(".", "").replace(",", ".").strip())
            except:
                valor = 0.0

            total_por_comp[comp] = total_por_comp.get(comp, 0.0) + valor

            status = str(row[status_col]) if status_col else ""
            if "pago" in status.lower():
                continue

            if comp not in inadimplentes:
                inadimplentes[comp] = []
            
            inadimplentes[comp].append({
                "uc": row[uc_e_col],
                "titular": row[titular_col] if titular_col else "—",
                "usina": row[usina_e_col] if usina_e_col else "—",
                "valor": valor,
                "status": status
            })

    return {
        "errors": [],
        "missing": missing,
        "inadimplentes": inadimplentes,
        "total_por_comp": total_por_comp,
        "n_ucs_rateio": len(ucs_rateio),
        "n_extrato": len(df_extrato),
    }


# ── Componentes HTML ──────────────────────────────────────────────────────────
def render_header(user: dict):
    st.markdown(f"""
    <div class="sunne-header">
        <div>
            <span class="sunne-logo-mark">S</span>
            <span class="sunne-header-title">Sunne Performance</span>
            <div class="sunne-header-sub" style="margin-left:52px">Gestão de Captura &amp; Inadimplência</div>
        </div>
        <div>
            <span class="user-pill">{user['name']} · {user['email'].split('@')[0]}@sunne</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def table_html(rows: list, cols: list, headers: list) -> str:
    html = '<table class="sunne-table"><thead><tr>'
    for h in headers:
        html += f"<th>{h}</th>"
    html += "</tr></thead><tbody>"
    for row in rows:
        html += "<tr>"
        for i, c in enumerate(cols):
            val = row.get(c, "—") or "—"
            style = ' class="uc-mono"' if c == "uc" else ""
            if c == "valor":
                val = f"R$ {float(val or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            html += f"<td{style}>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def csv_from_list(rows: list, cols: list, headers: list) -> bytes:
    lines = [";".join(headers)]
    for r in rows:
        lines.append(";".join([str(r.get(c, "")) for c in cols]))
    return ("\n".join(lines)).encode("utf-8-sig")


# ── Tela de Login ─────────────────────────────────────────────────────────────
def page_login():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="min-height:10vh"></div>
    <div class="login-wrap">
        <div class="login-mark">S</div>
        <div class="login-title">Sunne Performance</div>
        <div class="login-sub">Sistema de Gestão de Faturas e Inadimplência</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("E-mail", placeholder="analista@sunne.com.br")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            user = authenticate(email, senha)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")


# ── Aba: Upload ───────────────────────────────────────────────────────────────
def tab_upload():
    st.markdown('<div class="sunne-card"><div class="sunne-card-title">📂 Importar Planilhas</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="upload-hint"><strong>Planilha de Rateio</strong><br/>UC Nova/Atual · Usina · Apelido UC · CNPJ</div>', unsafe_allow_html=True)
        f_rateio = st.file_uploader("Rateio", type=["xlsx", "xls", "csv"], label_visibility="collapsed", key="up_rateio")
    with col2:
        st.markdown('<div class="upload-hint"><strong>Extrato Detalhado</strong><br/>Nº UC · Titular · Competência · Leitura Atual · Status</div>', unsafe_allow_html=True)
        f_extrato = st.file_uploader("Extrato", type=["xlsx", "xls", "csv"], label_visibility="collapsed", key="up_extrato")

    st.markdown('</div>', unsafe_allow_html=True)

    if f_rateio:
        st.session_state["df_rateio"] = load_planilha(f_rateio)
        st.success(f"✓ Rateio carregado — {len(st.session_state['df_rateio'])} linhas")
    if f_extrato:
        st.session_state["df_extrato"] = load_planilha(f_extrato)
        st.success(f"✓ Extrato carregado — {len(st.session_state['df_extrato'])} linhas")

    has_both = st.session_state.get("df_rateio") is not None and st.session_state.get("df_extrato") is not None

    if has_both:
        if st.button("Analisar Planilhas"):
            with st.spinner("Cruzando dados..."):
                result = analyze(st.session_state["df_rateio"], st.session_state["df_extrato"])
                st.session_state["analysis"] = result
            if result.get("errors"):
                for e in result["errors"]:
                    st.error(e)
            else:
                st.success(
                    f"✓ Análise concluída — {result['n_ucs_rateio']} UCs no rateio × "
                    f"{result['n_extrato']} registros no extrato."
                )
    else:
        st.info("Faça upload das duas planilhas para habilitar a análise.")

    # Guia de uso
    st.markdown("""
    <div class="sunne-card" style="margin-top:1rem">
        <div class="sunne-card-title">Como usar</div>
        <div style="font-size:13px;color:#7A5060;line-height:1.9">
            <p>1. Upload da <strong>Planilha de Rateio</strong> com todas as UCs do gerador.</p>
            <p>2. Upload do <strong>Extrato Detalhado</strong> puxado pelo gerador (mínimo 3 meses recomendado).</p>
            <p>3. Clique em <strong>Analisar Planilhas</strong>. O sistema cruza as UCs e sinaliza faltantes e inadimplentes por mês.</p>
            <p>4. <strong>Regra de atraso:</strong> fatura só é sinalizada como faltante se <code>hoje &gt; Leitura Atual + 40 dias</code>.</p>
            <p>5. Taxa de inadimplência acima de <strong>5%</strong> é destacada em vermelho.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Aba: Gestão de Captura ────────────────────────────────────────────────────
def tab_captura():
    result = st.session_state.get("analysis")
    if not result:
        st.markdown('<div class="empty" style="text-align:center;padding:3rem;color:#7A5060">📊 Faça o upload e análise das planilhas primeiro.</div>', unsafe_allow_html=True)
        return

    missing = result.get("missing", {})
    if not missing:
        st.markdown('<div class="sunne-card"><div style="text-align:center;padding:2rem;color:#0A7A6A;font-family:Syne,sans-serif;font-size:15px">✅ Nenhuma fatura faltante — todas as UCs estão capturadas!</div></div>', unsafe_allow_html=True)
        return

    total_faltantes = sum(len(v) for v in missing.values())
    st.markdown(f'<div class="alert-bar">⚠ {len(missing)} mês(es) com faturas não capturadas — {total_faltantes} ocorrência(s) no total.</div>', unsafe_allow_html=True)

    month_tabs = st.tabs(list(missing.keys()))
    for tab, (comp, items) in zip(month_tabs, missing.items()):
        with tab:
            leitura = items[0].get("leitura") if items else None
            limite = items[0].get("limite") if items else None
            leitura_str = leitura.strftime("%d/%m/%Y") if leitura else "—"
            limite_str = limite.strftime("%d/%m/%Y") if limite else "—"

            col_info, col_dl = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <span class="badge badge-warn">{len(items)} UC{'s' if len(items)>1 else ''} sem fatura</span>
                &nbsp;
                <span style="font-size:12px;color:#7A5060">Leitura: {leitura_str} · Prazo limite: {limite_str}</span>
                """, unsafe_allow_html=True)
            with col_dl:
                csv_bytes = csv_from_list(
                    items,
                    ["comp", "uc", "apelido", "usina"],
                    ["Competência", "Número da UC", "Apelido/Titular", "Usina"]
                )
                st.download_button(
                    label="⬇ Baixar CSV",
                    data=csv_bytes,
                    file_name=f"captura_faltante_{comp.replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"dl_cap_{comp}",
                )

            st.markdown(table_html(
                items,
                ["uc", "apelido", "usina", "comp"],
                ["Nº UC", "Apelido / Titular", "Usina", "Competência"]
            ), unsafe_allow_html=True)


# ── Aba: Inadimplência ────────────────────────────────────────────────────────
def tab_inadimplencia():
    result = st.session_state.get("analysis")
    if not result:
        st.markdown('<div style="text-align:center;padding:3rem;color:#7A5060">💳 Faça o upload e análise das planilhas primeiro.</div>', unsafe_allow_html=True)
        return

    inadimplentes = result.get("inadimplentes", {})
    total_por_comp = result.get("total_por_comp", {})

    if not inadimplentes:
        st.markdown('<div class="sunne-card"><div style="text-align:center;padding:2rem;color:#0A7A6A;font-family:Syne,sans-serif;font-size:15px">✅ Sem inadimplência — todas as faturas estão pagas!</div></div>', unsafe_allow_html=True)
        return

    for comp, rows in inadimplentes.items():
        total_inad = sum(r["valor"] for r in rows)
        total_mes = total_por_comp.get(comp, 0.0)
        taxa = (total_inad / total_mes * 100) if total_mes > 0 else 0.0
        danger = taxa > 5.0

        fmt = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        st.markdown(f"""
        <div class="sunne-card">
            <div class="section-head" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.75rem">
                <span class="sunne-card-title" style="margin-bottom:0">{comp}</span>
                <span class="badge {'badge-warn' if danger else 'badge-info'}">{len(rows)} fatura{'s' if len(rows)>1 else ''} em aberto</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(table_html(
            rows,
            ["uc", "titular", "usina", "valor", "status"],
            ["Nº UC", "Titular", "Usina", "Valor (R$)", "Status"]
        ), unsafe_allow_html=True)

        taxa_class = "danger" if danger else "ok"
        taxa_icon = " ▲" if danger else " ✓"
        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-box">
                <div class="kpi-label">Total Inadimplente</div>
                <div class="kpi-value {taxa_class}">{fmt(total_inad)}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">Total Gerado no Mês</div>
                <div class="kpi-value">{fmt(total_mes)}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">Taxa de Inadimplência</div>
                <div class="kpi-value {taxa_class}">{taxa:.1f}%{taxa_icon}</div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)

        csv_bytes = csv_from_list(
            rows,
            ["uc", "titular", "usina", "valor", "status"],
            ["Nº UC", "Titular", "Usina", "Valor", "Status"]
        )
        st.download_button(
            label=f"⬇ Baixar inadimplência — {comp}",
            data=csv_bytes,
            file_name=f"inadimplencia_{comp.replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"dl_inad_{comp}",
        )


# ── Aba: Admin ────────────────────────────────────────────────────────────────
def tab_admin():
    st.markdown('<div class="sunne-card"><div class="sunne-card-title">👤 Cadastrar Novo Usuário</div>', unsafe_allow_html=True)
    with st.form("new_user_form"):
        name = st.text_input("Nome completo")
        email = st.text_input("E-mail (@sunne.com.br)")
        password = st.text_input("Senha inicial", type="password")
        role = st.selectbox("Perfil", ["user", "admin"])
        submitted = st.form_submit_button("Cadastrar Usuário")

    if submitted:
        if not name or not email or not password:
            st.error("Preencha todos os campos.")
        elif "@sunne" not in email.lower():
            st.error("O e-mail deve ser @sunne.")
        else:
            users = load_users()
            if any(u["email"].lower() == email.lower() for u in users):
                st.error("Este e-mail já está cadastrado.")
            else:
                users.append({"name": name, "email": email, "password": password, "role": role})
                save_users(users)
                st.success(f"✓ Usuário {name} ({email}) cadastrado com sucesso!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sunne-card"><div class="sunne-card-title">📋 Usuários Cadastrados</div>', unsafe_allow_html=True)
    users = load_users()
    rows_html = ""
    for u in users:
        badge = '<span class="badge badge-warn">admin</span>' if u["role"] == "admin" else '<span class="badge badge-info">user</span>'
        rows_html += f"<tr><td>{u['name']}</td><td>{u['email']}</td><td>{badge}</td></tr>"

    st.markdown(f"""
    <table class="sunne-table">
        <thead><tr><th>Nome</th><th>E-mail</th><th>Perfil</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)


# ── App principal ─────────────────────────────────────────────────────────────
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    if "user" not in st.session_state:
        page_login()
        return

    user = st.session_state["user"]
    render_header(user)

    # Botão de logout na sidebar
    with st.sidebar:
        st.markdown(f"**{user['name']}**  \n{user['email']}")
        if st.button("🚪 Sair"):
            for key in ["user", "df_rateio", "df_extrato", "analysis"]:
                st.session_state.pop(key, None)
            st.rerun()

    # Abas principais
    tab_labels = ["📂 Upload de Planilhas", "🔍 Gestão de Captura", "💳 Inadimplência"]
    if user.get("role") == "admin":
        tab_labels.append("⚙️ Admin")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        tab_upload()
    with tabs[1]:
        tab_captura()
    with tabs[2]:
        tab_inadimplencia()
    if user.get("role") == "admin" and len(tabs) > 3:
        with tabs[3]:
            tab_admin()


if __name__ == "__main__":
    main()
