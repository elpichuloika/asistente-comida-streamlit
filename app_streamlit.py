import streamlit as st # Asegúrate de que esta línea esté al inicio.
import google.generativeai as genai
import re
import os 

# --- Interfaz de Usuario de Streamlit ---
# !!! ESTO DEBE SER LA PRIMERA FUNCIÓN DE STREAMLIT QUE SE LLAMA EN TODO EL SCRIPT !!!
st.set_page_config(
    page_title="Asistente para Locales de Comida Chile",
    page_icon="🍔", # Puedes usar un emoji como icono
    layout="centered" # El contenido se centra en la página
)

# --- Configuración de la API Key de Gemini ---
# Después de st.set_page_config(), ahora puedes poner la lógica de la API Key.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    # No mostramos la advertencia si se carga correctamente con st.secrets
except (AttributeError, KeyError):
    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD3tqVFUePrWzc6qwsVP5L2z7VCqezfbv8")
    # Si la API Key no se carga desde st.secrets, entonces mostramos la advertencia aquí.
    st.warning("Advertencia: No se pudo cargar la API Key con st.secrets. Asegúrate de que .streamlit/secrets.toml esté configurado correctamente para producción.")

genai.configure(api_key=API_KEY)

# Usamos la última versión de Gemini Pro que admite 'generateContent'
# 'gemini-1.5-pro-latest' es la más avanzada.
model = genai.GenerativeModel('gemini-1.5-pro-latest') 

# --- Base de Datos de Recursos (Imágenes y Enlaces) ---
# ... (Tu diccionario RECURSOS_EDUCATIVOS se mantiene aquí) ...
RECURSOS_EDUCATIVOS = {
    "sii_inicio_sesion": "https://i.imgur.com/ejemplo_sii_inicio_sesion.png", 
    "sii_menu_tramites": "https://i.imgur.com/ejemplo_sii_menu_tramites.png",   
    "municipalidad_santiago_citas": "https://www.munistgo.cl/agendar-hora", 
    "municipalidad_providencia_tramites": "https://www.providencia.cl/tramites-online", 
    "municipalidad_maipu_tramites": "https://maipu.cl/tramites/", 
    "ejemplo_patente_municipal": "https://i.imgur.com/ejemplo_patente_municipal.png", 
}

# --- Función para interactuar con Gemini ---
def obtener_respuesta_gemini(pregunta_usuario):
    # ... (Esta función no necesita cambios) ...
    # Se ha omitido el contenido para brevedad.
    prompt_completo = f"""
    Eres un asistente virtual experto en la creación y habilitación de locales alimenticios en la Región Metropolitana de Chile.
    Tu objetivo es guiar a los usuarios paso a paso por los trámites del Servicio de Impuestos Internos (SII)
    y las municipalidades chilenas (especialmente en Santiago, Maipú y Providencia), proporcionando información clara, concisa y precisa.
    
    Cuando sea relevante, puedes hacer referencia a imágenes o enlaces específicos que ayuden al usuario a visualizar los pasos o acceder a información directa.
    Para ello, incluye el identificador del recurso entre corchetes con el prefijo `[RECURSO:identificador_recurso]`.
    Solo usa los identificadores que conoces de tu base de datos de recursos.
    
    Ejemplo de cómo referenciar un recurso:
    "Para iniciar actividades en el SII, busca el botón `[RECURSO:sii_inicio_sesion]`."
    "Puedes agendar una cita en la Municipalidad de Santiago aquí: `[RECURSO:municipalidad_santiago_citas]`."
    "La Municipalidad de Maipú tiene información relevante en `[RECURSO:municipalidad_maipu_tramites]`."
    
    Pregunta del usuario: {pregunta_usuario}
    
    Respuesta:
    """
    
    try:
        response = model.generate_content(prompt_completo)
        gemini_text = response.text
        
        recursos_para_mostrar = []
        
        matches = re.findall(r'\[RECURSO:([a-zA-Z0-9_]+)\]', gemini_text)
        
        for identificador in matches:
            if identificador in RECURSOS_EDUCATIVOS:
                recurso_url = RECURSOS_EDUCATIVOS[identificador]
                tipo_recurso = 'image' if any(recurso_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']) else 'link'
                
                recursos_para_mostrar.append({
                    'id': identificador,
                    'url': recurso_url,
                    'type': tipo_recurso
                })
                gemini_text = gemini_text.replace(f'[RECURSO:{identificador}]', '').strip()

        return gemini_text, recursos_para_mostrar

    except Exception as e:
        print(f"Error al conectar con Gemini o procesar la respuesta: {e}")
        st.error("Lo siento, hubo un problema al procesar tu solicitud. Por favor, inténtalo de nuevo.")
        return "Lo siento, no puedo responder en este momento.", []

# El resto de tu código de Streamlit va aquí, *después* de st.set_page_config()
st.title("🍔 Asistente para Abrir tu Local de Comida en Chile")
st.markdown("Soy tu guía virtual para los trámites del SII y municipalidades en la Región Metropolitana. ¡Pregúntame lo que necesites!")

# Inicializar el historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy para tu local de comida en Chile?"})

# Mostrar todos los mensajes del historial en la interfaz
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "resources" in message and message["resources"]:
            for res in message["resources"]:
                if res['type'] == 'image':
                    st.image(res['url'], caption=f"Referencia: {res['id'].replace('_', ' ').title()}", width=250)
                elif res['type'] == 'link':
                    st.markdown(f"**Ver más:** [{res['id'].replace('_', ' ').title()}]({res['url']})")

# Campo de entrada para el usuario
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("El asistente está pensando..."):
            response_text, resources_list = obtener_respuesta_gemini(prompt)
            st.markdown(response_text)
            
            if resources_list:
                for res in resources_list:
                    if res['type'] == 'image':
                        st.image(res['url'], caption=f"Referencia: {res['id'].replace('_', ' ').title()}", width=250)
                    elif res['type'] == 'link':
                        st.markdown(f"**Ver más:** [{res['id'].replace('_', ' ').title()}]({res['url']})")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "resources": resources_list 
            })
