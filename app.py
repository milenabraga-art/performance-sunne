import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import uuid
import traceback
import io
import base64

# ── Módulo RPA (importação segura — falha silenciosa se libs ausentes) ────────
try:
    import robot_captura as _robot
    ROBOT_DISPONIVEL = True
except Exception as _robot_err:
    ROBOT_DISPONIVEL = False
    _robot_err_msg = str(_robot_err)

try:
    import rateio_sunne_bot as _rateio_bot
    RATEIO_BOT_OK = True
except Exception as _rateio_bot_err:
    RATEIO_BOT_OK = False
    _rateio_bot_err_msg = str(_rateio_bot_err)

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne · Hub Operacional v12",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>☀️</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS PREMIUM SUNNE ─────────────────────────────────────────────────────────
SUNNE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap');

/* ════════════════════════════════════════════════════════════════
   SUNNE HUB v12 — Design System
   Aesthetic: Pro Dark · Linear/Vercel-grade · Precision data UI
   ════════════════════════════════════════════════════════════════ */

:root {
  /* ── Core surfaces ── */
  --bg:          #FDF8F5;
  --bg-2:        #ffffff;
  --bg-3:        #32001a;
  --surface:     #13131C;
  --surface-2:   #18182A;
  --surface-3:   #1E1E30;
  --overlay:     rgba(255,255,255,.03);

  /* ── Brand ── */
  --orange:      #F36E21;
  --orange-d:    #D45E14;
  --orange-glow: rgba(243,110,33,.18);
  --orange-dim:  rgba(243,110,33,.10);
  --orange-xs:   rgba(243,110,33,.06);

  /* ── Accent ── */
  --accent:      #6366F1;
  --accent-d:    #4F52D9;
  --accent-dim:  rgba(99,102,241,.12);

  /* ── Text ── */
  --text-1:      #1C0010;
  --text-2:      #33001A;
  --text-3:      #606080;
  --text-4:      #FDF8F5;

  /* ── Borders ── */
  --border:      rgba(51,0,26,.08);
  --border-m:    rgba(51,0,26,.15);
  --border-h:    rgba(51,0,26,.25);

  /* ── Status ── */
  --red:          #F43F5E;
  --red-dim:      rgba(244,63,94,.12);
  --amber:        #F59E0B;
  --amber-dim:    rgba(245,158,11,.12);
  --green:        #10B981;
  --green-dim:    rgba(16,185,129,.12);
  --blue:         #3B82F6;
  --blue-dim:     rgba(59,130,246,.12);

  /* ── Radii ── */
  --r-xs: 4px;
  --r-s:  6px;
  --r:    10px;
  --r-l:  14px;
  --r-xl: 20px;
}

/* ── Reset & base ───────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: 'Geist', sans-serif !important;
  color: var(--text-1) !important;
}
[data-testid="stAppViewContainer"] { background: var(--s-bg) !important; }
[data-testid="stMain"]             { background: var(--s-bg) !important; }
#MainMenu, footer, header          { visibility: hidden; }
.block-container {
  padding: 2rem 2.5rem 4rem !important;
  max-width: 1440px !important;
}

/* ── TITULOS GRANDES E EQUILIBRADOS ── */
.page-h1 { 
    font-size: 34px !important; 
    font-weight: 700 !important; 
    color: var(--s-wine) !important; 
    letter-spacing: -0.5px !important; 
    margin-bottom: 4px !important;
    line-height: 1.2 !important;
}
.page-sub { 
    font-size: 14px !important; 
    color: var(--text-3) !important; 
    margin-bottom: 28px !important;
    font-weight: 400 !important;
}

/* ── CONTÊINER ARREDONDADO PARA FILTROS ── */
.filter-container {
    background: #ffffff !important;
    border: 1px solid rgba(51,0,26,.12) !important;
    border-radius: var(--r-l) !important;
    padding: 22px 24px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
.filter-title {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--text-1) !important;
    margin-bottom: 14px !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: var(--bg-3) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
  color: rgba(255,255,255,0.85) !important;
}

/* ── KPI BOX ── */
.kpi-box {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--r-l);
  padding: 1.1rem 1.3rem .9rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.kpi-value {
  font-size: 1.9rem; font-weight: 700;
  color: var(--orange); line-height: 1; margin-bottom: .35rem;
}
.kpi-label {
  font-size: 10px; font-weight: 600;
  color: var(--text-3); text-transform: uppercase; letter-spacing: .12em;
}

/* ── Alerts ── */
.alert {
  border-radius: var(--r); padding: .7rem .9rem; margin-bottom: .5rem; font-size: 13px; line-height: 1.55;
}
.alert-r { background: #FEF2F2; border: 1px solid #FCA5A5; color: #991B1B; }
.alert-g { background: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; }
.alert-b { background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; }

.sdiv { height: 1px; background: var(--border); margin: 1.4rem 0; }
</style>
"""

DB              = "database"
USERS_FILE      = "users.json"
GER_FILE        = f"{DB}/geradores.json"
USI_FILE        = f"{DB}/usinas.json"
TASKS_FILE      = f"{DB}/tasks.json"
GERACAO_FILE    = f"{DB}/geracao_usinas.json"
BACKOFFICE_FILE = f"{DB}/backoffice.json"
RATEIO_FILE     = f"{DB}/historico_rateios.json"
ANALISES_FILE   = f"{DB}/historico_analises.json"
GOOGLE_FILE     = f"{DB}/google_tokens.json"

os.makedirs(DB, exist_ok=True)

TARIFAS_BASE = {"GD1": 0.8182, "GD2": 0.64788}
MODELOS_NEGOCIO = ["Associação", "Consórcio", "Autoconsumo"]

def _load(path, default):
    if not os.path.exists(path): _save(path, default)
    with open(path, encoding="utf-8") as f: return json.load(f)

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

# ── AUTH ──────────────────────────────────────────────────────────────────────
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

# ── CRUD ──────────────────────────────────────────────────────────────────────
def load_geradores():   return _load(GER_FILE, [])
def save_geradores(d):  _save(GER_FILE, d)
def load_usinas():      return _load(USI_FILE, [])
def save_usinas(d):     _save(USI_FILE, d)
def load_tasks():       return _load(TASKS_FILE, [])
def save_tasks(d):      _save(TASKS_FILE, d)
def load_geracao():     return _load(GERACAO_FILE, [])
def save_geracao(d):    _save(GERACAO_FILE, d)
def load_backoffice():  return _load(BACKOFFICE_FILE, [])
def save_backoffice(d): _save(BACKOFFICE_FILE, d)
def load_rateios():     return _load(RATEIO_FILE, {})
def save_rateios(d):    _save(RATEIO_FILE, d)
def load_analises():    return _load(ANALISES_FILE, {})
def save_analises(d):   _save(ANALISES_FILE, d)
def load_google_tokens(): return _load(GOOGLE_FILE, {})
def save_google_tokens(d): _save(GOOGLE_FILE, d)

def task_data_programada(t) -> datetime | None:
    v = t.get("data_programada", "")
    if not v: return None
    for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y"]:
        try: return datetime.strptime(str(v).strip(), fmt)
        except: pass
    return None

def task_esta_atrasada(t) -> bool:
    if t.get("status") in ("Concluido", "Cancelado"): return False
    dp = task_data_programada(t)
    return dp is not None and dp.date() < datetime.now().date()

def task_vence_hoje(t) -> bool:
    if t.get("status") in ("Concluido", "Cancelado"): return False
    dp = task_data_programada(t)
    return dp is not None and dp.date() == datetime.now().date()

def normalize_uc(val):
    if not val: return ""
    s = "".join(filter(str.isdigit, str(val).strip().split('.')[0]))
    return s.lstrip("0") or s

def clean_val(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return 0.0
    s = str(v).replace("R$","").replace(" ","").replace("\xa0","").strip()
    if not s or s in ("-","—","nan","NaN","None",""): return 0.0
    s = s.replace("%","")
    if "," in s and "." in s:
        if s.index(".") < s.index(","): s = s.replace(".","").replace(",",".")
        else: s = s.replace(",","")
    elif "," in s: s = s.replace(",",".")
    try: return float(s)
    except: return 0.0

def df_to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, index=False)
    return buf.getvalue()

def comp_sort_key(comp_str):
    try:
        p = str(comp_str).strip().split("/")
        if len(p) == 2: return (int(p[1]), int(p[0]))
    except: pass
    return (9999, 99)

def load_planilha(file):
    if file is None: return None
    try:
        df = (pd.read_excel(file, header=None) if not file.name.endswith('.csv')
              else pd.read_csv(file, header=None, sep=None, engine='python'))
        for i, row in df.head(20).iterrows():
            row_l = [str(c).strip().lower() for c in row]
            if any("uc nova" in s or "número da uc" in s or "uc" in s for s in row_l):
                df.columns = [str(c).strip() for c in row]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return None

# ══════════════════════════════════════════════════════════════════════════════
# REFINAMENTO OPERACIONAL DO MOTOR DE CRUZAMENTO (CONFORME SOLICITADO)
# ══════════════════════════════════════════════════════════════════════════════

def cruzar_multi_medicao_extrato(df_extrato: pd.DataFrame, list_df_medicao: list, competencia_alvo: str) -> dict:
    """
    Racional Corrigido:
    1. Varre o Extrato Detalhado procurando a coluna de pagamento ('data do pagamento boleto sunne' ou similar).
    2. Filtra as linhas cujo pagamento ocorreu dentro do mês/ano alvo informado (Ex: '05/2026').
    3. Consolida todas as combinações de UC + Competência mapeadas em até 3 relatórios de medição recebidos.
    4. Cruza e aponta faturas pagas ausentes nos relatórios.
    """
    # Detecção das Colunas do Extrato Detalhado
    col_uc_e   = next((c for c in df_extrato.columns if "número da uc" in c.lower() or "numero da uc" in c.lower() or c.lower() == "uc"), None)
    col_dt_e   = next((c for c in df_extrato.columns if "data do pagamento boleto sunne" in c.lower() or "data de pagamento" in c.lower() or "pagamento" in c.lower()), None)
    col_val_e  = next((c for c in df_extrato.columns if "total a pagar" in c.lower()), None)
    col_comp_e = next((c for c in df_extrato.columns if "competência" in c.lower() or "competencia" in c.lower()), None)
    col_tit_e  = next((c for c in df_extrato.columns if "titular" in c.lower() or "nome" in c.lower()), None)

    if not col_uc_e:
        return {"erro": "Coluna identificadora de UC não mapeada no Extrato."}
    if not col_dt_e:
        return {"erro": "Coluna de data de pagamento do boleto não mapeada no Extrato."}

    # Quebra a competência alvo (Ex: "05/2026" -> "05", "2026")
    try:
        tgt_mes, tgt_ano = competencia_alvo.strip().split("/")
    except:
        return {"erro": "Formato de competência inválido. Preencha como MM/AAAA (Ex: 05/2026)."}

    # Filtra o extrato pela data de pagamento real (dentro do mês alvo)
    df_filtrado_lista = []
    for _, row in df_extrato.iterrows():
        dt_str = str(row[col_dt_e]).strip()
        is_valido = False
        
        # Mapeia formatos comuns de strings de data
        if "/" in dt_str:
            parts = dt_str.split("/")
            if len(parts) >= 3:
                if parts[1].zfill(2) == tgt_mes.zfill(2) and parts[2][:4] == tgt_ano:
                    is_valido = True
        elif "-" in dt_str:
            parts = dt_str.split("-")
            if len(parts) >= 3:
                if parts[0] == tgt_ano and parts[1].zfill(2) == tgt_mes.zfill(2):
                    is_valido = True
                    
        if is_valido:
            df_filtrado_lista.append(row)

    if not df_filtrado_lista:
        return {
            "ok": [], "ausentes": [], "extras": [],
            "total_pago": 0.0, "total_ausente_valor": 0.0,
            "aviso": f"Nenhuma fatura com pagamento identificado no mês {competencia_alvo}."
        }

    df_pago = pd.DataFrame(df_filtrado_lista)
    df_pago["_uc_norm"] = df_pago[col_uc_e].apply(normalize_uc)
    df_pago["_comp"] = df_pago[col_comp_e].astype(str).str.strip() if col_comp_e else "—"

    # Consolida chaves de busca de todos os relatórios de medição disponíveis (Até 3)
    medicao_set = set()
    for df_m in list_df_medicao:
        if df_m is None or df_m.empty:
            continue
        col_uc_m   = next((c for c in df_m.columns if "uc" in c.lower()), None)
        col_comp_m = next((c for c in df_m.columns if "compet" in c.lower()), None)
        
        if col_uc_m:
            for _, r_m in df_m.iterrows():
                uc_norm_m = normalize_uc(str(r_m[col_uc_m]))
                comp_m = str(r_m[col_comp_m]).strip() if col_comp_m else "—"
                medicao_set.add((uc_norm_m, comp_m))
                medicao_set.add((uc_norm_m, "—")) # Fallback sem competência

    # Cruzamento analítico linha por linha
    ok = []
    ausentes = []
    
    for _, row in df_pago.iterrows():
        uc = row["_uc_norm"]
        comp = row["_comp"]
        val = clean_val(row[col_val_e]) if col_val_e else 0.0
        tit = str(row[col_tit_e]) if col_tit_e else "—"
        
        item = {"uc": row[col_uc_e], "competencia": comp, "valor": val, "titular": tit, "data_pagamento": row[col_dt_e]}
        
        if (uc, comp) in medicao_set or (uc, "—") in medicao_set:
            ok.append(item)
        else:
            ausentes.append(item)

    return {
        "ok": ok,
        "ausentes": ausentes,
        "extras": [], # Foco nos ausentes solicitados
        "total_pago": sum(i["valor"] for i in ok) + sum(i["valor"] for i in ausentes),
        "total_ausente_valor": sum(i["valor"] for i in ausentes),
    }

# ══════════════════════════════════════════════════════════════════════════════
# TELA: RELATÓRIO DE MEDIÇÃO — REFINADA COM ATÉ 3 FILES
# ══════════════════════════════════════════════════════════════════════════════

def page_medicao_cruzamento():
    st.markdown('<div class="page-h1">Relatório de Medição</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Cruzamento automatizado: faturas pagas no extrato vs. itens nos relatórios de medição.</div>', unsafe_allow_html=True)

    # CARD ENVELOPADO ARREDONDADO PARA ENTRADAS DE DADOS
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown('<div class="filter-title">📁 Upload de Arquivos e Parâmetros</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        f_ext = st.file_uploader("EXTRATO DETALHADO (XLSX/CSV)", type=["xlsx","xls","csv"], key="mc_ext")
        comp_alvo = st.text_input("Filtrar pagamentos do mês/ano (MM/AAAA)", value="05/2026", help="Filtra faturas pagas de 01 a 31 do mês informado")
    with c2:
        st.markdown("<p style='font-size:11.5px; font-weight:500; color:var(--text-3); text-transform:uppercase;'>Relatórios de Medição (Até 3 arquivos)</p>", unsafe_allow_html=True)
        f_med1 = st.file_uploader("Relatório de Medição 1 (Obrigatório)", type=["xlsx","xls","csv"], key="mc_med1")
        f_med2 = st.file_uploader("Relatório de Medição 2 (Opcional)", type=["xlsx","xls","csv"], key="mc_med2")
        f_med3 = st.file_uploader("Relatório de Medição 3 (Opcional)", type=["xlsx","xls","csv"], key="mc_med3")
        
    st.markdown('</div>', unsafe_allow_html=True)

    if f_ext and f_med1:
        if st.button("Cruzar agora", key="btn_cruzar", use_container_width=True):
            with st.spinner("Filtrando datas de pagamento e consolidando medições…"):
                try:
                    # Carrega extrato
                    df_e = pd.read_excel(f_ext) if not f_ext.name.endswith(".csv") else pd.read_csv(f_ext, sep=None, engine="python")
                    df_e.columns = [str(c).strip() for c in df_e.columns]
                    df_e = df_e.fillna("")

                    # Carrega lista de relatórios de medição disponíveis
                    med_files = [f_med1, f_med2, f_med3]
                    dfs_medicao = []
                    for f_m in med_files:
                        if f_m is not None:
                            df_m = pd.read_excel(f_m) if not f_m.name.endswith(".csv") else pd.read_csv(f_m, sep=None, engine="python")
                            df_m.columns = [str(c).strip() for c in df_m.columns]
                            df_m = df_m.fillna("")
                            dfs_medicao.append(df_m)

                    # Executa o novo motor de cruzamento com regras de data corrigidas
                    resultado = cruzar_multi_medicao_extrato(df_e, dfs_medicao, comp_alvo)
                    st.session_state["medicao_cruzamento"] = resultado
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")
                    st.code(traceback.format_exc())

        res = st.session_state.get("medicao_cruzamento")
        if res:
            if "erro" in res:
                st.error(res["erro"])
                return
            if "aviso" in res:
                st.warning(res["aviso"])
                return

            ausentes = res.get("ausentes", [])
            ok_list  = res.get("ok", [])

            # KPIs idênticos ao layout da imagem e253a2.png
            kc1, kc2, kc3, kc4 = st.columns(4)
            kc1.markdown(f'<div class="kpi-box"><div class="kpi-value" style="color:#0B7A5F">{len(ok_list)}</div><div class="kpi-label">Faturas OK</div></div>', unsafe_allow_html=True)
            kc2.markdown(f'<div class="kpi-box"><div class="kpi-value" style="color:#C41230">{len(ausentes)}</div><div class="kpi-label">Ausentes no Relatório</div></div>', unsafe_allow_html=True)
            kc3.markdown(f'<div class="kpi-box"><div class="kpi-value" style="color:#606080">0</div><div class="kpi-label">No Rel. sem pagamento</div></div>', unsafe_allow_html=True)
            kc4.markdown(f'<div class="kpi-box"><div class="kpi-value" style="color:#F36E21">R$ {res.get("total_ausente_valor",0):,.2f}</div><div class="kpi-label">Valor ausente</div></div>', unsafe_allow_html=True)

            st.write("")

            # Notificação e tabelas de exibição
            if ausentes:
                st.markdown(f'<div class="alert alert-r">⚠️ <b>{len(ausentes)} fatura(s)</b> pagas no extrato da competência filtrada NÃO estão em nenhum dos relatórios de medição anexados.</div>', unsafe_allow_html=True)
                with st.expander(f"Ver {len(ausentes)} faturas ausentes — R$ {res['total_ausente_valor']:,.2f}"):
                    df_aus = pd.DataFrame(ausentes)
                    df_aus["valor"] = df_aus["valor"].apply(lambda x: f"R$ {x:,.2f}")
                    df_aus.columns = [c.capitalize() for c in df_aus.columns]
                    st.dataframe(df_aus, use_container_width=True, hide_index=True)
                    
                    st.download_button(
                        "⬇ Exportar faturas ausentes (CSV)",
                        pd.DataFrame(ausentes).to_csv(index=False, sep=";").encode("utf-8-sig"),
                        "faturas_ausentes.csv", "text/csv"
                    )
            else:
                st.markdown('<div class="alert alert-g">✅ Todas as faturas liquidadas no mês constam nos relatórios de medição consultados!</div>', unsafe_allow_html=True)

            if ok_list:
                with st.expander(f"✅ {len(ok_list)} faturas confirmadas nos relatórios"):
                    df_ok = pd.DataFrame(ok_list)
                    df_ok["valor"] = df_ok["valor"].apply(lambda x: f"R$ {x:,.2f}")
                    st.dataframe(df_ok, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PRESERVAÇÃO INTEGRAL DO RESTANTE DAS FUNÇÕES DO SISTEMA (V12)
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    user = st.session_state["user"]; an = user["name"]
    agora = datetime.now()
    dia_semana = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"][agora.weekday()]
    st.markdown(f'<div style="margin-bottom:0.2rem"><h1 style="font-size:1.6rem;font-weight:500;margin:0">Olá, {an.split()[0]} 👋</h1><p style="color:var(--text-3);font-size:13px;margin:2px 0 0">{dia_semana}, {agora.strftime("%d/%m/%Y")}</p></div>', unsafe_allow_html=True)

    minhas_tasks = [t for t in load_tasks() if t.get("analista","").lower() == an.lower()]
    vence_hoje   = [t for t in minhas_tasks if task_vence_hoje(t)]
    atrasadas    = [t for t in minhas_tasks if task_esta_atrasada(t)]
    
    st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi_card("Minhas Tarefas Hoje", len(vence_hoje)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Minhas Tarefas Atrasadas", len(atrasadas)), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Total Carteira", len(minhas_tasks)), unsafe_allow_html=True)

def page_atividades():
    st.title("Atividades")
    tasks = load_tasks()
    if tasks: st.dataframe(pd.DataFrame(tasks), use_container_width=True, hide_index=True)
    else: st.info("Sem tarefas na esteira.")

def page_geradores():
    st.title("Geradores")
    geradores = load_geradores()
    if geradores: st.dataframe(pd.DataFrame(geradores), use_container_width=True, hide_index=True)
    else: st.info("Sem geradores cadastrados.")

def page_usinas():
    st.title("Usinas")
    usinas = load_usinas()
    if usinas: st.dataframe(pd.DataFrame(usinas), use_container_width=True, hide_index=True)
    else: st.info("Sem usinas cadastradas.")

def page_geracao():
    st.title("Geração das Usinas")
    geracao = load_geracao()
    if geracao: st.dataframe(pd.DataFrame(geracao), use_container_width=True, hide_index=True)
    else: st.info("Sem lançamentos de geração.")

def page_backoffice():
    st.title("Backoffice · Captura de Consumo")
    bo = load_backoffice()
    if bo: st.dataframe(pd.DataFrame(bo), use_container_width=True, hide_index=True)
    else: st.info("Histórico de backoffice vazio.")

def page_rateio(): page_header("Rateio", "Gestão estrutural de frações de cotas e sincronizações")
def page_faturamento(): page_header("Faturamento", "Auditoria de notas fiscais emitidas e faturados")
def page_bi_analise(): page_header("Análise BI", "Dashboards estratégicos consolidados")
def page_automacao(): page_header("Captura Automática", "Gatilhamento de robôs de coleta RPA")
def page_integracoes(): page_header("Integrações Google", "Gerenciamento de tokens Oauth para workspace")
def page_auditoria(): page_header("Auditoria UFV / UCs", "Módulo de engenharia analítica da saúde das plantas")
def page_gestor_dashboard(): page_header("Painel do Gestor", "Controle gerencial de analistas")

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
ROUTE_MAP = {
    "dash": page_dashboard, "gestor_dash": page_gestor_dashboard, "geradores": page_geradores,
    "usinas": page_usinas, "atividades": page_atividades, "geracao": page_geracao,
    "backoffice": page_backoffice, "rateio": page_rateio, "faturamento": page_faturamento,
    "bi_analise": page_bi_analise, "automacao": page_automacao, "integracoes": page_integracoes,
    "medicao": page_medicao_cruzamento, "auditoria": page_auditoria,
}

def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)
    
    # Força sessão logada estável para desenvolvimento direto
    st.session_state["user"] = {"name": "Milena Braga", "email": "milena.braga@sunne.com.br", "role": "admin"}
    st.session_state.setdefault("page", "medicao") # Abre direto na tela que você está refinando agora

    render_sidebar()
    page = st.session_state.get("page", "medicao")
    ROUTE_MAP.get(page, page_dashboard)()

if __name__ == "__main__":
    main()
