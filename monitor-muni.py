import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pytz
import urllib3
import os

# --- CONFIGURACIÓN ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TOKEN_TELEGRAM = "8613120185:AAH5u4790dTCU4VekKf4e4LS8TC5dl7KxEM"
CHAT_ID_TELEGRAM = "7240660332"
chile_tz = pytz.timezone('America/Santiago')

def extrair_nombre_muni(url):
    nombres_municipios = {
        "pintana.cl": "La Pintana",
        "mpuentealto.cl": "Puente Alto",
        "municipalidadelbosque.cl": "El Bosque",
        "sanbernardo.cl": "San Bernardo",
        "laflorida.cl": "La Florida",
        "municipalidadlagranja.cl": "La Granja",
        "sanramon.cl": "San Ramón",
        "cisterna.cl": "La Cisterna",
        "loespejo.cl": "Lo Espejo",
        "sanmiguel.cl": "San Miguel",
        "sanjoaquin.cl": "San Joaquín",
        "macul.cl": "Macul",
        "penalolen.cl": "Peñalolén",
        "mcerrillos.cl": "Cerrillos",
        "estacioncentral.cl": "Estación Central",
        "munistgo.cl": "Santiago Centro",
        "nunoa.cl": "Ñuñoa",
        "providencia.cl": "Providencia",
        "independencia.cl": "Independencia",
        "recoleta.cl": "Recoleta",
        "pirque.cl": "Pirque",
        "loprado.cl": "Lo Prado",
        "lareina.cl": "La Reina",
        "empleospublicos.cl": "Portal Empleos Públicos"
    }
    url_lower = url.lower()
    for dominio, nombre_real in nombres_municipios.items():
        if dominio in url_lower:
            return nombre_real
    return url.split("//")[-1].split("/")[0]

def es_contenido_valido(texto_o_url):
    basura = [
        "vacunacion", "vacunación", "influenza", "covid", "campaña", 
        "youtube", "watch?v", "facebook", "twitter", "instagram",
        "cuenta-publica", "eleccionarios", "pago-de-permiso", "pagos",
        "tgr.cl", "servel.cl", "en-vivo", "taller", "deporte", "cultura"
    ]
    texto_lower = texto_o_url.lower()
    if any(b in texto_lower for b in basura):
        return False
    años_viejos = ["2021", "2022", "2023", "2024", "2025"]
    if any(año in texto_lower for año in años_viejos):
        if "2026" not in texto_lower:
            return False
    return True

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID_TELEGRAM, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def cargar_urls():
    if os.path.exists("sitios.txt"):
        with open("sitios.txt", "r") as f:
            return f.read()
    return "https://www.munistgo.cl/transparencia/concursos/"

# --- INTERFAZ ---
st.set_page_config(page_title="Monitor Municipal PRO", page_icon="📊", layout="wide")
st.title("📊 Monitor Municipal (Versión Dashboard 24/7)")

st.markdown("""
    <style>
    .muni-card {
        border-radius: 10px;
        padding: 15px;
        margin: 10px;
        border: 2px solid #f0f2f6;
        height: 280px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }
    .muni-alerta { border: 2px solid #ff4b4b; background-color: #fffafa; }
    .muni-ok { border: 2px solid #28a745; background-color: #f8fff9; }
    .muni-error { border: 2px solid #ffa500; background-color: #fffaf0; }
    .btn-muni {
        width: 100%;
        border: none;
        border-radius: 5px;
        background-color: #52a1e5;
        color: white;
        padding: 8px;
        margin-top: 5px;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuración")
    urls_input = st.text_area("URLs Municipales", value=cargar_urls(), height=200)
    keywords_input = st.text_input("Palabras Clave", value="concurso público, informática, soporte, técnico, bases, llamado")
    intervalo = st.number_input("Intervalo (minutos)", min_value=1, value=120)
    if st.button("💾 Guardar y Reiniciar"):
        with open("sitios.txt", "w") as f:
            f.write(urls_input)
        st.rerun()

# --- LÓGICA DE ESCANEO AGRUPADO ---
lista_urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
lista_keywords = [kw.strip().lower() for kw in keywords_input.split(',') if kw.strip()]

# Diccionario para agrupar links y hallazgos por nombre de municipio
comunas_data = {}

for url in lista_urls:
    nombre_muni = extrair_nombre_muni(url)
    if nombre_muni not in comunas_data:
        comunas_data[nombre_muni] = {"urls": [], "hallazgos": [], "error": False}
    
    comunas_data[nombre_muni]["urls"].append(url)
    
    try:
        header_fake = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=header_fake, timeout=20, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            texto_link = a.get_text().lower()
            href = a['href']
            if any(kw in texto_link for kw in lista_keywords) and es_contenido_valido(texto_link) and es_contenido_valido(href):
                final_link = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                comunas_data[nombre_muni]["hallazgos"].append(final_link)
    except:
        comunas_data[nombre_muni]["error"] = True

# --- RENDERIZADO DE CUBOS ---
ahora_chile = datetime.now(chile_tz).strftime("%H:%M:%S")
st.info(f"🚀 Monitor activo. Última revisión: {ahora_chile}")

cols = st.columns(4)
idx_col = 0

for nombre, data in comunas_data.items():
    with cols[idx_col % 4]:
        # Determinar estado para el color
        clase_css = "muni-ok"
        if data["error"]: clase_css = "muni-error"
        if data["hallazgos"]: clase_css = "muni-alerta"
        
        hallazgos_unicos = list(set(data["hallazgos"]))
        
        # Generar botones para las URLs (Opción 1, Opción 2...)
        botones_html = ""
        for i, u in enumerate(data["urls"]):
            label = "Ir a la Web" if len(data["urls"]) == 1 else f"Opción {i+1}"
            botones_html += f"<a href='{u}' target='_blank' class='btn-muni'>{label}</a>"

        # Crear el cubo
        alerta_txt = f"<p style='color:red;'><b>🚨 {len(hallazgos_unicos)} hallazgos!</b></p>" if hallazgos_unicos else "<p style='color:green;'>Sin novedades.</p>"
        error_txt = "<p style='color:orange;'>Error parcial de conexión.</p>" if data["error"] and not hallazgos_unicos else ""

        st.markdown(f"""
            <div class='muni-card {clase_css}'>
                <h3 style='margin-bottom:5px;'>{nombre}</h3>
                <hr style='margin:5px 0;'>
                {alerta_txt}
                {error_txt}
                <div style='margin-top: auto;'>
                    {botones_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if hallazgos_unicos:
            enviar_telegram(f"🚨 ALERTA: {nombre}\nSe encontraron {len(hallazgos_unicos)} posibles concursos. Revisa las opciones en el Dashboard.")
    
    idx_col += 1

# --- ESPERA Y REINICIO ---
time.sleep(intervalo * 60)
st.rerun()