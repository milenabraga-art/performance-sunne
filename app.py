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

# ── 2. CSS BACKOFFICE (BOTÕES LARANJA ESTÁTICOS - SEM BALÃO) ────────────────
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

/* Texto de saudação e separadores em branco */
[data-testid="stSidebar"] * { 
    color: white !important; 
}

/* BOTÕES DA SIDEBAR - LARANJA ESTÁTICO E PLANO (SEM BALÃO) */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: #F36E21 !important;
    color: white !important;
    border: none !important;
    padding: 10px 15px !important;
    border-radius: 5px !important; /* Bordas menos arredondadas para tirar o aspecto de balão */
    font-weight: 700 !important;
    margin-bottom: 10px !important;
    width: 100% !important;
    height: 45px !important;
    display: inline-flex !important;
    justify-content: center !important;
    box-shadow: none !important; /* Remove sombras/efeito balão */
}

/* Forçar a cor do texto das palavras nos botões */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
    color: white !important;
    font-size: 14px !important;
    font-weight: 700 !important;
}

/* Efeito Hover discreto */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background-color: #d65a1b !important;
}

/* KPIs e Cards */
.kpi-box { background: white; border-radius: 15px; padding: 1.2rem; border: 1px solid #EAD8D0; text-align: center; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: var(--rubi); }
.login-card { background: white; padding: 3rem; border-radius: 25px; box-shadow: 0 15px 35px rgba(51
