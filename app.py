import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import io
import base64

# ── 1. PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne · Hub Operacional",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. CSS ────────────────────────────────────────────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root {
  --rubi:    #33001A;
  --rubi-l:  #4D0028;
  --gold:    #F36E21;
  --gold-l:  rgba(243,110,33,.12);
  --cream:   #FDF8F5;
  --cream-d: #F5EDE6;
  --ink:     #1A0D10;
  --ink-m:   #5A3040;
  --border:  rgba(51,0,26,.10);
  --border-s:rgba(51,0,26,.06);
  --white:   #FFFFFF;
  --radius:  14px;
  --radius-s:8px;
  --shadow:  0 2px 16px rgba(51,0,26,.08);
  --shadow-l:0 8px 40px rgba(51,0,26,.14);
}

html,body,[class*="css"]    { font-family:'DM Sans',sans-serif; color:var(--ink); }
[data-testid="stAppViewContainer"] { background:var(--cream); }
#MainMenu,footer,header     { visibility:hidden; }
.block-container            { padding-top:2rem!important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background:var(--rubi)!important;
  border-right:1px solid var(--rubi-l);
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
  background:transparent!important; border:none!important;
  padding:0!important; margin-bottom:4px!important; width:100%!important;
  display:flex!important; justify-content:flex-start!important; box-shadow:none!important;
  border-radius:8px!important; transition:all .18s!important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
  background:rgba(255,255,255,.08)!important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
  color:rgba(255,255,255,.8)!important; font-size:14px!important;
  font-weight:400!important; letter-spacing:.01em; padding:4px 0!important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p {
  color:#fff!important; font-weight:500!important;
}

/* ── Buttons ── */
.stButton>button {
  background:var(--gold)!important; color:white!important;
  border:none!important; border-radius:var(--radius-s)!important;
  font-weight:500!important; font-size:13.5px!important;
  padding:.55rem 1.4rem!important; letter-spacing:.01em!important;
  box-shadow:0 1px 6px rgba(243,110,33,.3)!important; transition:all .15s!important;
}
.stButton>button:hover {
  background:#D45E18!important; transform:translateY(-1px)!important;
}
.stDownloadButton>button {
  background:var(--rubi)!important; color:white!important;
  border:none!important; border-radius:var(--radius-s)!important;
  font-size:13px!important; padding:.5rem 1.2rem!important;
}

/* ── Typography ── */
h1 { font-family:'Instrument Serif',serif!important; font-size:2rem!important;
     font-weight:400!important; color:var(--rubi)!important; letter-spacing:-.01em!important;
     margin-bottom:.1rem!important; }
h2 { font-size:1.1rem!important; font-weight:600!important; color:var(--rubi)!important; }
h3 { font-size:.95rem!important; font-weight:600!important; color:var(--ink)!important; }

/* ── KPI ── */
.kpi-box {
  background:var(--white); border:1px solid var(--border);
  border-radius:var(--radius); padding:1.2rem 1.4rem;
  box-shadow:var(--shadow); position:relative; overflow:hidden;
}
.kpi-box::before {
  content:''; position:absolute; top:0; left:0; right:0;
  height:3px; background:var(--gold);
  border-radius:var(--radius) var(--radius) 0 0;
}
.kpi-value { font-family:'Instrument Serif',serif; font-size:2rem;
             font-weight:400; color:var(--rubi); line-height:1; margin-bottom:.25rem; }
.kpi-label { font-size:11px; font-weight:600; color:var(--ink-m);
             text-transform:uppercase; letter-spacing:.07em; }

/* ── Kanban ── */
.kb-col-head {
  font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.09em;
  padding:.45rem .9rem; border-radius:8px; margin-bottom:.75rem;
  display:flex; align-items:center; justify-content:space-between;
}
.kb-aberto    { background:#FFF3EC; color:#A84010; }
.kb-andamento { background:#FFFBEC; color:#7A5010; }
.kb-travado   { background:#FFF0F0; color:#8B1010; }
.kb-concluido { background:#EDFCF6; color:#0A6A50; }
.kb-cancelado { background:#F5F5F5; color:#444; }

.kb-card {
  background:var(--white); border:1px solid var(--border); border-radius:10px;
  padding:.85rem 1rem; margin-bottom:.5rem; cursor:pointer;
  transition:box-shadow .15s, border-color .15s, transform .1s;
}
.kb-card:hover {
  border-color:var(--gold); box-shadow:0 4px 16px rgba(51,0,26,.1); transform:translateY(-1px);
}
.kb-card-title { font-weight:600; font-size:13px; color:var(--rubi); margin-bottom:5px; }
.kb-card-meta  { font-size:11.5px; color:var(--ink-m); line-height:1.75; }
.kb-sla-ok  { color:#0B7A5F; font-size:11px; font-weight:600; margin-top:4px; }
.kb-sla-med { color:#7A5010; font-size:11px; font-weight:600; margin-top:4px; }
.kb-sla-bad { color:#C41230; font-size:11px; font-weight:600; margin-top:4px; }
.kb-motivo  { font-size:11px; color:#8B1010; margin-top:4px; font-style:italic; }
.kb-obs-badge {
  display:inline-block; background:var(--gold-l); color:var(--gold);
  border-radius:4px; padding:1px 7px; font-size:10.5px; font-weight:600; margin-top:4px;
}
.kb-wrap    { min-height:80px; }
.kb-empty   { font-size:12px; color:#C0A0A8; text-align:center; padding:1.5rem 0; }
.kb-metric  { font-size:11px; color:var(--ink-m); text-align:center; margin-top:.5rem;
              background:var(--cream-d); border-radius:6px; padding:.3rem; }

/* ── Panel (substitui dialog) ── */
.panel {
  background:var(--white); border:1.5px solid var(--border); border-radius:var(--radius);
  padding:1.75rem; box-shadow:var(--shadow-l); margin-bottom:1.5rem;
  border-left:4px solid var(--gold);
}
.panel-title { font-family:'Instrument Serif',serif; font-size:1.3rem;
               color:var(--rubi); margin-bottom:1.2rem; }
.panel-close-hint { font-size:11px; color:var(--ink-m); float:right; margin-top:3px; }

/* ── Alerts ── */
.alert { border-radius:10px; padding:.7rem 1rem; margin-bottom:.5rem; font-size:13px; }
.alert-r { background:#FFF0F3; border:1px solid #FFC8D0; color:#8B1530; }
.alert-y { background:#FFFBEC; border:1px solid #FFE580; color:#6B4A00; }
.alert-g { background:#EDFCF6; border:1px solid #A0EDCE; color:#0A5040; }

/* ── Misc ── */
.sdiv { height:1px; background:var(--border); margin:1.25rem 0; }
.sb-user { background:rgba(255,255,255,.08); border-radius:10px;
           padding:.6rem .8rem; margin-bottom:1rem; }
.sb-user-name { font-size:13px; color:white; font-weight:500; }
.sb-user-role { font-size:11px; color:rgba(255,255,255,.5); }
.sec-label { font-size:10px; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
             color:rgba(255,255,255,.35); margin-bottom:6px; margin-top:14px; padding-left:4px; }
</style>
"""

# ── 3. PATHS ──────────────────────────────────────────────────────────────────
DB              = "database"
USERS_FILE      = "users.json"
GER_FILE        = f"{DB}/geradores.json"
USI_FILE        = f"{DB}/usinas.json"
TASKS_FILE      = f"{DB}/tasks.json"
GERACAO_FILE    = f"{DB}/geracao_usinas.json"
BACKOFFICE_FILE = f"{DB}/backoffice.json"
RATEIO_FILE     = f"{DB}/historico_rateios.json"

os.makedirs(DB, exist_ok=True)

def _load(path, default):
    if not os.path.exists(path): _save(path, default)
    with open(path, encoding="utf-8") as f: return json.load(f)

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── 4. AUTH ───────────────────────────────────────────────────────────────────
def load_users():
    if not os.path.exists(USERS_FILE):
        _save(USERS_FILE, {"users": [
            {"name":"Milena",   "email":"milena@sunne.com.br",   "password":"sunne2026","role":"admin"},
            {"name":"Analista", "email":"analista@sunne.com.br", "password":"sunne2026","role":"user"},
        ]})
    with open(USERS_FILE) as f: return json.load(f).get("users", [])

def authenticate(email, password):
    for u in load_users():
        if u["email"].lower() == email.lower() and u["password"] == password:
            return u
    return None

# ── 5. CRUD ───────────────────────────────────────────────────────────────────
def load_geradores():    return _load(GER_FILE, [])
def save_geradores(d):   _save(GER_FILE, d)
def load_usinas():       return _load(USI_FILE, [])
def save_usinas(d):      _save(USI_FILE, d)
def load_tasks():        return _load(TASKS_FILE, [])
def save_tasks(d):       _save(TASKS_FILE, d)
def load_geracao():      return _load(GERACAO_FILE, [])
def save_geracao(d):     _save(GERACAO_FILE, d)
def load_backoffice():   return _load(BACKOFFICE_FILE, [])
def save_backoffice(d):  _save(BACKOFFICE_FILE, d)
def load_rateios():      return _load(RATEIO_FILE, {})
def save_rateios(d):     _save(RATEIO_FILE, d)

# ── 6. TASK HELPERS ───────────────────────────────────────────────────────────
TIPOS        = ["Avulsa","Análise de Faturamento","Rateio","Captura","Relatório","Auditoria"]
STATUS_LIST  = ["Em aberto","Em andamento","Travado","Concluido","Cancelado"]
MOTIVO_OBRIG = {"Travado","Cancelado"}
KB_CSS       = {
    "Em aberto":    "kb-aberto",
    "Em andamento": "kb-andamento",
    "Travado":      "kb-travado",
    "Concluido":    "kb-concluido",
    "Cancelado":    "kb-cancelado",
}

def new_task(titulo, usina, gerador, analista, tipo="Avulsa",
             agendamento="", descricao="", anexo_nome="", anexo_b64=""):
    tasks = load_tasks()
    tasks.append({
        "id":             datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "titulo":         titulo,  "usina":usina,  "gerador":gerador,
        "analista":       analista, "tipo":tipo,   "agendamento":agendamento,
        "descricao":      descricao, "observacoes":"",
        "anexo_nome":     anexo_nome, "anexo_b64":anexo_b64,
        "status":         "Em aberto", "motivo_bloqueio":"",
        "criado_em":      datetime.now().strftime("%d/%m/%Y %H:%M"),
        "historico":      [],
    })
    save_tasks(tasks)

def update_task(tid, **kwargs):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == tid:
            if "status" in kwargs and kwargs["status"] != t["status"]:
                t.setdefault("historico", []).append({
                    "de": t["status"], "para": kwargs["status"],
                    "em": datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
            t.update(kwargs)
    save_tasks(tasks)

def sla_days(t):
    try: return (datetime.now() - datetime.strptime(t["criado_em"], "%d/%m/%Y %H:%M")).days
    except: return 0

def sla_cls(d):
    if d <= 3: return "kb-sla-ok"
    if d <= 7: return "kb-sla-med"
    return "kb-sla-bad"

# ── 7. DATA UTILS ─────────────────────────────────────────────────────────────
def normalize_uc(val):
    if not val: return ""
    return "".join(filter(str.isdigit, str(val).strip().split('.')[0]))

def clean_val(v):
    if not v: return 0.0
    s = str(v).replace("R$","").replace(" ","").strip()
    if "," in s and "." in s: s = s.replace(".","").replace(",",".")
    elif "," in s: s = s.replace(",",".")
    try: return float(s)
    except: return 0.0

def csv_from_list(rows, cols, headers):
    out = io.StringIO(); df = pd.DataFrame(rows)
    if not df.empty:
        ex = df[[c for c in cols if c in df.columns]]
        ex.columns = headers[:len(ex.columns)]
        ex.to_csv(out, index=False, sep=';', encoding='utf-8-sig')
    return out.getvalue().encode('utf-8-sig')

def style_critical(row):
    if row['Dias de Atraso'] > 90:
        return ['background:#ffcccc;color:#990000;font-weight:bold'] * len(row)
    return ['background:#fff4cc;color:#856404;font-weight:bold'] * len(row)

def df_to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Rateio')
    return buf.getvalue()

def load_planilha(file):
    if file is None: return None
    try:
        df = (pd.read_excel(file, header=None) if not file.name.endswith('.csv')
              else pd.read_csv(file, header=None, sep=None, engine='python'))
        for i, row in df.head(20).iterrows():
            row_l = [str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s for s in row_l):
                df.columns = [str(c).strip() for c in row]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

def comp_sort_key(comp_str):
    try:
        p = str(comp_str).strip().split("/")
        if len(p) == 2: return (int(p[1]), int(p[0]))
    except: pass
    return (9999, 99)

def get_usinas_do_gerador(nome_ger):
    return [u for u in load_usinas()
            if u.get("gerador","").strip().lower() == nome_ger.strip().lower()]

# ── 8. ANALYZE FATURAMENTO (original intocada) ────────────────────────────────
def analyze_performance(df_r, df_e):
    uc_r_col    = next((c for c in df_r.columns if "UC Nova"       in c), df_r.columns[0])
    uc_e_col    = next((c for c in df_e.columns if "Número da UC"  in c), df_e.columns[0])
    comp_col    = next((c for c in df_e.columns if "Competência"   in c), None)
    status_col  = next((c for c in df_e.columns if "Status"        in c), None)
    valor_col   = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular"       in c), None)
    venc_col    = next((c for c in df_e.columns if "Vencimento"    in c), None)

    df_r["UC_NORM"] = df_r[uc_r_col].apply(normalize_uc)
    df_e["UC_NORM"] = df_e[uc_e_col].apply(normalize_uc)

    missing_res={}; inad_res={}; t_gerado={}; t_pago={}; t_vencido={}; critical_inad=[]
    hoje = datetime.now()
    if venc_col:
        df_e[venc_col] = pd.to_datetime(df_e[venc_col], errors='coerce', dayfirst=True)

    for _, row in df_e.iterrows():
        comp   = str(row[comp_col])           if comp_col    else "Geral"
        status = str(row[status_col]).lower() if status_col  else ""
        valor  = clean_val(row[valor_col])
        venc   = row[venc_col]                if venc_col    else None

        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status:
            t_pago[comp] = t_pago.get(comp, 0.0) + valor
        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp, 0.0) + valor
            item = {"uc": row[uc_e_col], "valor": valor,
                    "titular": row[titular_col] if titular_col else "—"}
            inad_res.setdefault(comp, []).append(item)
            if pd.notnull(venc):
                dias = (hoje - venc).days
                if dias > 60:
                    critical_inad.append({
                        "Titular": item["titular"], "UC": item["uc"],
                        "Vencimento": venc.strftime('%d/%m/%Y'),
                        "Dias de Atraso": dias, "Valor": valor, "Mês Ref": comp,
                    })

    critical_inad = sorted(critical_inad, key=lambda x: x['Dias de Atraso'], reverse=True)
    extrato_set   = set(zip(df_e["UC_NORM"], df_e[comp_col].astype(str)))
    ucs_rateio    = df_r["UC_NORM"].unique()

    for comp in df_e[comp_col].unique():
        if not comp or str(comp).lower() == 'nan': continue
        for uc in ucs_rateio:
            if (uc, str(comp)) not in extrato_set:
                r = df_r[df_r["UC_NORM"] == uc].iloc[0]
                missing_res.setdefault(comp, []).append({
                    "uc":      r[uc_r_col],
                    "apelido": r.get("Apelido UC", "—"),
                    "usina":   r.get("Usina", "—"),
                })

    return {"missing": missing_res, "inad": inad_res, "t_gerado": t_gerado,
            "t_pago": t_pago, "t_vencido": t_vencido, "critical_inad": critical_inad}


# ══════════════════════════════════════════════════════════════════════════════
# PANEL HELPERS  (substituem st.dialog — compatível com Streamlit >=1.34)
# ══════════════════════════════════════════════════════════════════════════════

def open_panel(key, **kwargs):
    """Abre um painel inline passando dados pelo session_state."""
    st.session_state[f"panel_{key}"] = True
    for k, v in kwargs.items():
        st.session_state[f"panel_{key}_{k}"] = v

def close_panel(key):
    for k in list(st.session_state.keys()):
        if k.startswith(f"panel_{key}"):
            del st.session_state[k]

def is_panel_open(key):
    return st.session_state.get(f"panel_{key}", False)

def panel_get(key, field, default=None):
    return st.session_state.get(f"panel_{key}_{field}", default)


def render_panel_criar_atividade():
    """Painel inline de criação de atividade (substitui st.dialog)."""
    if not is_panel_open("nova_ativ"): return

    uc_pre  = panel_get("nova_ativ", "uc", "")
    ger_pre = panel_get("nova_ativ", "gerador", "")
    analista = st.session_state["user"]["name"]

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📝 Nova Atividade</div>', unsafe_allow_html=True)

    with st.form("form_nova_ativ", clear_on_submit=True):
        c1, c2 = st.columns(2)
        uv = c1.text_input("Usina",   value=uc_pre,  disabled=bool(uc_pre))
        gv = c2.text_input("Gerador", value=ger_pre, disabled=bool(ger_pre))
        titulo = st.text_input("Título da atividade *")
        d1, d2 = st.columns(2)
        tipo  = d1.selectbox("Tipo", TIPOS)
        agend = d2.text_input("Agendamento", placeholder="20/05/2026 09:00")
        desc  = st.text_area("Descrição / Contexto", height=90,
                             placeholder="Cole links HubSpot, tickets, notas de atendimento…")
        anex  = st.file_uploader("Anexo (PDF/Excel — opcional)", type=["pdf","xlsx","xls"])
        col_s, col_c = st.columns(2)
        ok   = col_s.form_submit_button("✅ Criar Atividade", use_container_width=True)
        cncl = col_c.form_submit_button("Cancelar",           use_container_width=True)

    if ok:
        if not titulo.strip():
            st.warning("Título obrigatório.")
        else:
            an, ab = "", ""
            if anex:
                an = anex.name
                ab = base64.b64encode(anex.read()).decode()
            new_task(titulo.strip(), uv, gv, analista, tipo, agend, desc, an, ab)
            close_panel("nova_ativ")
            st.success("✅ Atividade criada! Acesse **Atividades**.")
            st.rerun()
    if cncl:
        close_panel("nova_ativ")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_panel_task_detail():
    """Painel inline de detalhe/edição de tarefa (substitui st.dialog)."""
    if not is_panel_open("task_detail"): return

    tid = panel_get("task_detail", "tid")
    tasks = load_tasks()
    t = next((x for x in tasks if x["id"] == tid), None)
    if not t:
        close_panel("task_detail"); return

    st.markdown('<div class="panel">', unsafe_allow_html=True)

    hc1, hc2 = st.columns([8, 1])
    hc1.markdown(f'<div class="panel-title">{t["titulo"]}</div>', unsafe_allow_html=True)
    if hc2.button("✕ Fechar", key="close_task_detail"):
        close_panel("task_detail"); st.rerun()

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Usina** · {t.get('usina','—')}")
    c2.markdown(f"**Gerador** · {t.get('gerador','—')}")
    c3.markdown(f"**Tipo** · {t.get('tipo','—')}")
    d1, d2 = st.columns(2)
    d1.markdown(f"**Analista** · {t.get('analista','—')}")
    d2.markdown(f"**Criado** · {t.get('criado_em','—')}")
    if t.get("agendamento"): st.markdown(f"**⏰ Agendamento** · {t['agendamento']}")
    if t.get("motivo_bloqueio"): st.markdown(f"**🔒 Motivo** · {t['motivo_bloqueio']}")
    if t.get("descricao","").strip():
        with st.expander("Descrição original"):
            st.write(t["descricao"])

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)

    # Observações / log
    st.markdown("**📝 Log de Atividade**")
    st.caption("Registre atualizações, links HubSpot, notas de chamadas:")
    nova_obs = st.text_area("Nova observação", height=100, key=f"obs_txt_{tid}",
                            placeholder="Ex: Ligou 14/05 — aguardando doc. Ticket: https://…",
                            label_visibility="collapsed")
    if st.button("Registrar observação", key=f"btn_obs_{tid}"):
        if nova_obs.strip():
            ts  = datetime.now().strftime("%d/%m/%Y %H:%M")
            an  = st.session_state["user"]["name"]
            log = t.get("observacoes","") + f"\n[{ts} — {an}]\n{nova_obs.strip()}\n"
            update_task(tid, observacoes=log)
            st.success("Observação salva."); st.rerun()

    if t.get("observacoes","").strip():
        with st.expander(f"Ver histórico de observações"):
            st.text(t["observacoes"].strip())

    # Histórico movimentações
    if t.get("historico"):
        with st.expander("🔄 Histórico de movimentações"):
            for h in t["historico"]:
                st.write(f"· {h['em']}  `{h['de']}` → `{h['para']}`")

    # Anexo
    if t.get("anexo_nome") and t.get("anexo_b64"):
        st.download_button(
            f"📎 {t['anexo_nome']}",
            base64.b64decode(t["anexo_b64"]),
            t["anexo_nome"],
            key=f"dl_anex_{tid}",
        )

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)

    # Mover status
    st.markdown("**↗ Mover para:**")
    opcoes = [s for s in STATUS_LIST if s != t["status"]]
    dest   = st.selectbox("", opcoes, key=f"dest_detail_{tid}", label_visibility="collapsed")
    mot    = ""
    if dest in MOTIVO_OBRIG:
        mot = st.text_area("Motivo obrigatório *", key=f"mot_detail_{tid}")
    if st.button("Confirmar movimentação", key=f"mv_detail_{tid}", use_container_width=True):
        if dest in MOTIVO_OBRIG and not mot.strip():
            st.warning("O motivo é obrigatório.")
        else:
            update_task(tid, status=dest, motivo_bloqueio=mot.strip())
            close_panel("task_detail"); st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        try:
            st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=110)
        except:
            st.markdown("**☀️ Sunne**")

        u = st.session_state["user"]
        st.markdown(
            f'<div class="sb-user">'
            f'<div class="sb-user-name">{u["name"]}</div>'
            f'<div class="sb-user-role">{u.get("role","user")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.session_state.setdefault("page", "dash")

        st.markdown('<div class="sec-label">Operação</div>', unsafe_allow_html=True)
        for key, label in [("dash","Dashboard"),("geradores","Geradores"),
                           ("usinas","Usinas"),("atividades","Atividades")]:
            if st.button(label, key=f"nav_{key}"):
                st.session_state["page"] = key

        st.markdown('<div class="sec-label">Energia</div>', unsafe_allow_html=True)
        for key, label in [("geracao","Geração"),("backoffice","Backoffice")]:
            if st.button(label, key=f"nav_{key}"):
                st.session_state["page"] = key

        st.markdown('<div class="sec-label">Financeiro</div>', unsafe_allow_html=True)
        for key, label in [("rateio","Rateio"),("faturamento","Faturamento")]:
            if st.button(label, key=f"nav_{key}"):
                st.session_state["page"] = key

        st.markdown("---")
        if st.button("Sair", key="nav_sair"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def page_dashboard():
    user = st.session_state["user"]; an = user["name"]
    st.title("Dashboard")

    gers    = [g for g in load_geradores() if g.get("analista","").lower() == an.lower()]
    usis    = [u for u in load_usinas()    if u.get("analista","").lower() == an.lower()]
    tasks   = load_tasks()
    geracao = load_geracao()
    bo      = load_backoffice()

    ab   = [t for t in tasks if t["status"] == "Em aberto"]
    and_ = [t for t in tasks if t["status"] == "Em andamento"]
    trav = [t for t in tasks if t["status"] == "Travado"]
    ativos = [t for t in tasks if t["status"] not in ("Concluido","Cancelado")]
    sla    = round(sum(sla_days(t) for t in ativos)/len(ativos), 1) if ativos else 0

    cols = st.columns(6)
    for col, lbl, val in zip(cols,
        ["Geradores","Usinas","Em Aberto","Em Andamento","Travadas","SLA Médio"],
        [len(gers), len(usis), len(ab), len(and_), len(trav), f"{sla}d"]):
        col.markdown(
            f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
            f'<div class="kpi-label">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("#### Alertas Operacionais")
    mes = datetime.now().strftime("%m/%Y")
    uc_ger_mes = {g["uc"] for g in geracao if g.get("competencia","") == mes}
    usi_ids    = {u["uc"] for u in usis}
    alerts = []

    for uc in usi_ids - uc_ger_mes:
        ui = next((x for x in usis if x["uc"] == uc), {})
        alerts.append(("r", f"⚡ Usina <b>{ui.get('ufv',uc)}</b> sem geração registrada em {mes}."))
    for uc in uc_ger_mes:
        r = next((x for x in bo if str(x.get("uc","")) == str(uc)), None)
        if r:
            c = clean_val(r.get("consumo_total",0)); s = clean_val(r.get("saldo_credito",0))
            if c > 0 and s/c > 6:
                ui = next((x for x in usis if str(x["uc"]) == str(uc)), {})
                alerts.append(("y", f"💰 Usina <b>{ui.get('ufv',uc)}</b>: saldo acumulado > 6 meses."))

    if not alerts:
        st.markdown('<div class="alert alert-g">✅ Nenhum alerta operacional.</div>', unsafe_allow_html=True)
    else:
        for k, m in alerts:
            st.markdown(f'<div class="alert alert-{k}">{m}</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("#### Tarefas Abertas")
    pend = ab + and_
    if pend:
        df_p = pd.DataFrame(pend)[["titulo","usina","gerador","analista","status","criado_em"]]
        df_p.columns = ["Título","Usina","Gerador","Analista","Status","Criado em"]
        st.dataframe(df_p, use_container_width=True, hide_index=True)
    else:
        st.success("Nenhuma tarefa pendente.")


# ─── FATURAMENTO ──────────────────────────────────────────────────────────────
def page_faturamento():
    st.title("Faturamento")
    t1, t2, t3 = st.tabs(["Importar","Captura","Inadimplência"])
    with t1:
        c1, c2 = st.columns(2)
        f_r = c1.file_uploader("Rateio")
        f_e = c2.file_uploader("Extrato")
        if f_r and f_e and st.button("Rodar Análise"):
            st.session_state["results"] = analyze_performance(
                load_planilha(f_r), load_planilha(f_e))
            st.success("Análise concluída.")
    res = st.session_state.get("results")
    if res:
        with t2:
            if res["missing"]:
                for comp, items in res["missing"].items():
                    with st.expander(f"⚠️ {comp} — {len(items)} faltantes"):
                        st.download_button(
                            f"Baixar CSV ({comp})",
                            csv_from_list(items,["uc","apelido","usina"],["UC","Apelido","Usina"]),
                            f"faltantes_{comp.replace('/','-')}.csv","text/csv")
                        st.table(pd.DataFrame(items))
            else:
                st.success("Nenhuma fatura faltante.")
        with t3:
            for comp, rows in res["inad"].items():
                g = res["t_gerado"].get(comp, 0.0); v = res["t_vencido"].get(comp, 0.0)
                taxa = (v/g*100) if g > 0 else 0
                st.markdown(f"#### {comp}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Gerado",        f"R$ {g:,.2f}")
                c2.metric("Vencido",       f"R$ {v:,.2f}")
                c3.metric("Inadimplência", f"{taxa:.1f}%")
                with st.expander(f"Clientes ({comp})"):
                    st.table(pd.DataFrame(rows))
            st.markdown("---")
            st.markdown("#### Inadimplência Crítica > 60 dias")
            if res["critical_inad"]:
                st.dataframe(
                    pd.DataFrame(res["critical_inad"]).style.apply(style_critical, axis=1),
                    use_container_width=True, hide_index=True)
            else:
                st.success("Nenhuma.")


# ─── GERADORES ────────────────────────────────────────────────────────────────
def page_geradores():
    user = st.session_state["user"]; an = user["name"]
    st.title("Geradores")
    tc, ti = st.tabs(["Carteira","Importar"])
    with tc:
        minha = [g for g in load_geradores() if g.get("analista","").lower() == an.lower()]
        if not minha: st.info("Nenhum gerador cadastrado."); return
        conc  = {g.get("concessionaria","") for g in minha if g.get("concessionaria","")}
        tot   = sum(int(g.get("usinas",0) or 0) for g in minha)
        c1, c2, c3 = st.columns(3)
        for col, lbl, val in zip([c1,c2,c3],
            ["Geradores","Concessionárias","Usinas Totais"],[len(minha),len(conc),tot]):
            col.markdown(
                f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
                f'<div class="kpi-label">{lbl}</div></div>',
                unsafe_allow_html=True)
        st.write("")
        filtro = st.selectbox("Concessionária", ["Todas"] + sorted(conc))
        lista  = minha if filtro == "Todas" else [g for g in minha if g.get("concessionaria") == filtro]
        df_s   = pd.DataFrame(lista)
        cols_s = [c for c in ["gerador","contato","concessionaria","usinas","porte","origem"] if c in df_s.columns]
        df_s   = df_s[cols_s]; df_s.columns = [c.capitalize() for c in cols_s]
        st.dataframe(df_s, use_container_width=True, hide_index=True)
    with ti:
        st.caption("Colunas: Gerador · Contato · Analista · Concessionária · Usinas · Porte · Origem")
        f = st.file_uploader("Arquivo", type=["xlsx","xls","csv"], key="up_ger")
        if f and st.button("Salvar", key="btn_sg"):
            try:
                df = pd.read_excel(f, dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f, dtype=str)
                df.columns = df.columns.str.strip().str.lower()
                df.rename(columns={"concessionária":"concessionaria"}, inplace=True)
                df = df.fillna("")
                ex = load_geradores(); nex = {g["gerador"].lower() for g in ex}; n = 0
                for _, row in df.iterrows():
                    nm = str(row.get("gerador","")).strip()
                    if nm and nm.lower() not in nex:
                        ex.append({k: str(row.get(k,"")) for k in
                            ["gerador","contato","analista","concessionaria","usinas","porte","origem"]})
                        nex.add(nm.lower()); n += 1
                save_geradores(ex); st.success(f"{n} gerador(es) importado(s)."); st.rerun()
            except Exception as e: st.error(str(e))


# ─── USINAS ───────────────────────────────────────────────────────────────────
def page_usinas():
    user = st.session_state["user"]; an = user["name"]
    st.title("Usinas")

    # Renderizar painel de criar atividade se aberto
    render_panel_criar_atividade()

    ca, cb, _ = st.columns([1.3, 1.7, 6])
    if ca.button("Adicionar"):
        st.session_state["show_add_usi"] = not st.session_state.get("show_add_usi", False)
    if cb.button("Importar Planilha"):
        st.session_state["show_imp_usi"] = not st.session_state.get("show_imp_usi", False)

    if st.session_state.get("show_add_usi"):
        with st.form("fau", clear_on_submit=True):
            st.markdown("**Nova Usina**")
            a1, a2 = st.columns(2); b1, b2, b3 = st.columns(3)
            uc    = a1.text_input("UC *"); ger = a2.text_input("Gerador")
            ufv   = b1.text_input("UFV"); ativa = b2.selectbox("Ativa", ["Sim","Não"])
            gest  = b3.number_input("Geração estimada kWh", min_value=0.0, step=1.0)
            s, c  = st.columns(2)
            sal   = s.form_submit_button("Salvar")
            canc  = c.form_submit_button("Cancelar")
        if sal:
            if not uc.strip(): st.warning("UC obrigatória.")
            else:
                us = load_usinas()
                us.append({"uc":str(uc).strip(), "gerador":ger.strip(), "ufv":ufv.strip(),
                            "analista":an, "ativa":ativa, "geracao_estimada":gest,
                            "criado_em":datetime.now().strftime("%d/%m/%Y")})
                save_usinas(us); st.session_state["show_add_usi"] = False; st.rerun()
        if canc: st.session_state["show_add_usi"] = False; st.rerun()

    if st.session_state.get("show_imp_usi"):
        st.caption("Colunas: UC · Gerador · UFV · Analista · Ativa · Geração")
        f = st.file_uploader("Arquivo", type=["xlsx","xls","csv"], key="up_usi")
        i1, i2 = st.columns([1, 5])
        if i1.button("Importar", key="btn_iusi") and f:
            try:
                df = pd.read_excel(f, dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f, dtype=str)
                df.columns = df.columns.str.strip().str.lower(); df = df.fillna("")
                for col in list(df.columns):
                    cl = col.lower()
                    if "gerador" in cl and col != "gerador": df.rename(columns={col:"gerador"}, inplace=True)
                    if cl in ("geração","geracao","geração (kwh)","geracao (kwh)"):
                        df.rename(columns={col:"geracao_estimada"}, inplace=True)
                us = load_usinas(); uc_ex = {u["uc"] for u in us}; n = 0
                for _, row in df.iterrows():
                    uv = str(row.get("uc","")).strip()
                    if uv and uv not in uc_ex:
                        us.append({"uc":uv, "gerador":str(row.get("gerador","")),
                            "ufv":str(row.get("ufv","")), "analista":an,
                            "ativa":str(row.get("ativa","Sim")),
                            "geracao_estimada":clean_val(row.get("geracao_estimada",0)),
                            "criado_em":datetime.now().strftime("%d/%m/%Y")})
                        uc_ex.add(uv); n += 1
                save_usinas(us); st.session_state["show_imp_usi"] = False
                st.success(f"{n} usina(s) importada(s)."); st.rerun()
            except Exception as e: st.error(str(e))
        if i2.button("Fechar", key="fusi"):
            st.session_state["show_imp_usi"] = False; st.rerun()

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)
    usinas = load_usinas()
    minhas = [u for u in usinas if u.get("analista","").lower() == an.lower()]
    if not minhas: st.info("Nenhuma usina cadastrada."); return

    ger_opts = ["Todos"] + sorted({u.get("gerador","—") for u in minhas})
    filtro   = st.selectbox("Filtrar por Gerador", ger_opts)
    lista    = minhas if filtro == "Todos" else [u for u in minhas if u.get("gerador") == filtro]

    h = st.columns([1.4, 1.8, 2.5, 1.4, 0.7, 0.8])
    for col, txt in zip(h, ["UC","Gerador","UFV","Analista","Ativa","Atividade"]):
        col.markdown(f"**{txt}**")
    st.markdown("<hr style='margin:4px 0 8px;border:none;border-top:1px solid rgba(51,0,26,.08)'>",
                unsafe_allow_html=True)

    for idx, u in enumerate(lista):
        r = st.columns([1.4, 1.8, 2.5, 1.4, 0.7, 0.8])
        r[0].write(str(u.get("uc","—")))
        r[1].write(u.get("gerador","—"))
        r[2].write(u.get("ufv","—"))
        r[3].write(u.get("analista","—"))
        r[4].write("✅" if u.get("ativa","Sim") == "Sim" else "❌")
        if r[5].button("📝 Nova", key=f"ativ_{idx}_{u['uc']}"):
            open_panel("nova_ativ", uc=str(u.get("uc","")), gerador=u.get("gerador",""))
            st.rerun()


# ─── ATIVIDADES ───────────────────────────────────────────────────────────────
def page_atividades():
    st.title("Atividades")

    # Painel de criar atividade avulsa
    render_panel_criar_atividade()

    # Painel de detalhe de tarefa
    render_panel_task_detail()

    hc1, _ = st.columns([2, 8])
    if hc1.button("➕ Nova Atividade"):
        open_panel("nova_ativ")
        st.rerun()

    fc1, fc2 = st.columns(2)
    f_an = fc1.text_input("Filtrar Analista", placeholder="todos")
    f_ge = fc2.text_input("Filtrar Gerador",  placeholder="todos")

    def match(t):
        if f_an and f_an.lower() not in t.get("analista","").lower(): return False
        if f_ge and f_ge.lower() not in t.get("gerador","").lower():  return False
        return True

    tasks = [t for t in load_tasks() if match(t)]

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)
    kb_cols = st.columns(5)

    for col_ui, status in zip(kb_cols, STATUS_LIST):
        css   = KB_CSS[status]
        grupo = [t for t in tasks if t["status"] == status]
        with col_ui:
            count_badge = (
                f'<span style="background:rgba(0,0,0,.08);border-radius:12px;'
                f'padding:1px 8px">{len(grupo)}</span>'
            )
            st.markdown(
                f'<div class="kb-col-head {css}"><span>{status}</span>{count_badge}</div>',
                unsafe_allow_html=True)
            st.markdown('<div class="kb-wrap">', unsafe_allow_html=True)

            if not grupo:
                st.markdown('<div class="kb-empty">—</div>', unsafe_allow_html=True)

            for t in grupo:
                tid  = t["id"]
                dias = sla_days(t)
                sc   = sla_cls(dias)
                mot_h = (f'<div class="kb-motivo">🔒 {t["motivo_bloqueio"]}</div>'
                         if t.get("motivo_bloqueio") else "")
                n_obs = len([l for l in t.get("observacoes","").split("\n")
                              if l.startswith("[")]) if t.get("observacoes") else 0
                obs_h = f'<span class="kb-obs-badge">📝 {n_obs}</span>' if n_obs > 0 else ""

                st.markdown(f"""
                <div class="kb-card">
                  <div class="kb-card-title">{t['titulo']}</div>
                  <div class="kb-card-meta">
                    🏭 {t.get('usina','—')}<br>
                    ⚡ {t.get('gerador','—')}<br>
                    👤 {t.get('analista','—')}<br>
                    📅 {t.get('criado_em','')}
                  </div>
                  <div class="{sc}">⏱ SLA: {dias}d</div>
                  {obs_h}{mot_h}
                </div>""", unsafe_allow_html=True)

                # Botão abrir painel de detalhe
                if st.button("Abrir", key=f"open_{tid}", use_container_width=True):
                    open_panel("task_detail", tid=tid)
                    st.rerun()

                # Mover rápido inline
                opcoes = [s for s in STATUS_LIST if s != status]
                dest   = st.selectbox("", opcoes, key=f"dest_{tid}",
                                      label_visibility="collapsed")
                if st.button("↗", key=f"mv_{tid}", help="Mover para status selecionado"):
                    if dest in MOTIVO_OBRIG:
                        st.session_state[f"pm_{tid}"] = dest
                    else:
                        update_task(tid, status=dest, motivo_bloqueio=""); st.rerun()

                if st.session_state.get(f"pm_{tid}"):
                    dv  = st.session_state[f"pm_{tid}"]
                    mot = st.text_area(f"Motivo para '{dv}' *", key=f"mot_{tid}")
                    mc1, mc2 = st.columns(2)
                    if mc1.button("OK", key=f"conf_{tid}"):
                        if mot.strip():
                            update_task(tid, status=dv, motivo_bloqueio=mot.strip())
                            del st.session_state[f"pm_{tid}"]; st.rerun()
                        else: st.warning("Motivo obrigatório.")
                    if mc2.button("✕", key=f"cno_{tid}"):
                        del st.session_state[f"pm_{tid}"]; st.rerun()

                st.markdown(
                    "<hr style='margin:4px 0;border:none;border-top:1px solid rgba(51,0,26,.06)'>",
                    unsafe_allow_html=True)

            if grupo:
                med = round(sum(sla_days(t) for t in grupo)/len(grupo), 1)
                st.markdown(f'<div class="kb-metric">⏱ Média {med}d</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ─── GERAÇÃO ──────────────────────────────────────────────────────────────────
def page_geracao():
    st.title("Geração das Usinas")
    tm, ti = st.tabs(["Lançamento Manual","Importar Excel"])

    with tm:
        # Campo UC fora do form — autocompletar em tempo real
        uc_inp = st.text_input("UC da Usina *", key="ger_uc_inp", placeholder="Digite a UC…")

        nome_auto    = ""
        gerador_auto = ""
        if uc_inp.strip():
            usinas = load_usinas()
            m = next((u for u in usinas
                      if normalize_uc(u["uc"]) == normalize_uc(uc_inp)), None)
            if m:
                nome_auto    = m.get("ufv","")
                gerador_auto = m.get("gerador","")
                st.success(f"✅ **{nome_auto}** · Gerador: **{gerador_auto}**")
            else:
                st.caption("UC não encontrada no cadastro — preencha o nome manualmente.")

        with st.form("form_geracao", clear_on_submit=True):
            g1, g2 = st.columns(2)
            nome_g = g1.text_input("Nome Usina", value=nome_auto,
                                   placeholder="Preenchido automaticamente")
            comp_g = g2.text_input("Competência (MM/AAAA)",
                                   value=datetime.now().strftime("%m/%Y"))
            g3, g4 = st.columns(2)
            inj_g  = g3.number_input("Energia Injetada (kWh)", min_value=0.0, step=0.1)
            sld_g  = g4.number_input("Saldo (kWh)",             min_value=0.0, step=0.1)
            ok = st.form_submit_button("Salvar Geração", use_container_width=True)

        if ok:
            if not uc_inp.strip():
                st.warning("UC obrigatória.")
            else:
                usinas = load_usinas()
                m2     = next((u for u in usinas
                               if normalize_uc(u["uc"]) == normalize_uc(uc_inp)), None)
                nf = m2.get("ufv","") if m2 else nome_g
                gd = m2.get("gerador","") if m2 else gerador_auto
                ger = load_geracao()
                ger.append({
                    "uc":              str(uc_inp).strip(),
                    "nome_usina":      nf,
                    "gerador":         gd,
                    "competencia":     comp_g,
                    "energia_injetada":inj_g,
                    "saldo":           sld_g,
                    "registrado_em":   datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
                save_geracao(ger)
                st.success(f"✅ Geração registrada — **{nf or uc_inp}**")

    with ti:
        st.caption("Colunas: Nome da Usina · Número da UG · Competência · Energia Injetada · Saldo")
        f = st.file_uploader("Arquivo", type=["xlsx","xls","csv"], key="up_ger2")
        if f and st.button("Importar", key="btn_iger"):
            try:
                df = (pd.read_excel(f, dtype=str) if not f.name.endswith(".csv")
                      else pd.read_csv(f, dtype=str))
                df.columns = df.columns.str.strip().str.lower(); df = df.fillna("")
                df.rename(columns={"nome da usina":"nome_usina","número da ug":"uc",
                                   "numero da ug":"uc","energia injetada":"energia_injetada"}, inplace=True)
                usinas = load_usinas(); ger = load_geracao(); n = 0
                for _, row in df.iterrows():
                    uv = str(row.get("uc","")).strip()
                    m  = next((u for u in usinas if normalize_uc(u["uc"]) == normalize_uc(uv)), None)
                    nm = m.get("ufv","") if m else str(row.get("nome_usina",""))
                    gd = m.get("gerador","") if m else ""
                    ger.append({
                        "uc":str(uv),"nome_usina":nm,"gerador":gd,
                        "competencia":str(row.get("competência",row.get("competencia",""))),
                        "energia_injetada":clean_val(row.get("energia_injetada",0)),
                        "saldo":clean_val(row.get("saldo",0)),
                        "registrado_em":datetime.now().strftime("%d/%m/%Y %H:%M"),
                    }); n += 1
                save_geracao(ger); st.success(f"{n} registro(s) importado(s).")
            except Exception as e: st.error(str(e))

    # Registros com filtro + ordenação por competência
    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)
    st.markdown("#### Registros de Geração")
    ger = load_geracao()
    if not ger: st.info("Nenhum registro ainda."); return

    df_g = pd.DataFrame(ger)
    for cn in ["uc","nome_usina","gerador","competencia","energia_injetada","saldo"]:
        if cn not in df_g.columns: df_g[cn] = ""

    fa, fb, _ = st.columns([2, 2, 3])
    gers_list  = sorted({str(x) for x in df_g["gerador"].unique() if x})
    ger_filtro = fa.selectbox("Gerador", ["Todos"] + gers_list, key="gf_ger")

    usi_list = []
    if ger_filtro != "Todos":
        usi_list = sorted({str(r) for r in df_g[df_g["gerador"]==ger_filtro]["nome_usina"].unique() if r})
    usi_filtro = fb.selectbox("Usina", ["Todas"] + usi_list, key="gf_usi",
                              disabled=(ger_filtro=="Todos"))

    df_f = df_g.copy()
    if ger_filtro != "Todos":
        df_f = df_f[df_f["gerador"] == ger_filtro]
    if usi_filtro != "Todas" and ger_filtro != "Todos":
        df_f = df_f[df_f["nome_usina"] == usi_filtro]

    df_f = df_f.copy()
    df_f["_sort"] = df_f["competencia"].apply(comp_sort_key)
    df_f = df_f.sort_values("_sort", ascending=False).drop(columns=["_sort"])

    cols_show = [c for c in ["uc","nome_usina","gerador","competencia",
                              "energia_injetada","saldo","registrado_em"] if c in df_f.columns]
    st.dataframe(df_f[cols_show], use_container_width=True, hide_index=True)


# ─── BACKOFFICE ───────────────────────────────────────────────────────────────
def page_backoffice():
    st.title("Backoffice · Captura de Consumo")

    geradores = load_geradores(); nomes = [g["gerador"] for g in geradores]
    if not nomes: st.warning("Cadastre geradores primeiro."); return

    sel_ger = st.selectbox("Vincular ao Gerador", sorted(set(nomes)), key="bo_ger")
    st.caption("O extrato importado será associado a este gerador.")

    f = st.file_uploader("Extrato Detalhado", type=["xlsx","xls","csv"], key="up_bo")
    if f and st.button("Processar Extrato"):
        try:
            df = (pd.read_excel(f, header=None) if not f.name.endswith(".csv")
                  else pd.read_csv(f, header=None, sep=None, engine='python'))
            for i, row in df.head(20).iterrows():
                if any("número da uc" in str(c).lower() for c in row):
                    df.columns = [str(c).strip() for c in row]
                    df = df.iloc[i+1:].reset_index(drop=True); break
            df.columns = [str(c).strip() for c in df.columns]; df = df.fillna("")
            uc_c  = next((c for c in df.columns if "Número da UC" in c), None)
            co_c  = next((c for c in df.columns if "Consumo"      in c), None)
            sa_c  = next((c for c in df.columns if "Saldo"        in c), None)
            ti_c  = next((c for c in df.columns if "Tipo"         in c or "Instalação" in c), None)
            tt_c  = next((c for c in df.columns if "Titular"      in c), None)
            if not uc_c: st.error("Coluna 'Número da UC' não encontrada."); return
            bo = load_backoffice(); nn = nu = 0
            for _, row in df.iterrows():
                uv = str(row[uc_c]).strip()
                if not uv: continue
                rec = {
                    "uc":              uv,
                    "gerador":         sel_ger,
                    "titular":         str(row[tt_c]) if tt_c else "—",
                    "consumo_total":   clean_val(row[co_c]) if co_c else 0,
                    "saldo_credito":   clean_val(row[sa_c]) if sa_c else 0,
                    "tipo_instalacao": str(row[ti_c]) if ti_c else "—",
                    "atualizado_em":   datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                ix = next((i for i, b in enumerate(bo) if str(b["uc"]) == uv), None)
                if ix is not None: bo[ix] = rec; nu += 1
                else: bo.append(rec); nn += 1
            save_backoffice(bo)
            st.success(f"✅ {nn} novos · {nu} atualizados — Gerador: **{sel_ger}**")
        except Exception as e: st.error(str(e))

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)
    bo = load_backoffice()
    if bo:
        st.markdown("#### Base de Consumo")
        gf = st.selectbox("Filtrar Gerador",
                          ["Todos"] + sorted({b.get("gerador","—") for b in bo}), key="bo_f")
        bof = bo if gf == "Todos" else [b for b in bo if b.get("gerador","") == gf]
        st.dataframe(pd.DataFrame(bof), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado ainda.")


# ─── RATEIO ───────────────────────────────────────────────────────────────────
def page_rateio():
    st.title("Rateio")
    ta, tb, tc, td = st.tabs(["Rebalancear","Atualizar Vigente","Consultar","Buscar UC"])

    geradores = load_geradores()
    nomes_ger = sorted({g["gerador"] for g in geradores})

    # ══ A ══
    with ta:
        st.markdown("#### Rebalanceamento de Rateio")
        if not nomes_ger: st.info("Cadastre geradores."); st.stop()
        sg = st.selectbox("Gerador", nomes_ger, key="rb_ger")
        ug = get_usinas_do_gerador(sg)
        if not ug:
            st.warning(f"Nenhuma usina vinculada a **{sg}**."); st.stop()
        nms = [u.get("ufv") or u["uc"] for u in ug]
        su  = st.selectbox("Usina", nms, key="rb_usi")
        su_obj = ug[nms.index(su)]; uc_u = str(su_obj["uc"])

        gm  = load_geracao(); mes = datetime.now().strftime("%m/%Y")
        rg  = next((g for g in gm if normalize_uc(str(g.get("uc",""))) == normalize_uc(uc_u)
                    and g.get("competencia","") == mes), None)
        if not rg:
            st.warning(f"Geração de **{su}** para {mes} não registrada. Registre em Geração primeiro.")
            st.stop()

        gkwh = clean_val(rg.get("energia_injetada",0))
        st.info(f"Geração {mes}: **{gkwh:,.2f} kWh**")
        aut = st.number_input("Meses de autonomia desejada", 1, 12, 3, key="rb_aut")

        ra1, ra2 = st.columns(2)
        f_rat = ra1.file_uploader("Rateio Vigente",   type=["xlsx","xls","csv"], key="up_rat")
        f_ext = ra2.file_uploader("Extrato Detalhado",type=["xlsx","xls","csv"], key="up_ext_rat")

        st.markdown("**UCs Saindo:**")
        ns = st.number_input("Qtd", 0, 30, 0, step=1, key="rb_ns")
        ucs_s = []
        for i in range(int(ns)):
            c1, c2 = st.columns(2)
            us2 = c1.text_input(f"UC #{i+1}", key=f"us_{i}")
            ms2 = c2.text_input(f"Motivo #{i+1}", key=f"ms_{i}")
            if us2: ucs_s.append({"uc":str(us2).strip(),"motivo":ms2})

        st.markdown("**Novas UCs:**")
        nn2 = st.number_input("Qtd", 0, 30, 0, step=1, key="rb_nn")
        ucs_n = []
        for i in range(int(nn2)):
            c1, c2, c3 = st.columns(3)
            un = c1.text_input(f"UC #{i+1}",     key=f"un_{i}")
            an2= c2.text_input(f"Apelido #{i+1}",key=f"an2_{i}")
            cn = c3.number_input(f"Consumo kWh #{i+1}", 0.0, step=1.0, key=f"cn_{i}")
            if un: ucs_n.append({"uc":str(un).strip(),"apelido":an2,"consumo":cn})

        ancora = st.text_input("Unidade Âncora (opcional)", key="rb_anc")

        if st.button("Calcular", key="btn_rb"):
            if not f_rat or not f_ext: st.error("Faça upload dos dois arquivos."); st.stop()
            try:
                df_rat = (pd.read_excel(f_rat, dtype=str) if not f_rat.name.endswith(".csv")
                          else pd.read_csv(f_rat, dtype=str))
                df_rat.columns = df_rat.columns.str.strip(); df_rat = df_rat.fillna("")
                df_ext = load_planilha(f_ext)
                if df_ext is None: st.error("Erro no extrato."); st.stop()

                uc_e = next((c for c in df_ext.columns if "Número da UC" in c), df_ext.columns[0])
                co_c = next((c for c in df_ext.columns if "Consumo"      in c), None)
                sa_c = next((c for c in df_ext.columns if "Saldo"        in c), None)
                ti_c = next((c for c in df_ext.columns if "Tipo"         in c or "Instalação" in c), None)
                df_ext["UC_NORM"] = df_ext[uc_e].apply(normalize_uc)

                uc_r = next((c for c in df_rat.columns if "UC" in c), df_rat.columns[0])
                ap_c = next((c for c in df_rat.columns if "Apelido" in c), None)
                cn_c = next((c for c in df_rat.columns if "CNPJ"    in c), None)
                df_rat["UC_NORM"] = df_rat[uc_r].apply(normalize_uc)

                sn = {normalize_uc(x["uc"]) for x in ucs_s}
                df_rat = df_rat[~df_rat["UC_NORM"].isin(sn)].copy()

                res = []
                for _, rr in df_rat.iterrows():
                    un = rr["UC_NORM"]
                    ap = rr[ap_c] if ap_c else "—"
                    cn = rr[cn_c] if cn_c else "—"
                    er = df_ext[df_ext["UC_NORM"] == un]
                    if er.empty: ct=sa=0; tp="monofasico"
                    else:
                        er = er.iloc[0]
                        ct = clean_val(er[co_c]) if co_c else 0
                        sa = clean_val(er[sa_c]) if sa_c else 0
                        tp = str(er[ti_c]).lower() if ti_c else "monofasico"
                    cc  = max(ct-100, 0) if "trif" in tp else max(ct-30, 0)
                    nec = cc*0.20 if ct > 0 and sa/ct > aut else cc
                    res.append({"UC_NORM":un,"UC":rr[uc_r],"Apelido":ap,"CNPJ":cn,
                                "Consumo Comp.":round(cc,2),"Saldo":round(sa,2),"Necessidade":round(nec,2)})

                for nu_item in ucs_n:
                    cc = max(nu_item["consumo"]-30, 0)
                    res.append({"UC_NORM":normalize_uc(nu_item["uc"]),"UC":nu_item["uc"],
                                "Apelido":nu_item.get("apelido","—"),"CNPJ":"—",
                                "Consumo Comp.":round(cc,2),"Saldo":0,"Necessidade":round(cc,2)})

                tn = sum(r["Necessidade"] for r in res)
                for r in res:
                    r["Rateio %"] = round((r["Necessidade"]/gkwh*100), 4) if gkwh > 0 else 0

                soma  = sum(r["Rateio %"] for r in res)
                sobra = round(100.0 - soma, 4)
                if sobra != 0:
                    anorm = normalize_uc(ancora) if ancora else None
                    ia = next((i for i,r in enumerate(res) if r["UC_NORM"]==anorm), None) if anorm else None
                    if ia is not None:
                        res[ia]["Rateio %"] = round(res[ia]["Rateio %"] + sobra, 4)
                    elif tn > 0:
                        for r in res:
                            r["Rateio %"] = round(r["Rateio %"] + sobra*(r["Necessidade"]/tn), 4)

                df_res  = pd.DataFrame(res)
                df_res.insert(0,"#",range(1,len(df_res)+1))
                cols_f  = ["#","UC","Apelido","CNPJ","Consumo Comp.","Saldo","Rateio %"]
                df_show = df_res[[c for c in cols_f if c in df_res.columns]]
                total   = {"#":"TOTAL","UC":"","Apelido":"","CNPJ":"",
                           "Consumo Comp.":df_show["Consumo Comp."].sum(),
                           "Saldo":df_show["Saldo"].sum(),"Rateio %":df_show["Rateio %"].sum()}
                df_show = pd.concat([df_show, pd.DataFrame([total])], ignore_index=True)

                st.success(f"Soma: {df_res['Rateio %'].sum():.4f}% · Geração: {gkwh:,.2f} kWh")
                st.dataframe(df_show, use_container_width=True, hide_index=True)
                st.download_button("Exportar Excel", df_to_excel_bytes(df_show),
                    f"rateio_{sg}_{su}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(str(e)); import traceback; st.code(traceback.format_exc())

    # ══ B ══
    with tb:
        st.markdown("#### Atualizar Rateio Vigente")
        st.caption("Modelo Sunne — colunas: # · UC · Apelido · CNPJ · Consumo Comp. · Saldo · Rateio Ideal % · Rateio Verificado % · Percentual · Estimado Verificado · Estimado Ideal · Déficit Mensal · Autonomia · kWh Disponível · Observações")
        if not nomes_ger: st.info("Cadastre geradores."); st.stop()
        sg2 = st.selectbox("Gerador", nomes_ger, key="upd_ger")
        ug2 = get_usinas_do_gerador(sg2)
        if not ug2: st.warning(f"Nenhuma usina em **{sg2}**."); st.stop()
        nm2 = [u.get("ufv") or u["uc"] for u in ug2]
        su2 = st.selectbox("Usina", nm2, key="upd_usi")
        uc2 = ug2[nm2.index(su2)]["uc"]
        gv2 = clean_val(ug2[nm2.index(su2)].get("geracao_estimada",0))
        f_u = st.file_uploader("Planilha do novo rateio (modelo Sunne)",
                               type=["xlsx","xls","csv"], key="up_upd")
        if f_u and st.button("Salvar como Vigente"):
            try:
                df_u = (pd.read_excel(f_u, dtype=str) if not f_u.name.endswith(".csv")
                        else pd.read_csv(f_u, dtype=str))
                df_u.columns = df_u.columns.str.strip(); df_u = df_u.fillna("")
                hist = load_rateios(); ch = f"{sg2}||{uc2}"
                hist.setdefault(ch, [])
                hist[ch].append({"versao":len(hist[ch])+1,
                                 "salvo_em":datetime.now().strftime("%d/%m/%Y %H:%M"),
                                 "gerador":sg2,"usina_nome":su2,"uc":uc2,
                                 "geracao_kwh":gv2,"dados":df_u.to_dict(orient="records")})
                save_rateios(hist)
                st.success(f"Rateio v{len(hist[ch])} salvo — **{su2}**")
            except Exception as e: st.error(str(e))

    # ══ C ══
    with tc:
        st.markdown("#### Consultar Rateio")
        if not nomes_ger: st.info("Cadastre geradores."); st.stop()
        sg3 = st.selectbox("Gerador", nomes_ger, key="cons_ger")
        ug3 = get_usinas_do_gerador(sg3)
        if not ug3: st.warning(f"Nenhuma usina em **{sg3}**."); st.stop()
        nm3 = [u.get("ufv") or u["uc"] for u in ug3]
        su3 = st.selectbox("Usina", nm3, key="cons_usi")
        uc3 = ug3[nm3.index(su3)]["uc"]
        ch3 = f"{sg3}||{uc3}"
        hist = load_rateios(); vers = hist.get(ch3,[])
        if not vers: st.info(f"Nenhum rateio salvo para **{su3}**."); st.stop()
        opts = [f"v{v['versao']} — {v['salvo_em']}" for v in vers]
        sv   = st.selectbox("Versão", opts, index=len(opts)-1, key="cons_v")
        iv   = opts.index(sv); vd = vers[iv]
        lbl  = "✅ Vigente" if iv==len(vers)-1 else f"📁 Histórico v{vd['versao']}"
        st.markdown(f"**{lbl}** · {vd['salvo_em']}")
        if vd.get("geracao_kwh"): st.info(f"Geração: **{vd['geracao_kwh']:,.2f} kWh**")
        df_v = pd.DataFrame(vd["dados"])
        st.dataframe(df_v, use_container_width=True, hide_index=True)
        st.download_button(
            f"Exportar Excel — {su3}",
            df_to_excel_bytes(df_v),
            f"rateio_vigente_{sg3}_{su3}_v{vd['versao']}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ══ D ══
    with td:
        st.markdown("#### Buscar Beneficiário por UC")
        st.markdown("Pesquisa em todos os rateios vigentes cadastrados no sistema.")

        col_inp, col_btn = st.columns([4, 1])
        uc_b    = col_inp.text_input("Número da UC", placeholder="Ex: 65447775",
                                     label_visibility="collapsed", key="uc_busca_td")
        buscar  = col_btn.button("🔍 Buscar", key="btn_busca_td", use_container_width=True)

        if buscar:
            if not uc_b.strip():
                st.warning("Digite uma UC.")
            else:
                unb   = normalize_uc(uc_b)
                hist  = load_rateios()
                bo    = load_backoffice()
                found = False

                for ch, vers in hist.items():
                    if not vers: continue
                    vig = vers[-1]
                    gen, uc_key = ch.split("||") if "||" in ch else (ch,"")
                    for row in vig["dados"]:
                        for k, v in row.items():
                            if normalize_uc(str(v)) == unb:
                                found = True
                                ap_k  = next((k2 for k2 in row if any(x in k2.lower()
                                              for x in ["apelido","titular","nome"])), None)
                                nome_c = row.get(ap_k,"—") if ap_k else "—"
                                pt_k   = next((k2 for k2 in row if "%" in k2
                                               or "rateio" in k2.lower()
                                               or "verificado" in k2.lower()), None)
                                pct    = row.get(pt_k,"—") if pt_k else "—"
                                usinas = load_usinas()
                                um     = next((u for u in usinas
                                              if normalize_uc(u["uc"])==normalize_uc(uc_key)),{})
                                unome  = um.get("ufv", uc_key)
                                bo_r   = next((b for b in bo
                                              if normalize_uc(str(b.get("uc","")))==unb), None)

                                st.success(f"UC **{uc_b}** encontrada.")
                                st.markdown(f"""
| Campo | Valor |
|---|---|
| **UC** | `{uc_b}` |
| **Nome / Apelido** | {nome_c} |
| **Gerador** | {gen} |
| **Usina** | {unome} |
| **% Rateio** | {pct} |
| **Versão** | v{vig['versao']} · {vig['salvo_em']} |
""")
                                if bo_r:
                                    b1, b2, b3 = st.columns(3)
                                    b1.metric("Consumo",  f"{bo_r.get('consumo_total',0):,.1f} kWh")
                                    b2.metric("Saldo",    f"{bo_r.get('saldo_credito',0):,.1f} kWh")
                                    b3.metric("Tipo Inst.",bo_r.get("tipo_instalacao","—"))
                                else:
                                    st.info("UC não encontrada no Backoffice. Importe o extrato para ver consumo e saldo.")
                                break
                        if found: break
                    if found: break

                if not found:
                    st.warning(f"UC **{uc_b}** não encontrada em nenhum rateio ativo.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    # ── Login
    if "user" not in st.session_state:
        _, mid, _ = st.columns([1, 1.4, 1])
        with mid:
            st.markdown("<div style='margin-top:8vh'>", unsafe_allow_html=True)
            try:
                st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=110)
            except:
                st.markdown("### ☀️ Sunne")
            st.markdown('<p style="font-family:\'Instrument Serif\',serif;font-size:1.6rem;color:#33001A;margin-bottom:.2rem">Hub Operacional</p>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:13px;color:#5A3040;margin-bottom:1.5rem">Plataforma de gestão de geração distribuída</p>', unsafe_allow_html=True)
            with st.form("login"):
                e = st.text_input("E-mail", placeholder="seu@sunne.com.br")
                s = st.text_input("Senha",  type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    u = authenticate(e, s)
                    if u:
                        st.session_state["user"] = u
                        st.session_state.setdefault("page","dash")
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
            st.markdown("</div>", unsafe_allow_html=True)
        return

    render_sidebar()

    page  = st.session_state.get("page","dash")
    pages = {
        "dash":        page_dashboard,
        "geradores":   page_geradores,
        "usinas":      page_usinas,
        "atividades":  page_atividades,
        "geracao":     page_geracao,
        "backoffice":  page_backoffice,
        "rateio":      page_rateio,
        "faturamento": page_faturamento,
    }
    pages.get(page, page_dashboard)()


if __name__ == "__main__":
    main()
