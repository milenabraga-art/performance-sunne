"""
rateio_sunne_bot.py  ·  Sincronização de Rateios Ativos – rateios.sunne.com.br
===============================================================================
Roda automaticamente às 07h via verificar_agendamento_rateio().
Dependências: selenium>=4.18.0, webdriver-manager>=4.0.1
Secrets (.streamlit/secrets.toml):
    [sunne_rateios]
    email    = "milena.braga@sunne.com.br"
    password = "Milena1968@"
"""
from __future__ import annotations
import io, json, os, re, time, traceback
from datetime import datetime
from typing import Optional

import streamlit as st

DB                   = "database"
RATEIO_ATIVO_FILE    = f"{DB}/rateios_ativos_sunne.json"
RATEIO_SYNC_SCHED    = f"{DB}/rateio_sync_schedule.json"
RATEIO_SYNC_LOG      = f"{DB}/rateio_sync_log.json"

os.makedirs(DB, exist_ok=True)

PORTAL_URL  = "https://rateios.sunne.com.br"
LOGIN_URL   = f"{PORTAL_URL}/login"
TIMEOUT     = 20

try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    SELENIUM_OK = True
except ImportError:
    SELENIUM_OK = False


# ─── JSON helpers ─────────────────────────────────────────────────────────────

def _load(path, default):
    if not os.path.exists(path):
        _save(path, default)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def load_rateios_ativos():   return _load(RATEIO_ATIVO_FILE, [])
def save_rateios_ativos(d):  _save(RATEIO_ATIVO_FILE, d)
def load_sync_schedule():    return _load(RATEIO_SYNC_SCHED, {"hora":"07:00","ultima":"","auto":True})
def save_sync_schedule(d):   _save(RATEIO_SYNC_SCHED, d)
def load_sync_log():         return _load(RATEIO_SYNC_LOG, [])
def save_sync_log(d):        _save(RATEIO_SYNC_LOG, d)


# ─── Chrome driver ────────────────────────────────────────────────────────────

def _build_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    for candidate in ["/usr/bin/chromium-browser","/usr/bin/chromium","/usr/bin/google-chrome"]:
        if os.path.exists(candidate):
            opts.binary_location = candidate
            break
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        svc = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    except Exception:
        for cd in ["/usr/bin/chromedriver","/usr/local/bin/chromedriver"]:
            if os.path.exists(cd): svc = Service(cd); break
        else: svc = Service()
    return webdriver.Chrome(service=svc, options=opts)


def _wait_click(driver, by, selector, timeout=TIMEOUT):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.2); el.click(); return el


# ─── Login no portal de rateios ───────────────────────────────────────────────

def _login_rateios(driver, email: str, senha: str) -> bool:
    try:
        driver.get(LOGIN_URL)
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'],input[type='text']"))
        )
        time.sleep(1.5)
        inp_e = driver.find_element(By.CSS_SELECTOR,
            "input[type='email'],input[formcontrolname='email'],input[placeholder*='mail']")
        inp_e.clear(); inp_e.send_keys(email)
        inp_s = driver.find_element(By.CSS_SELECTOR,
            "input[type='password'],input[formcontrolname='password']")
        inp_s.clear(); inp_s.send_keys(senha)
        try:
            _wait_click(driver, By.CSS_SELECTOR, ".mat-mdc-button-touch-target")
        except Exception:
            inp_s.send_keys(Keys.RETURN)
        time.sleep(3)
        return "login" not in driver.current_url.lower()
    except Exception:
        return False


# ─── Extrair rateio ativo de uma UG ──────────────────────────────────────────

def _buscar_rateio_ug(driver, ug: str) -> Optional[dict]:
    """
    Navega na tela de consulta de rateios ativos, busca pela UG e extrai os dados.
    Retorna dict com os campos disponíveis ou None se não encontrado.
    """
    try:
        # Tenta localizar campo de busca
        inp = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "input[placeholder*='UG'],input[placeholder*='ug'],input[placeholder*='Buscar'],"
                "input[placeholder*='buscar'],input[placeholder*='número'],mat-form-field input"
            ))
        )
        inp.clear(); inp.send_keys(ug)
        time.sleep(2)

        # Aguarda resultado
        rows = driver.find_elements(By.CSS_SELECTOR, "mat-row,tr.mat-row,.list-item,.card-rateio")
        if not rows:
            # Tenta verificar se retornou vazio
            vazios = driver.find_elements(By.XPATH,
                "//*[contains(text(),'Nenhum') or contains(text(),'nenhum') or contains(text(),'vazio')]")
            if vazios:
                return None
            return None

        # Extrai texto da primeira linha
        row = rows[0]
        cells = row.find_elements(By.CSS_SELECTOR, "mat-cell,td")

        # Tenta extrair porcentagens e UC beneficiárias via texto da linha
        row_text = row.text

        # Estrutura genérica — parseia o texto
        dados = {
            "ug":          ug,
            "texto_bruto": row_text[:500],
            "coletado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "beneficiarios": [],
        }

        # Tenta clicar para expandir e ver lista de UCs + percentuais
        try:
            btn_det = row.find_element(By.CSS_SELECTOR,
                "button,mat-icon,.mat-icon,[class*='detail'],[class*='expand']")
            driver.execute_script("arguments[0].click();", btn_det)
            time.sleep(1.5)

            # Captura linhas de beneficiários
            sub_rows = driver.find_elements(By.CSS_SELECTOR,
                ".beneficiario-row,mat-expansion-panel-content mat-row,tr.sub-row")
            for sr in sub_rows:
                sr_text = sr.text
                nums = re.findall(r"\d[\d.,]+", sr_text)
                if nums:
                    dados["beneficiarios"].append({
                        "texto": sr_text[:200],
                        "valores": nums[:5],
                    })
        except Exception:
            pass

        # Tenta extrair percentuais do texto bruto
        pcts = re.findall(r"(\d{1,3}[,.]\d{1,4})\s*%", row_text)
        if pcts:
            dados["percentuais_encontrados"] = pcts

        # Limpa o campo de busca para próxima UG
        try:
            inp.clear(); inp.send_keys(Keys.ESCAPE)
        except Exception:
            pass

        return dados

    except Exception as e:
        return {"ug": ug, "erro": str(e)[:200], "coletado_em": datetime.now().strftime("%d/%m/%Y %H:%M")}


# ─── Navegar para tela de rateios ativos ─────────────────────────────────────

def _navegar_rateios(driver) -> bool:
    """Tenta acessar a tela de consulta de rateios ativos."""
    try:
        # Tenta acessar diretamente URLs prováveis
        for path in ["/rateios", "/consulta", "/rateios/ativos", "/home", "/"]:
            driver.get(f"{PORTAL_URL}{path}")
            time.sleep(2)
            if "login" not in driver.current_url.lower():
                return True
        return False
    except Exception:
        return False


# ─── Varredura completa ───────────────────────────────────────────────────────

def executar_sync_rateios(
    progress_cb=None,
    log_cb=None,
    ugs_alvo: list = None,
) -> list:
    """
    Sincroniza os rateios ativos de todas as UGs cadastradas em usinas.json.
    Retorna lista de resultados.
    """
    if not SELENIUM_OK:
        raise RuntimeError("Selenium não instalado.")

    try:
        email = st.secrets["sunne_rateios"]["email"]
        senha = st.secrets["sunne_rateios"]["password"]
    except Exception:
        email = os.environ.get("SUNNE_RATEIOS_EMAIL", "milena.braga@sunne.com.br")
        senha = os.environ.get("SUNNE_RATEIOS_SENHA", "Milena1968@")

    # Carrega UGs das usinas cadastradas
    try:
        with open(f"{DB}/usinas.json", encoding="utf-8") as f:
            usinas = json.load(f)
    except Exception:
        usinas = []

    ugs = [str(u.get("uc","")).strip() for u in usinas if u.get("uc","")]
    if ugs_alvo:
        ugs = [u for u in ugs if u in ugs_alvo]
    if not ugs:
        return [{"ug":"—","status":"erro","obs":"Nenhuma UG cadastrada."}]

    resultados  = []
    novos_ativos = load_rateios_ativos()
    driver = None

    try:
        if progress_cb: progress_cb(0.05, "⚙️ Iniciando Chrome…")
        driver = _build_driver()

        if progress_cb: progress_cb(0.10, "🔐 Login no portal de rateios…")
        ok = _login_rateios(driver, email, senha)
        if not ok:
            resultados.append({"ug":"—","status":"erro","obs":"Falha no login."})
            return resultados

        if progress_cb: progress_cb(0.15, "📂 Navegando para rateios ativos…")
        _navegar_rateios(driver)

        total = len(ugs)
        for idx, ug in enumerate(ugs):
            pct = 0.15 + (idx / total) * 0.80
            if progress_cb: progress_cb(pct, f"🔍 UG {ug} ({idx+1}/{total})")

            dados = _buscar_rateio_ug(driver, ug)

            if dados is None:
                entry = {"ug":ug,"status":"não_encontrado","obs":"Sem rateio ativo","coletado_em":datetime.now().strftime("%d/%m/%Y %H:%M")}
            elif "erro" in dados:
                entry = {"ug":ug,"status":"erro","obs":dados["erro"],"coletado_em":dados.get("coletado_em","")}
            else:
                entry = {"ug":ug,"status":"sincronizado",**dados}
                # Upsert em rateios_ativos
                novos_ativos = [r for r in novos_ativos if str(r.get("ug","")) != ug]
                novos_ativos.append(entry)

            resultados.append(entry)
            # Log
            hist = load_sync_log(); hist.insert(0, entry); save_sync_log(hist[:300])
            if log_cb: log_cb(entry)

        save_rateios_ativos(novos_ativos)

    except Exception as e:
        resultados.append({"ug":"—","status":"erro_geral","obs":traceback.format_exc()[:400]})
    finally:
        if driver:
            try: driver.quit()
            except Exception: pass

    if progress_cb: progress_cb(1.0, "✅ Sincronização concluída!")
    return resultados


# ─── Agendamento 07h ──────────────────────────────────────────────────────────

def verificar_agendamento_rateio() -> bool:
    sched = load_sync_schedule()
    if not sched.get("auto", True): return False
    hora_alvo = sched.get("hora","07:00")
    ultima    = sched.get("ultima","")
    agora     = datetime.now()
    hora_str  = agora.strftime("%H:%M")
    hoje_str  = agora.strftime("%Y-%m-%d")
    if hora_str == hora_alvo and ultima != hoje_str:
        sched["ultima"] = hoje_str
        save_sync_schedule(sched)
        return True
    return False
