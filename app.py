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

# ── 2. CSS CUSTOMIZADO (BACKOFFICE SUNNE STYLE) ──────────────────────────────
SUNNE_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

/* Reset Geral */
[data-testid="stAppViewContainer"] { background-color: #F8F9FA; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; }

/* Barra Superior (Top Bar) */
.top-header {
    background-color: #33001A;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 30px;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 999;
}
.header-left { display: flex; align-items: center; gap: 15px; }
.header-right { color: white; display: flex; align-items: center; gap: 8px; cursor: pointer; }

/* Menu Lateral (Sidebar / Abas) */
[data-testid="stSidebar"] {
    background-color: white !important;
    border-right: 1px solid #E0E0E0;
    padding-top: 80px !important;
}
[data-testid="stSidebarNav"] { display: none; } /* Esconde o padrão */

.menu-item {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 15px;
    color: #666;
    text-decoration: none;
    font-size: 14px;
    transition: 0.3s;
    border-left: 4px solid transparent;
}
.menu-item:hover { background-color: #FFF5F0; color: #F36E21; }
.menu-item-active { 
    background-color: #FFF5F0; 
    color: #F36E21 !important; 
    border-left: 4px solid #F36E21;
    font-weight: 700;
}

/* Card de Perfil (Igual à imagem 2) */
.profile-card {
    background: white;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    position: fixed;
    top: 70px; right: 20px;
    width: 300px;
    z-index: 1000;
    border: 1px solid #EEE;
}
.profile-name { font-weight: 700; font-size: 16px; color: #333; margin-bottom: 2px; }
.profile-email { font-size: 13px; color: #888; margin-bottom: 15px; }
.profile-action {
    padding: 10px 0;
    border-top: 1px solid #F5F5F5;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: #333;
    cursor: pointer;
}

/* Tabelas e Botões */
.stButton>button { background-color: #F36E21 !important; color: white !important; border-radius: 8px !important; border: none !important; }
.sunne-table th { background-color: #F8F9FA !important; color: #666 !important; text-transform: uppercase; font-size: 11px; }

/* Login */
.login-box {
    max-width: 400px; margin: 100px auto; padding: 40px;
    background: white; border-radius: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.05);
    text-align: center; border: 1px solid #F0F0F0;
}
</style>
"""

# ── 3. FUNÇÕES DE INFRAESTRUTURA ─────────────────────────────────────────────
USERS_FILE = "users_db.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        initial = [{"name": "Milena Braga", "email": "milena.braga@sunne.com.br", "password": "sunne2026", "role": "admin"}]
        with open(USERS_FILE, "w") as f: json.dump(initial, f)
        return initial
    with open(USERS_FILE, "r") as f: return json.load(f)

def clean_val(v):
    if not v: return 0.0
    s = str(v).replace("R$", "").replace(" ", "").strip()
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

# ── 4. LÓGICA DE LOGIN & HEADER ──────────────────────────────────────────────
def main():
    st.markdown(SUNNE_THEME_CSS, unsafe_allow_html=True)
    
    if "user_data" not in st.session_state:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.image("https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png", width=150) # Logo real
        st.markdown("<h3 style='margin-top:20px'>Sunne Hub</h3>", unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail corporativo")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Sistema", use_container_width=True):
                users = load_users()
                found = next((u for u in users if u["email"] == e and u["password"] == s), None)
                if found:
                    st.session_state["user_data"] = found
                    st.rerun()
                else: st.error("Credenciais inválidas.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    user = st.session_state["user_data"]

    # Barra Superior (Header)
    st.markdown(f"""
        <div class="top-header">
            <div class="header-left">
                <img src="https://ops.sunne.com.br/static/media/logo-sunne.9e4fbe.png" height="30">
            </div>
            <div class="header-right">
                {user['name']} ▾
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Menu Lateral (Aparecia de Abas)
    with st.sidebar:
        st.markdown(f'<div style="height:20px"></div>', unsafe_allow_html=True)
        
        # Simulação das abas da imagem 1
        menu_items = {
            "📊 Faturamento": "performance",
            "📈 Rateio": "rateio",
            "👥 Usuários": "usuarios",
            "⚙️ Configurações": "configs"
        }
        
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "performance"
            
        for label, page in menu_items.items():
            is_active = "menu-item-active" if st.session_state["current_page"] == page else ""
            if st.button(label, key=f"btn_{page}", use_container_width=True):
                st.session_state["current_page"] = page
                st.rerun()

    # Conteúdo Principal (Ajuste de margem por causa do Header Fixo)
    st.markdown('<div style="height:80px"></div>', unsafe_allow_html=True)
    
    page = st.session_state["current_page"]

    # ── ABA: FATURAMENTO (PERFORMANCE) ──────────────────────────────────────────
    if page == "performance":
        st.markdown("### 📊 Análise de Performance")
        
        # Filtros (Estilo imagem 1)
        with st.expander("🔍 Filtros Avançados", expanded=True):
            c1, c2, c3 = st.columns(3)
            search_uc = c1.text_input("Buscar pela UC", placeholder="Ex: 58730075")
            comp_filter = c2.selectbox("Competência", ["Todas", "03/2026", "02/2026", "01/2026"])
            status_filter = c3.selectbox("Status", ["Todos", "Vencido", "Pago", "Cancelado"])
            st.button("Buscar", type="primary")

        # Tabs de funcionalidade interna
        t1, t2 = st.tabs(["📂 Importar Planilhas", "💳 Inadimplência"])
        
        with t1:
            st.info("Suba os arquivos para processar os dados.")
            c1, c2 = st.columns(2)
            f_r = c1.file_uploader("Rateio")
            f_e = c2.file_uploader("Extrato")
            if f_r and f_e:
                if st.button("🔄 Rodar Análise"):
                    st.success("Dados carregados com sucesso!")

    # ── ABA: USUÁRIOS (GERENCIAMENTO) ──────────────────────────────────────────
    elif page == "usuarios":
        st.markdown("### 👥 Gestão de Analistas")
        # Visual do card de perfil para teste
        with st.expander("Visualizar Perfil (Exemplo da Imagem 2)"):
            st.markdown(f"""
                <div style="background:white; padding:20px; border-radius:15px; border:1px solid #EEE;">
                    <div class="profile-name">{user['name']}</div>
                    <div class="profile-email">{user['email']}</div>
                    <div class="profile-action">📑 Termos de Uso</div>
                    <div class="profile-action">🚀 Ir para Workspaces</div>
                    <div class="profile-action" style="color:red">➡️ Sair</div>
                </div>
            """, unsafe_allow_html=True)

    # Botão de Logoff (Simulando o card da imagem 2)
    if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
        del st.session_state["user_data"]
        st.rerun()

if __name__ == "__main__":
    main()
