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
        with open(USERS
