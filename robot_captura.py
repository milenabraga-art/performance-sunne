"""
robot_captura.py  ·  Módulo RPA – Captura automática de faturas  ·  Sunne Hub v7
=================================================================================
Dependências (requirements.txt):
    selenium>=4.18.0
    webdriver-manager>=4.0.1
    pdfplumber>=0.11.0

Dependências (packages.txt – Streamlit Cloud):
    chromium-driver
    chromium

Secrets (.streamlit/secrets.toml):
    [sunne_portal]
    email    = "milena.braga@sunne.com.br"
    password = "Milena@2025"
"""

from __future__ import annotations
import io, json, os, re, time, traceback
from datetime import datetime
from typing import Optional

import pdfplumber
import streamlit as st

# ─── Selenium / Chrome ───────────────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.common.exceptions import (
        NoSuchElementException, TimeoutException, WebDriverException,
    )
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    SELENIUM_OK = True
except ImportError:
    SELENIUM_OK = False

# ─── Paths ───────────────────────────────────────────────────────────────────
DB               = "database"
GERACAO_FILE     = f"{DB}/geracao_usinas.json"
ROBOT_LOG_FILE   = f"{DB}/robot_log.json"
ROBOT_TEMPLATES  = f"{DB}/pdf_templates.json"   # aprendizado de layout
ROBOT_SCHEDULE   = f"{DB}/robot_schedule.json"  # agendamento 08h

os.makedirs(DB, exist_ok=True)

# ─── Constantes portal ───────────────────────────────────────────────────────
PORTAL_URL   = "https://ops.sunne.com.br"
LOGIN_URL    = f"{PORTAL_URL}/login"
TIMEOUT      = 20  # segundos WebDriverWait

MESES_PT = {
    1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
    7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro",
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS JSON
# ─────────────────────────────────────────────────────────────────────────────

def _load(path, default):
    if not os.path.exists(path):
        _save(path, default)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def load_geracao():   return _load(GERACAO_FILE, [])
def save_geracao(d):  _save(GERACAO_FILE, d)
def load_log():       return _load(ROBOT_LOG_FILE, [])
def save_log(d):      _save(ROBOT_LOG_FILE, d)
def load_templates(): return _load(ROBOT_TEMPLATES, {})
def save_templates(d):_save(ROBOT_TEMPLATES, d)
def load_schedule():  return _load(ROBOT_SCHEDULE, {"hora":"08:00","ultima_execucao":None,"auto":False})
def save_schedule(d): _save(ROBOT_SCHEDULE, d)
def load_usinas():    return _load(f"{DB}/usinas.json", [])


# ─────────────────────────────────────────────────────────────────────────────
# CHROME DRIVER FACTORY
# ─────────────────────────────────────────────────────────────────────────────

def _build_driver() -> webdriver.Chrome:
    """Cria o Chrome headless compatível com Streamlit Cloud."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    # Chromium do sistema (Streamlit Cloud / Debian)
    for candidate in [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
    ]:
        if os.path.exists(candidate):
            opts.binary_location = candidate
            break
    # ChromeDriver via webdriver-manager com fallback para sistema
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        svc = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    except Exception:
        for cd in ["/usr/bin/chromedriver","/usr/local/bin/chromedriver"]:
            if os.path.exists(cd):
                svc = Service(cd); break
        else:
            svc = Service()
    return webdriver.Chrome(service=svc, options=opts)


def _wait(driver, by, selector, timeout=TIMEOUT):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))

def _click(driver, by, selector, timeout=TIMEOUT):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.3)
    el.click()
    return el


# ─────────────────────────────────────────────────────────────────────────────
# FLUXO DE LOGIN
# ─────────────────────────────────────────────────────────────────────────────

def _login(driver, email: str, senha: str) -> bool:
    try:
        driver.get(LOGIN_URL)
        _wait(driver, By.CSS_SELECTOR, "input[type='email'], input[type='text']")
        time.sleep(1.5)

        # E-mail
        inp_email = driver.find_element(By.CSS_SELECTOR,
            "input[type='email'], input[formcontrolname='email'], input[placeholder*='mail']")
        inp_email.clear(); inp_email.send_keys(email)

        # Senha
        inp_senha = driver.find_element(By.CSS_SELECTOR,
            "input[type='password'], input[formcontrolname='password']")
        inp_senha.clear(); inp_senha.send_keys(senha)

        # Botão login — Material MDC
        try:
            _click(driver, By.CSS_SELECTOR, ".mat-mdc-button-touch-target")
        except Exception:
            inp_senha.send_keys(Keys.RETURN)

        time.sleep(3)
        return "login" not in driver.current_url.lower()
    except Exception as e:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# NAVEGAR ATÉ FATURAS DAS UGs
# ─────────────────────────────────────────────────────────────────────────────

def _navegar_para_faturas(driver) -> bool:
    try:
        # Clica em Faturamento (ícone request_quote)
        faturamento = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH,
                "//*[contains(@class,'mat-icon') and text()='request_quote']"
                "/ancestor::*[contains(@class,'nav') or contains(@class,'menu') or contains(@class,'item')][1]"
            ))
        )
        driver.execute_script("arguments[0].click();", faturamento)
        time.sleep(1.5)

        # Clica em Faturas das UGs (ícone solar_power)
        ug_link = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH,
                "//*[contains(@class,'mat-icon') and text()='solar_power']"
                "/ancestor::a | //*[contains(@class,'mat-icon') and text()='solar_power']"
                "/ancestor::button | //*[contains(text(),'Faturas das UG')]"
            ))
        )
        driver.execute_script("arguments[0].click();", ug_link)
        time.sleep(2)
        return True
    except Exception as e:
        # Fallback: tenta encontrar pelo texto
        try:
            for text in ["Faturas das UG", "Faturas UG", "solar_power"]:
                els = driver.find_elements(By.XPATH, f"//*[contains(text(),'{text}')]")
                if els:
                    driver.execute_script("arguments[0].click();", els[0])
                    time.sleep(2)
                    return True
        except Exception:
            pass
        return False


# ─────────────────────────────────────────────────────────────────────────────
# BUSCAR UC E BAIXAR FATURA
# ─────────────────────────────────────────────────────────────────────────────

def _buscar_uc_e_baixar(driver, uc: str, comp_mes: str) -> Optional[bytes]:
    """
    Retorna os bytes do PDF da fatura, ou None se não encontrar.
    comp_mes: nome do mês em português ex "Abril"
    """
    try:
        # Limpar e digitar UC no campo de busca
        inp_busca = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "input[placeholder*='Buscar'], input[placeholder*='buscar'], "
                "input[placeholder*='usina'], mat-form-field input"
            ))
        )
        inp_busca.clear(); inp_busca.send_keys(uc)
        time.sleep(2)

        # Filtro de competência (mat-select)
        try:
            selects = driver.find_elements(By.CSS_SELECTOR, "mat-select")
            for sel in selects:
                aria = sel.get_attribute("aria-label") or sel.get_attribute("placeholder") or ""
                if "competência" in aria.lower() or "mês" in aria.lower() or not aria:
                    driver.execute_script("arguments[0].click();", sel)
                    time.sleep(1)
                    # Procura a opção pelo mês
                    opcoes = driver.find_elements(By.CSS_SELECTOR, "mat-option")
                    for op in opcoes:
                        if comp_mes.lower() in op.text.lower():
                            op.click(); time.sleep(1); break
                    else:
                        # Fecha sem selecionar
                        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    break
        except Exception:
            pass

        time.sleep(2)

        # Verifica se há resultados (tabela vazia = nenhuma fatura)
        vazios = driver.find_elements(By.XPATH,
            "//*[contains(text(),'Nenhum resultado') or contains(text(),'nenhum') "
            "or contains(text(),'não encontrado') or contains(text(),'vazio')]")
        rows = driver.find_elements(By.CSS_SELECTOR, "mat-row, tr.mat-row, .list-item")
        if vazios or not rows:
            return None

        # Clicar no menu de ações (more_vert)
        more_vert = rows[0].find_element(By.XPATH,
            ".//*[contains(@class,'mat-icon') and text()='more_vert'] | "
            ".//*[contains(@class,'more-vert')]")
        driver.execute_script("arguments[0].click();", more_vert)
        time.sleep(1)

        # Clicar em "Ver fatura"
        ver_fatura = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH,
                "//*[contains(text(),'Ver fatura') or contains(text(),'ver fatura') "
                "or contains(text(),'Visualizar') or contains(text(),'Download')]"
            ))
        )
        ver_fatura.click()
        time.sleep(3)

        # PDF pode abrir em nova aba ou como blob URL
        abas = driver.window_handles
        if len(abas) > 1:
            driver.switch_to.window(abas[-1])
            time.sleep(2)

        url_atual = driver.current_url
        pdf_bytes = None

        if url_atual.lower().endswith(".pdf") or "pdf" in url_atual.lower():
            import urllib.request
            # Captura cookies da sessão para autenticação
            cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            req = urllib.request.Request(url_atual)
            for k, v in cookies.items():
                req.add_header("Cookie", f"{k}={v}")
            req.add_header("User-Agent", driver.execute_script("return navigator.userAgent"))
            with urllib.request.urlopen(req, timeout=30) as r:
                pdf_bytes = r.read()

        elif url_atual.startswith("blob:") or "blob" in url_atual:
            # Lê blob via JavaScript
            pdf_b64 = driver.execute_async_script("""
                var url = arguments[0]; var done = arguments[1];
                fetch(url).then(r=>r.blob()).then(b=>{
                    var reader = new FileReader();
                    reader.onload = function(){done(reader.result.split(',')[1])};
                    reader.readAsDataURL(b);
                }).catch(()=>done(null));
            """, url_atual)
            if pdf_b64:
                import base64
                pdf_bytes = base64.b64decode(pdf_b64)

        # Fecha aba extra e volta
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        return pdf_bytes

    except Exception as e:
        # Garante voltar à aba principal
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
        return None


# ─────────────────────────────────────────────────────────────────────────────
# PDF PARSER — EXTRAÇÃO INTELIGENTE
# ─────────────────────────────────────────────────────────────────────────────

# Padrões conhecidos por concessionária
PATTERNS_CONHECIDOS = {
    "enel_ce": {
        "nome":     ["ENEL CE", "COELCE", "Enel Distribuição Ceará"],
        "injetada": [r"Energia\s+Injetada[\s:]+(\d[\d.,]+)", r"Injet\.?\s+(\d[\d.,]+)"],
        "consumo":  [r"Consumo[\s:]+(\d[\d.,]+)\s*kWh"],
        "saldo":    [r"Saldo\s+(?:Créditos?|kWh)[\s:]+(\d[\d.,]+)", r"Saldo\s+(\d[\d.,]+)\s*kWh"],
    },
    "equatorial_pi": {
        "nome":     ["EQUATORIAL", "CEPISA", "Equatorial Piauí"],
        "injetada": [r"En\.\s*Injetada[\s:]+(\d[\d.,]+)", r"Injeção[\s:]+(\d[\d.,]+)"],
        "consumo":  [r"Consumo\s+Faturado[\s:]+(\d[\d.,]+)"],
        "saldo":    [r"Saldo[\s:]+(\d[\d.,]+)"],
    },
    "celesc": {
        "nome":     ["CELESC"],
        "injetada": [r"Geração\s+(?:Própria|Distribuída)[\s:]+(\d[\d.,]+)"],
        "consumo":  [r"Consumo[\s:]+(\d[\d.,]+)"],
        "saldo":    [r"Saldo[\s:]+(\d[\d.,]+)"],
    },
    "generica": {
        "nome":     [],  # fallback
        "injetada": [
            r"[Ee]nergia\s+[Ii]njetada[\s:R$]*(\d[\d.,]+)",
            r"[Ii]njeç[aã]o[\s:R$]*(\d[\d.,]+)",
            r"GD\s+[Ii]njetad[ao][\s:R$]*(\d[\d.,]+)",
            r"kWh\s+[Ii]njetad[ao][\s:R$]*(\d[\d.,]+)",
            r"[Gg]eração\s+(?:[Pp]rópria|[Dd]istribuída)[\s:R$]*(\d[\d.,]+)",
        ],
        "consumo":  [
            r"[Cc]onsumo\s+(?:[Ff]aturado|[Tt]otal)?[\s:R$]*(\d[\d.,]+)\s*kWh",
            r"kWh\s+[Cc]onsumid[ao][\s:]*(\d[\d.,]+)",
        ],
        "saldo":    [
            r"[Ss]aldo\s+(?:[Cc]réditos?|kWh|[Aa]nterior)?[\s:R$]*(\d[\d.,]+)",
            r"[Cc]réditos?\s+[Aa]cumul[ao]dos?[\s:R$]*(\d[\d.,]+)",
        ],
    },
}


def _clean_num(s: str) -> float:
    """Converte '1.234,56' ou '1234.56' em float."""
    s = s.strip().replace(" ", "")
    if "," in s and "." in s:
        if s.index(".") < s.index(","): s = s.replace(".", "").replace(",", ".")
        else: s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:   return float(s)
    except: return 0.0


def _detectar_concessionaria(texto: str) -> str:
    for conc, info in PATTERNS_CONHECIDOS.items():
        if conc == "generica": continue
        for nome in info["nome"]:
            if nome.upper() in texto.upper():
                return conc
    return "generica"


def _aplicar_patterns(texto: str, patterns: list) -> float:
    for p in patterns:
        m = re.search(p, texto, re.IGNORECASE | re.MULTILINE)
        if m:
            return _clean_num(m.group(1))
    return 0.0


def extrair_dados_pdf(pdf_bytes: bytes, concessionaria_hint: str = "") -> dict:
    """
    Extrai Energia Injetada, Consumo e Saldo de uma fatura em bytes.
    Retorna dict com os campos e 'confianca' (0-1).
    """
    resultado = {
        "energia_injetada": 0.0,
        "consumo": 0.0,
        "saldo": 0.0,
        "concessionaria": concessionaria_hint or "desconhecida",
        "confianca": 0.0,
        "texto_bruto": "",
        "precisa_template": False,
    }
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            texto = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
        resultado["texto_bruto"] = texto[:3000]  # primeiros 3k chars para debug

        if not texto.strip():
            resultado["precisa_template"] = True
            return resultado

        # Detecta concessionária
        conc = _detectar_concessionaria(texto)
        resultado["concessionaria"] = conc
        pats = PATTERNS_CONHECIDOS.get(conc, PATTERNS_CONHECIDOS["generica"])

        inj = _aplicar_patterns(texto, pats["injetada"])
        con = _aplicar_patterns(texto, pats["consumo"])
        sal = _aplicar_patterns(texto, pats["saldo"])

        # Fallback: genérica se não achou nada
        if inj == 0.0:
            inj = _aplicar_patterns(texto, PATTERNS_CONHECIDOS["generica"]["injetada"])
        if sal == 0.0:
            sal = _aplicar_patterns(texto, PATTERNS_CONHECIDOS["generica"]["saldo"])

        resultado["energia_injetada"] = inj
        resultado["consumo"] = con
        resultado["saldo"] = sal

        # Confiança: quantos campos foram extraídos
        achados = sum(1 for v in [inj, sal] if v > 0)
        resultado["confianca"] = achados / 2

        if resultado["confianca"] == 0:
            resultado["precisa_template"] = True

    except Exception as e:
        resultado["precisa_template"] = True
        resultado["erro"] = str(e)

    return resultado


def extrair_dados_pdf_com_template(pdf_bytes: bytes, template: dict) -> dict:
    """
    Extrai usando template aprendido: coordenadas de página/bbox salvas pelo usuário.
    template: {page_num, bbox_injetada, bbox_saldo, bbox_consumo}
    """
    resultado = {"energia_injetada": 0.0, "consumo": 0.0, "saldo": 0.0,
                 "concessionaria": template.get("concessionaria","custom"),
                 "confianca": 0.0, "precisa_template": False}
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pn = min(template.get("page_num", 0), len(pdf.pages)-1)
            page = pdf.pages[pn]
            for campo, key in [("bbox_injetada","energia_injetada"),
                                ("bbox_saldo","saldo"),
                                ("bbox_consumo","consumo")]:
                bbox = template.get(campo)
                if bbox:
                    region = page.within_bbox(bbox)
                    txt = region.extract_text() or ""
                    nums = re.findall(r"\d[\d.,]+", txt)
                    if nums: resultado[key] = _clean_num(nums[-1])

        achados = sum(1 for k in ["energia_injetada","saldo"] if resultado[k] > 0)
        resultado["confianca"] = achados / 2
    except Exception as e:
        resultado["erro"] = str(e)
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# SALVAR GERAÇÃO NO HUB
# ─────────────────────────────────────────────────────────────────────────────

def salvar_geracao_hub(uc: str, dados: dict, competencia: str):
    """Upsert em geracao_usinas.json."""
    usinas = _load(f"{DB}/usinas.json", [])
    uc_match = next((u for u in usinas if
                     "".join(filter(str.isdigit, str(u["uc"]))) ==
                     "".join(filter(str.isdigit, str(uc)))), None)

    nome_usina = uc_match.get("ufv", uc) if uc_match else uc
    gerador    = uc_match.get("gerador", "") if uc_match else ""

    ger = load_geracao()
    # Remove registro anterior para mesma UC + competência
    ger = [g for g in ger if not (
        "".join(filter(str.isdigit, str(g.get("uc","")))) ==
        "".join(filter(str.isdigit, str(uc))) and
        g.get("competencia","") == competencia
    )]
    ger.append({
        "uc":               uc,
        "nome_usina":       nome_usina,
        "gerador":          gerador,
        "competencia":      competencia,
        "energia_injetada": dados.get("energia_injetada", 0.0),
        "saldo":            dados.get("saldo", 0.0),
        "consumo":          dados.get("consumo", 0.0),
        "fonte":            "robô_captura",
        "concessionaria":   dados.get("concessionaria", ""),
        "confianca_extr":   dados.get("confianca", 0.0),
        "registrado_em":    datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    save_geracao(ger)


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO PRINCIPAL DO ROBÔ (chamada pelo Streamlit)
# ─────────────────────────────────────────────────────────────────────────────

def executar_varredura(
    progress_cb=None,       # callback(pct, mensagem)
    log_cb=None,            # callback(dict_log_entry)
    competencia_mes: str = "",   # "Abril" — vazio = mês atual
    ucs_alvo: list = None,  # lista de UCs; vazio = todas do usinas.json
) -> list:
    """
    Executa a varredura completa.
    Retorna lista de log entries.
    """
    if not SELENIUM_OK:
        raise RuntimeError("Selenium não instalado. Adicione ao requirements.txt.")

    # Credenciais via st.secrets
    try:
        email = st.secrets["sunne_portal"]["email"]
        senha = st.secrets["sunne_portal"]["password"]
    except Exception:
        # Fallback para dev local
        email = os.environ.get("SUNNE_EMAIL", "milena.braga@sunne.com.br")
        senha = os.environ.get("SUNNE_SENHA", "Milena@2025")

    if not competencia_mes:
        competencia_mes = MESES_PT[datetime.now().month]

    comp_mmaaaa = datetime.now().strftime("%m/%Y")

    usinas = load_usinas()
    if ucs_alvo:
        usinas = [u for u in usinas if str(u.get("uc","")) in ucs_alvo]

    log_entries = []
    templates   = load_templates()

    def _log(uc, status, injetada=0.0, saldo=0.0, obs=""):
        entry = {
            "ts":       datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "uc":       uc,
            "status":   status,
            "injetada": injetada,
            "saldo":    saldo,
            "obs":      obs,
            "comp":     comp_mmaaaa,
        }
        log_entries.append(entry)
        # Persiste no log geral
        hist = load_log()
        hist.insert(0, entry)
        save_log(hist[:500])   # mantém últimas 500 linhas
        if log_cb: log_cb(entry)
        return entry

    if not usinas:
        _log("—", "erro", obs="Nenhuma usina cadastrada.")
        return log_entries

    driver = None
    try:
        if progress_cb: progress_cb(0.02, "⚙️ Iniciando Chrome headless…")
        driver = _build_driver()

        # Login
        if progress_cb: progress_cb(0.05, "🔐 Fazendo login no portal…")
        ok_login = _login(driver, email, senha)
        if not ok_login:
            _log("—", "erro", obs="Falha no login. Verifique credenciais em st.secrets.")
            return log_entries

        # Navegar até faturas
        if progress_cb: progress_cb(0.10, "📂 Navegando para Faturas das UGs…")
        ok_nav = _navegar_para_faturas(driver)
        if not ok_nav:
            _log("—", "erro", obs="Não foi possível navegar até Faturas das UGs.")
            return log_entries

        total = len(usinas)

        for idx, usina in enumerate(usinas):
            uc       = str(usina.get("uc","")).strip()
            ufv      = usina.get("ufv", uc)
            conc     = usina.get("concessionaria","")
            pct      = 0.10 + (idx / total) * 0.85

            if progress_cb:
                progress_cb(pct, f"🔍 Buscando UC {uc} · {ufv} ({idx+1}/{total})")

            try:
                pdf_bytes = _buscar_uc_e_baixar(driver, uc, competencia_mes)

                if pdf_bytes is None:
                    _log(uc, "não_disponível", obs=f"Fatura {competencia_mes} não encontrada")
                    continue

                # Extração com template se disponível
                template_key = f"{conc}||{uc}" if conc else uc
                template_gen = conc if conc else "generica"
                template     = (templates.get(template_key)
                                or templates.get(conc)
                                or templates.get(template_gen))

                if template and template.get("bbox_injetada"):
                    dados = extrair_dados_pdf_com_template(pdf_bytes, template)
                else:
                    dados = extrair_dados_pdf(pdf_bytes, concessionaria_hint=conc)

                if dados.get("precisa_template"):
                    # Sinaliza para o Streamlit que precisamos de ajuda
                    _log(uc, "precisa_template",
                         obs=f"Layout desconhecido ({conc}). Por favor, ensine o robô.")
                    # Salva o PDF para visualização posterior
                    pdf_path = f"{DB}/pdf_pendente_{uc}.pdf"
                    with open(pdf_path, "wb") as fp:
                        fp.write(pdf_bytes)
                    continue

                # Salva no hub
                salvar_geracao_hub(uc, dados, comp_mmaaaa)
                _log(uc, "baixado",
                     injetada=dados["energia_injetada"],
                     saldo=dados["saldo"],
                     obs=f"Confiança extração: {dados['confianca']*100:.0f}%")

            except Exception as e:
                _log(uc, "erro", obs=str(e)[:200])

            # Volta ao estado inicial da página de busca
            try:
                inp = driver.find_elements(By.CSS_SELECTOR,
                    "input[placeholder*='Buscar'], input[placeholder*='buscar']")
                if inp:
                    inp[0].clear()
                    inp[0].send_keys(Keys.ESCAPE)
                time.sleep(0.8)
            except Exception:
                pass

    except Exception as e:
        _log("—", "erro_geral", obs=traceback.format_exc()[:400])
    finally:
        if driver:
            try: driver.quit()
            except Exception: pass

    if progress_cb: progress_cb(1.0, "✅ Varredura concluída!")
    return log_entries


# ─────────────────────────────────────────────────────────────────────────────
# APRENDIZADO DE TEMPLATE (chamado pelo Streamlit quando usuário sobe fatura)
# ─────────────────────────────────────────────────────────────────────────────

def aprender_template_de_pdf(
    pdf_bytes: bytes,
    uc: str,
    concessionaria: str,
    energia_injetada: float,
    saldo: float,
    consumo: float,
) -> dict:
    """
    Dado que o usuário subiu uma fatura e informou os valores corretos,
    tenta descobrir em que página/região esses valores aparecem e salva o template.
    """
    templates = load_templates()
    key = concessionaria or uc

    # Tenta extração simples com os valores do usuário como "gabarito"
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            alvo_str = str(int(energia_injetada)) if energia_injetada > 0 else None
            for pi, page in enumerate(pdf.pages):
                texto = page.extract_text() or ""
                if alvo_str and alvo_str in texto.replace(",","").replace(".",""):
                    # Acha a bbox do valor
                    words = page.extract_words()
                    for w in words:
                        num_clean = re.sub(r"[^0-9]","", w["text"])
                        if num_clean == alvo_str or (alvo_str in num_clean and len(num_clean) <= len(alvo_str)+2):
                            templates[key] = {
                                "concessionaria": concessionaria,
                                "uc":             uc,
                                "page_num":       pi,
                                "bbox_injetada":  [w["x0"]-5, w["top"]-5, w["x1"]+5, w["bottom"]+5],
                                "bbox_saldo":     None,
                                "bbox_consumo":   None,
                                "aprendido_em":   datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "manual":         True,
                            }
                            break

        # Mesmo sem bbox, salva os padrões de texto para futuras extrações
        if key not in templates:
            templates[key] = {
                "concessionaria": concessionaria,
                "uc":             uc,
                "page_num":       0,
                "bbox_injetada":  None,
                "bbox_saldo":     None,
                "bbox_consumo":   None,
                "valores_ref":    {"injetada": energia_injetada, "saldo": saldo, "consumo": consumo},
                "aprendido_em":   datetime.now().strftime("%d/%m/%Y %H:%M"),
                "manual":         True,
            }
        save_templates(templates)
    except Exception as e:
        pass

    return templates.get(key, {})


# ─────────────────────────────────────────────────────────────────────────────
# AGENDADOR — VERIFICAR SE DEVE RODAR AGORA (08h)
# ─────────────────────────────────────────────────────────────────────────────

def verificar_agendamento() -> bool:
    """
    Retorna True se deve disparar a automação agora.
    Chamada a cada rerun do Streamlit.
    """
    sched = load_schedule()
    if not sched.get("auto", False):
        return False

    hora_alvo = sched.get("hora", "08:00")
    ultima    = sched.get("ultima_execucao")
    agora     = datetime.now()
    hora_str  = agora.strftime("%H:%M")
    hoje_str  = agora.strftime("%Y-%m-%d")

    # Só roda se a hora bater E não tiver rodado hoje
    if hora_str == hora_alvo and ultima != hoje_str:
        sched["ultima_execucao"] = hoje_str
        save_schedule(sched)
        return True
    return False
