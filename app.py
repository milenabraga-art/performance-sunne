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

# ── 2. CSS BACKOFFICE (ORIGINAL INTOCADO + EXTENSÕES KANBAN) ─────────────────
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

/* Sidebar Rubi */
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

.kpi-box {
    background: white;
    border-radius: 15px;
    padding: 1.2rem;
    border: 1px solid #EAD8D0;
    text-align: center;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--rubi);
}
.login-card {
    background: white;
    padding: 3rem;
    border-radius: 25px;
    box-shadow: 0 15px 35px rgba(51,0,26,0.1);
    border: 1px solid #EAD8D0;
    max-width: 400px;
    margin: auto;
    text-align: center;
}

/* ── Kanban ── */
.kanban-card {
    background: white;
    border: 1px solid #EAD8D0;
    border-radius: 12px;
    padding: .85rem 1rem;
    margin-bottom: .65rem;
    font-size: 13px;
    box-shadow: 0 1px 4px rgba(51,0,26,.06);
}
.kanban-card .k-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 13px;
    color: var(--rubi);
    margin-bottom: 4px;
}
.kanban-card .k-meta {
    font-size: 11px;
    color: #7A5060;
    line-height: 1.6;
}
.kanban-card .k-motivo {
    font-size: 11px;
    color: #990000;
    margin-top: 4px;
    font-style: italic;
}
.kanban-header {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .07em;
    padding: .4rem .8rem;
    border-radius: 8px;
    margin-bottom: .85rem;
    display: block;
    text-align: center;
}
.col-aberto    { background:#FFF3EC; color:#C04010; }
.col-andamento { background:#FFF8E6; color:#7A5010; }
.col-travado   { background:#FFECEC; color:#990000; }
.col-concluido { background:#EDFCF9; color:#0A7A6A; }
.col-cancelado { background:#F3F3F3; color:#555555; }

.kanban-wrap {
    background: #FBF5F0;
    border-radius: 14px;
    border: 1px solid #EAD8D0;
    padding: 1rem;
    min-height: 160px;
}
</style>
"""

# ── 3. PERSISTÊNCIA ───────────────────────────────────────────────────────────
DB_DIR     = "database"
USERS_FILE = "users.json"
GER_FILE   = os.path.join(DB_DIR, "geradores.json")
USI_FILE   = os.path.join(DB_DIR, "usinas.json")
TASK_FILE  = os.path.join(DB_DIR, "tarefas.json")

os.makedirs(DB_DIR, exist_ok=True)

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
        default = {"users": [
            {"name": "Milena",   "email": "milena@sunne.com.br",   "password": "sunne2026", "role": "admin"},
            {"name": "Analista", "email": "analista@sunne.com.br", "password": "sunne2026", "role": "user"},
        ]}
        with open(USERS_FILE, "w") as f:
            json.dump(default, f, indent=2)
    with open(USERS_FILE) as f:
        return json.load(f).get("users", [])

def authenticate(email, password):
    for u in load_users():
        if u["email"].lower() == email.lower() and u["password"] == password:
            return u
    return None

# ── 5. GERADORES ──────────────────────────────────────────────────────────────
def load_geradores():           return _load(GER_FILE, [])
def save_geradores(data):       _save(GER_FILE, data)

# ── 6. USINAS ─────────────────────────────────────────────────────────────────
def load_usinas():              return _load(USI_FILE, [])
def save_usinas(data):          _save(USI_FILE, data)

# ── 7. TAREFAS ────────────────────────────────────────────────────────────────
def load_tarefas():             return _load(TASK_FILE, [])
def save_tarefas(data):         _save(TASK_FILE, data)

def add_tarefa(titulo, usina, gerador, analista, anexo=""):
    tarefas = load_tarefas()
    tarefas.append({
        "id":              datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "titulo":          titulo,
        "usina":           usina,
        "gerador":         gerador,
        "analista":        analista,
        "anexo":           anexo,
        "status":          "Em aberto",
        "motivo_bloqueio": "",
        "criado_em":       datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    save_tarefas(tarefas)

def update_tarefa(tid, **kwargs):
    tarefas = load_tarefas()
    for t in tarefas:
        if t["id"] == tid:
            t.update(kwargs)
    save_tarefas(tarefas)

# ── 8. UTILITÁRIOS DE DADOS (ORIGINAIS INTOCADOS) ────────────────────────────
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

def style_critical(row):
    dias = row['Dias de Atraso']
    if dias > 90:
        return ['background-color: #ffcccc; color: #990000; font-weight: bold'] * len(row)
    return ['background-color: #fff4cc; color: #856404; font-weight: bold'] * len(row)

# ── 9. ANÁLISE DE FATURAMENTO (ORIGINAL INTOCADA) ────────────────────────────
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
    except:
        return None

def analyze_performance(df_r, df_e):
    uc_r_col    = next((c for c in df_r.columns if "UC Nova"       in c), df_r.columns[0])
    uc_e_col    = next((c for c in df_e.columns if "Número da UC"  in c), df_e.columns[0])
    comp_col    = next((c for c in df_e.columns if "Competência"   in c), None)
    status_col  = next((c for c in df_e.columns if "Status"        in c), None)
    valor_col   = next((c for c in df_e.columns if "Total a Pagar" in c), None)
    titular_col = next((c for c in df_e.columns if "Titular"       in c), None)
    venc_col    = next((c for c in df_e.columns if "Vencimento"    in c), None)

    df_r['UC_NORM'] = df_r[uc_r_col].apply(normalize_uc)
    df_e['UC_NORM'] = df_e[uc_e_col].apply(normalize_uc)

    missing_res = {}; inad_res = {}
    t_gerado = {}; t_pago = {}; t_vencido = {}
    critical_inad = []
    hoje = datetime.now()

    if venc_col:
        df_e[venc_col] = pd.to_datetime(df_e[venc_col], errors='coerce', dayfirst=True)

    for _, row in df_e.iterrows():
        comp       = str(row[comp_col])    if comp_col    else "Geral"
        status     = str(row[status_col]).lower() if status_col else ""
        valor      = clean_val(row[valor_col])
        vencimento = row[venc_col]         if venc_col    else None

        t_gerado[comp] = t_gerado.get(comp, 0.0) + valor
        if "pago" in status:
            t_pago[comp] = t_pago.get(comp, 0.0) + valor

        if "vencido" in status:
            t_vencido[comp] = t_vencido.get(comp, 0.0) + valor
            item = {
                "uc":      row[uc_e_col],
                "valor":   valor,
                "titular": row[titular_col] if titular_col else "—",
            }
            if comp not in inad_res: inad_res[comp] = []
            inad_res[comp].append(item)

            if pd.notnull(vencimento):
                dias_atraso = (hoje - vencimento).days
                if dias_atraso > 60:
                    critical_inad.append({
                        "Titular":        item["titular"],
                        "UC":             item["uc"],
                        "Vencimento":     vencimento.strftime('%d/%m/%Y'),
                        "Dias de Atraso": dias_atraso,
                        "Valor":          valor,
                        "Mês Ref":        comp,
                    })

    critical_inad = sorted(critical_inad, key=lambda x: x['Dias de Atraso'], reverse=True)

    extrato_set = set(zip(df_e['UC_NORM'], df_e[comp_col].astype(str)))
    ucs_rateio  = df_r['UC_NORM'].unique()

    for comp in df_e[comp_col].unique():
        if not comp or str(comp).lower() == 'nan': continue
        for uc_norm in ucs_rateio:
            if (uc_norm, str(comp)) not in extrato_set:
                r_orig = df_r[df_r['UC_NORM'] == uc_norm].iloc[0]
                if comp not in missing_res: missing_res[comp] = []
                missing_res[comp].append({
                    "uc":      r_orig[uc_r_col],
                    "apelido": r_orig.get("Apelido UC", "—"),
                    "usina":   r_orig.get("Usina", "—"),
                })

    return {
        "missing":       missing_res,
        "inad":          inad_res,
        "t_gerado":      t_gerado,
        "t_pago":        t_pago,
        "t_vencido":     t_vencido,
        "critical_inad": critical_inad,
    }

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINAS
# ══════════════════════════════════════════════════════════════════════════════

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def page_dashboard():
    user     = st.session_state["user"]
    analista = user["name"]
    st.title("📊 Dashboard")

    gers   = [g for g in load_geradores() if g.get("analista","").lower() == analista.lower()]
    usis   = [u for u in load_usinas()    if u.get("analista","").lower() == analista.lower()]
    tarefas = load_tarefas()

    abertas   = [t for t in tarefas if t["status"] == "Em aberto"]
    andamento = [t for t in tarefas if t["status"] == "Em andamento"]
    travadas  = [t for t in tarefas if t["status"] == "Travado"]

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, label, val in zip(
        [c1, c2, c3, c4, c5],
        ["Geradores", "Usinas", "Em Aberto", "Em Andamento", "Travadas"],
        [len(gers), len(usis), len(abertas), len(andamento), len(travadas)],
    ):
        col.markdown(
            f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
            f'<div style="font-size:12px;color:#7A5060">{label}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.subheader("🕐 Tarefas em Aberto / Em Andamento")
    pendentes = abertas + andamento
    if pendentes:
        df_p = pd.DataFrame(pendentes)[["titulo","usina","gerador","analista","status","criado_em"]]
        df_p.columns = ["Título","Usina","Gerador","Analista","Status","Criado em"]
        st.dataframe(df_p, use_container_width=True, hide_index=True)
    else:
        st.success("Nenhuma tarefa pendente no momento.")


# ─── FATURAMENTO (ORIGINAL INTOCADO) ─────────────────────────────────────────
def page_faturamento():
    st.title("💳 Gestão de Faturamento")
    t1, t2, t3 = st.tabs(["📂 Importar", "🔍 Captura", "💳 Inadimplência"])

    with t1:
        c1, c2 = st.columns(2)
        f_r = c1.file_uploader("Rateio")
        f_e = c2.file_uploader("Extrato")
        if f_r and f_e and st.button("🔄 Rodar Análise"):
            st.session_state["results"] = analyze_performance(
                load_planilha(f_r), load_planilha(f_e)
            )
            st.success("✓ Concluído!")

    res = st.session_state.get("results")
    if res:
        with t2:
            for comp, items in res["missing"].items():
                with st.expander(f"⚠️ {comp} - {len(items)} faltantes"):
                    csv_data = csv_from_list(
                        items, ["uc","apelido","usina"], ["UC","Apelido","Usina"]
                    )
                    st.download_button(
                        f"⬇️ Baixar Lista de Faltantes ({comp})",
                        csv_data,
                        f"faltantes_{comp.replace('/','-')}.csv",
                        "text/csv",
                    )
                    st.table(pd.DataFrame(items))

        with t3:
            for comp, rows in res["inad"].items():
                gerado  = res["t_gerado"].get(comp, 0.0)
                vencido = res["t_vencido"].get(comp, 0.0)
                taxa    = (vencido / gerado * 100) if gerado > 0 else 0
                st.markdown(f"### {comp}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Gerado",        f"R$ {gerado:,.2f}")
                c2.metric("Vencido",       f"R$ {vencido:,.2f}")
                c3.metric("Inadimplência", f"{taxa:.1f}%")
                with st.expander(f"Ver lista de clientes inadimplentes ({comp})"):
                    st.table(pd.DataFrame(rows))

            st.write("---")
            st.markdown("## 🚨 Inadimplência Crítica (>60 dias)")
            st.info("Clientes abaixo possuem faturas com status 'vencido' há mais de 60 dias. "
                    "Devem ser avaliados para retirada do rateio.")
            if res["critical_inad"]:
                df_critico = pd.DataFrame(res["critical_inad"])
                st.dataframe(
                    df_critico.style.apply(style_critical, axis=1),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("Nenhum cliente com inadimplência superior a 60 dias encontrada.")


# ─── GERADORES ────────────────────────────────────────────────────────────────
def page_geradores():
    user     = st.session_state["user"]
    analista = user["name"]
    st.title("⚡ Geradores")

    tab_carteira, tab_import = st.tabs(["📋 Minha Carteira", "📥 Importar Planilha"])

    # ── Carteira do analista
    with tab_carteira:
        geradores      = load_geradores()
        minha_carteira = [g for g in geradores
                          if g.get("analista","").lower() == analista.lower()]

        if not minha_carteira:
            st.info("Nenhum gerador cadastrado para você. Use a aba 'Importar Planilha'.")
        else:
            c1, c2, c3 = st.columns(3)
            total_usinas_ger = sum(int(g.get("usinas", 0) or 0) for g in minha_carteira)
            concessoes = {g.get("concessionaria","") for g in minha_carteira if g.get("concessionaria")}
            c1.markdown(f'<div class="kpi-box"><div class="kpi-value">{len(minha_carteira)}</div>'
                        f'<div style="font-size:12px;color:#7A5060">Geradores</div></div>',
                        unsafe_allow_html=True)
            c2.markdown(f'<div class="kpi-box"><div class="kpi-value">{len(concessoes)}</div>'
                        f'<div style="font-size:12px;color:#7A5060">Concessionárias</div></div>',
                        unsafe_allow_html=True)
            c3.markdown(f'<div class="kpi-box"><div class="kpi-value">{total_usinas_ger}</div>'
                        f'<div style="font-size:12px;color:#7A5060">Usinas Totais</div></div>',
                        unsafe_allow_html=True)

            st.write("")
            opcoes = ["Todas"] + sorted(concessoes)
            filtro = st.selectbox("Filtrar por Concessionária", opcoes)
            lista  = (minha_carteira if filtro == "Todas"
                      else [g for g in minha_carteira if g.get("concessionaria") == filtro])

            df_show = pd.DataFrame(lista)
            colunas = [c for c in ["gerador","contato","concessionaria","usinas","porte","origem"]
                       if c in df_show.columns]
            df_show = df_show[colunas]
            df_show.columns = [c.capitalize() for c in colunas]
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    # ── Importar planilha
    with tab_import:
        st.markdown("**Colunas esperadas:** Gerador · Contato · Analista · Concessionária · Usinas · Porte · Origem")
        f = st.file_uploader("Selecionar arquivo", type=["xlsx","xls","csv"], key="up_ger")
        if f and st.button("💾 Salvar Geradores", key="btn_salvar_ger"):
            try:
                df = (pd.read_excel(f, dtype=str)
                      if not f.name.endswith(".csv")
                      else pd.read_csv(f, dtype=str))
                df.columns = df.columns.str.strip().str.lower()
                rename = {
                    "concessionária": "concessionaria",
                    "concessionaria": "concessionaria",
                }
                df.rename(columns=rename, inplace=True)
                df = df.fillna("")

                existentes     = load_geradores()
                existentes_nomes = {g["gerador"].lower() for g in existentes}
                novos = 0
                for _, row in df.iterrows():
                    nome = str(row.get("gerador","")).strip()
                    if nome and nome.lower() not in existentes_nomes:
                        existentes.append({
                            k: str(row.get(k,""))
                            for k in ["gerador","contato","analista","concessionaria","usinas","porte","origem"]
                        })
                        existentes_nomes.add(nome.lower())
                        novos += 1
                save_geradores(existentes)
                st.success(f"✅ {novos} gerador(es) importado(s) com sucesso!")
                st.rerun()
            except Exception as ex:
                st.error(f"Erro ao importar: {ex}")


# ─── USINAS ───────────────────────────────────────────────────────────────────
def page_usinas():
    user     = st.session_state["user"]
    analista = user["name"]
    st.title("🏭 Usinas")

    # ── Botões de ação
    col_a, col_b, _ = st.columns([1.4, 1.8, 6])
    if col_a.button("➕ Adicionar Manual"):
        st.session_state["show_add_usina"] = not st.session_state.get("show_add_usina", False)
    if col_b.button("📥 Importar Planilha"):
        st.session_state["show_imp_usina"] = not st.session_state.get("show_imp_usina", False)

    # ── Formulário: adicionar manual
    if st.session_state.get("show_add_usina"):
        with st.form("form_add_usina", clear_on_submit=True):
            st.subheader("Nova Usina")
            fa1, fa2 = st.columns(2)
            uc      = fa1.text_input("UC da Usina *")
            gerador = fa2.text_input("Gerador")
            fb1, fb2 = st.columns(2)
            ufv   = fb1.text_input("Nome UFV")
            ativa = fb2.selectbox("Ativa?", ["Sim","Não"])
            ok, cancel = st.columns(2)
            salvar   = ok.form_submit_button("✅ Salvar")
            cancelar = cancel.form_submit_button("Cancelar")

        if salvar:
            if not uc.strip():
                st.warning("O campo UC é obrigatório.")
            else:
                usinas = load_usinas()
                usinas.append({
                    "uc":       uc.strip(),
                    "gerador":  gerador.strip(),
                    "ufv":      ufv.strip(),
                    "analista": analista,
                    "ativa":    ativa,
                    "criado_em": datetime.now().strftime("%d/%m/%Y"),
                })
                save_usinas(usinas)
                st.session_state["show_add_usina"] = False
                st.success("✅ Usina adicionada!")
                st.rerun()
        if cancelar:
            st.session_state["show_add_usina"] = False
            st.rerun()

    # ── Formulário: importar planilha
    if st.session_state.get("show_imp_usina"):
        st.markdown("**Colunas esperadas:** UC · Gerador · UFV · Analista · Ativa")
        f = st.file_uploader("Arquivo de Usinas", type=["xlsx","xls","csv"], key="up_usi")
        ic1, ic2 = st.columns([1, 5])
        if ic1.button("Importar", key="btn_imp_usi"):
            if f:
                try:
                    df = (pd.read_excel(f, dtype=str)
                          if not f.name.endswith(".csv")
                          else pd.read_csv(f, dtype=str))
                    df.columns = df.columns.str.strip().str.lower()
                    df = df.fillna("")
                    usinas     = load_usinas()
                    ucs_exist  = {u["uc"] for u in usinas}
                    novos = 0
                    for _, row in df.iterrows():
                        uc_val = str(row.get("uc","")).strip()
                        if uc_val and uc_val not in ucs_exist:
                            usinas.append({
                                "uc":       uc_val,
                                "gerador":  str(row.get("gerador","")),
                                "ufv":      str(row.get("ufv","")),
                                "analista": analista,
                                "ativa":    str(row.get("ativa","Sim")),
                                "criado_em": datetime.now().strftime("%d/%m/%Y"),
                            })
                            ucs_exist.add(uc_val)
                            novos += 1
                    save_usinas(usinas)
                    st.session_state["show_imp_usina"] = False
                    st.success(f"✅ {novos} usina(s) importada(s)!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erro: {ex}")
        if ic2.button("Fechar", key="btn_close_usi"):
            st.session_state["show_imp_usina"] = False
            st.rerun()

    st.write("---")

    # ── Listagem
    usinas = load_usinas()
    minhas = [u for u in usinas if u.get("analista","").lower() == analista.lower()]

    if not minhas:
        st.info("Nenhuma usina cadastrada para você ainda.")
        return

    # Filtro por gerador
    ger_opts = ["Todos"] + sorted({u.get("gerador","—") for u in minhas})
    filtro   = st.selectbox("Filtrar por Gerador", ger_opts)
    lista    = minhas if filtro == "Todos" else [u for u in minhas if u.get("gerador") == filtro]

    # Cabeçalho
    h = st.columns([1.4, 1.8, 2.2, 1.6, 0.8, 0.5])
    for col, txt in zip(h, ["UC","Gerador","UFV","Analista","Ativa","📝"]):
        col.markdown(f"**{txt}**")
    st.markdown("<hr style='margin:4px 0 6px'>", unsafe_allow_html=True)

    # Linhas
    for idx, u in enumerate(lista):
        r = st.columns([1.4, 1.8, 2.2, 1.6, 0.8, 0.5])
        r[0].write(u.get("uc","—"))
        r[1].write(u.get("gerador","—"))
        r[2].write(u.get("ufv","—"))
        r[3].write(u.get("analista","—"))
        r[4].write("✅" if u.get("ativa","Sim") == "Sim" else "❌")
        if r[5].button("📝", key=f"ativ_{idx}_{u['uc']}"):
            st.session_state["ativ_usina"]   = u.get("uc","")
            st.session_state["ativ_gerador"] = u.get("gerador","")
            st.session_state["show_nova_ativ"] = True

    # ── Formulário nova atividade (aparece ao clicar 📝)
    if st.session_state.get("show_nova_ativ"):
        st.write("---")
        st.subheader("📝 Criar Nova Atividade")
        with st.form("form_nova_ativ", clear_on_submit=True):
            na1, na2 = st.columns(2)
            na1.text_input("Usina",   value=st.session_state.get("ativ_usina",""),   disabled=True, key="dis_usina")
            na2.text_input("Gerador", value=st.session_state.get("ativ_gerador",""), disabled=True, key="dis_ger")
            titulo = st.text_input("Título da Tarefa *")
            anexo  = st.text_input("Anexo (link ou descrição) — opcional")
            nb1, nb2 = st.columns(2)
            ok_form  = nb1.form_submit_button("✅ Criar Tarefa")
            nok_form = nb2.form_submit_button("Cancelar")

        if ok_form:
            if not titulo.strip():
                st.warning("O título é obrigatório.")
            else:
                add_tarefa(
                    titulo.strip(),
                    st.session_state.get("ativ_usina",""),
                    st.session_state.get("ativ_gerador",""),
                    analista,
                    anexo.strip(),
                )
                st.session_state["show_nova_ativ"] = False
                st.success("✅ Tarefa criada! Veja em 'Atividades'.")
                st.rerun()
        if nok_form:
            st.session_state["show_nova_ativ"] = False
            st.rerun()


# ─── KANBAN DE ATIVIDADES ─────────────────────────────────────────────────────
STATUS_LIST    = ["Em aberto", "Em andamento", "Travado", "Concluido", "Cancelado"]
MOTIVO_OBRIG   = {"Travado", "Cancelado"}
STATUS_CSS     = {
    "Em aberto":    "col-aberto",
    "Em andamento": "col-andamento",
    "Travado":      "col-travado",
    "Concluido":    "col-concluido",
    "Cancelado":    "col-cancelado",
}

def page_atividades():
    st.title("📋 Gerenciamento de Atividades")

    # ── Botão nova tarefa avulsa
    if st.button("➕ Nova Tarefa Avulsa"):
        st.session_state["show_avulsa"] = not st.session_state.get("show_avulsa", False)

    if st.session_state.get("show_avulsa"):
        with st.form("form_avulsa", clear_on_submit=True):
            av1, av2 = st.columns(2)
            titulo  = av1.text_input("Título *")
            usina   = av1.text_input("Usina")
            gerador = av2.text_input("Gerador")
            anexo   = av2.text_input("Anexo — opcional")
            ok_av, no_av = st.columns(2)
            sub_av = ok_av.form_submit_button("Criar")
            can_av = no_av.form_submit_button("Cancelar")
        if sub_av and titulo.strip():
            add_tarefa(titulo.strip(), usina, gerador,
                       st.session_state["user"]["name"], anexo)
            st.session_state["show_avulsa"] = False
            st.rerun()
        if can_av:
            st.session_state["show_avulsa"] = False
            st.rerun()

    # ── Filtros
    st.write("")
    fc1, fc2 = st.columns(2)
    f_analista = fc1.text_input("Filtrar por Analista", placeholder="em branco = todos")
    f_gerador  = fc2.text_input("Filtrar por Gerador",  placeholder="em branco = todos")

    def match(t):
        if f_analista and f_analista.lower() not in t.get("analista","").lower(): return False
        if f_gerador  and f_gerador.lower()  not in t.get("gerador","").lower():  return False
        return True

    tarefas = [t for t in load_tarefas() if match(t)]

    st.write("---")

    # ── Board: 5 colunas
    cols = st.columns(5)

    for col_ui, status in zip(cols, STATUS_LIST):
        css_cls = STATUS_CSS[status]
        grupo   = [t for t in tarefas if t["status"] == status]

        with col_ui:
            st.markdown(
                f'<span class="kanban-header {css_cls}">{status} ({len(grupo)})</span>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="kanban-wrap">', unsafe_allow_html=True)

            if not grupo:
                st.markdown(
                    '<p style="font-size:12px;color:#bbb;text-align:center;padding:.75rem 0">Vazio</p>',
                    unsafe_allow_html=True,
                )

            for t in grupo:
                tid = t["id"]
                motivo_html = (
                    f'<div class="k-motivo">🔒 {t["motivo_bloqueio"]}</div>'
                    if t.get("motivo_bloqueio") else ""
                )
                st.markdown(f"""
                <div class="kanban-card">
                    <div class="k-title">{t['titulo']}</div>
                    <div class="k-meta">
                        🏭 {t.get('usina','—')}<br>
                        ⚡ {t.get('gerador','—')}<br>
                        👤 {t.get('analista','—')}<br>
                        📅 {t.get('criado_em','')}
                    </div>
                    {motivo_html}
                </div>
                """, unsafe_allow_html=True)

                # Selectbox de destino + botão mover
                opcoes_dest = [s for s in STATUS_LIST if s != status]
                dest = st.selectbox(
                    "Mover para",
                    opcoes_dest,
                    key=f"dest_{tid}",
                    label_visibility="collapsed",
                )
                if st.button("↗ Mover", key=f"mv_{tid}"):
                    if dest in MOTIVO_OBRIG:
                        # Pedir motivo antes de mover
                        st.session_state[f"pede_motivo_{tid}"] = dest
                    else:
                        update_tarefa(tid, status=dest, motivo_bloqueio="")
                        st.rerun()

                # ── Pedido de motivo (inline, abaixo do card)
                if st.session_state.get(f"pede_motivo_{tid}"):
                    destino_alvo = st.session_state[f"pede_motivo_{tid}"]
                    motivo_txt = st.text_area(
                        f"Motivo para mover para '{destino_alvo}' *",
                        key=f"mot_{tid}",
                    )
                    mc1, mc2 = st.columns(2)
                    if mc1.button("Confirmar", key=f"conf_{tid}"):
                        if motivo_txt.strip():
                            update_tarefa(tid, status=destino_alvo,
                                          motivo_bloqueio=motivo_txt.strip())
                            del st.session_state[f"pede_motivo_{tid}"]
                            st.rerun()
                        else:
                            st.warning("O motivo é obrigatório.")
                    if mc2.button("Cancelar ação", key=f"cno_{tid}"):
                        del st.session_state[f"pede_motivo_{tid}"]
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown(SUNNE_CSS, unsafe_allow_html=True)

    # ── Tela de login
    if "user" not in st.session_state:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        try:
            st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        except:
            st.markdown("### ☀️ Sunne")
        with st.form("login"):
            e = st.text_input("E-mail", value="milena@sunne.com.br")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Hub", use_container_width=True):
                u = authenticate(e, s)
                if u:
                    st.session_state["user"] = u
                    st.session_state.setdefault("page", "dash")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Sidebar navegação (minimalista - somente texto)
    with st.sidebar:
        try:
            st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=120)
        except:
            st.markdown("### ☀️ Sunne")

        st.write(f"Olá, {st.session_state['user']['name']} 👋")
        st.write("---")

        st.session_state.setdefault("page", "dash")

        nav = [
            ("dash",        "Dashboard"),
            ("geradores",   "Geradores"),
            ("usinas",      "Usinas"),
            ("atividades",  "Atividades"),
            ("faturamento", "Faturamento"),
        ]
        for key, label in nav:
            if st.button(label, key=f"nav_{key}"):
                st.session_state["page"] = key

        st.write("---")
        if st.button("Sair", key="nav_sair"):
            # Limpa sessão mas preserva session_state base
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── Roteamento
    page = st.session_state.get("page", "dash")
    if   page == "dash":        page_dashboard()
    elif page == "geradores":   page_geradores()
    elif page == "usinas":      page_usinas()
    elif page == "atividades":  page_atividades()
    elif page == "faturamento": page_faturamento()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
