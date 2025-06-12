import streamlit as st
import google.generativeai as genai
import re
import os # Para acceder a variables de entorno si no usas st.secrets

# --- Configuración de la API Key de Gemini ---
# Opción 1 (Recomendado para Streamlit Cloud y producción): Usar st.secrets
# Si despliegas en Streamlit Cloud, debes añadir tu API_KEY a secrets.toml
# En PyCharm, crea una carpeta llamada '.streamlit' en la raíz de tu proyecto
# y dentro de ella un archivo llamado 'secrets.toml'.
# Dentro de secrets.toml, pon:
# GEMINI_API_KEY = "AIzaSyD3tqVFUePrWzc6qwsVP5L2z7VCqezfbv8"
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except (AttributeError, KeyError):
    # Opción 2 (Para desarrollo local si no quieres usar secrets.toml todavía):
    # Si NO CREAS secrets.toml, esta línea de fallback usará la clave directamente.
    # Es menos seguro pero sirve para pruebas rápidas.
    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD3tqVFUePrWzc6qwsVP5L2z7VCqezfbv8") # ¡Tu API Key ya está aquí!
    st.warning("Usando API Key directamente en el código o variable de entorno. Para producción, usa st.secrets.")


genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- Base de Datos de Recursos (Imágenes y Enlaces) ---
# **Importante:** Las URLs de las imágenes deben ser públicas (ej: subidas a Imgur, Google Cloud Storage, etc.).
# Los enlaces pueden ser a cualquier página web.
# ¡REEMPLAZA ESTAS URLs de ejemplo con las TUS REALES!
RECURSOS_EDUCATIVOS = {
    "sii_inicio_sesion": "https://i.imgur.com/tu_imagen_sii_inicio_sesion.png", # URL REAL DE TU IMAGEN
    "sii_menu_tramites": "https://i.imgur.com/tu_imagen_sii_menu_tramites.png", # URL REAL DE TU IMAGEN
    "municipalidad_santiago_citas": "https://www.munistgo.cl/agendar-hora", # URL REAL DEL ENLACE
    "municipalidad_providencia_tramites": "https://www.providencia.cl/tramites-online", # URL REAL DEL ENLACE
    "ejemplo_patente_municipal": "https://i.imgur.com/tu_imagen_patente_municipal.png", # URL REAL DE TU IMAGEN
    # Añade más recursos que tu IA pueda referenciar
    # Por ejemplo: "permiso_sanitario_seremi": "https://www.seremi-salud.cl/permiso-sanitario"
}

# --- Función para interactuar con Gemini ---
def obtener_respuesta_gemini(pregunta_usuario):
    """
    Envía una pregunta a Gemini y retorna su respuesta junto con los recursos
    (imágenes/enlaces) que el modelo sugiera.
    """
    prompt_completo = f"""
    Eres un asistente virtual experto en la creación y habilitación de locales alimenticios en la Región Metropolitana de Chile.
    Tu objetivo es guiar a los usuarios paso a paso por los trámites del Servicio de Impuestos Internos (SII)
    y las municipalidades chilenas (especialmente en Santiago y Maipú, dada la ubicación actual del usuario).
    Proporciona información clara, concisa y precisa.

    Si consideras que una imagen o un enlace puede complementar tu respuesta,
    incluye el identificador del recurso entre corchetes con el prefijo `[RECURSO:identificador_recurso]`.
    Solo usa los identificadores que te he proporcionado en tu conocimiento.

    Ejemplo de uso de recursos: "Para iniciar actividades en el SII, busca el botón `[RECURSO:sii_inicio_sesion]`."
    "Puedes agendar una cita en la Municipalidad de Santiago aquí: `[RECURSO:municipalidad_santiago_citas]`."
    "La Municipalidad de Maipú tiene información en `[RECURSO:municipalidad_maipu_tramites]`."

    Pregunta del usuario: {pregunta_usuario}

    Respuesta:
    """

    try:
        response = model.generate_content(prompt_completo)
        gemini_text = response.text

        recursos_para_mostrar = []

        # Encontrar todos los identificadores de recursos en el texto de Gemini
        # Esto buscará patrones como [RECURSO:nombre_del_recurso]
        matches = re.findall(r'\[RECURSO:([a-zA-Z0-9_]+)\]', gemini_text)

        for identificador in matches:
            if identificador in RECURSOS_EDUCATIVOS:
                recurso_url = RECURSOS_EDUCATIVOS[identificador]
                # Determinar si es una imagen o un enlace por la extensión o por una lista de extensiones comunes
                tipo_recurso = 'image' if any(recurso_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']) else 'link'

                recursos_para_mostrar.append({
                    'id': identificador,
                    'url': recurso_url,
                    'type': tipo_recurso
                })
                # Opcional: reemplazar el marcador en el texto para que no se muestre al usuario
                gemini_text = gemini_text.replace(f'[RECURSO:{identificador}]', '').strip()

        return gemini_text, recursos_para_mostrar

    except Exception as e:
        st.error(f"Error al conectar con Gemini o procesar la respuesta: {e}")
        return "Lo siento, hubo un problema al procesar tu solicitud. Por favor, inténtalo de nuevo.", []

# --- Interfaz de Streamlit ---

st.set_page_config(
    page_title="Asistente para Locales de Comida Chile",
    page_icon="🍔",
    layout="centered"
)

st.title("🍔 Asistente para Abrir tu Local de Comida en Chile")
st.markdown("Soy tu guía virtual para los trámites del SII y municipalidades. ¡Pregúntame lo que necesites!")

# Inicializar historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy para tu local de comida en Chile?"})

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "resources" in message and message["resources"]:
            for res in message["resources"]:
                if res['type'] == 'image':
                    st.image(res['url'], caption=f"Referencia: {res['id'].replace('_', ' ').title()}", width=200)
                elif res['type'] == 'link':
                    st.markdown(f"**Ver más:** [{res['id'].replace('_', ' ').title()}]({res['url']})")

# Campo de entrada de usuario
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # Añadir la pregunta del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Obtener respuesta del asistente y añadirla al historial
    with st.chat_message("assistant"):
        with st.spinner("El asistente está pensando..."): # Mensaje de carga
            response_text, resources_list = obtener_respuesta_gemini(prompt)
            st.markdown(response_text)

            # Mostrar los recursos asociados
            if resources_list:
                for res in resources_list:
                    if res['type'] == 'image':
                        st.image(res['url'], caption=f"Referencia: {res['id'].replace('_', ' ').title()}", width=200)
                    elif res['type'] == 'link':
                        st.markdown(f"**Ver más:** [{res['id'].replace('_', ' ').title()}]({res['url']})")

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "resources": resources_list # Almacenar recursos en el estado de la sesión para mostrarlos al recargar
            })