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
        "empleospublicos.cl": "Portal Empleos Públicos"
    }
    url_lower = url.lower()
    for dominio, nombre_real in nombres_municipios.items():
        if dominio in url_lower:
            return nombre_real
    return url.split("//")[-1].split("/")[0]

def es_contenido_valido(texto_o_url):
    palabras_basura = ["vacunacion", "vacunación", "influenza", "cuenta-publica", "youtube", "watch?v", "eleccionarios", "pago-de-permiso", "pagos"]
    texto_lower = texto_o_url.lower()
    if any(basura in texto_lower for basura in palabras_basura):
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
        height: 250px;
        overflow-y: auto;
    }
    .muni-alerta { border: 2px solid #ff4b4b; background-color: #fffafa; }
    .muni-ok { border: 2px solid #28a745; background-color: #f8fff9; }
    .muni-error { border: 2px solid #ffa500; background-color: #fffaf0; }
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

# --- LÓGICA DE ESCANEO ---
lista_urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
lista_keywords = [kw.strip().lower() for kw in keywords_input.split(',') if kw.strip()]

ahora_chile = datetime.now(chile_tz).strftime("%H:%M:%S")
st.info(f"🚀 Monitor activo. Última revisión: {ahora_chile}")

cols = st.columns(4)
idx_col = 0
header_fake = {'User-Agent': 'Mozilla/5.0'}

for url in lista_urls:
    nombre_muni = extrair_nombre_muni(url)
    enlaces_encontrados = []
    error_msg = None
    
    # 1. Intenta conectarse a la web
    try:
        res = requests.get(url, headers=header_fake, timeout=20, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            texto_link = a.get_text().lower()
            href = a['href']
            if any(kw in texto_link for kw in lista_keywords) and es_contenido_valido(texto_link) and es_contenido_valido(href):
                final_link = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                enlaces_encontrados.append(final_link)
    except:
        error_msg = "Error de conexión."

    # 2. Dibuja el cubo con el botón de "Ir a la Web"
    with cols[idx_col % 4]:
        if error_msg:
            st.markdown(f"""
                <div class='muni-card muni-error'>
                    <h3>{nombre_muni}</h3>
                    <p style='color:orange;'>{error_msg}</p>
                    <a href='{url}' target='_blank'><button style='width:100%; border:none; border-radius:5px; background-color:#52a1e5; color:white; padding:5px; cursor:pointer;'>Ir a la Web</button></a>
                </div>
            """, unsafe_allow_html=True)
        elif enlaces_encontrados:
            enlaces_unicos = list(set(enlaces_encontrados))
            st.markdown(f"""
                <div class='muni-card muni-alerta'>
                    <h3>{nombre_muni}</h3>
                    <p style='color:red;'><b>¡Alerta! {len(enlaces_unicos)} hallazgos.</b></p>
                    <a href='{url}' target='_blank'><button style='width:100%; border:none; border-radius:5px; background-color:#52a1e5; color:white; padding:5px; cursor:pointer;'>Ir a la Web</button></a>
                </div>
            """, unsafe_allow_html=True)
            enviar_telegram(f"🚨 ALERTA: {nombre_muni} - {enlaces_unicos[0]}")
        else:
            st.markdown(f"""
                <div class='muni-card muni-ok'>
                    <h3>{nombre_muni}</h3>
                    <p style='color:green;'>Sin novedades.</p>
                    <a href='{url}' target='_blank'><button style='width:100%; border:none; border-radius:5px; background-color:#52a1e5; color:white; padding:5px; cursor:pointer;'>Ir a la Web</button></a>
                </div>
            """, unsafe_allow_html=True)
    
    idx_col += 1

# --- ESPERA Y REINICIO ---
time.sleep(intervalo * 60)
st.rerun()