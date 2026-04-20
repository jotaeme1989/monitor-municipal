

import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import urllib3
import os

# --- CONFIGURACIÓN DE TELEGRAM ---
TOKEN_TELEGRAM = "8613120185:AAH5u4790dTCU4VekKf4e4LS8TC5dl7KxEM"
CHAT_ID_TELEGRAM = "7240660332"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID_TELEGRAM, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except:
        pass

def cargar_urls():
    if os.path.exists("sitios.txt"):
        with open("sitios.txt", "r") as f:
            return f.read()
    return "https://www.munistgo.cl/transparencia/concursos/"

st.set_page_config(page_title="Monitor Municipal PRO", page_icon="🤖", layout="wide")
st.title("🤖 Monitor Municipal & Empleos Públicos")

if st.button("🔔 Probar mi Telegram"):
    enviar_telegram("¡Conexión exitosa! El monitor está vinculado correctamente.")
    st.success("Mensaje de prueba enviado. Revisa tu celular.")

with st.sidebar:
    st.header("Configuración")
    urls_input = st.text_area("Lista de URLs Municipales", value=cargar_urls(), height=200)
    keywords_input = st.text_input("Palabras Clave", value="concurso público, informática, soporte, técnico")
    intervalo = st.number_input("Intervalo (minutos)", min_value=1, value=60)
    
    st.divider()
    st.subheader("Configuración Empleos Públicos")
    activar_ep = st.checkbox("Monitorear EmpleosPublicos.cl", value=True)
    busqueda_ep = st.text_input("Cargo a buscar en Portal", value="informatica")

header_fake = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

if st.sidebar.button("💾 Guardar configuración"):
    with open("sitios.txt", "w") as f:
        f.write(urls_input)
    st.sidebar.success("¡Configuración guardada!")

lista_urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
lista_keywords = [kw.strip().lower() for kw in keywords_input.split(',') if kw.strip()]

if st.button("🚀 Iniciar Monitoreo Total"):
    st.info(f"Monitor activo. Revisando cada {intervalo} minutos...")
    contenedor = st.container()
    
    while True:
        ahora = datetime.now().strftime("%H:%M:%S")
        with contenedor:
            st.write(f"### --- Revisión: {ahora} ---")
            
            # --- SECCIÓN 1: MUNICIPALIDADES ---
            for url in lista_urls:
                try:
                    res = requests.get(url, headers=header_fake, timeout=15, verify=False)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    links_encontrados = []
                    for a in soup.find_all('a', href=True):
                        if any(kw in a.get_text().lower() for kw in lista_keywords):
                            href = a['href']
                            link_final = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                            links_encontrados.append(link_final)

                    if links_encontrados:
                        links_encontrados = list(set(links_encontrados))
                        st.success(f"🚨 Detectado en {url}")
                        mensaje_tele = f"🏢 *MUNICIPIO:* {url}\n"
                        for l in links_encontrados: mensaje_tele += f"🔗 {l}\n"
                        enviar_telegram(mensaje_tele)
                    else:
                        st.text(f"⚪ {url}: Sin novedades")
                except:
                    st.warning(f"⚠️ Error en: {url}")

            # --- SECCIÓN 2: EMPLEOS PÚBLICOS ---
            if activar_ep:
                st.write("---")
                st.write(f"🔎 Buscando '{busqueda_ep}' en EmpleosPublicos.cl...")
                try:
                    # URL de búsqueda directa del portal
                    url_ep = f"https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?pPalabrasClaves={busqueda_ep}"
                    res_ep = requests.get(url_ep, headers=header_fake, timeout=20)
                    soup_ep = BeautifulSoup(res_ep.text, 'html.parser')
                    
                    # Buscamos las filas de la tabla de resultados
                    empleos = []
                    for row in soup_ep.find_all('tr'):
                        if busqueda_ep.lower() in row.get_text().lower():
                            link = row.find('a', href=True)
                            if link:
                                full_link = "https://www.empleospublicos.cl" + link['href']
                                titulo = link.get_text().strip()
                                empleos.append(f"📌 {titulo}\n🔗 {full_link}")

                    if empleos:
                        st.success(f"🔥 ¡Encontrado en Portal Empleos Públicos!")
                        for emp in empleos: st.write(emp)
                        enviar_telegram(f"💼 *PORTAL EMPLEOS PÚBLICOS*\n\n" + "\n\n".join(empleos))
                    else:
                        st.text("⚪ Empleos Públicos: Sin novedades específicas.")
                except Exception as e:
                    st.warning("⚠️ No se pudo conectar con el Portal de Empleos Públicos.")

            st.divider()
            time.sleep(intervalo * 60)
            st.rerun()