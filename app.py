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

# ── 2. CSS BACKOFFICE (BOTÕES LARANJA ESTÁTICOS E SIDEBAR RUBI) ──────────────
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

/* FORÇAR TEXTO BRANCO NA SIDEBAR */
[data-testid="stSidebar"] * { 
    color: white !important; 
}

/* BOTÕES DA SIDEBAR - LARANJA ESTÁTICO (COR FIXA) */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] button {
    background-color: #F36E21 !important;
    color: white !important;
    border: 1px solid #F36E21 !important;
    padding: 10px 15px !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    margin-bottom: 10px !important;
    width: 100% !important;
    display: inline-flex !important;
    justify-content: center !important;
}

/* Garantir texto branco dentro do botão */
[data-testid="stSidebar"] button p {
    color: white !important;
    font-weight: 700 !important;
}

/* Hover para feedback */
[data-testid="stSidebar"] button:hover {
    background-color: #ff8342 !important;
    border-color: #ff8342 !important;
}

/* KPIs */
.kpi-box { background: white; border-radius: 15px; padding: 1.2rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: var(--rubi); }

/* Login */
.login-card {
    background: white; padding: 3rem; border-radius: 25px;
    box-shadow: 0 15px 35px rgba(51, 0, 26, 0.1);
    border: 1px solid #EAD8D0; max-width: 400px; margin: auto; text-align: center;
}
</style>
"""

# ── 3. UTILITÁRIOS E SEGURANÇA ────────────────────────────────────────────────
USERS_FILE = "users.json"
TODAY = datetime.now()
DELAY_DAYS = 40 

def load_users():
    if not os.path.exists(USERS_FILE):
        default = {"users": [{"name": "Milena", "email": "milena@sunne.com.br", "password": "sunne2026", "role": "admin"}]}
        with open(USERS_FILE, "w") as f: json.dump(default, f, indent=2)
    with open(USERS_FILE) as f: return json.load(f).get("users", [])

def authenticate(email, password):
    for u in load_users():
        if u["email"].lower() == email.lower() and u["password"] == password: return u
    return None

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

# ── 4. LÓGICA DE ANÁLISE ─────────────────────────────────────────────────────
def load_planilha(file):
    if file is None: return None
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.csv') else pd.read_csv(file, header=None, sep=None, engine='python')
        for i, row in df.head(20).iterrows():
            row_l = [str(
