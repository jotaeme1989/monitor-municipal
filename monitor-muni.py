import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pytz 
import urllib3
import os

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = "8613120185:AAH5u4790dTCU4VekKf4e4LS8TC5dl7KxEM"
CHAT_ID_TELEGRAM = "7240660332"
chile_tz = pytz.timezone('America/Santiago')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
st.set_page_config(page_title="Monitor Municipal PRO", page_icon="🤖", layout="wide")
st.title("🤖 Monitor Municipal & Empleos Públicos")

if st.button("🔔 Probar mi Telegram"):
    enviar_telegram("¡Conexión exitosa! El monitor está vinculado correctamente.")
    st.success("Mensaje de prueba enviado.")

with st.sidebar:
    st.header("Configuración")
    urls_input = st.text_area("URLs Municipales", value=cargar_urls(), height=200)
    keywords_input = st.text_input("Palabras Clave", value="concurso público, informática, soporte, técnico")
    intervalo = st.number_input("Intervalo (minutos)", min_value=1, value=120)
    st.divider()
    activar_ep = st.checkbox("Monitorear EmpleosPublicos.cl", value=True)
    busqueda_ep = st.text_input("Cargo en Portal", value="informatica")

if st.sidebar.button("💾 Guardar configuración"):
    with open("sitios.txt", "w") as f:
        f.write(urls_input)
    st.sidebar.success("Guardado.")

# --- LÓGICA ---
header_fake = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
lista_urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
lista_keywords = [kw.strip().lower() for kw in keywords_input.split(',') if kw.strip()]

st.info(f"🚀 Monitor activo cada {intervalo} minutos.")
contenedor = st.container()

while True:
    # 1. Obtener la hora actual de Chile
    ahora_completa = datetime.now(chile_tz)
    hora_actual = ahora_completa.hour
    ahora_str = ahora_completa.strftime("%H:%M:%S")

    # 2. Verificar el horario (de 7 a 23 hrs)
    if 7 <= hora_actual < 23:
        with contenedor:
            st.write(f"### --- Revisión (Chile): {ahora_str} ---")
            
            # --- ESCANEO DE MUNICIPIOS ---
            for url in lista_urls:
                try:
                    res = requests.get(url, headers=header_fake, timeout=20, verify=False)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    enlaces = []
                    for a in soup.find_all('a', href=True):
                        if any(kw in a.get_text().lower() for kw in lista_keywords):
                            href = a['href']
                            final = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                            enlaces.append(final)
                    
                    if enlaces:
                        enlaces = list(set(enlaces))
                        st.success(f"🚨 Encontrado en {url}")
                        enviar_telegram(f"🏢 *MUNICIPIO:* {url}\n🔗 " + "\n🔗 ".join(enlaces))
                    else:
                        st.text(f"⚪ {url}: Sin novedades")
                except:
                    st.warning(f"⚠️ Error: {url}")
            
            # --- ESCANEO EMPLEOS PÚBLICOS ---
            if activar_ep:
                try:
                    url_ep = f"https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?pPalabrasClaves={busqueda_ep}"
                    res_ep = requests.get(url_ep, headers=header_fake, timeout=25)
                    soup_ep = BeautifulSoup(res_ep.text, 'html.parser')
                    found = False
                    for row in soup_ep.find_all('tr'):
                        if busqueda_ep.lower() in row.get_text().lower():
                            link = row.find('a', href=True)
                            if link:
                                found = True
                                full_link = "https://www.empleospublicos.cl" + link['href']
                                enviar_telegram(f"💼 *PORTAL:* {link.get_text().strip()}\n🔗 {full_link}")
                    if not found: st.text("⚪ Empleos Públicos: Sin novedades.")
                except:
                    st.warning("⚠️ Error en Portal Empleos Públicos")

        enviar_telegram(f"🤖 *Monitor Activo*\nRevisión de las {ahora_str} completa.")
    
    else:
        # Modo descanso
        with contenedor:
            st.write(f"💤 Fuera de horario (Son las {ahora_str}). El monitor descansará hasta las 07:00 AM.")

    # 3. Esperar el intervalo y reiniciar
    time.sleep(intervalo * 60)
    st.rerun()
