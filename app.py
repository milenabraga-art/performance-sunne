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

# ── 2. CSS ───────────────────────────────────────────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root { --rubi:#33001A; --laranja:#F36E21; --bg:#FDF8F5; }

[data-testid="stAppViewContainer"] { background-color:var(--bg); }
html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
#MainMenu,footer,header { visibility:hidden; }

[data-testid="stSidebar"] { background-color:var(--rubi)!important; border-right:1px solid rgba(255,255,255,.1); }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color:transparent!important; border:none!important; color:white!important;
    padding:0!important; margin-bottom:20px!important; width:100%!important;
    display:flex!important; justify-content:flex-start!important; box-shadow:none!important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
    color:white!important; font-size:16px!important; font-weight:500!important; transition:.3s;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p {
    color:var(--laranja)!important; font-weight:700!important;
}
.stButton>button { background-color:var(--laranja)!important; color:white!important; border-radius:8px!important; border:none!important; }

.kpi-box { background:white; border-radius:15px; padding:1.2rem; border:1px solid #EAD8D0; text-align:center; }
.kpi-value { font-family:'Syne',sans-serif; font-size:20px; font-weight:700; color:var(--rubi); }
.login-card { background:white; padding:3rem; border-radius:25px; box-shadow:0 15px 35px rgba(51,0,26,.1); border:1px solid #EAD8D0; max-width:400px; margin:auto; text-align:center; }

/* Kanban */
.kanban-card {
    background:white; border:1.5px solid #EAD8D0; border-radius:12px;
    padding:.9rem 1rem; margin-bottom:.65rem; font-size:13px;
    box-shadow:0 1px 4px rgba(51,0,26,.06); cursor:pointer;
    transition: box-shadow .15s, border-color .15s;
}
.kanban-card:hover { box-shadow:0 4px 12px rgba(51,0,26,.12); border-color:var(--laranja); }
.k-title { font-family:'Syne',sans-serif; font-weight:700; font-size:13px; color:var(--rubi); margin-bottom:4px; }
.k-meta  { font-size:11px; color:#7A5060; line-height:1.7; }
.k-sla-ok  { font-size:11px; color:#0A7A6A; font-weight:600; }
.k-sla-med { font-size:11px; color:#856404; font-weight:600; }
.k-sla-bad { font-size:11px; color:#CC1A3A; font-weight:600; }
.k-motivo  { font-size:11px; color:#990000; margin-top:4px; font-style:italic; }
.kanban-header {
    font-family:'Syne',sans-serif; font-weight:700; font-size:12px; text-transform:uppercase;
    letter-spacing:.07em; padding:.4rem .8rem; border-radius:8px; margin-bottom:.85rem;
    display:block; text-align:center;
}
.col-aberto    { background:#FFF3EC; color:#C04010; }
.col-andamento { background:#FFF8E6; color:#7A5010; }
.col-travado   { background:#FFECEC; color:#990000; }
.col-concluido { background:#EDFCF9; color:#0A7A6A; }
.col-cancelado { background:#F3F3F3; color:#555555; }
.kanban-wrap   { background:#FBF5F0; border-radius:14px; border:1px solid #EAD8D0; padding:1rem; min-height:180px; }
.kanban-metric { font-size:11px; color:#7A5060; text-align:center; margin-top:.5rem; padding:.3rem; background:white; border-radius:6px; border:1px solid #EAD8D0; }

/* Rateio table */
.rt-table { width:100%; border-collapse:collapse; font-size:12px; }
.rt-table th { background:var(--rubi); color:white; padding:.45rem .6rem; text-align:center; font-family:'Syne',sans-serif; font-size:11px; }
.rt-table td { padding:.4rem .6rem; border-bottom:1px solid #EAD8D0; text-align:center; }
.rt-table tr:last-child td { background:#FFF3EC; font-weight:700; border-top:2px solid var(--rubi); }
.rt-table tr:hover td { background:#FBF5F0; }

/* Alertas */
.alert-card { border-radius:10px; padding:.75rem 1rem; margin-bottom:.5rem; font-size:13px; }
.alert-red    { background:#FFF0F3; border:1px solid #FFCDD5; color:#8B1530; }
.alert-yellow { background:#FFFBEC; border:1px solid #FFE69C; color:#664D03; }
.alert-green  { background:#EDFCF9; border:1px solid #A8EFE5; color:#0A5040; }

/* Drag hint */
.drag-hint { font-size:11px; color:#B08090; text-align:center; margin-bottom:.5rem; font-style:italic; }
</style>
"""

# ── 3. PATHS ─────────────────────────────────────────────────────────────────
DB             = "database"
USERS_FILE     = "users.json"
GER_FILE       = f"{DB}/geradores.json"
USI_FILE       = f"{DB}/usinas.json"
TASKS_FILE     = f"{DB}/tasks.json"
GERACAO_FILE   = f"{DB}/geracao_usinas.json"
BACKOFFICE_FILE= f"{DB}/backoffice.json"
RATEIO_FILE    = f"{DB}/historico_rateios.json"

os.makedirs(DB, exist_ok=True)

def _load(path, default):
    if not os.path.exists(path): _save(path, default)
    with open(path, encoding="utf-8") as f: return json.load(f)

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── 4. USUÁRIOS ───────────────────────────────────────────────────────────────
def load_users():
    if not os.path.exists(USERS_FILE):
        _save(USERS_FILE, {"users":[
            {"name":"Milena","email":"milena@sunne.com.br","password":"sunne2026","role":"admin"},
            {"name":"Analista","email":"analista@sunne.com.br","password":"sunne2026","role":"user"},
        ]})
    with open(USERS_FILE) as f: return json.load(f).get("users",[])

def authenticate(email, password):
    for u in load_users():
        if u["email"].lower()==email.lower() and u["password"]==password: return u
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
TIPOS_TAREFA = ["Avulsa","Análise de Faturamento","Rateio","Captura","Relatório","Auditoria"]
STATUS_LIST  = ["Em aberto","Em andamento","Travado","Concluido","Cancelado"]
MOTIVO_OBRIG = {"Travado","Cancelado"}
STATUS_CSS   = {"Em aberto":"col-aberto","Em andamento":"col-andamento",
                "Travado":"col-travado","Concluido":"col-concluido","Cancelado":"col-cancelado"}

def new_task(titulo, usina, gerador, analista, tipo="Avulsa",
             agendamento="", descricao="", anexo_nome="", anexo_b64=""):
    tasks = load_tasks()
    tasks.append({
        "id":             datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "titulo":         titulo, "usina":usina, "gerador":gerador,
        "analista":       analista, "tipo":tipo, "agendamento":agendamento,
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
        if t["id"]==tid:
            if "status" in kwargs and kwargs["status"]!=t["status"]:
                t.setdefault("historico",[]).append({
                    "de":t["status"],"para":kwargs["status"],
                    "em":datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
            t.update(kwargs)
    save_tasks(tasks)

def sla_days(t):
    try: return (datetime.now()-datetime.strptime(t["criado_em"],"%d/%m/%Y %H:%M")).days
    except: return 0

def sla_class(d):
    if d<=3: return "k-sla-ok"
    if d<=7: return "k-sla-med"
    return "k-sla-bad"

# ── 7. UTILS ──────────────────────────────────────────────────────────────────
def normalize_uc(val):
    if not val: return ""
    return "".join(filter(str.isdigit, str(val).strip().split('.')[0]))

def clean_val(v):
    if not v: return 0.0
    s = str(v).replace("R$","").replace(" ","").strip()
    if "," in s and "." in s: s=s.replace(".","").replace(",",".")
    elif "," in s: s=s.replace(",",".")
    try: return float(s)
    except: return 0.0

def csv_from_list(rows, cols, headers):
    out=io.StringIO(); df=pd.DataFrame(rows)
    if not df.empty:
        ex=df[[c for c in cols if c in df.columns]]
        ex.columns=headers[:len(ex.columns)]
        ex.to_csv(out,index=False,sep=';',encoding='utf-8-sig')
    return out.getvalue().encode('utf-8-sig')

def style_critical(row):
    if row['Dias de Atraso']>90: return ['background-color:#ffcccc;color:#990000;font-weight:bold']*len(row)
    return ['background-color:#fff4cc;color:#856404;font-weight:bold']*len(row)

def df_to_excel_bytes(df):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine='openpyxl') as w: df.to_excel(w,index=False,sheet_name='Rateio')
    return buf.getvalue()

# ── 8. LOAD PLANILHA (ORIGINAL) ───────────────────────────────────────────────
def load_planilha(file):
    if file is None: return None
    try:
        df=(pd.read_excel(file,header=None) if not file.name.endswith('.csv')
            else pd.read_csv(file,header=None,sep=None,engine='python'))
        for i,row in df.head(20).iterrows():
            row_l=[str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s for s in row_l):
                df.columns=[str(c).strip() for c in row]; df=df.iloc[i+1:].reset_index(drop=True); break
        df.columns=[str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

# ── 9. ANALYZE PERFORMANCE (ORIGINAL INTOCADA) ───────────────────────────────
def analyze_performance(df_r, df_e):
    uc_r_col    = next((c for c in df_r.columns if "UC Nova"       in c), df_r.columns[0])
    uc_e_col    = next((c for c in df_e.columns if "Número da UC"  in c), df_e.columns[0])
    comp_col    = next((c for c in df_e.columns if "Competência"   in c), None)
    status_col  = next((c for c in df_e.columns if "Status"        in c), None)
    valor_col   = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular"       in c), None)
    venc_col    = next((c for c in df_e.columns if "Vencimento"    in c), None)

    df_r["UC_NORM"]=df_r[uc_r_col].apply(normalize_uc)
    df_e["UC_NORM"]=df_e[uc_e_col].apply(normalize_uc)

    missing_res={}; inad_res={}; t_gerado={}; t_pago={}; t_vencido={}; critical_inad=[]
    hoje=datetime.now()
    if venc_col: df_e[venc_col]=pd.to_datetime(df_e[venc_col],errors='coerce',dayfirst=True)

    for _,row in df_e.iterrows():
        comp     =str(row[comp_col])          if comp_col   else "Geral"
        status   =str(row[status_col]).lower()if status_col else ""
        valor    =clean_val(row[valor_col])
        venc     =row[venc_col]               if venc_col   else None
        t_gerado[comp]=t_gerado.get(comp,0.0)+valor
        if "pago" in status: t_pago[comp]=t_pago.get(comp,0.0)+valor
        if "vencido" in status:
            t_vencido[comp]=t_vencido.get(comp,0.0)+valor
            item={"uc":row[uc_e_col],"valor":valor,"titular":row[titular_col] if titular_col else "—"}
            inad_res.setdefault(comp,[]).append(item)
            if pd.notnull(venc):
                dias=(hoje-venc).days
                if dias>60: critical_inad.append({"Titular":item["titular"],"UC":item["uc"],
                    "Vencimento":venc.strftime('%d/%m/%Y'),"Dias de Atraso":dias,"Valor":valor,"Mês Ref":comp})

    critical_inad=sorted(critical_inad,key=lambda x:x['Dias de Atraso'],reverse=True)
    extrato_set=set(zip(df_e["UC_NORM"],df_e[comp_col].astype(str)))
    ucs_rateio=df_r["UC_NORM"].unique()
    for comp in df_e[comp_col].unique():
        if not comp or str(comp).lower()=='nan': continue
        for uc in ucs_rateio:
            if (uc,str(comp)) not in extrato_set:
                r=df_r[df_r["UC_NORM"]==uc].iloc[0]
                missing_res.setdefault(comp,[]).append({
                    "uc":r[uc_r_col],"apelido":r.get("Apelido UC","—"),"usina":r.get("Usina","—")})
    return {"missing":missing_res,"inad":inad_res,"t_gerado":t_gerado,
            "t_pago":t_pago,"t_vencido":t_vencido,"critical_inad":critical_inad}

# ══════════════════════════════════════════════════════════════════════════════
# DIALOGS
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("📝 Criar Nova Atividade")
def dialog_criar_atividade(uc_usina="", ger_usina=""):
    analista=st.session_state["user"]["name"]
    with st.form("dlg_nova_ativ", clear_on_submit=True):
        c1,c2=st.columns(2)
        usina_v  =c1.text_input("Usina",  value=uc_usina,  disabled=bool(uc_usina))
        gerador_v=c2.text_input("Gerador",value=ger_usina, disabled=bool(ger_usina))
        titulo=st.text_input("Título da Tarefa *")
        d1,d2=st.columns(2)
        tipo =d1.selectbox("Tipo",TIPOS_TAREFA)
        agend=d2.text_input("Agendamento (Data/Hora)",placeholder="20/05/2026 09:00")
        descricao=st.text_area("Descrição / Observações iniciais",height=100,
                               placeholder="Descreva a atividade, cole links do HubSpot, tickets, etc.")
        anexo_f=st.file_uploader("Anexo (PDF/Excel — opcional)",type=["pdf","xlsx","xls"])
        ok=st.form_submit_button("✅ Criar Tarefa",use_container_width=True)
    if ok:
        if not titulo.strip(): st.warning("O título é obrigatório.")
        else:
            anexo_nome,anexo_b64="",""
            if anexo_f:
                anexo_nome=anexo_f.name
                anexo_b64=base64.b64encode(anexo_f.read()).decode()
            new_task(titulo.strip(),usina_v,gerador_v,analista,tipo,agend,descricao,anexo_nome,anexo_b64)
            st.success("✅ Tarefa criada! Acesse a aba **Atividades**.")
            st.rerun()


@st.dialog("📋 Detalhes da Tarefa", width="large")
def dialog_task_detail(tid):
    tasks=load_tasks()
    t=next((x for x in tasks if x["id"]==tid),None)
    if not t: st.error("Tarefa não encontrada."); return

    st.markdown(f"## {t['titulo']}")
    i1,i2,i3=st.columns(3)
    i1.markdown(f"**Usina:** {t.get('usina','—')}")
    i2.markdown(f"**Gerador:** {t.get('gerador','—')}")
    i3.markdown(f"**Tipo:** {t.get('tipo','—')}")
    j1,j2=st.columns(2)
    j1.markdown(f"**Analista:** {t.get('analista','—')}")
    j2.markdown(f"**Criado em:** {t.get('criado_em','—')}")
    if t.get('agendamento'):
        st.markdown(f"**⏰ Agendamento:** {t['agendamento']}")
    if t.get('motivo_bloqueio'):
        st.markdown(f"**🔒 Motivo bloqueio:** {t['motivo_bloqueio']}")

    st.divider()

    # ── Campo de observações (editável, múltiplas entradas)
    st.markdown("**📝 Observações / Log de Atividade**")
    st.caption("Cole links do HubSpot, tickets, notas de atendimento, histórico de ações:")
    obs_atual=t.get("observacoes","")
    nova_obs=st.text_area("Adicionar observação",height=120,
                          placeholder="Ex: Falou com cliente em 14/05, aguardando retorno. Ticket HubSpot: https://...")
    if st.button("💾 Salvar Observação",key=f"salv_obs_{tid}"):
        if nova_obs.strip():
            timestamp=datetime.now().strftime("%d/%m/%Y %H:%M")
            analista_obs=st.session_state["user"]["name"]
            nova_linha=f"\n[{timestamp} — {analista_obs}]\n{nova_obs.strip()}"
            update_task(tid, observacoes=obs_atual+nova_linha)
            st.success("Observação salva!"); st.rerun()

    if obs_atual:
        with st.expander("📜 Ver todas as observações anteriores"):
            st.text(obs_atual)

    st.divider()

    # ── Histórico de movimentações
    hist=t.get("historico",[])
    if hist:
        with st.expander("🔄 Histórico de movimentações"):
            for h in hist: st.write(f"• {h['em']} — `{h['de']}` → `{h['para']}`")

    # ── Anexo
    if t.get("anexo_nome") and t.get("anexo_b64"):
        raw=base64.b64decode(t["anexo_b64"])
        st.download_button(f"📎 Baixar {t['anexo_nome']}",raw,t["anexo_nome"])

    st.divider()
    st.markdown("**↗ Mover tarefa para:**")
    opcoes=[s for s in STATUS_LIST if s!=t["status"]]
    dest=st.selectbox("Novo status",opcoes,label_visibility="collapsed")
    motivo_txt=""
    if dest in MOTIVO_OBRIG:
        motivo_txt=st.text_area("Motivo obrigatório *")
    if st.button("↗ Confirmar movimentação",use_container_width=True):
        if dest in MOTIVO_OBRIG and not motivo_txt.strip():
            st.warning("O motivo é obrigatório.")
        else:
            update_task(tid,status=dest,motivo_bloqueio=motivo_txt.strip())
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINAS
# ══════════════════════════════════════════════════════════════════════════════

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def page_dashboard():
    user=st.session_state["user"]; analista=user["name"]
    st.title("📊 Dashboard")

    gers   =[g for g in load_geradores() if g.get("analista","").lower()==analista.lower()]
    usis   =[u for u in load_usinas()    if u.get("analista","").lower()==analista.lower()]
    tasks  =load_tasks()
    geracao=load_geracao()

    ab  =[t for t in tasks if t["status"]=="Em aberto"]
    and_=[t for t in tasks if t["status"]=="Em andamento"]
    trav=[t for t in tasks if t["status"]=="Travado"]
    sla_tasks=[t for t in tasks if t["status"] not in ("Concluido","Cancelado")]
    sla_medio=round(sum(sla_days(t) for t in sla_tasks)/len(sla_tasks),1) if sla_tasks else 0

    c1,c2,c3,c4,c5,c6=st.columns(6)
    for col,lbl,val in zip([c1,c2,c3,c4,c5,c6],
        ["Geradores","Usinas","Em Aberto","Em Andamento","Travadas","SLA Médio (d)"],
        [len(gers),len(usis),len(ab),len(and_),len(trav),sla_medio]):
        col.markdown(f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
                     f'<div style="font-size:12px;color:#7A5060">{lbl}</div></div>',unsafe_allow_html=True)

    st.write("")
    st.subheader("🚨 Alertas Operacionais")
    mes_atual=datetime.now().strftime("%m/%Y")
    ucs_com_geracao={g["uc"] for g in geracao if g.get("competencia","")==mes_atual}
    usi_ids={u["uc"] for u in usis}
    bo=load_backoffice()
    alertas=[]

    for uc in usi_ids-ucs_com_geracao:
        u=next((x for x in usis if x["uc"]==uc),{})
        alertas.append(("red",f"⚡ Usina <b>{u.get('ufv',uc)}</b> sem geração registrada em {mes_atual}."))

    for uc in ucs_com_geracao:
        rec=next((x for x in bo if str(x.get("uc",""))==str(uc)),None)
        if rec:
            cons=clean_val(rec.get("consumo_total",0)); saldo=clean_val(rec.get("saldo_credito",0))
            if cons>0 and saldo/cons>6:
                u=next((x for x in usis if str(x["uc"])==str(uc)),{})
                alertas.append(("yellow",f"💰 Usina <b>{u.get('ufv',uc)}</b>: saldo > 6 meses ({saldo/cons:.1f}x consumo)."))
            inj_rec=next((g for g in geracao if str(g.get("uc",""))==str(uc) and g.get("competencia","")==mes_atual),None)
            if inj_rec and cons>clean_val(inj_rec.get("energia_injetada",0)):
                u=next((x for x in usis if str(x["uc"])==str(uc)),{})
                alertas.append(("yellow",f"📉 Usina <b>{u.get('ufv',uc)}</b>: consumo > geração. Avaliar rebalanceamento."))

    if not alertas:
        st.markdown('<div class="alert-card alert-green">✅ Nenhum alerta no momento.</div>',unsafe_allow_html=True)
    else:
        for kind,msg in alertas:
            st.markdown(f'<div class="alert-card alert-{kind}">{msg}</div>',unsafe_allow_html=True)

    st.write(""); st.subheader("🕐 Tarefas Pendentes")
    pendentes=ab+and_
    if pendentes:
        df_p=pd.DataFrame(pendentes)[["titulo","usina","gerador","analista","status","criado_em"]]
        df_p.columns=["Título","Usina","Gerador","Analista","Status","Criado em"]
        st.dataframe(df_p,use_container_width=True,hide_index=True)
    else: st.success("Nenhuma tarefa pendente.")


# ─── FATURAMENTO (ORIGINAL INTOCADO) ─────────────────────────────────────────
def page_faturamento():
    st.title("💳 Gestão de Faturamento")
    t1,t2,t3=st.tabs(["📂 Importar","🔍 Captura","💳 Inadimplência"])
    with t1:
        c1,c2=st.columns(2)
        f_r=c1.file_uploader("Rateio"); f_e=c2.file_uploader("Extrato")
        if f_r and f_e and st.button("🔄 Rodar Análise"):
            st.session_state["results"]=analyze_performance(load_planilha(f_r),load_planilha(f_e))
            st.success("✓ Concluído!")
    res=st.session_state.get("results")
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
                ger=res["t_gerado"].get(comp,0.0); ven=res["t_vencido"].get(comp,0.0)
                taxa=(ven/ger*100) if ger>0 else 0
                st.markdown(f"### {comp}")
                c1,c2,c3=st.columns(3)
                c1.metric("Gerado",f"R$ {ger:,.2f}"); c2.metric("Vencido",f"R$ {ven:,.2f}")
                c3.metric("Inadimplência",f"{taxa:.1f}%")
                with st.expander(f"Ver clientes ({comp})"): st.table(pd.DataFrame(rows))
            st.write("---"); st.markdown("## 🚨 Inadimplência Crítica (>60 dias)")
            st.info("Clientes com status 'vencido' há mais de 60 dias.")
            if res["critical_inad"]:
                st.dataframe(pd.DataFrame(res["critical_inad"]).style.apply(style_critical,axis=1),
                             use_container_width=True,hide_index=True)
            else: st.success("Nenhum cliente com inadimplência superior a 60 dias.")


# ─── GERADORES ────────────────────────────────────────────────────────────────
def page_geradores():
    user=st.session_state["user"]; analista=user["name"]
    st.title("⚡ Geradores")
    tc,ti=st.tabs(["📋 Minha Carteira","📥 Importar Planilha"])
    with tc:
        minha=[g for g in load_geradores() if g.get("analista","").lower()==analista.lower()]
        if not minha: st.info("Nenhum gerador cadastrado. Use 'Importar Planilha'.")
        else:
            conc={g.get("concessionaria","") for g in minha if g.get("concessionaria")}
            total_u=sum(int(g.get("usinas",0) or 0) for g in minha)
            c1,c2,c3=st.columns(3)
            for col,lbl,val in zip([c1,c2,c3],["Geradores","Concessionárias","Usinas Totais"],
                                   [len(minha),len(conc),total_u]):
                col.markdown(f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
                             f'<div style="font-size:12px;color:#7A5060">{lbl}</div></div>',unsafe_allow_html=True)
            st.write("")
            filtro=st.selectbox("Filtrar por Concessionária",["Todas"]+sorted(conc))
            lista=minha if filtro=="Todas" else [g for g in minha if g.get("concessionaria")==filtro]
            df_s=pd.DataFrame(lista)
            cols=[c for c in ["gerador","contato","concessionaria","usinas","porte","origem"] if c in df_s.columns]
            df_s=df_s[cols]; df_s.columns=[c.capitalize() for c in cols]
            st.dataframe(df_s,use_container_width=True,hide_index=True)
    with ti:
        st.markdown("**Colunas esperadas:** Gerador · Contato · Analista · Concessionária · Usinas · Porte · Origem")
        f=st.file_uploader("Arquivo",type=["xlsx","xls","csv"],key="up_ger")
        if f and st.button("💾 Salvar Geradores",key="btn_sg"):
            try:
                df=pd.read_excel(f,dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f,dtype=str)
                df.columns=df.columns.str.strip().str.lower()
                df.rename(columns={"concessionária":"concessionaria"},inplace=True); df=df.fillna("")
                existentes=load_geradores(); nomes_ex={g["gerador"].lower() for g in existentes}; novos=0
                for _,row in df.iterrows():
                    nome=str(row.get("gerador","")).strip()
                    if nome and nome.lower() not in nomes_ex:
                        existentes.append({k:str(row.get(k,"")) for k in
                            ["gerador","contato","analista","concessionaria","usinas","porte","origem"]})
                        nomes_ex.add(nome.lower()); novos+=1
                save_geradores(existentes); st.success(f"✅ {novos} gerador(es) importado(s)!"); st.rerun()
            except Exception as ex: st.error(f"Erro: {ex}")


# ─── USINAS ───────────────────────────────────────────────────────────────────
def page_usinas():
    user=st.session_state["user"]; analista=user["name"]
    st.title("🏭 Usinas")

    # Colunas modelo: UC | Gerador | UFV | Analista | Ativa | Geração
    ca,cb,_=st.columns([1.4,1.8,6])
    if ca.button("➕ Adicionar Manual"):
        st.session_state["show_add_usina"]=not st.session_state.get("show_add_usina",False)
    if cb.button("📥 Importar Planilha"):
        st.session_state["show_imp_usina"]=not st.session_state.get("show_imp_usina",False)

    if st.session_state.get("show_add_usina"):
        with st.form("form_add_usi",clear_on_submit=True):
            st.subheader("Nova Usina")
            a1,a2=st.columns(2); b1,b2,b3=st.columns(3)
            uc     =a1.text_input("UC *"); gerador=a2.text_input("Gerador")
            ufv    =b1.text_input("Nome UFV")
            ativa  =b2.selectbox("Ativa?",["Sim","Não"])
            geracao=b3.number_input("Geração estimada (kWh)",min_value=0.0,step=1.0)
            s,c=st.columns(2)
            salvar=s.form_submit_button("✅ Salvar"); canc=c.form_submit_button("Cancelar")
        if salvar:
            if not uc.strip(): st.warning("UC obrigatória.")
            else:
                us=load_usinas()
                us.append({"uc":str(uc).strip(),"gerador":gerador.strip(),"ufv":ufv.strip(),
                            "analista":analista,"ativa":ativa,
                            "geracao_estimada":geracao,"criado_em":datetime.now().strftime("%d/%m/%Y")})
                save_usinas(us); st.session_state["show_add_usina"]=False
                st.success("✅ Usina adicionada!"); st.rerun()
        if canc: st.session_state["show_add_usina"]=False; st.rerun()

    if st.session_state.get("show_imp_usina"):
        st.markdown("**Colunas esperadas:** UC · Gerador · UFV · Analista · Ativa · Geração")
        f=st.file_uploader("Arquivo de Usinas",type=["xlsx","xls","csv"],key="up_usi")
        i1,i2=st.columns([1,5])
        if i1.button("Importar",key="btn_iusi"):
            if f:
                try:
                    df=pd.read_excel(f,dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f,dtype=str)
                    df.columns=df.columns.str.strip().str.lower(); df=df.fillna("")
                    # Normaliza coluna "gerador" — aceita "gerador" ou qualquer variação
                    rename_map={}
                    for col in df.columns:
                        cl=col.lower()
                        if "gerador" in cl and col!="gerador": rename_map[col]="gerador"
                        if "ufv" in cl and col!="ufv": rename_map[col]="ufv"
                        if cl in ("geração","geracao","geração (kwh)"): rename_map[col]="geracao_estimada"
                    df.rename(columns=rename_map,inplace=True)
                    us=load_usinas(); uc_ex={u["uc"] for u in us}; novos=0
                    for _,row in df.iterrows():
                        uv=str(row.get("uc","")).strip()
                        if uv and uv not in uc_ex:
                            # Garantir que usa coluna "gerador", não "contato"
                            gerador_val=str(row.get("gerador","")).strip()
                            us.append({"uc":uv,"gerador":gerador_val,
                                       "ufv":str(row.get("ufv","")),"analista":analista,
                                       "ativa":str(row.get("ativa","Sim")),
                                       "geracao_estimada":clean_val(row.get("geracao_estimada",0)),
                                       "criado_em":datetime.now().strftime("%d/%m/%Y")})
                            uc_ex.add(uv); novos+=1
                    save_usinas(us); st.session_state["show_imp_usina"]=False
                    st.success(f"✅ {novos} usina(s) importada(s)!"); st.rerun()
                except Exception as ex: st.error(f"Erro: {ex}")
        if i2.button("Fechar",key="btn_fusi"): st.session_state["show_imp_usina"]=False; st.rerun()

    st.write("---")
    usinas=load_usinas()
    minhas=[u for u in usinas if u.get("analista","").lower()==analista.lower()]
    if not minhas: st.info("Nenhuma usina cadastrada."); return

    ger_opts=["Todos"]+sorted({u.get("gerador","—") for u in minhas})
    filtro=st.selectbox("Filtrar por Gerador",ger_opts)
    lista=minhas if filtro=="Todos" else [u for u in minhas if u.get("gerador")==filtro]

    h=st.columns([1.4,1.8,2.5,1.4,0.7,0.5])
    for col,txt in zip(h,["UC","Gerador","UFV","Analista","Ativa","📝"]): col.markdown(f"**{txt}**")
    st.markdown("<hr style='margin:4px 0 6px'>",unsafe_allow_html=True)

    for idx,u in enumerate(lista):
        r=st.columns([1.4,1.8,2.5,1.4,0.7,0.5])
        r[0].write(str(u.get("uc","—"))); r[1].write(u.get("gerador","—"))
        r[2].write(u.get("ufv","—"));     r[3].write(u.get("analista","—"))
        r[4].write("✅" if u.get("ativa","Sim")=="Sim" else "❌")
        if r[5].button("📝",key=f"btn_ativ_{idx}_{u['uc']}"):
            dialog_criar_atividade(str(u.get("uc","")),u.get("gerador",""))


# ─── ATIVIDADES (KANBAN) ──────────────────────────────────────────────────────
def page_atividades():
    st.title("📋 Atividades")

    if st.button("➕ Nova Tarefa Avulsa"):
        dialog_criar_atividade()

    fc1,fc2=st.columns(2)
    f_an=fc1.text_input("Filtrar Analista",placeholder="em branco = todos")
    f_ge=fc2.text_input("Filtrar Gerador", placeholder="em branco = todos")

    def match(t):
        if f_an and f_an.lower() not in t.get("analista","").lower(): return False
        if f_ge and f_ge.lower() not in t.get("gerador","").lower():  return False
        return True

    tasks=[t for t in load_tasks() if match(t)]

    # Drag-and-drop hint
    st.markdown('<div class="drag-hint">💡 Clique em um card para abrir detalhes. Use o seletor abaixo do card para mover entre etapas.</div>',
                unsafe_allow_html=True)
    st.write("---")

    cols=st.columns(5)
    for col_ui,status in zip(cols,STATUS_LIST):
        css=STATUS_CSS[status]
        grupo=[t for t in tasks if t["status"]==status]
        with col_ui:
            st.markdown(f'<span class="kanban-header {css}">{status} ({len(grupo)})</span>',
                        unsafe_allow_html=True)
            st.markdown('<div class="kanban-wrap">',unsafe_allow_html=True)
            if not grupo:
                st.markdown('<p style="font-size:12px;color:#bbb;text-align:center;padding:.75rem 0">Vazio</p>',
                            unsafe_allow_html=True)
            for t in grupo:
                tid=t["id"]; dias=sla_days(t); s_cls=sla_class(dias)
                motivo_html=(f'<div class="k-motivo">🔒 {t["motivo_bloqueio"]}</div>'
                             if t.get("motivo_bloqueio") else "")
                obs_preview=""
                if t.get("observacoes"):
                    linhas=t["observacoes"].strip().split("\n")
                    n_obs=len([l for l in linhas if l.startswith("[")])
                    obs_preview=f'<div class="k-meta" style="color:#7A5060;font-style:italic;margin-top:3px">📝 {n_obs} obs.</div>'
                st.markdown(f"""
                <div class="kanban-card">
                    <div class="k-title">{t['titulo']}</div>
                    <div class="k-meta">
                        🏭 {t.get('usina','—')}<br>
                        ⚡ {t.get('gerador','—')}<br>
                        👤 {t.get('analista','—')}<br>
                        📅 {t.get('criado_em','')}
                    </div>
                    <div class="{s_cls}">⏱ SLA: {dias}d</div>
                    {obs_preview}{motivo_html}
                </div>""",unsafe_allow_html=True)

                # Botão abrir dialog
                if st.button("🔍 Abrir",key=f"open_{tid}"):
                    dialog_task_detail(tid)

                # Mover rápido (sem abrir dialog)
                opcoes=[s for s in STATUS_LIST if s!=status]
                dest=st.selectbox("Mover para",opcoes,key=f"dest_{tid}",label_visibility="collapsed")
                if st.button("↗",key=f"mv_{tid}",help="Mover para status selecionado"):
                    if dest in MOTIVO_OBRIG:
                        st.session_state[f"pede_motivo_{tid}"]=dest
                    else:
                        update_task(tid,status=dest,motivo_bloqueio=""); st.rerun()

                if st.session_state.get(f"pede_motivo_{tid}"):
                    dest_alvo=st.session_state[f"pede_motivo_{tid}"]
                    mot=st.text_area(f"Motivo para '{dest_alvo}' *",key=f"mot_{tid}")
                    mc1,mc2=st.columns(2)
                    if mc1.button("Confirmar",key=f"conf_{tid}"):
                        if mot.strip():
                            update_task(tid,status=dest_alvo,motivo_bloqueio=mot.strip())
                            del st.session_state[f"pede_motivo_{tid}"]; st.rerun()
                        else: st.warning("Motivo obrigatório.")
                    if mc2.button("Cancelar ação",key=f"cno_{tid}"):
                        del st.session_state[f"pede_motivo_{tid}"]; st.rerun()

            if grupo:
                media=round(sum(sla_days(t) for t in grupo)/len(grupo),1)
                st.markdown(f'<div class="kanban-metric">⏱ Média SLA: {media}d</div>',unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)


# ─── GERAÇÃO DAS USINAS ───────────────────────────────────────────────────────
def page_geracao():
    st.title("⚡ Geração das Usinas")
    tm,ti=st.tabs(["✏️ Lançamento Manual","📥 Importar Excel"])

    with tm:
        with st.form("form_geracao",clear_on_submit=True):
            g1,g2=st.columns(2)
            uc_g  =g1.text_input("UC da Usina *",placeholder="Digite a UC...")
            nome_g=g2.text_input("Nome Usina",placeholder="Preenchido automaticamente",
                                 disabled=False,key="nome_usi_geracao")
            g3,g4=st.columns(2)
            comp_g=g3.text_input("Competência (MM/AAAA)",
                                 value=datetime.now().strftime("%m/%Y"))
            inj_g =g4.number_input("Energia Injetada (kWh)",min_value=0.0,step=0.1)
            saldo_g=st.number_input("Saldo (kWh)",min_value=0.0,step=0.1)
            ok_g=st.form_submit_button("✅ Salvar",use_container_width=True)

        if ok_g:
            if not uc_g.strip(): st.warning("UC obrigatória.")
            else:
                # Buscar nome automaticamente
                usinas=load_usinas()
                uc_norm_g=normalize_uc(uc_g)
                usi_match=next((u for u in usinas if normalize_uc(u["uc"])==uc_norm_g),None)
                nome_auto=usi_match.get("ufv","") if usi_match else nome_g
                ger=load_geracao()
                ger.append({"uc":str(uc_g).strip(),"nome_usina":nome_auto,
                             "competencia":comp_g,"energia_injetada":inj_g,"saldo":saldo_g,
                             "registrado_em":datetime.now().strftime("%d/%m/%Y %H:%M")})
                save_geracao(ger); st.success(f"✅ Geração registrada para {nome_auto or uc_g}!")

        # Preenchimento automático ao digitar UC (fora do form)
        uc_lookup=st.text_input("🔍 Buscar nome da usina pela UC (prévia)",
                                placeholder="Digite a UC para ver o nome cadastrado",key="uc_lookup_ger")
        if uc_lookup.strip():
            usinas=load_usinas()
            match=next((u for u in usinas if normalize_uc(u["uc"])==normalize_uc(uc_lookup)),None)
            if match: st.success(f"✅ Usina encontrada: **{match.get('ufv','—')}** | Gerador: **{match.get('gerador','—')}**")
            else: st.warning("UC não encontrada no cadastro de Usinas.")

    with ti:
        st.markdown("**Colunas esperadas:** Nome da Usina · Número da UG · Competência · Energia Injetada · Saldo")
        f=st.file_uploader("Arquivo",type=["xlsx","xls","csv"],key="up_ger2")
        if f and st.button("Importar",key="btn_iger"):
            try:
                df=pd.read_excel(f,dtype=str) if not f.name.endswith(".csv") else pd.read_csv(f,dtype=str)
                df.columns=df.columns.str.strip().str.lower(); df=df.fillna("")
                df.rename(columns={"nome da usina":"nome_usina","número da ug":"uc","numero da ug":"uc",
                                   "energia injetada":"energia_injetada"},inplace=True)
                ger=load_geracao(); novos=0
                usinas=load_usinas()
                for _,row in df.iterrows():
                    uc_val=str(row.get("uc","")).strip()
                    usi_match=next((u for u in usinas if normalize_uc(u["uc"])==normalize_uc(uc_val)),None)
                    nome_auto=usi_match.get("ufv","") if usi_match else str(row.get("nome_usina",""))
                    ger.append({"uc":uc_val,"nome_usina":nome_auto,
                                "competencia":str(row.get("competência",row.get("competencia",""))),
                                "energia_injetada":clean_val(row.get("energia_injetada",0)),
                                "saldo":clean_val(row.get("saldo",0)),
                                "registrado_em":datetime.now().strftime("%d/%m/%Y %H:%M")}); novos+=1
                save_geracao(ger); st.success(f"✅ {novos} registro(s) importado(s)!")
            except Exception as ex: st.error(f"Erro: {ex}")

    st.write("---")
    st.subheader("📋 Registros de Geração")
    ger=load_geracao()
    if ger:
        df_g=pd.DataFrame(ger)
        cols_show=[c for c in ["uc","nome_usina","competencia","energia_injetada","saldo","registrado_em"] if c in df_g.columns]
        st.dataframe(df_g[cols_show],use_container_width=True,hide_index=True)
    else: st.info("Nenhum registro de geração ainda.")


# ─── BACKOFFICE ───────────────────────────────────────────────────────────────
def page_backoffice():
    st.title("🗂️ Backoffice — Captura de Consumo")

    # ── SELEÇÃO DE GERADOR (vínculo)
    geradores=load_geradores()
    nomes_ger=sorted({g["gerador"] for g in geradores}) if geradores else []
    if not nomes_ger:
        st.warning("Cadastre geradores antes de importar o backoffice.")
        return

    sel_ger_bo=st.selectbox("📌 Vincular extrato ao Gerador",nomes_ger,key="bo_gerador")
    st.caption("O extrato importado será associado a este gerador para cruzamento nos relatórios.")

    f=st.file_uploader("Extrato Detalhado",type=["xlsx","xls","csv"],key="up_bo")
    if f and st.button("📥 Processar Extrato",key="btn_bo"):
        try:
            df=(pd.read_excel(f,header=None) if not f.name.endswith(".csv")
                else pd.read_csv(f,header=None,sep=None,engine='python'))
            for i,row in df.head(20).iterrows():
                row_l=[str(c).strip().lower() for c in row]
                if any("número da uc" in s for s in row_l):
                    df.columns=[str(c).strip() for c in row]; df=df.iloc[i+1:].reset_index(drop=True); break
            df.columns=[str(c).strip() for c in df.columns]; df=df.fillna("")

            uc_col  =next((c for c in df.columns if "Número da UC" in c),None)
            cons_col=next((c for c in df.columns if "Consumo"      in c),None)
            sald_col=next((c for c in df.columns if "Saldo"        in c),None)
            tipo_col=next((c for c in df.columns if "Tipo"         in c or "Instalação" in c),None)
            titu_col=next((c for c in df.columns if "Titular"      in c),None)

            if not uc_col: st.error("Coluna 'Número da UC' não encontrada."); return

            bo=load_backoffice(); atualizados=0; novos=0
            for _,row in df.iterrows():
                uc_val=str(row[uc_col]).strip()
                if not uc_val: continue
                rec={"uc":uc_val,
                     "gerador":sel_ger_bo,
                     "titular":str(row[titu_col]) if titu_col else "—",
                     "consumo_total":clean_val(row[cons_col]) if cons_col else 0,
                     "saldo_credito":clean_val(row[sald_col]) if sald_col else 0,
                     "tipo_instalacao":str(row[tipo_col]) if tipo_col else "—",
                     "atualizado_em":datetime.now().strftime("%d/%m/%Y %H:%M")}
                idx_ex=next((i for i,b in enumerate(bo) if str(b["uc"])==uc_val),None)
                if idx_ex is not None: bo[idx_ex]=rec; atualizados+=1
                else: bo.append(rec); novos+=1
            save_backoffice(bo)
            st.success(f"✅ Processado! {novos} novo(s), {atualizados} atualizado(s) — Gerador: **{sel_ger_bo}**")
        except Exception as ex: st.error(f"Erro: {ex}")

    st.write("---")
    bo=load_backoffice()
    if bo:
        st.subheader("📋 Base de Consumo")
        # Filtro por gerador
        geradores_bo=sorted({b.get("gerador","—") for b in bo})
        f_ger_bo=st.selectbox("Filtrar por Gerador",["Todos"]+geradores_bo,key="bo_filtro")
        bo_filtrado=bo if f_ger_bo=="Todos" else [b for b in bo if b.get("gerador","")==f_ger_bo]
        st.dataframe(pd.DataFrame(bo_filtrado),use_container_width=True,hide_index=True)
    else: st.info("Nenhum dado de backoffice ainda. Importe um extrato.")


# ─── RATEIO ───────────────────────────────────────────────────────────────────
def _get_usinas_do_gerador(nome_ger):
    """Retorna lista de usinas vinculadas ao gerador pelo campo 'gerador'."""
    return [u for u in load_usinas() if u.get("gerador","").strip().lower()==nome_ger.strip().lower()]

def page_rateio():
    st.title("⚖️ Rateio")
    ta,tb,tc,td=st.tabs(["🔄 Rebalancear","📤 Atualizar Vigente","📋 Consultar","🔍 Buscar UC"])

    geradores=load_geradores()
    nomes_ger=sorted({g["gerador"] for g in geradores})

    # ══ A. REBALANCEAMENTO ══
    with ta:
        st.subheader("🔄 Rebalanceamento de Rateio")
        if not nomes_ger: st.info("Cadastre geradores antes."); st.stop()

        sel_ger=st.selectbox("Gerador",nomes_ger,key="rb_ger")
        usinas_ger=_get_usinas_do_gerador(sel_ger)
        if not usinas_ger:
            st.warning(f"Nenhuma usina vinculada ao gerador **{sel_ger}**. "
                       "Verifique se as usinas estão cadastradas com o campo Gerador correto."); st.stop()

        nomes_usi=[u.get("ufv") or u["uc"] for u in usinas_ger]
        sel_usi_nome=st.selectbox("Usina",nomes_usi,key="rb_usi")
        sel_usi=usinas_ger[nomes_usi.index(sel_usi_nome)]
        uc_usina=str(sel_usi["uc"])

        # Verificar geração do mês
        ger_mes=load_geracao(); mes_atual=datetime.now().strftime("%m/%Y")
        rec_ger=next((g for g in ger_mes if normalize_uc(str(g.get("uc","")))==normalize_uc(uc_usina)
                      and g.get("competencia","")==mes_atual),None)
        if not rec_ger:
            st.warning(f"⚠️ Geração de **{sel_usi_nome}** para {mes_atual} não registrada. "
                       "Registre em **Geração** antes."); st.stop()

        geracao_kwh=clean_val(rec_ger.get("energia_injetada",0))
        st.info(f"✅ Geração registrada para {mes_atual}: **{geracao_kwh:,.2f} kWh**")

        autonomia=st.number_input("Meses de autonomia desejada",min_value=1,max_value=12,value=3,key="rb_aut")

        ra1,ra2=st.columns(2)
        f_rat=ra1.file_uploader("Rateio Vigente (UC, Apelido, % Atual, CNPJ)",type=["xlsx","xls","csv"],key="up_rat")
        f_ext=ra2.file_uploader("Extrato Detalhado (UC, Consumo, Saldo, Tipo)",type=["xlsx","xls","csv"],key="up_ext_rat")

        st.markdown("**UCs Saindo (opcional):**")
        n_saindo=st.number_input("Qtd saindo",min_value=0,max_value=30,value=0,step=1,key="rb_ns")
        ucs_saindo=[]
        for i in range(int(n_saindo)):
            sc1,sc2=st.columns(2)
            uc_s=sc1.text_input(f"UC saindo #{i+1}",key=f"uc_s_{i}")
            mot_s=sc2.text_input(f"Motivo #{i+1}",key=f"mot_s_{i}")
            if uc_s: ucs_saindo.append({"uc":str(uc_s).strip(),"motivo":mot_s})

        st.markdown("**Novas UCs (opcional):**")
        n_novas=st.number_input("Qtd novas",min_value=0,max_value=30,value=0,step=1,key="rb_nn")
        ucs_novas=[]
        for i in range(int(n_novas)):
            nc1,nc2,nc3=st.columns(3)
            uc_n=nc1.text_input(f"Nova UC #{i+1}",key=f"uc_n_{i}")
            ap_n=nc2.text_input(f"Apelido #{i+1}",key=f"ap_n_{i}")
            cn_n=nc3.number_input(f"Consumo Médio kWh #{i+1}",min_value=0.0,step=1.0,key=f"cn_{i}")
            if uc_n: ucs_novas.append({"uc":str(uc_n).strip(),"apelido":ap_n,"consumo":cn_n})

        ancora=st.text_input("Unidade Âncora (UC) — opcional",key="rb_anc")

        if st.button("⚙️ Calcular Rebalanceamento",key="btn_rb"):
            if not f_rat or not f_ext: st.error("Faça upload dos dois arquivos."); st.stop()
            try:
                # Rateio vigente
                df_rat=(pd.read_excel(f_rat,dtype=str) if not f_rat.name.endswith(".csv")
                        else pd.read_csv(f_rat,dtype=str))
                df_rat.columns=df_rat.columns.str.strip(); df_rat=df_rat.fillna("")

                # Extrato
                df_ext2=load_planilha(f_ext)
                if df_ext2 is None: st.error("Erro ao ler o extrato."); st.stop()

                uc_e_col =next((c for c in df_ext2.columns if "Número da UC" in c),df_ext2.columns[0])
                cons_col =next((c for c in df_ext2.columns if "Consumo"      in c),None)
                sald_col =next((c for c in df_ext2.columns if "Saldo"        in c),None)
                tipo_col =next((c for c in df_ext2.columns if "Tipo"         in c or "Instalação" in c),None)
                df_ext2["UC_NORM"]=df_ext2[uc_e_col].apply(normalize_uc)

                uc_r_col=next((c for c in df_rat.columns if "UC" in c),df_rat.columns[0])
                ap_col  =next((c for c in df_rat.columns if "Apelido" in c),None)
                cnpj_col=next((c for c in df_rat.columns if "CNPJ" in c),None)
                df_rat["UC_NORM"]=df_rat[uc_r_col].apply(normalize_uc)

                saindo_norms={normalize_uc(x["uc"]) for x in ucs_saindo}
                df_rat=df_rat[~df_rat["UC_NORM"].isin(saindo_norms)].copy()

                resultado=[]
                for _,r_row in df_rat.iterrows():
                    uc_norm=r_row["UC_NORM"]
                    apelido=r_row[ap_col] if ap_col else "—"
                    cnpj   =r_row[cnpj_col] if cnpj_col else "—"
                    ext_row=df_ext2[df_ext2["UC_NORM"]==uc_norm]
                    if ext_row.empty: consumo_total=saldo=0; tipo="monofasico"
                    else:
                        ext_row=ext_row.iloc[0]
                        consumo_total=clean_val(ext_row[cons_col]) if cons_col else 0
                        saldo        =clean_val(ext_row[sald_col]) if sald_col else 0
                        tipo         =str(ext_row[tipo_col]).lower() if tipo_col else "monofasico"

                    consumo_comp=max(consumo_total-100,0) if "trif" in tipo else max(consumo_total-30,0)
                    necessidade =consumo_comp*0.20 if (consumo_total>0 and saldo/consumo_total>autonomia) else consumo_comp

                    resultado.append({"UC_NORM":uc_norm,"UC":r_row[uc_r_col],"Apelido":apelido,"CNPJ":cnpj,
                                      "Consumo Comp. (kWh)":round(consumo_comp,2),"Saldo (kWh)":round(saldo,2),
                                      "Necessidade (kWh)":round(necessidade,2)})

                for nu in ucs_novas:
                    cc=max(nu["consumo"]-30,0)
                    resultado.append({"UC_NORM":normalize_uc(nu["uc"]),"UC":nu["uc"],"Apelido":nu.get("apelido","—"),
                                      "CNPJ":"—","Consumo Comp. (kWh)":round(cc,2),"Saldo (kWh)":0,"Necessidade (kWh)":round(cc,2)})

                total_nec=sum(r["Necessidade (kWh)"] for r in resultado)
                for r in resultado:
                    r["Rateio Verificado (%)"]=round((r["Necessidade (kWh)"]/geracao_kwh*100),4) if geracao_kwh>0 else 0

                soma=sum(r["Rateio Verificado (%)"] for r in resultado)
                sobra=round(100.0-soma,4)
                if sobra!=0:
                    ancora_norm=normalize_uc(ancora) if ancora else None
                    idx_anc=next((i for i,r in enumerate(resultado) if r["UC_NORM"]==ancora_norm),None) if ancora_norm else None
                    if idx_anc is not None:
                        resultado[idx_anc]["Rateio Verificado (%)"]=round(resultado[idx_anc]["Rateio Verificado (%)"]+sobra,4)
                    elif total_nec>0:
                        for r in resultado:
                            r["Rateio Verificado (%)"]=round(r["Rateio Verificado (%)"]+sobra*(r["Necessidade (kWh)"]/total_nec),4)

                df_res=pd.DataFrame(resultado)
                df_res.insert(0,"#",range(1,len(df_res)+1))
                # Linha TOTAL
                total_row={"#":"TOTAL","UC":"","Apelido":"","CNPJ":"",
                           "Consumo Comp. (kWh)":df_res["Consumo Comp. (kWh)"].sum(),
                           "Saldo (kWh)":df_res["Saldo (kWh)"].sum(),
                           "Necessidade (kWh)":df_res["Necessidade (kWh)"].sum(),
                           "Rateio Verificado (%)":df_res["Rateio Verificado (%)"].sum()}
                df_show=pd.concat([df_res[["#","UC","Apelido","CNPJ","Consumo Comp. (kWh)","Saldo (kWh)","Rateio Verificado (%)"]],
                                   pd.DataFrame([total_row])],ignore_index=True)

                soma_final=df_res["Rateio Verificado (%)"].sum()
                st.success(f"✅ Soma: {soma_final:.4f}% | Geração: {geracao_kwh:,.2f} kWh")
                st.dataframe(df_show,use_container_width=True,hide_index=True)
                st.download_button("⬇️ Exportar Excel",df_to_excel_bytes(df_show),
                    f"rateio_{sel_ger}_{sel_usi_nome}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as ex:
                st.error(f"Erro no cálculo: {ex}")
                import traceback; st.code(traceback.format_exc())

    # ══ B. ATUALIZAR VIGENTE ══
    with tb:
        st.subheader("📤 Atualizar Rateio Vigente")
        st.markdown("""
        **Modelo esperado da planilha (colunas):**
        `#` · `UC` · `Apelido` · `CNPJ` · `Consumo Compensável` · `Saldo` ·
        `Rateio Ideal (%)` · `Rateio Verificado (%)` · `Percentual` · `Estimado Verificado` ·
        `Estimado Ideal` · `Déficit Mensal` · `Autonomia` · `kWh Disponível` · `Observações`
        """)
        if not nomes_ger: st.info("Cadastre geradores antes."); st.stop()

        sel_ger2=st.selectbox("Gerador",nomes_ger,key="upd_ger")
        usinas2=_get_usinas_do_gerador(sel_ger2)
        if not usinas2: st.warning(f"Nenhuma usina vinculada ao gerador **{sel_ger2}**."); st.stop()
        nomes2=[u.get("ufv") or u["uc"] for u in usinas2]
        sel_u2=st.selectbox("Usina",nomes2,key="upd_usi")
        uc_u2=usinas2[nomes2.index(sel_u2)]["uc"]
        geracao_upd=clean_val(usinas2[nomes2.index(sel_u2)].get("geracao_estimada",0))

        f_upd=st.file_uploader("Planilha do novo rateio (modelo Sunne)",type=["xlsx","xls","csv"],key="up_upd")
        if f_upd and st.button("💾 Salvar como Vigente",key="btn_upd"):
            try:
                df_upd=(pd.read_excel(f_upd,dtype=str) if not f_upd.name.endswith(".csv")
                        else pd.read_csv(f_upd,dtype=str))
                df_upd.columns=df_upd.columns.str.strip(); df_upd=df_upd.fillna("")
                hist=load_rateios(); chave=f"{sel_ger2}||{uc_u2}"
                hist.setdefault(chave,[])
                hist[chave].append({"versao":len(hist[chave])+1,
                                    "salvo_em":datetime.now().strftime("%d/%m/%Y %H:%M"),
                                    "gerador":sel_ger2,"usina_nome":sel_u2,"uc":uc_u2,
                                    "geracao_kwh":geracao_upd,
                                    "dados":df_upd.to_dict(orient="records")})
                save_rateios(hist)
                st.success(f"✅ Rateio v{len(hist[chave])} salvo para **{sel_u2}** ({sel_ger2})!")
            except Exception as ex: st.error(f"Erro: {ex}")

    # ══ C. CONSULTAR ══
    with tc:
        st.subheader("📋 Consultar Rateio Vigente e Histórico")
        if not nomes_ger: st.info("Cadastre geradores antes."); st.stop()

        sel_ger3=st.selectbox("Gerador",nomes_ger,key="cons_ger")
        usinas3=_get_usinas_do_gerador(sel_ger3)
        if not usinas3: st.warning(f"Nenhuma usina para **{sel_ger3}**."); st.stop()
        nomes3=[u.get("ufv") or u["uc"] for u in usinas3]
        sel_u3=st.selectbox("Usina",nomes3,key="cons_usi")
        uc_u3=usinas3[nomes3.index(sel_u3)]["uc"]
        chave3=f"{sel_ger3}||{uc_u3}"

        hist=load_rateios()
        versoes=hist.get(chave3,[])
        if not versoes:
            st.info(f"Nenhum rateio salvo para **{sel_u3}** ({sel_ger3})."); st.stop()

        opts=[f"v{v['versao']} — {v['salvo_em']}" for v in versoes]
        sel_v=st.selectbox("Versão",opts,key="cons_v",index=len(opts)-1)
        idx_v=opts.index(sel_v)
        v_data=versoes[idx_v]

        label="✅ Vigente (mais recente)" if idx_v==len(versoes)-1 else f"📁 Histórico — v{v_data['versao']}"
        st.markdown(f"**{label}** · Salvo em: {v_data['salvo_em']}")

        df_v=pd.DataFrame(v_data["dados"])
        geracao_v=v_data.get("geracao_kwh",0)
        if geracao_v: st.info(f"⚡ Geração da usina no período: **{geracao_v:,.2f} kWh**")

        # Exibir no modelo da imagem 5 com destaque TOTAL
        st.dataframe(df_v,use_container_width=True,hide_index=True)

        # Exportar no modelo Sunne
        excel_bytes=df_to_excel_bytes(df_v)
        st.download_button(f"⬇️ Exportar Excel — {sel_u3}",excel_bytes,
            f"rateio_vigente_{sel_ger3}_{sel_u3}_v{v_data['versao']}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ══ D. BUSCAR UC ══
    with td:
        st.subheader("🔍 Buscar Beneficiário por UC")
        st.markdown("Pesquisa em todos os rateios vigentes cadastrados no sistema.")

        uc_busca=st.text_input("Número da UC do cliente",placeholder="Digite a UC completa...",key="uc_busca_inp")
        if st.button("🔍 Buscar",key="btn_busca"):
            if not uc_busca.strip():
                st.warning("Digite uma UC para buscar.")
            else:
                uc_norm_b=normalize_uc(uc_busca)
                hist=load_rateios(); bo=load_backoffice(); encontrado=False

                for chave,versoes in hist.items():
                    if not versoes: continue
                    vigente=versoes[-1]
                    gen,uc_usina_key=chave.split("||") if "||" in chave else (chave,"")

                    for row in vigente["dados"]:
                        # Procurar a UC em todas as colunas
                        uc_encontrada=None
                        for k,v in row.items():
                            if normalize_uc(str(v))==uc_norm_b:
                                uc_encontrada=str(v); break
                        if uc_encontrada:
                            encontrado=True
                            # Buscar nome/apelido
                            ap_col_r=next((k for k in row if "apelido" in k.lower() or "titular" in k.lower() or "nome" in k.lower()),"")
                            nome_cliente=row.get(ap_col_r,"—") if ap_col_r else "—"
                            # % rateio
                            pct_col=next((k for k in row if "%" in k or "rateio" in k.lower() or "verificado" in k.lower()),"")
                            pct=row.get(pct_col,"—") if pct_col else "—"

                            # Buscar usina
                            usinas=load_usinas()
                            usi_match=next((u for u in usinas if normalize_uc(u["uc"])==normalize_uc(uc_usina_key)),{})
                            usina_nome=usi_match.get("ufv",uc_usina_key)

                            # Dados do backoffice
                            bo_rec=next((b for b in bo if normalize_uc(str(b.get("uc","")))==uc_norm_b),None)

                            st.success(f"✅ UC **{uc_busca}** encontrada!")
                            st.markdown(f"""
| Campo | Valor |
|---|---|
| **UC** | `{uc_busca}` |
| **Nome / Apelido** | {nome_cliente} |
| **Gerador** | {gen} |
| **Usina** | {usina_nome} |
| **% Rateio Atual** | {pct} |
| **Rateio (versão)** | v{vigente['versao']} — {vigente['salvo_em']} |
""")
                            if bo_rec:
                                b1,b2,b3=st.columns(3)
                                b1.metric("Consumo Total",f"{bo_rec.get('consumo_total',0):,.1f} kWh")
                                b2.metric("Saldo de Crédito",f"{bo_rec.get('saldo_credito',0):,.1f} kWh")
                                b3.metric("Tipo Instalação",bo_rec.get("tipo_instalacao","—"))
                            else:
                                st.info("UC não encontrada no Backoffice. Importe o extrato detalhado para ver consumo e saldo.")
                            break
                    if encontrado: break

                if not encontrado:
                    st.warning(f"UC **{uc_busca}** não encontrada em nenhum rateio ativo. "
                               "O cliente pode ter saído do rateio ou ainda não foi cadastrado.")


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
            e=st.text_input("E-mail",value="milena@sunne.com.br")
            s=st.text_input("Senha",type="password")
            if st.form_submit_button("Acessar Hub",use_container_width=True):
                u=authenticate(e,s)
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
        for key,label in [("dash","Dashboard"),("geradores","Geradores"),("usinas","Usinas"),
                          ("atividades","Atividades"),("geracao","Geração"),
                          ("backoffice","Backoffice"),("rateio","Rateio"),("faturamento","Faturamento")]:
            if st.button(label,key=f"nav_{key}"): st.session_state["page"]=key
        st.write("---")
        if st.button("Sair",key="nav_sair"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    pages={"dash":page_dashboard,"geradores":page_geradores,"usinas":page_usinas,
           "atividades":page_atividades,"geracao":page_geracao,
           "backoffice":page_backoffice,"rateio":page_rateio,"faturamento":page_faturamento}
    pages.get(st.session_state.get("page","dash"),page_dashboard)()


if __name__=="__main__":
    main()
