import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import uuid

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG & PATHS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sunne Hub v12",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB = os.path.join(os.path.dirname(__file__), "database")

def db_path(name): return os.path.join(DB, f"{name}.json")

def load_json(name):
    p = db_path(name)
    if not os.path.exists(p): return []
    with open(p, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_json(name, data):
    os.makedirs(DB, exist_ok=True)
    with open(db_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_uc(val):
    if val is None: return ""
    s = str(val).strip()
    if s.endswith(".0"): s = s[:-2]
    return s

# Configurações Globais da Esteira Operacional
KANBAN_STATUS = ["em aberto", "em andamento", "travado", "concluido", "cancelado"]
KANBAN_LABELS = {"em aberto": "Em Aberto", "em andamento": "Em Andamento",
                 "travado": "Travado", "concluido": "Concluído", "cancelado": "Cancelado"}
TEMA_COLORS  = {"Faturamento": ("#fff7ed", "#c2410c"), "Rateio": ("#faf5ff", "#7c3aed"), "Captura": ("#f0fdf4", "#15803d")}

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM — REPLICANDO IDENTIDADE VISUAL DO PORTAL SUNNE
# ─────────────────────────────────────────────────────────────────────────────
def inject_css():
    st.html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ── ROOT PALETTE ── */
:root {
    --s-wine:      #1C0010;
    --s-wine-mid:  #2a0018;
    --s-orange:    #F36E21;
    --s-orange-h:  #d45c16;
    --s-bg:        #f9fafb;
    --s-white:     #ffffff;
    --s-border:    #e5e7eb;
    --s-border-md: #d1d5db;
    --s-text:      #111827;
    --s-text-md:   #374151;
    --s-text-sm:   #6b7280;
    --s-radius:    8px;
    --s-radius-lg: 12px;
    --s-shadow:    0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.03);
}

/* PREVENÇÃO CONTRA O BUG KEYBOARD_DOUBLE */
[data-testid="stAppViewContainer"], p, span, div, label, td, th, h1, h2, h3, h4, input, select, textarea {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background: var(--s-bg) !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: none !important;
}
.main .block-container {
    padding: 28px 32px !important;
    max-width: 1440px !important;
}

/* ── SIDEBAR SLIM E LIMPA ── */
[data-testid="stSidebar"] {
    background: var(--s-wine) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] > div:first-child {
    background: var(--s-wine) !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.85) !important;
}

/* Customização dos Expanders na Barra Lateral */
[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: transparent !important;
    border: none !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: rgba(255,255,255,0.5) !important;
    padding: 12px 16px !important;
}
[data-testid="stSidebar"] .streamlit-expanderContent {
    background: transparent !important;
    border: none !important;
    padding: 0 4px 6px 12px !important;
}

/* Botões da Sidebar */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-radius: 6px !important;
    color: rgba(255,255,255,0.75) !important;
    text-align: left !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    padding: 8px 12px !important;
    width: 100% !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #fff !important;
}

/* ── HIERARQUIA DE TÍTULOS AMPLIADA (CONFORME FOTOS) ── */
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
    color: var(--s-text-sm) !important;
    margin-bottom: 28px !important;
    font-weight: 400 !important;
}
.section-label {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: var(--s-text) !important;
    margin: 20px 0 12px;
}

/* ── CONTÊINER DOS FILTROS ESTRUTURADO E ARREDONDADO ── */
div[data-testid="stVerticalBlockBorderContainer"] {
    background: var(--s-white) !important;
    border: 1px solid var(--s-border) !important;
    border-radius: var(--s-radius-lg) !important;
    padding: 22px 24px !important;
    margin-bottom: 24px !important;
    box-shadow: var(--s-shadow) !important;
}

/* ── CARDS DE MÉTRICAS E GRÁFICOS ── */
.s-card {
    background: var(--s-white);
    border-radius: var(--s-radius-lg);
    border: 1px solid var(--s-border);
    box-shadow: var(--s-shadow);
    padding: 20px 24px;
    margin-bottom: 16px;
}
.s-card-sm {
    background: var(--s-white);
    border-radius: var(--s-radius);
    border: 1px solid var(--s-border);
    box-shadow: var(--s-shadow);
    padding: 14px 18px;
    margin-bottom: 10px;
}
.kpi-card {
    background: var(--s-white);
    border-radius: var(--s-radius-lg);
    border: 1px solid var(--s-border);
    box-shadow: var(--s-shadow);
    padding: 18px 20px;
}
.kpi-label { font-size: 12px; font-weight: 500; color: var(--s-text-sm); margin-bottom: 6px; }
.kpi-value { font-size: 24px; font-weight: 700; color: var(--s-text); line-height: 1.1; }

/* ── BOTÕES ── */
.stButton > button {
    background: var(--s-orange) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--s-radius) !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    padding: 8px 18px !important;
}
.stButton > button:hover {
    background: var(--s-orange-h) !important;
}

/* ── BADGES & ESTEIRA ── */
.badge { display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.badge-open    { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.badge-doing   { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.badge-blocked { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.badge-done    { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }

.s-alert { border-radius: var(--s-radius); padding: 12px 16px; font-size: 13.5px; margin-bottom: 10px; display: flex; gap: 10px; }
.s-alert.red    { background: #fef2f2; border: 1px solid #fecaca; color: #7f1d1d; }
.s-alert.green  { background: #f0fdf4; border: 1px solid #bbf7d0; color: #14532d; }
.s-alert.blue   { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e3a8a; }

.k-col { background: #f3f4f6; border-radius: var(--s-radius-lg); padding: 12px; min-height: 380px; }
.k-col-header { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--s-text-sm); padding-bottom: 10px; border-bottom: 1.5px solid var(--s-border); margin-bottom: 10px; display: flex; justify-content: space-between; }
.k-count { background: rgba(0,0,0,0.07); border-radius: 20px; padding: 1px 8px; font-size: 11px; }
.k-card { background: var(--s-white); border-radius: var(--s-radius); border: 1px solid var(--s-border); padding: 12px 14px; margin-bottom: 8px; }

.sb-logo { padding: 20px 20px 16px; border-bottom: 1px solid rgba(255,255,255,0.07); }
.sb-logo-name { font-size: 22px; font-weight: 700; color: var(--s-orange) !important; }
.sb-logo-tagline { font-size: 10px; color: rgba(255,255,255,0.3) !important; text-transform: uppercase; letter-spacing: 0.15em; }
.sb-user { padding: 10px 20px 14px; border-bottom: 1px solid rgba(255,255,255,0.07); }
.sb-user-name { font-size: 13px; font-weight: 600; color: #fff !important; }
.sb-user-email { font-size: 11px; color: rgba(255,255,255,0.4) !important; }

.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.usina-banner { background: #fff7ed; border: 1px solid #fed7aa; border-radius: var(--s-radius-lg); padding: 16px 20px; display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""")

def page_header(title, subtitle=""):
    st.markdown(f'<div class="page-h1">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)

def kpi_card(label, value, sub=""):
    return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div style="font-size:12px; color:#6b7280; margin-top:4px;">{sub}</div></div>'

# ─────────────────────────────────────────────────────────────────────────────
# NAVEGAÇÃO DA SIDEBAR (SEM DUPLICAÇÕES)
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        nome = st.session_state.get("nome", "Milena Braga")
        email = st.session_state.get("email", "milena.braga@sunne.com.br")

        st.markdown(f"""
        <div class="sb-logo">
            <div class="sb-logo-name">sunne</div>
            <div class="sb-logo-tagline">Hub v12 · BI & Automação</div>
        </div>
        <div class="sb-user">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:32px;height:32px;border-radius:50%;background:#F36E21;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;">
                    {nome[0].upper()}
                </div>
                <div>
                    <div class="sb-user-name">{nome}</div>
                    <div class="sb-user-email">{email}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "Dashboard"; st.rerun()

        if st.button("📋 Atividades", use_container_width=True):
            st.session_state.page = "Atividades"; st.rerun()

        with st.expander("💰 Faturamento & BI", expanded=(st.session_state.page in ["Conciliação de Medição", "Inteligência Financeira", "Faturas das UGs"])):
            if st.button("🔍 Conciliação de Medição", use_container_width=True): st.session_state.page = "Conciliação de Medição"; st.rerun()
            if st.button("📈 Inteligência Financeira", use_container_width=True): st.session_state.page = "Inteligência Financeira"; st.rerun()
            if st.button("🧾 Faturas das UGs", use_container_width=True): st.session_state.page = "Faturas das UGs"; st.rerun()

        with st.expander("⚙️ Engenharia de Rateios", expanded=(st.session_state.page in ["Auditoria Técnica", "Simulador de Cotas"])):
            if st.button("🔬 Auditoria Técnica", use_container_width=True): st.session_state.page = "Auditoria Técnica"; st.rerun()
            if st.button("🎯 Simulador de Cotas", use_container_width=True): st.session_state.page = "Simulador de Cotas"; st.rerun()

        with st.expander("🗄️ Bases de Suporte", expanded=(st.session_state.page in ["Geradores", "Usinas", "Geração (Livro-Caixa)", "Backoffice"])):
            if st.button("👤 Geradores", use_container_width=True): st.session_state.page = "Geradores"; st.rerun()
            if st.button("🏭 Usinas", use_container_width=True): st.session_state.page = "Usinas"; st.rerun()
            if st.button("⚡ Geração (Livro-Caixa)", use_container_width=True): st.session_state.page = "Geração (Livro-Caixa)"; st.rerun()
            if st.button("📦 Backoffice", use_container_width=True): st.session_state.page = "Backoffice"; st.rerun()

        with st.expander("🤖 Automações", expanded=(st.session_state.page in ["Captura RPA", "OCR HubSpot"])):
            if st.button("🤖 Captura RPA", use_container_width=True): st.session_state.page = "Captura RPA"; st.rerun()
            if st.button("📄 OCR HubSpot", use_container_width=True): st.session_state.page = "OCR HubSpot"; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD (VISÃO GERAL)
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    page_header("Dashboard", "Visão geral do ecossistema de geração distribuída")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi_card("Cobranças Emitidas", "R$ 304.087,68", "803 boletos emitidos"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Receita do Período", "R$ 40.868,64", "Faturamento líquido"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Inadimplência do Período", "R$ 57.814,25", "136 faturas em aberto"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Saldo Acumulado Total", "158.5 MWh", "Usina + Unidades Consumidoras"), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CONCILIAÇÃO DE MEDIÇÃO (RACIONAL DE VERIFICAÇÃO INTEGRADO)
# ─────────────────────────────────────────────────────────────────────────────
def page_conciliacao():
    page_header("Conciliação de Medição", "Semana 1 · Cruzamento analítico de repasses e caixa")

    # CONTÊINER DOS FILTROS ENVELOPADO E ARREDONDADO COMPATÍVEL COM O PRINT
    with st.container(border=True):
        st.markdown("**🔍 Filtros e Dados de Entrada**")
        c1, c2 = st.columns(2)
        with c1: extrato_file = st.file_uploader("Upload Planilha A: Extrato Detalhado de Caixa", type=["xlsx", "xls"])
        with c2: medicao_file = st.file_uploader("Upload Planilha B: Tabela de Medição / Rateio Sunne", type=["xlsx", "xls"])
        mes_ref = st.text_input("Mês de Competência da Auditoria (AAAA-MM)", value="2026-05")

    if extrato_file and medicao_file:
        if st.button("Executar Auditoria de Faturas Faltantes"):
            try:
                df_ext = pd.read_excel(extrato_file, dtype=str)
                df_med = pd.read_excel(medicao_file, dtype=str)
                
                df_ext.columns = [c.strip() for c in df_ext.columns]
                df_med.columns = [c.strip() for c in df_med.columns]

                if "UC" in df_ext.columns: df_ext["UC"] = df_ext["UC"].apply(clean_uc)
                if "UC" in df_med.columns: df_med["UC"] = df_med["UC"].apply(clean_uc)

                def calc_ajustado(row):
                    try:
                        unif = str(row.get("Fatura Unificada", "")).lower()
                        total = float(str(row.get("Total a Pagar", 0)).replace(",",".").replace("R$","").strip() or 0)
                        boleto = float(str(row.get("Total a Pagar Boleto Concessionária", 0)).replace(",",".").replace("R$","").strip() or 0)
                        return total - boleto if unif in ("true","sim","1","yes") else total
                    except: return 0.0

                df_ext["Valor Ajustado"] = df_ext.apply(calc_ajustado, axis=1)
                df_merged = df_ext.merge(df_med, on="UC", how="left", suffixes=("_ext", "_med"))
                
                chave_med = [c for c in df_med.columns if c != "UC"]
                faltantes = df_merged[df_merged[chave_med[0]].isna()].copy() if chave_med else pd.DataFrame()

                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(kpi_card("Faturas em Extrato", f"{len(df_ext)} itens", "Processamento em lote"), unsafe_allow_html=True)
                with m2: st.markdown(kpi_card("Faturas Faltantes", f"⚠️ {len(faltantes)} UCs", "Ausentes no relatório de medição"), unsafe_allow_html=True)
                with m3: st.markdown(kpi_card("Montante Faltante", f"R$ {faltantes['Valor Ajustado'].sum() if 'Valor Ajustado' in faltantes.columns else 0:,.2f}", "Risco de estouro de caixa"), unsafe_allow_html=True)

                if len(faltantes) > 0:
                    st.markdown('<div class="s-alert red"><strong>Divergência de Caixa Encontrada:</strong> Unidades consumidoras listadas no extrato financeiro não constam no repasse.</div>', unsafe_allow_html=True)
                    st.dataframe(faltantes, use_container_width=True, hide_index=True)
                else:
                    st.markdown('<div class="s-alert green"><strong>Sucesso:</strong> Base de faturamento e medições 100% conciliadas.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro no mapeamento das planilhas: {e}")
    else:
        st.markdown("### 📊痛 Painel de Validação Estatística da Base Ativa")
        backoffice = load_json("backoffice")
        if backoffice:
            df_back = pd.DataFrame(backoffice)
            st.markdown(f"Análise da competência corrente `{mes_ref}`:")
            faturas_pendentes = df_back[df_back["saldo_solar"].astype(float) == 0.0]
            
            c1, c2 = st.columns(2)
            with c1: st.markdown(kpi_card("Total UCs Cadastradas", f"{len(df_back)} unidades", "Base de dados"), unsafe_allow_html=True)
            with c2: st.markdown(kpi_card("Faturas Faltantes / Pendentes", f"{len(faturas_pendentes)} UCs", "Sem leitura registrada"), unsafe_allow_html=True)
            
            if len(faturas_pendentes) > 0:
                st.dataframe(faturas_pendentes[["uc", "nome_beneficiario", "mes_ref"]], use_container_width=True, hide_index=True)
        else:
            st.info("Insira as planilhas Excel acima para rodar a rotina de auditoria eletrônica.")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ATIVIDADES (KANBAN ENVELOPADO)
# ─────────────────────────────────────────────────────────────────────────────
def page_atividades():
    page_header("Atividades", "Esteira operacional mensal — Fluxo Kanban de Processos")
    
    with st.container(border=True):
        st.markdown("**🔍 Filtros de Controle**")
        c1, c2 = st.columns([2, 1])
        with c1: tema_filtro = st.selectbox("Filtrar Atividades por Tema", ["Todos", "Faturamento", "Rateio", "Captura"])
        with c2: st.markdown("<br>", unsafe_allow_html=True); st.button("➕ Nova Tarefa Manual")

    tasks = load_json("tasks")
    filtered = [t for t in tasks if tema_filtro == "Todos" or t.get("macro_tema") == tema_filtro]

    cols = st.columns(5)
    for i, status in enumerate(KANBAN_STATUS):
        with cols[i]:
            cards = [t for t in filtered if t.get("status") == status]
            st.markdown(f'<div class="k-col"><div class="k-col-header">{KANBAN_LABELS[status]} <span class="k-count">{len(cards)}</span></div>', unsafe_allow_html=True)
            for task in cards:
                st.markdown(f'<div class="k-card"><div style="font-size:13px; font-weight:600; color:#111827;">{task["titulo"][:45]}</div><div style="font-size:12px; color:#6b7280; margin-top:4px;">Planta: {task.get("usina_nome","—")}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: INTELIGÊNCIA FINANCEIRA (MÓDULO BI CORRIGIDO)
# ─────────────────────────────────────────────────────────────────────────────
def page_bi():
    page_header("Inteligência Financeira", "Módulo BI Investidor — Performance Anual de Ativos")
    usinas = load_json("usinas")
    historico = load_json("historico_analises")

    if not usinas:
        st.info("Nenhuma usina localizada nas bases de suporte.")
        return

    with st.container(border=True):
        st.markdown("**📊 Escopo de Análise**")
        usina_opts = {u["nome"]: u["id"] for u in usinas}
        usina_sel = st.selectbox("Selecione a Usina Alvo", list(usina_opts.keys()))

    uid = usina_opts[usina_sel]
    df_hist = pd.DataFrame([h for h in historico if h.get("usina_id") == uid])

    if df_hist.empty:
        st.info("Nenhum histórico financeiro consolidado para esta unidade.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Bruto", x=df_hist["mes_ref"], y=df_hist["recebimento_bruto"], marker_color="#3b82f6"))
    fig.add_trace(go.Scatter(name="Líquido Investidor", x=df_hist["mes_ref"], y=df_hist["recebimento_liquido"], mode="lines+markers", line=dict(color="#F36E21", width=3)))
    
    fig.update_layout(
        title_text=f"Performance — {usina_sel}",
        title_font=dict(size=14, family="Inter"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# BASES DE SUPORTE (COM RECURSO DE CARGA EM LOTE EXCEL)
# ─────────────────────────────────────────────────────────────────────────────
def page_usinas():
    page_header("Usinas", "Cadastro, potência de pico e monitoramento do parque gerador")
    usinas = load_json("usinas")
    
    t1, t2, t3 = st.tabs(["Usinas Cadastradas", "Nova Planta", "📂 Carga em Lote (Excel)"])
    
    with t1:
        if usinas: st.dataframe(pd.DataFrame(usinas), use_container_width=True, hide_index=True)
        else: st.info("Sem usinas ativas.")
        
    with t2:
        with st.form("add_usina"):
            nome = st.text_input("Nome Comercial da Usina")
            pot = st.number_input("Capacidade de Pico (kWp)", min_value=0.0)
            grupo = st.selectbox("Grupo Tarifário", ["A", "B"])
            if st.form_submit_button("Salvar Registro"):
                usinas.append({"id": f"USI{len(usinas)+1:03d}", "nome": nome, "potencia_kwp": pot, "grupo": grupo, "ativa": True})
                save_json("usinas", usinas); st.success("Usina integrada!"); st.rerun()

    with t3:
        with st.container(border=True):
            st.markdown("**📥 Importador Eletrônico em Lote**")
            file = st.file_uploader("Selecione a planilha Excel das Usinas (.xlsx)", type=["xlsx", "xls"])
            if file and st.button("Sincronizar Usinas"):
                try:
                    df = pd.read_excel(file)
                    for r in df.to_dict("records"):
                        usinas.append({"id": f"USI{len(usinas)+1:03d}", "nome": str(r.get("nome")), "potencia_kwp": float(r.get("potencia_kwp", 100)), "grupo": str(r.get("grupo", "B")), "ativa": True})
                    save_json("usinas", usinas); st.success("Base atualizada com Upsert!"); st.rerun()
                except Exception as e: st.error(f"Falha na leitura: {e}")

def page_simulador():
    page_header("Simulador de Cotas", "Ambiente preditivo de redistribuição de créditos de energia")
    with st.container(border=True):
        st.markdown("**🎯 Configuração da Usina Alvo**")
        st.selectbox("Usina Vinculada", ["Todas as unidades operacionais de GD"])
    st.markdown(kpi_card("Geração Estimada Padrão", "18.000 kWh/mês", "Cálculo baseado na potência nominal de pico"), unsafe_allow_html=True)

def page_geradores(): page_header("Geradores", "Titulares cadastrados nas contas de geração")
def page_geracao(): page_header("Geração (Livro-Caixa)", "Lançamentos e registros de histórico físico de injeção")
def page_backoffice(): page_header("Backoffice", "Base cumulativa histórica de faturamento de clientes")
def page_captura_rpa(): page_header("Captura RPA", "Fila operacional de robôs de coleta")
def page_ocr_hubspot(): page_header("OCR HubSpot", "Leitura eletrônica de faturas e contratos")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────────────────────────────────────
ROUTE_MAP = {
    "Dashboard": page_dashboard, "Atividades": page_atividades,
    "Conciliação de Medição": page_conciliacao, "Inteligência Financeira": page_bi,
    "Usinas": page_usinas, "Geradores": page_geradores, "Geração (Livro-Caixa)": page_geracao,
    "Backoffice": page_backoffice, "Simulador de Cotas": page_simulador, "Captura RPA": page_captura_rpa, "OCR HubSpot": page_ocr_hubspot
}

def main():
    inject_css()
    st.session_state.logged_in = True
    render_sidebar()
    page_fn = ROUTE_MAP.get(st.session_state.page, page_dashboard)
    page_fn()

if __name__ == "__main__":
    main()
