import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import io
import base64

# ── 1. CONFIGURAÇÃO DA PÁGINA ────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne Hub",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. CSS (ORIGINAL INTOCADO + EXTENSÕES) ───────────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root { --rubi:#33001A; --laranja:#F36E21; --bg:#FDF8F5; }

[data-testid="stAppViewContainer"] { background-color: var(--bg); }
html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
#MainMenu,footer,header { visibility:hidden; }

[data-testid="stSidebar"] { background-color:var(--rubi)!important; border-right:1px solid rgba(255,255,255,.1); }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color:transparent!important; border:none!important; color:white!important;
    padding:0!important; margin-bottom:20px!important; width:100%!important;
    display:flex!important; justify-content:flex-start!important; text-align:left!important; box-shadow:none!important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p { color:white!important; font-size:16px!important; font-weight:500!important; transition:.3s; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p { color:var(--laranja)!important; font-weight:700!important; }

.stButton>button { background-color:var(--laranja)!important; color:white!important; border-radius:8px!important; border:none!important; }

.kpi-box { background:white; border-radius:15px; padding:1.2rem; border:1px solid #EAD8D0; text-align:center; }
.kpi-value { font-family:'Syne',sans-serif; font-size:20px; font-weight:700; color:var(--rubi); }
.login-card { background:white; padding:3rem; border-radius:25px; box-shadow:0 15px 35px rgba(51,0,26,.1); border:1px solid #EAD8D0; max-width:400px; margin:auto; text-align:center; }

/* Kanban */
.kanban-card { background:white; border:1px solid #EAD8D0; border-radius:12px; padding:.85rem 1rem; margin-bottom:.65rem; font-size:13px; box-shadow:0 1px 4px rgba(51,0,26,.06); cursor:pointer; }
.k-title { font-family:'Syne',sans-serif; font-weight:700; font-size:13px; color:var(--rubi); margin-bottom:4px; }
.k-meta { font-size:11px; color:#7A5060; line-height:1.6; }
.k-sla-ok  { font-size:11px; color:#0A7A6A; font-weight:600; }
.k-sla-med { font-size:11px; color:#856404; font-weight:600; }
.k-sla-bad { font-size:11px; color:#CC1A3A; font-weight:600; }
.k-motivo  { font-size:11px; color:#990000; margin-top:4px; font-style:italic; }
.kanban-header { font-family:'Syne',sans-serif; font-weight:700; font-size:12px; text-transform:uppercase; letter-spacing:.07em; padding:.4rem .8rem; border-radius:8px; margin-bottom:.85rem; display:block; text-align:center; }
.col-aberto    { background:#FFF3EC; color:#C04010; }
.col-andamento { background:#FFF8E6; color:#7A5010; }
.col-travado   { background:#FFECEC; color:#990000; }
.col-concluido { background:#EDFCF9; color:#0A7A6A; }
.col-cancelado { background:#F3F3F3; color:#555555; }
.kanban-wrap   { background:#FBF5F0; border-radius:14px; border:1px solid #EAD8D0; padding:1rem; min-height:160px; }
.kanban-metric { font-size:11px; color:#7A5060; text-align:center; margin-top:.5rem; padding:.3rem; background:white; border-radius:6px; border:1px solid #EAD8D0; }

/* Alertas dashboard */
.alert-card { border-radius:10px; padding:.75rem 1rem; margin-bottom:.5rem; font-size:13px; }
.alert-red    { background:#FFF0F3; border:1px solid #FFCDD5; color:#8B1530; }
.alert-yellow { background:#FFFBEC; border:1px solid #FFE69C; color:#664D03; }
.alert-green  { background:#EDFCF9; border:1px solid #A8EFE5; color:#0A5040; }
</style>
"""

# ── 3. PATHS DE PERSISTÊNCIA ──────────────────────────────────────────────────
DB            = "database"
USERS_FILE    = "users.json"
GER_FILE      = f"{DB}/geradores.json"
USI_FILE      = f"{DB}/usinas.json"
TASKS_FILE    = f"{DB}/tasks.json"
GERACAO_FILE  = f"{DB}/geracao_usinas.json"
BACKOFFICE_FILE = f"{DB}/backoffice.json"
RATEIO_FILE   = f"{DB}/historico_rateios.json"

os.makedirs(DB, exist_ok=True)

def _load(path, default):
    if not os.path.exists(path):
        _save(path, default)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── 4. USUÁRIOS ───────────────────────────────────────────────────────────────
def load_users():
    if not os.path.exists(USERS_FILE):
        _save(USERS_FILE, {"users":[
            {"name":"Milena",   "email":"milena@sunne.com.br",   "password":"sunne2026","role":"admin"},
            {"name":"Analista", "email":"analista@sunne.com.br", "password":"sunne2026","role":"user"},
        ]})
    with open(USERS_FILE) as f: return json.load(f).get("users",[])

def authenticate(email, password):
    for u in load_users():
        if u["email"].lower()==email.lower() and u["password"]==password: return u
    return None

# ── 5. CRUD GENÉRICO ──────────────────────────────────────────────────────────
def load_geradores():      return _load(GER_FILE, [])
def save_geradores(d):     _save(GER_FILE, d)
def load_usinas():         return _load(USI_FILE, [])
def save_usinas(d):        _save(USI_FILE, d)
def load_tasks():          return _load(TASKS_FILE, [])
def save_tasks(d):         _save(TASKS_FILE, d)
def load_geracao():        return _load(GERACAO_FILE, [])
def save_geracao(d):       _save(GERACAO_FILE, d)
def load_backoffice():     return _load(BACKOFFICE_FILE, [])
def save_backoffice(d):    _save(BACKOFFICE_FILE, d)
def load_rateios():        return _load(RATEIO_FILE, {})
def save_rateios(d):       _save(RATEIO_FILE, d)

# ── 6. TASKS HELPERS ──────────────────────────────────────────────────────────
TIPOS_TAREFA = ["Avulsa","Análise de Faturamento","Rateio","Captura","Relatório","Auditoria"]
STATUS_LIST  = ["Em aberto","Em andamento","Travado","Concluido","Cancelado"]
MOTIVO_OBRIG = {"Travado","Cancelado"}
STATUS_CSS   = {"Em aberto":"col-aberto","Em andamento":"col-andamento",
                "Travado":"col-travado","Concluido":"col-concluido","Cancelado":"col-cancelado"}

def new_task(titulo, usina, gerador, analista, tipo="Avulsa",
             agendamento="", descricao="", anexo_nome="", anexo_b64=""):
    tasks = load_tasks()
    tasks.append({
        "id":            datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "titulo":        titulo,
        "usina":         usina,
        "gerador":       gerador,
        "analista":      analista,
        "tipo":          tipo,
        "agendamento":   agendamento,
        "descricao":     descricao,
        "anexo_nome":    anexo_nome,
        "anexo_b64":     anexo_b64,
        "status":        "Em aberto",
        "motivo_bloqueio":"",
        "criado_em":     datetime.now().strftime("%d/%m/%Y %H:%M"),
        "historico":     [],
    })
    save_tasks(tasks)

def update_task(tid, **kwargs):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == tid:
            if "status" in kwargs and kwargs["status"] != t["status"]:
                t.setdefault("historico",[]).append({
                    "de": t["status"], "para": kwargs["status"],
                    "em": datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
            t.update(kwargs)
    save_tasks(tasks)

def sla_days(t):
    try:
        return (datetime.now() - datetime.strptime(t["criado_em"], "%d/%m/%Y %H:%M")).days
    except: return 0

def sla_class(d):
    if d <= 3: return "k-sla-ok"
    if d <= 7: return "k-sla-med"
    return "k-sla-bad"

# ── 7. UTILITÁRIOS DE DADOS (ORIGINAIS INTOCADOS) ────────────────────────────
def normalize_uc(val):
    if not val: return ""
    s = str(val).strip().split('.')[0]
    return "".join(filter(str.isdigit, s))

def clean_val(v):
    if not v: return 0.0
    s = str(v).replace("R$","").replace(" ","").strip()
    if "," in s and "." in s: s = s.replace(".","").replace(",",".")
    elif "," in s: s = s.replace(",",".")
    try: return float(s)
    except: return 0.0

def csv_from_list(rows, cols, headers):
    out = io.StringIO()
    df = pd.DataFrame(rows)
    if not df.empty:
        ex = df[[c for c in cols if c in df.columns]]
        ex.columns = headers[:len(ex.columns)]
        ex.to_csv(out, index=False, sep=';', encoding='utf-8-sig')
    return out.getvalue().encode('utf-8-sig')

def style_critical(row):
    if row['Dias de Atraso'] > 90:
        return ['background-color:#ffcccc;color:#990000;font-weight:bold']*len(row)
    return ['background-color:#fff4cc;color:#856404;font-weight:bold']*len(row)

def df_to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Rateio')
    return buf.getvalue()

# ── 8. ANÁLISE DE FATURAMENTO (ORIGINAL INTOCADA) ────────────────────────────
def load_planilha(file):
    if file is None: return None
    try:
        df = (pd.read_excel(file, header=None)
              if not file.name.endswith('.csv')
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
        comp      = str(row[comp_col])              if comp_col    else "Geral"
        status    = str(row[status_col]).lower()    if status_col  else ""
        valor     = clean_val(row[valor_col])
        venc      = row[venc_col]                   if venc_col    else None

        t_gerado[comp] = t_gerado.get(comp,0.0) + valor
        if "pago" in status: t_pago[comp] = t_pago.get(comp,0.0) + valor
        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp,0.0) + valor
            item = {"uc":row[uc_e_col],"valor":valor,"titular":row[titular_col] if titular_col else "—"}
            inad_res.setdefault(comp,[]).append(item)
            if pd.notnull(venc):
                dias = (hoje-venc).days
                if dias > 60:
                    critical_inad.append({"Titular":item["titular"],"UC":item["uc"],
                        "Vencimento":venc.strftime('%d/%m/%Y'),"Dias de Atraso":dias,
                        "Valor":valor,"Mês Ref":comp})

    critical_inad = sorted(critical_inad, key=lambda x: x['Dias de Atraso'], reverse=True)
    extrato_set = set(zip(df_e["UC_NORM"], df_e[comp_col].astype(str)))
    ucs_rateio  = df_r["UC_NORM"].unique()
    for comp in df_e[comp_col].unique():
        if not comp or str(comp).lower()=='nan': continue
        for uc in ucs_rateio:
            if (uc,str(comp)) not in extrato_set:
                r = df_r[df_r["UC_NORM"]==uc].iloc[0]
                missing_res.setdefault(comp,[]).append({
                    "uc":r[uc_r_col],"apelido":r.get("Apelido UC","—"),"usina":r.get("Usina","—")})

    return {"missing":missing_res,"inad":inad_res,"t_gerado":t_gerado,
            "t_pago":t_pago,"t_vencido":t_vencido,"critical_inad":critical_inad}

# ══════════════════════════════════════════════════════════════════════════════
# DIALOGS (st.dialog)
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("📝 Criar Nova Atividade")
def dialog_criar_atividade(uc_usina="", ger_usina=""):
    analista = st.session_state["user"]["name"]
    with st.form("dlg_nova_ativ", clear_on_submit=True):
        c1, c2 = st.columns(2)
        usina_v   = c1.text_input("Usina",   value=uc_usina,  disabled=bool(uc_usina))
        gerador_v = c2.text_input("Gerador", value=ger_usina, disabled=bool(ger_usina))
        titulo    = st.text_input("Título da Tarefa *")
        d1, d2    = st.columns(2)
        tipo      = d1.selectbox("Tipo", TIPOS_TAREFA)
        agend     = d2.text_input("Agendamento (Data/Hora)", placeholder="ex: 20/05/2026 09:00")
        descricao = st.text_area("Descrição", height=80)
        anexo_f   = st.file_uploader("Anexo (PDF/Excel — opcional)", type=["pdf","xlsx","xls"])
        ok = st.form_submit_button("✅ Criar Tarefa", use_container_width=True)

    if ok:
        if not titulo.strip():
            st.warning("O título é obrigatório.")
        else:
            anexo_nome, anexo_b64 = "", ""
            if anexo_f:
                anexo_nome = anexo_f.name
                anexo_b64  = base64.b64encode(anexo_f.read()).decode()
            new_task(titulo.strip(), usina_v, gerador_v, analista,
                     tipo, agend, descricao, anexo_nome, anexo_b64)
            st.success("✅ Tarefa criada! Acesse a aba **Atividades**.")
            st.rerun()


@st.dialog("📋 Detalhes da Tarefa")
def dialog_task_detail(tid):
    tasks = load_tasks()
    t = next((x for x in tasks if x["id"]==tid), None)
    if not t:
        st.error("Tarefa não encontrada."); return

    st.markdown(f"### {t['titulo']}")
    i1,i2,i3 = st.columns(3)
    i1.markdown(f"**Usina:** {t.get('usina','—')}")
    i2.markdown(f"**Gerador:** {t.get('gerador','—')}")
    i3.markdown(f"**Tipo:** {t.get('tipo','—')}")
    j1,j2 = st.columns(2)
    j1.markdown(f"**Analista:** {t.get('analista','—')}")
    j2.markdown(f"**Criado em:** {t.get('criado_em','—')}")
    if t.get('agendamento'):
        st.markdown(f"**Agendamento:** {t['agendamento']}")
    if t.get('descricao'):
        st.markdown(f"**Descrição:** {t['descricao']}")
    if t.get('motivo_bloqueio'):
        st.markdown(f"**🔒 Motivo:** {t['motivo_bloqueio']}")

    # Histórico de movimentações
    hist = t.get("historico",[])
    if hist:
        with st.expander("📜 Histórico de movimentações"):
            for h in hist:
                st.write(f"• {h['em']} — `{h['de']}` → `{h['para']}`")

    # Anexo download
    if t.get("anexo_nome") and t.get("anexo_b64"):
        raw = base64.b64decode(t["anexo_b64"])
        st.download_button(f"📎 Baixar {t['anexo_nome']}", raw, t["anexo_nome"])

    st.divider()
    st.markdown("**Mover tarefa para:**")

    opcoes = [s for s in STATUS_LIST if s != t["status"]]
    dest   = st.selectbox("Novo status", opcoes, label_visibility="collapsed")
    motivo_txt = ""
    if dest in MOTIVO_OBRIG:
        motivo_txt = st.text_area("Motivo obrigatório *")

    if st.button("↗ Confirmar movimentação", use_container_width=True):
        if dest in MOTIVO_OBRIG and not motivo_txt.strip():
            st.warning("O motivo é obrigatório para este status.")
        else:
            update_task(tid, status=dest, motivo_bloqueio=motivo_txt.strip())
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINAS
# ══════════════════════════════════════════════════════════════════════════════

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def page_dashboard():
    user     = st.session_state["user"]
    analista = user["name"]
    st.title("📊 Dashboard")

    gers    = [g for g in load_geradores() if g.get("analista","").lower()==analista.lower()]
    usis    = [u for u in load_usinas()    if u.get("analista","").lower()==analista.lower()]
    tasks   = load_tasks()
    geracao = load_geracao()

    ab  = [t for t in tasks if t["status"]=="Em aberto"]
    and_= [t for t in tasks if t["status"]=="Em andamento"]
    trav= [t for t in tasks if t["status"]=="Travado"]
    conc= [t for t in tasks if t["status"]=="Concluido"]

    # SLA médio por analista
    sla_tasks = [t for t in tasks if t["status"] not in ("Concluido","Cancelado")]
    sla_medio = round(sum(sla_days(t) for t in sla_tasks)/len(sla_tasks),1) if sla_tasks else 0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for col,lbl,val in zip([c1,c2,c3,c4,c5,c6],
        ["Geradores","Usinas","Em Aberto","Em Andamento","Travadas","SLA Médio (dias)"],
        [len(gers),len(usis),len(ab),len(and_),len(trav),sla_medio]):
        col.markdown(f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
                     f'<div style="font-size:12px;color:#7A5060">{lbl}</div></div>',
                     unsafe_allow_html=True)

    # ── Alertas inteligentes
    st.write("")
    st.subheader("🚨 Alertas Operacionais")

    mes_atual = datetime.now().strftime("%m/%Y")
    ucs_com_geracao_mes = {g["uc"] for g in geracao if g.get("competencia","") == mes_atual}
    usi_ids = {u["uc"] for u in usis}

    alertas = []

    # 1. Usinas sem geração no mês atual
    sem_geracao = usi_ids - ucs_com_geracao_mes
    for uc in sem_geracao:
        u = next((x for x in usis if x["uc"]==uc), {})
        alertas.append(("red", f"⚡ Usina <b>{u.get('ufv',uc)}</b> sem geração registrada em {mes_atual}."))

    # 2. Excesso de saldo (>6 meses acumulados) — só se geração registrada
    bo = load_backoffice()
    for uc in ucs_com_geracao_mes:
        rec = next((x for x in bo if str(x.get("uc",""))==str(uc)), None)
        if rec:
            consumo = clean_val(rec.get("consumo_total",0))
            saldo   = clean_val(rec.get("saldo_credito",0))
            if consumo > 0 and saldo / consumo > 6:
                u = next((x for x in usis if str(x["uc"])==str(uc)), {})
                alertas.append(("yellow", f"💰 Usina <b>{u.get('ufv',uc)}</b>: saldo acumulado > 6 meses ({saldo/consumo:.1f}x consumo)."))

    # 3. Consumo > Geração por meses consecutivos
    for uc in usi_ids & ucs_com_geracao_mes:
        historico_uc = sorted([g for g in geracao if str(g.get("uc",""))==str(uc)],
                               key=lambda x: x.get("competencia",""))[-3:]
        bo_rec = next((x for x in bo if str(x.get("uc",""))==str(uc)), None)
        if bo_rec and len(historico_uc)>=1:
            consumo_bo = clean_val(bo_rec.get("consumo_total",0))
            injecao    = clean_val(historico_uc[-1].get("energia_injetada",0))
            if consumo_bo > injecao:
                u = next((x for x in usis if str(x["uc"])==str(uc)), {})
                alertas.append(("yellow", f"📉 Usina <b>{u.get('ufv',uc)}</b>: consumo > geração. Avaliar rebalanceamento."))

    if not alertas:
        st.markdown('<div class="alert-card alert-green">✅ Nenhum alerta no momento.</div>', unsafe_allow_html=True)
    else:
        for kind, msg in alertas:
            st.markdown(f'<div class="alert-card alert-{kind}">{msg}</div>', unsafe_allow_html=True)

    st.write("")
    st.subheader("🕐 Tarefas Pendentes")
    pendentes = ab + and_
    if pendentes:
        df_p = pd.DataFrame(pendentes)[["titulo","usina","gerador","analista","status","criado_em"]]
        df_p.columns = ["Título","Usina","Gerador","Analista","Status","Criado em"]
        st.dataframe(df_p, use_container_width=True, hide_index=True)
    else:
        st.success("Nenhuma tarefa pendente.")


# ─── FATURAMENTO (ORIGINAL INTOCADO) ─────────────────────────────────────────
def page_faturamento():
    st.title("💳 Gestão de Faturamento")
    t1,t2,t3 = st.tabs(["📂 Importar","🔍 Captura","💳 Inadimplência"])
    with t1:
        c1,c2 = st.columns(2)
        f_r = c1.file_uploader("Rateio")
        f_e = c2.file_uploader("Extrato")
        if f_r and f_e and st.button("🔄 Rodar Análise"):
            st.session_state["results"] = analyze_performance(load_planilha(f_r), load_planilha(f_e))
            st.success("✓ Concluído!")
    res = st.session_state.get("results")
    if res:
        with t2:
            for comp,items in res["missing"].items():
                with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                    st.download_button(f"⬇️ Baixar Lista ({comp})",
                        csv_from_list(items,["uc","apelido","usina"],["UC","Apelido","Usina"]),
                        f"faltantes_{comp.replace('/','-')}.csv","text/csv")
                    st.table(pd.DataFrame(items))
        with t3:
            for comp,rows in res["inad"].items():
                ger = res["t_gerado"].get(comp,0.0)
                ven = res["t_vencido"].get(comp,0.0)
                taxa = (ven/ger*100) if ger>0 else 0
                st.markdown(f"### {comp}")
                c1,c2,c3 = st.columns(3)
                c1.metric("Gerado",f"R$ {ger:,.2f}")
                c2.metric("Vencido",f"R$ {ven:,.2f}")
                c3.metric("Inadimplência",f"{taxa:.1f}%")
                with st.expander(f"Ver clientes inadimplentes ({comp})"):
                    st.table(pd.DataFrame(rows))
            st.write("---")
            st.markdown("## 🚨 Inadimplência Crítica (>60 dias)")
            st.info("Clientes com status 'vencido' há mais de 60 dias. Avaliar retirada do rateio.")
            if res["critical_inad"]:
                st.dataframe(pd.DataFrame(res["critical_inad"]).style.apply(style_critical,axis=1),
                             use_container_width=True,hide_index=True)
            else:
                st.success("Nenhum cliente com inadimplência superior a 60 dias.")


# ─── GERADORES ────────────────────────────────────────────────────────────────
def page_geradores():
    user     = st.session_state["user"]
    analista = user["name"]
    st.title("⚡ Geradores")
    tc,ti = st.tabs(["📋 Minha Carteira","📥 Importar Planilha"])

    with tc:
        minha = [g for g in load_geradores() if g.get("analista","").lower()==analista.lower()]
        if not minha:
            st.info("Nenhum gerador cadastrado. Use a aba 'Importar Planilha'.")
        else:
            conc = {g.get("concessionaria","") for g in minha if g.get("concessionaria")}
            total_u = sum(int(g.get("usinas",0) or 0) for g in minha)
            c1,c2,c3 = st.columns(3)
            for col,lbl,val in zip([c1,c2,c3],["Geradores","Concessionárias","Usinas Totais"],
                                   [len(minha),len(conc),total_u]):
                col.markdown(f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
                             f'<div style="font-size:12px;color:#7A5060">{lbl}</div></div>',unsafe_allow_html=True)
            st.write("")
            opcoes = ["Todas"]+sorted(conc)
            filtro = st.selectbox("Filtrar por Concessionária",opcoes)
            lista  = minha if filtro=="Todas" else [g for g in minha if g.get("concessionaria")==filtro]
            df_s = pd.DataFrame(lista)
            cols = [c for c in ["gerador","contato","concessionaria","usinas","porte","origem"] if c in df_s.columns]
            df_s = df_s[cols]; df_s.columns = [c.capitalize() for c in cols]
            st.dataframe(df_s,use_container_width=True,hide_index=True)

    with ti:
        st.markdown("**Colunas esperadas:** Gerador · Contato · Analista · Concessionária · Usinas · Porte · Origem")
        f = st.file_uploader("Arquivo",type=["xlsx","xls","csv"],key="up_ger")
        if f and st.button("💾 Salvar Geradores",key="btn_sg"):
            try:
                df = pd.read_excel(f,dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f,dtype=str)
                df.columns = df.columns.str.strip().str.lower()
                df.rename(columns={"concessionária":"concessionaria"},inplace=True)
                df = df.fillna("")
                existentes = load_geradores()
                nomes_ex   = {g["gerador"].lower() for g in existentes}
                novos = 0
                for _,row in df.iterrows():
                    nome = str(row.get("gerador","")).strip()
                    if nome and nome.lower() not in nomes_ex:
                        existentes.append({k:str(row.get(k,"")) for k in
                            ["gerador","contato","analista","concessionaria","usinas","porte","origem"]})
                        nomes_ex.add(nome.lower()); novos+=1
                save_geradores(existentes)
                st.success(f"✅ {novos} gerador(es) importado(s)!")
                st.rerun()
            except Exception as ex: st.error(f"Erro: {ex}")


# ─── USINAS ───────────────────────────────────────────────────────────────────
def page_usinas():
    user     = st.session_state["user"]
    analista = user["name"]
    st.title("🏭 Usinas")

    ca,cb,_ = st.columns([1.4,1.8,6])
    if ca.button("➕ Adicionar Manual"):
        st.session_state["show_add_usina"] = not st.session_state.get("show_add_usina",False)
    if cb.button("📥 Importar Planilha"):
        st.session_state["show_imp_usina"] = not st.session_state.get("show_imp_usina",False)

    if st.session_state.get("show_add_usina"):
        with st.form("form_add_usi",clear_on_submit=True):
            st.subheader("Nova Usina")
            a1,a2 = st.columns(2); b1,b2 = st.columns(2)
            uc      = a1.text_input("UC *"); gerador = a2.text_input("Gerador")
            ufv     = b1.text_input("Nome UFV"); ativa = b2.selectbox("Ativa?",["Sim","Não"])
            s,c     = st.columns(2)
            salvar  = s.form_submit_button("✅ Salvar")
            canc    = c.form_submit_button("Cancelar")
        if salvar:
            if not uc.strip(): st.warning("UC obrigatória.")
            else:
                us = load_usinas()
                us.append({"uc":str(uc).strip(),"gerador":gerador.strip(),"ufv":ufv.strip(),
                            "analista":analista,"ativa":ativa,"criado_em":datetime.now().strftime("%d/%m/%Y")})
                save_usinas(us); st.session_state["show_add_usina"]=False
                st.success("✅ Usina adicionada!"); st.rerun()
        if canc: st.session_state["show_add_usina"]=False; st.rerun()

    if st.session_state.get("show_imp_usina"):
        st.markdown("**Colunas esperadas:** UC · Gerador · UFV · Analista · Ativa")
        f = st.file_uploader("Arquivo de Usinas",type=["xlsx","xls","csv"],key="up_usi")
        i1,i2 = st.columns([1,5])
        if i1.button("Importar",key="btn_iusi"):
            if f:
                try:
                    df = pd.read_excel(f,dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f,dtype=str)
                    df.columns = df.columns.str.strip().str.lower(); df=df.fillna("")
                    us = load_usinas(); uc_ex = {u["uc"] for u in us}; novos=0
                    for _,row in df.iterrows():
                        uv = str(row.get("uc","")).strip()
                        if uv and uv not in uc_ex:
                            us.append({"uc":uv,"gerador":str(row.get("gerador","")),
                                       "ufv":str(row.get("ufv","")),"analista":analista,
                                       "ativa":str(row.get("ativa","Sim")),
                                       "criado_em":datetime.now().strftime("%d/%m/%Y")})
                            uc_ex.add(uv); novos+=1
                    save_usinas(us); st.session_state["show_imp_usina"]=False
                    st.success(f"✅ {novos} usina(s) importada(s)!"); st.rerun()
                except Exception as ex: st.error(f"Erro: {ex}")
        if i2.button("Fechar",key="btn_fusi"): st.session_state["show_imp_usina"]=False; st.rerun()

    st.write("---")
    usinas = load_usinas()
    minhas = [u for u in usinas if u.get("analista","").lower()==analista.lower()]
    if not minhas: st.info("Nenhuma usina cadastrada."); return

    ger_opts = ["Todos"]+sorted({u.get("gerador","—") for u in minhas})
    filtro   = st.selectbox("Filtrar por Gerador",ger_opts)
    lista    = minhas if filtro=="Todos" else [u for u in minhas if u.get("gerador")==filtro]

    h = st.columns([1.4,1.8,2.2,1.6,0.8,0.5])
    for col,txt in zip(h,["UC","Gerador","UFV","Analista","Ativa","📝"]):
        col.markdown(f"**{txt}**")
    st.markdown("<hr style='margin:4px 0 6px'>",unsafe_allow_html=True)

    for idx,u in enumerate(lista):
        r = st.columns([1.4,1.8,2.2,1.6,0.8,0.5])
        r[0].write(str(u.get("uc","—")))
        r[1].write(u.get("gerador","—"))
        r[2].write(u.get("ufv","—"))
        r[3].write(u.get("analista","—"))
        r[4].write("✅" if u.get("ativa","Sim")=="Sim" else "❌")
        if r[5].button("📝",key=f"btn_ativ_{idx}_{u['uc']}"):
            dialog_criar_atividade(str(u.get("uc","")), u.get("gerador",""))


# ─── ATIVIDADES (KANBAN) ──────────────────────────────────────────────────────
def page_atividades():
    st.title("📋 Atividades")

    if st.button("➕ Nova Tarefa Avulsa"):
        dialog_criar_atividade()

    fc1,fc2 = st.columns(2)
    f_an = fc1.text_input("Filtrar Analista",placeholder="em branco = todos")
    f_ge = fc2.text_input("Filtrar Gerador", placeholder="em branco = todos")

    def match(t):
        if f_an and f_an.lower() not in t.get("analista","").lower(): return False
        if f_ge and f_ge.lower() not in t.get("gerador","").lower():  return False
        return True

    tasks = [t for t in load_tasks() if match(t)]
    st.write("---")
    cols = st.columns(5)

    for col_ui,status in zip(cols,STATUS_LIST):
        css = STATUS_CSS[status]
        grupo = [t for t in tasks if t["status"]==status]
        with col_ui:
            st.markdown(f'<span class="kanban-header {css}">{status} ({len(grupo)})</span>',
                        unsafe_allow_html=True)
            st.markdown('<div class="kanban-wrap">',unsafe_allow_html=True)

            if not grupo:
                st.markdown('<p style="font-size:12px;color:#bbb;text-align:center;padding:.75rem 0">Vazio</p>',
                            unsafe_allow_html=True)
            else:
                # Média de SLA da coluna
                media_sla = round(sum(sla_days(t) for t in grupo)/len(grupo),1)

            for t in grupo:
                tid   = t["id"]
                dias  = sla_days(t)
                s_cls = sla_class(dias)
                motivo_html = (f'<div class="k-motivo">🔒 {t["motivo_bloqueio"]}</div>'
                               if t.get("motivo_bloqueio") else "")
                st.markdown(f"""
                <div class="kanban-card">
                    <div class="k-title">{t['titulo']}</div>
                    <div class="k-meta">🏭 {t.get('usina','—')}<br>⚡ {t.get('gerador','—')}<br>
                    👤 {t.get('analista','—')}<br>📅 {t.get('criado_em','')}</div>
                    <div class="{s_cls}">⏱ SLA: {dias}d</div>
                    {motivo_html}
                </div>""", unsafe_allow_html=True)

                if st.button("🔍 Abrir",key=f"open_{tid}"):
                    dialog_task_detail(tid)

            if grupo:
                st.markdown(f'<div class="kanban-metric">⏱ Média SLA: {media_sla}d</div>',
                            unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)


# ─── GERAÇÃO DAS USINAS ───────────────────────────────────────────────────────
def page_geracao():
    st.title("⚡ Geração das Usinas")
    tm,ti = st.tabs(["✏️ Lançamento Manual","📥 Importar Excel"])

    with tm:
        with st.form("form_geracao",clear_on_submit=True):
            g1,g2,g3,g4 = st.columns(4)
            uc_g    = g1.text_input("UC da Usina *")
            nome_g  = g2.text_input("Nome Usina")
            comp_g  = g3.text_input("Competência (MM/AAAA)",placeholder="05/2026")
            inj_g   = g4.number_input("Energia Injetada (kWh)",min_value=0.0,step=0.1)
            saldo_g = st.number_input("Saldo (kWh)",min_value=0.0,step=0.1)
            ok_g    = st.form_submit_button("✅ Salvar",use_container_width=True)
        if ok_g:
            if not uc_g.strip(): st.warning("UC obrigatória.")
            else:
                ger = load_geracao()
                ger.append({"uc":str(uc_g).strip(),"nome_usina":nome_g,"competencia":comp_g,
                             "energia_injetada":inj_g,"saldo":saldo_g,
                             "registrado_em":datetime.now().strftime("%d/%m/%Y %H:%M")})
                save_geracao(ger); st.success("✅ Geração registrada!")

    with ti:
        st.markdown("**Colunas esperadas:** Nome da Usina · Número da UG · Competência · Energia Injetada · Saldo")
        f = st.file_uploader("Arquivo",type=["xlsx","xls","csv"],key="up_ger2")
        if f and st.button("Importar",key="btn_iger"):
            try:
                df = pd.read_excel(f,dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f,dtype=str)
                df.columns = df.columns.str.strip().str.lower(); df=df.fillna("")
                rename = {"nome da usina":"nome_usina","número da ug":"uc","numero da ug":"uc",
                          "energia injetada":"energia_injetada"}
                df.rename(columns=rename,inplace=True)
                ger = load_geracao(); novos=0
                for _,row in df.iterrows():
                    ger.append({"uc":str(row.get("uc","")).strip(),
                                "nome_usina":str(row.get("nome_usina","")),
                                "competencia":str(row.get("competência",row.get("competencia",""))),
                                "energia_injetada":clean_val(row.get("energia_injetada",0)),
                                "saldo":clean_val(row.get("saldo",0)),
                                "registrado_em":datetime.now().strftime("%d/%m/%Y %H:%M")})
                    novos+=1
                save_geracao(ger); st.success(f"✅ {novos} registro(s) importado(s)!")
            except Exception as ex: st.error(f"Erro: {ex}")

    st.write("---")
    st.subheader("📋 Registros de Geração")
    ger = load_geracao()
    if ger:
        df_g = pd.DataFrame(ger)
        cols_show = [c for c in ["uc","nome_usina","competencia","energia_injetada","saldo","registrado_em"]
                     if c in df_g.columns]
        st.dataframe(df_g[cols_show],use_container_width=True,hide_index=True)
    else:
        st.info("Nenhum registro de geração ainda.")


# ─── BACKOFFICE ───────────────────────────────────────────────────────────────
def page_backoffice():
    st.title("🗂️ Backoffice — Captura de Consumo")
    st.markdown("Faça upload do **Extrato Detalhado** para capturar: UC, Consumo Total, Saldo de Crédito e Tipo de Instalação.")

    f = st.file_uploader("Extrato Detalhado",type=["xlsx","xls","csv"],key="up_bo")
    if f and st.button("📥 Processar Extrato",key="btn_bo"):
        try:
            df = (pd.read_excel(f,header=None) if not f.name.endswith(".csv")
                  else pd.read_csv(f,header=None,sep=None,engine='python'))
            for i,row in df.head(20).iterrows():
                row_l = [str(c).strip().lower() for c in row]
                if any("número da uc" in s for s in row_l):
                    df.columns=[str(c).strip() for c in row]; df=df.iloc[i+1:].reset_index(drop=True); break
            df.columns=[str(c).strip() for c in df.columns]; df=df.fillna("")

            uc_col   = next((c for c in df.columns if "Número da UC"  in c),None)
            cons_col = next((c for c in df.columns if "Consumo"       in c),None)
            sald_col = next((c for c in df.columns if "Saldo"         in c),None)
            tipo_col = next((c for c in df.columns if "Tipo"          in c or "Instalação" in c),None)

            if not uc_col: st.error("Coluna 'Número da UC' não encontrada."); return

            bo = load_backoffice()
            uc_ex = {str(b["uc"]) for b in bo}
            novos=0
            for _,row in df.iterrows():
                uc_val = str(row[uc_col]).strip()
                if not uc_val: continue
                rec = {"uc":uc_val,
                       "consumo_total":clean_val(row[cons_col]) if cons_col else 0,
                       "saldo_credito":clean_val(row[sald_col]) if sald_col else 0,
                       "tipo_instalacao":str(row[tipo_col]) if tipo_col else "—",
                       "atualizado_em":datetime.now().strftime("%d/%m/%Y %H:%M")}
                # Upsert: atualiza se já existir
                idx_ex = next((i for i,b in enumerate(bo) if str(b["uc"])==uc_val),None)
                if idx_ex is not None: bo[idx_ex]=rec
                else: bo.append(rec); novos+=1
            save_backoffice(bo)
            st.success(f"✅ Extrato processado. {novos} novo(s) registro(s), demais atualizados.")
        except Exception as ex: st.error(f"Erro: {ex}")

    st.write("---")
    bo = load_backoffice()
    if bo:
        st.subheader("📋 Base de Consumo Capturada")
        st.dataframe(pd.DataFrame(bo),use_container_width=True,hide_index=True)
    else:
        st.info("Nenhum dado de backoffice ainda. Importe um extrato.")


# ─── RATEIO ───────────────────────────────────────────────────────────────────
def page_rateio():
    st.title("⚖️ Rateio")
    ta,tb,tc,td = st.tabs(["🔄 Rebalancear","📤 Atualizar Vigente","📋 Consultar","🔍 Buscar Beneficiário"])

    # ══ A. REBALANCEAMENTO ══
    with ta:
        st.subheader("🔄 Rebalanceamento de Rateio")

        geradores = load_geradores()
        nomes_ger = sorted({g["gerador"] for g in geradores})
        if not nomes_ger: st.info("Cadastre geradores antes."); return

        sel_ger = st.selectbox("Gerador",nomes_ger,key="rb_ger")
        usinas  = [u for u in load_usinas() if u.get("gerador","")==sel_ger]
        nomes_usi = [u.get("ufv",u["uc"]) for u in usinas]
        if not nomes_usi: st.warning("Nenhuma usina vinculada a este gerador."); st.stop()

        sel_usi_nome = st.selectbox("Usina",nomes_usi,key="rb_usi")
        sel_usi = usinas[nomes_usi.index(sel_usi_nome)]
        uc_usina = sel_usi["uc"]

        # Geração da usina para validação
        ger_mes = load_geracao()
        mes_atual = datetime.now().strftime("%m/%Y")
        rec_ger = next((g for g in ger_mes if str(g.get("uc",""))==str(uc_usina)
                        and g.get("competencia","")==mes_atual),None)

        if not rec_ger:
            st.warning(f"⚠️ Geração de **{sel_usi_nome}** para {mes_atual} ainda não registrada. "
                       "Registre em **Geração das Usinas** antes de rebalancear.")
            st.stop()

        geracao_kwh = clean_val(rec_ger.get("energia_injetada",0))
        st.info(f"✅ Geração registrada para {mes_atual}: **{geracao_kwh:,.1f} kWh**")

        autonomia = st.number_input("Meses de autonomia desejada",min_value=1,max_value=12,value=3,key="rb_aut")

        ra1,ra2 = st.columns(2)
        f_rat = ra1.file_uploader("Rateio Vigente (UC, Apelido, % Atual, CNPJ)",
                                   type=["xlsx","xls","csv"],key="up_rat")
        f_ext = ra2.file_uploader("Extrato Detalhado (UC, Consumo, Saldo, Tipo)",
                                   type=["xlsx","xls","csv"],key="up_ext_rat")

        # UCs saindo
        st.markdown("**UCs Saindo (opcional):**")
        n_saindo = st.number_input("Qtd UCs saindo",min_value=0,max_value=20,value=0,key="rb_ns",step=1)
        ucs_saindo = []
        for i in range(int(n_saindo)):
            sc1,sc2 = st.columns(2)
            uc_s  = sc1.text_input(f"UC saindo #{i+1}",key=f"uc_s_{i}")
            mot_s = sc2.text_input(f"Motivo #{i+1}",key=f"mot_s_{i}")
            if uc_s: ucs_saindo.append({"uc":str(uc_s).strip(),"motivo":mot_s})

        # Novas UCs
        st.markdown("**Novas UCs (opcional):**")
        n_novas = st.number_input("Qtd novas UCs",min_value=0,max_value=20,value=0,key="rb_nn",step=1)
        ucs_novas = []
        for i in range(int(n_novas)):
            nc1,nc2,nc3 = st.columns(3)
            uc_n  = nc1.text_input(f"Nova UC #{i+1}",key=f"uc_n_{i}")
            ap_n  = nc2.text_input(f"Apelido #{i+1}",key=f"ap_n_{i}")
            cons_n= nc3.number_input(f"Consumo Médio kWh #{i+1}",min_value=0.0,step=1.0,key=f"cn_{i}")
            if uc_n: ucs_novas.append({"uc":str(uc_n).strip(),"apelido":ap_n,"consumo":cons_n})

        # Âncora
        ancora = st.text_input("Unidade Âncora (UC) — opcional",key="rb_anc")

        if st.button("⚙️ Calcular Rebalanceamento",key="btn_rb"):
            if not f_rat or not f_ext:
                st.error("Faça upload dos dois arquivos."); st.stop()
            try:
                # Carregar rateio
                df_rat = (pd.read_excel(f_rat,dtype=str) if not f_rat.name.endswith(".csv")
                          else pd.read_csv(f_rat,dtype=str))
                df_rat.columns = df_rat.columns.str.strip()
                df_rat = df_rat.fillna("")

                # Carregar extrato
                df_ext2 = load_planilha(f_ext)
                if df_ext2 is None: st.error("Erro ao ler o extrato."); st.stop()

                # Colunas extrato
                uc_e_col  = next((c for c in df_ext2.columns if "Número da UC" in c), df_ext2.columns[0])
                cons_col  = next((c for c in df_ext2.columns if "Consumo"      in c), None)
                sald_col  = next((c for c in df_ext2.columns if "Saldo"        in c), None)
                tipo_col  = next((c for c in df_ext2.columns if "Tipo"         in c or "Instalação" in c), None)

                df_ext2["UC_NORM"] = df_ext2[uc_e_col].apply(normalize_uc)

                # Coluna UC do rateio
                uc_r_col = next((c for c in df_rat.columns if "UC" in c), df_rat.columns[0])
                ap_col   = next((c for c in df_rat.columns if "Apelido" in c), None)
                cnpj_col = next((c for c in df_rat.columns if "CNPJ" in c), None)
                df_rat["UC_NORM"] = df_rat[uc_r_col].apply(normalize_uc)

                # Remover saindo
                saindo_norms = {normalize_uc(x["uc"]) for x in ucs_saindo}
                df_rat = df_rat[~df_rat["UC_NORM"].isin(saindo_norms)].copy()

                resultado = []

                for _,r_row in df_rat.iterrows():
                    uc_norm = r_row["UC_NORM"]
                    apelido = r_row[ap_col] if ap_col else "—"
                    cnpj    = r_row[cnpj_col] if cnpj_col else "—"

                    ext_row = df_ext2[df_ext2["UC_NORM"]==uc_norm]
                    if ext_row.empty:
                        consumo_total=0; saldo=0; tipo="Monofásico"
                    else:
                        ext_row = ext_row.iloc[0]
                        consumo_total = clean_val(ext_row[cons_col]) if cons_col else 0
                        saldo         = clean_val(ext_row[sald_col]) if sald_col else 0
                        tipo          = str(ext_row[tipo_col]).lower() if tipo_col else "monofasico"

                    # Consumo compensável
                    if "trif" in tipo:
                        consumo_comp = max(consumo_total - 100, 0)
                    else:
                        consumo_comp = max(consumo_total - 30, 0)

                    # Regra de autonomia
                    if consumo_total > 0 and (saldo / consumo_total) > autonomia:
                        necessidade = consumo_comp * 0.20
                    else:
                        necessidade = consumo_comp

                    resultado.append({
                        "UC_NORM": uc_norm,
                        "UC": r_row[uc_r_col],
                        "Apelido": apelido,
                        "CNPJ": cnpj,
                        "Consumo Comp. (kWh)": round(consumo_comp,2),
                        "Saldo (kWh)": round(saldo,2),
                        "Necessidade (kWh)": round(necessidade,2),
                    })

                # Adicionar novas UCs
                for nu in ucs_novas:
                    consumo_comp = max(nu["consumo"]-30, 0)
                    resultado.append({
                        "UC_NORM": normalize_uc(nu["uc"]),
                        "UC": nu["uc"],
                        "Apelido": nu.get("apelido","—"),
                        "CNPJ": "—",
                        "Consumo Comp. (kWh)": round(consumo_comp,2),
                        "Saldo (kWh)": 0,
                        "Necessidade (kWh)": round(consumo_comp,2),
                    })

                total_nec = sum(r["Necessidade (kWh)"] for r in resultado)

                # Calcular % ideal
                for r in resultado:
                    r["Rateio Verificado (%)"] = (
                        round((r["Necessidade (kWh)"] / geracao_kwh * 100), 4)
                        if geracao_kwh > 0 else 0
                    )

                soma = sum(r["Rateio Verificado (%)"] for r in resultado)

                # Fechamento 100%
                sobra = round(100.0 - soma, 4)
                if sobra != 0:
                    ancora_norm = normalize_uc(ancora) if ancora else None
                    idx_anc = next((i for i,r in enumerate(resultado)
                                    if r["UC_NORM"]==ancora_norm), None) if ancora_norm else None
                    if idx_anc is not None:
                        resultado[idx_anc]["Rateio Verificado (%)"] = round(
                            resultado[idx_anc]["Rateio Verificado (%)"] + sobra, 4)
                    else:
                        # Distribuir proporcionalmente
                        if total_nec > 0:
                            for r in resultado:
                                r["Rateio Verificado (%)"] = round(
                                    r["Rateio Verificado (%)"] + sobra*(r["Necessidade (kWh)"]/total_nec), 4)

                # Exibir
                df_res = pd.DataFrame(resultado)
                df_res.insert(0,"#",range(1,len(df_res)+1))
                cols_final = ["#","UC","Apelido","CNPJ","Consumo Comp. (kWh)","Saldo (kWh)","Rateio Verificado (%)"]
                df_show = df_res[[c for c in cols_final if c in df_res.columns]]

                soma_final = df_show["Rateio Verificado (%)"].sum()
                st.success(f"✅ Soma total: {soma_final:.4f}% | Geração usada: {geracao_kwh:,.1f} kWh")
                st.dataframe(df_show,use_container_width=True,hide_index=True)

                excel_bytes = df_to_excel_bytes(df_show)
                st.download_button("⬇️ Exportar Excel",excel_bytes,
                    f"rateio_rebalanceado_{sel_ger}_{sel_usi_nome}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            except Exception as ex:
                st.error(f"Erro no cálculo: {ex}")
                import traceback; st.code(traceback.format_exc())

    # ══ B. ATUALIZAR VIGENTE ══
    with tb:
        st.subheader("📤 Atualizar Rateio Vigente")
        nomes_ger2 = sorted({g["gerador"] for g in load_geradores()})
        if not nomes_ger2: st.info("Cadastre geradores antes."); return
        sel_ger2 = st.selectbox("Gerador",nomes_ger2,key="upd_ger")
        usinas2  = [u for u in load_usinas() if u.get("gerador","")==sel_ger2]
        nomes2   = [u.get("ufv",u["uc"]) for u in usinas2]
        if not nomes2: st.warning("Nenhuma usina vinculada."); st.stop()
        sel_u2 = st.selectbox("Usina",nomes2,key="upd_usi")
        uc_u2  = usinas2[nomes2.index(sel_u2)]["uc"]

        f_upd = st.file_uploader("Planilha do novo rateio (modelo Sunne)",type=["xlsx","xls","csv"],key="up_upd")
        if f_upd and st.button("💾 Salvar como Vigente",key="btn_upd"):
            try:
                df_upd = (pd.read_excel(f_upd,dtype=str) if not f_upd.name.endswith(".csv")
                          else pd.read_csv(f_upd,dtype=str))
                df_upd.columns = df_upd.columns.str.strip(); df_upd=df_upd.fillna("")
                hist  = load_rateios()
                chave = f"{sel_ger2}||{uc_u2}"
                hist.setdefault(chave,[])
                hist[chave].append({
                    "versao":   len(hist[chave])+1,
                    "salvo_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "dados":    df_upd.to_dict(orient="records"),
                })
                save_rateios(hist)
                st.success(f"✅ Rateio v{len(hist[chave])} salvo para {sel_u2}!")
            except Exception as ex: st.error(f"Erro: {ex}")

    # ══ C. CONSULTAR ══
    with tc:
        st.subheader("📋 Consultar Rateio Vigente e Histórico")
        hist = load_rateios()
        if not hist: st.info("Nenhum rateio salvo ainda."); return

        chaves     = list(hist.keys())
        sel_chave  = st.selectbox("Gerador || Usina",chaves,key="cons_c")
        versoes    = hist[sel_chave]
        if not versoes: st.info("Sem versões salvas."); return

        opts = [f"v{v['versao']} — {v['salvo_em']}" for v in versoes]
        sel_v = st.selectbox("Versão",opts,key="cons_v")
        idx_v = opts.index(sel_v)
        df_v  = pd.DataFrame(versoes[idx_v]["dados"])
        st.markdown(f"**{'✅ Vigente (mais recente)' if idx_v==len(versoes)-1 else '📁 Histórico'}** · {versoes[idx_v]['salvo_em']}")
        st.dataframe(df_v,use_container_width=True,hide_index=True)

    # ══ D. BUSCAR BENEFICIÁRIO ══
    with td:
        st.subheader("🔍 Buscar Beneficiário por UC")
        uc_busca = st.text_input("Número da UC do cliente",placeholder="Digite a UC...")
        if st.button("🔍 Buscar",key="btn_busca") and uc_busca:
            uc_norm_b = normalize_uc(uc_busca)
            hist = load_rateios(); encontrado=False
            for chave,versoes in hist.items():
                if not versoes: continue
                vigente = versoes[-1]["dados"]
                for row in vigente:
                    # Procurar em qualquer coluna UC
                    for k,v in row.items():
                        if "uc" in k.lower() and normalize_uc(str(v))==uc_norm_b:
                            gen,usi = chave.split("||")
                            bo = load_backoffice()
                            bo_rec = next((b for b in bo if normalize_uc(str(b.get("uc","")))==uc_norm_b),None)
                            st.success(f"✅ UC **{uc_busca}** encontrada!")
                            r1,r2,r3 = st.columns(3)
                            r1.metric("Gerador",gen); r2.metric("Usina",usi)
                            # Buscar % rateio
                            pct_col = next((k2 for k2 in row if "%" in k2 or "rateio" in k2.lower()),"—")
                            r3.metric("Rateio",row.get(pct_col,"—"))
                            if bo_rec:
                                b1,b2 = st.columns(2)
                                b1.metric("Consumo Total",f"{bo_rec.get('consumo_total',0):,.1f} kWh")
                                b2.metric("Saldo de Crédito",f"{bo_rec.get('saldo_credito',0):,.1f} kWh")
                            encontrado=True; break
                    if encontrado: break
                if encontrado: break
            if not encontrado:
                st.warning(f"UC **{uc_busca}** não encontrada em nenhum rateio ativo. "
                           "O cliente pode ter saído do rateio ou a UC não foi cadastrada.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.markdown('<div class="login-card">',unsafe_allow_html=True)
        try: st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png",width=120)
        except: st.markdown("### ☀️ Sunne")
        with st.form("login"):
            e = st.text_input("E-mail",value="milena@sunne.com.br")
            s = st.text_input("Senha",type="password")
            if st.form_submit_button("Acessar Hub",use_container_width=True):
                u = authenticate(e,s)
                if u:
                    st.session_state["user"]=u
                    st.session_state.setdefault("page","dash")
                    st.rerun()
                else: st.error("E-mail ou senha incorretos.")
        st.markdown('</div>',unsafe_allow_html=True)
        return

    with st.sidebar:
        try: st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png",width=120)
        except: st.markdown("### ☀️ Sunne")
        st.write(f"Olá, {st.session_state['user']['name']} 👋")
        st.write("---")
        st.session_state.setdefault("page","dash")
        nav = [("dash","Dashboard"),("geradores","Geradores"),("usinas","Usinas"),
               ("atividades","Atividades"),("geracao","Geração"),("backoffice","Backoffice"),
               ("rateio","Rateio"),("faturamento","Faturamento")]
        for key,label in nav:
            if st.button(label,key=f"nav_{key}"):
                st.session_state["page"]=key
        st.write("---")
        if st.button("Sair",key="nav_sair"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    page = st.session_state.get("page","dash")
    pages = {"dash":page_dashboard,"geradores":page_geradores,"usinas":page_usinas,
             "atividades":page_atividades,"geracao":page_geracao,"backoffice":page_backoffice,
             "rateio":page_rateio,"faturamento":page_faturamento}
    pages.get(page, page_dashboard)()


if __name__ == "__main__":
    main()
