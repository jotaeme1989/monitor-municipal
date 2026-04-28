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

# --- ESTILOS CSS PERSONALIZADOS ---
def apply_custom_styles():
    st.markdown("""
        <style>
        /* Estilo general para las tarjetas */
        .muni-card {
            border-radius: 12px;
            padding: 20px;
            margin: 10px;
            min-height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .muni-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        }
        
        /* Colores por estado */
        .status-ok { background-color: #f0fff4; border: 2px solid #38a169; } /* Verde - Sin novedades */
        .status-found { background-color: #f7fff7; border: 2px solid #f56565; color: #f56565;} /* Verde clarito con rojo - Encontrado */
        .status-error { background-color: #fffaf0; border: 2px solid #ed8936; } /* Amarillo - Error */
        
        /* Textos */
        .card-title {
            font-size: 1.1rem;
            font-weight: bold;
            color: #2d3748;
            word-wrap: break-word;
            margin-bottom: 8px;
        }
        .card-status {
            font-size: 0.9rem;
            color: #718096;
            margin-bottom: 12px;
        }
        .card-links {
            font-size: 0.85rem;
            color: #4a5568;
            list-style: none;
            padding: 0;
            margin: 0;
            max-height: 80px;
            overflow-y: auto;
        }
        
        /* Botón/Enlace de la tarjeta */
        .card-btn {
            display: inline-block;
            background-color: #4299e1;
            color: white !important;
            padding: 8px 15px;
            text-decoration: none !important;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: bold;
            margin-top: 10px;
            text-align: center;
        }
        .card-btn:hover { background-color: #3182ce; }
        
        </style>
    """, unsafe_allow_html=True)

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
    return "https://mcerrillos.cl\nhttps://www.munistgo.cl/transparencia/concursos/"

def extrair_nombre_muni(url):
    try:
        nombre = url.split("//")[1].split(".")[1].capitalize()
        return nombre
    except:
        return "Muni Desconocida"

# --- INTERFAZ ---
st.set_page_config(page_title="Dashboard Municipal PRO", page_icon="📊", layout="wide")
apply_custom_styles() # Aplicar los estilos CSS

st.title("📊 Monitor Municipal (Versión Dashboard 24/7)")

with st.sidebar:
    st.header("⚙️ Configuración")
    urls_input = st.text_area("URLs Municipales (una por línea)", value=cargar_urls(), height=250)
    keywords_input = st.text_input("Palabras Clave (separadas por coma)", value="2026, informática, soporte, técnico, bases, llamado")
    intervalo = st.number_input("Intervalo de revisión (minutos)", min_value=1, value=120)
    st.divider()
    activar_ep = st.checkbox("Monitorear EmpleosPublicos.cl", value=True)
    busqueda_ep = st.text_input("Cargo en Portal", value="informatica")

if st.sidebar.button("💾 Guardar y Reiniciar"):
    with open("sitios.txt", "w") as f:
        f.write(urls_input)
    st.sidebar.success("Sincronizando...")
    st.rerun()

# --- LÓGICA DE SCRAPING ---
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8',
    'Connection': 'keep-alive',
}

lista_urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
lista_keywords = [kw.strip().lower() for kw in keywords_input.split(',') if kw.strip()]

st.info(f"🚀 Monitor activo. Ciclo de {intervalo} minutos.")
st.write(f"--- Última Revisión: **{datetime.now(chile_tz).strftime('%H:%M:%S')}** ---")

# --- GRIDS DE RESULTADOS ---
num_columnas = 4 # Define cuántos cubos por fila (3 o 4 se ve bien en escritorio)
contenedor_grid = st.container()

while True:
    with contenedor_grid:
        cols = st.columns(num_columnas)
        muni_idx = 0
        
        for url in lista_urls:
            nombre_muni = extrair_nombre_muni(url)
            status_class = "status-ok"
            status_text = "Sin novedades específicas."
            enlaces_texto_list = ""
            enviar_notif = False
            
            try:
                # 1. Intentar conectar
                res = requests.get(url, headers=headers, timeout=25, verify=False)
                res.raise_for_status() 
                soup = BeautifulSoup(res.text, 'html.parser')
                enlaces_encontrados = []
                
                # 2. Buscar palabras clave
                for a in soup.find_all('a', href=True):
                    texto = a.get_text().strip().lower()
                    href = a['href'].lower()
                    
                    if any(kw in texto for kw in lista_keywords) or any(kw in href for kw in lista_keywords):
                        if "facebook" in href or "twitter" in href or "instagram" in href: continue
                            
                        link_final = a['href']
                        if not link_final.startswith('http'):
                            link_final = url.rstrip('/') + '/' + link_final.lstrip('/')
                        enlaces_encontrados.append(link_final)
                
                # 3. Procesar resultados
                if enlaces_encontrados:
                    enlaces_encontrados = list(set(enlaces_encontrados)) # Eliminar duplicados
                    status_class = "status-found"
                    status_text = f"¡Alerta! {len(enlaces_encontrados)} hallazgo(s)."
                    for link in enlaces_encontrados[:3]: # Solo mostrar los primeros 3 links en la tarjeta
                        texto_recortado = link.split('/')[-1][:25] + "..." if len(link.split('/')[-1]) > 25 else link.split('/')[-1]
                        enlaces_texto_list += f"<li>🔗 {texto_recortado}</li>"
                    if len(enlaces_encontrados) > 3:
                        enlaces_texto_list += "<li>... y más</li>"
                    enviar_notif = True
                    enviar_telegram(f"🏢 *{nombre_muni.upper()}:* Hallazgo(s) detectado(s)\n🔗 " + "\n🔗 ".join(enlaces_encontrados))

            except Exception as e:
                # 4. Manejar Errores (Falla de conexión o bloqueo)
                status_class = "status-error"
                status_text = "Error de conexión/bloqueo."

            # --- DIBUJAR LA TARJETA (CUBO) ---
            with cols[muni_idx % num_columnas]:
                card_html = f"""
                    <div class="muni-card {status_class}">
                        <div>
                            <div class="card-title">{nombre_muni}</div>
                            <div class="card-status">{status_text}</div>
                            <ul class="card-links">
                                {enlaces_texto_list}
                            </ul>
                        </div>
                        <a href="{url}" target="_blank" class="card-btn">Ir a la Web</a>
                    </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
            
            muni_idx += 1

        # --- SECCIÓN EMPLEOS PÚBLICOS (FUERA DEL GRID) ---
        if activar_ep:
            try:
                # ... Lógica de Empleos Públicos (se mantiene igual, se dibuja abajo en formato lista o tarjeta grande)
                # ... (He omitido el bloque para no alargar el mensaje, pero debes mantenerlo en tu código real)
                pass 
            except: pass

    time.sleep(intervalo * 60)
    st.rerun()