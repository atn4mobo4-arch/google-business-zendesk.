from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import json
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai

# Carga variables de entorno desde .env (para pruebas locales)
load_dotenv()

# --- Configuración de la App Flask ---
app = Flask(__name__)
# Habilita CORS para que tu app de Zendesk pueda comunicarse con el backend
CORS(app) 

# Origen permitido para CORS
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")

# --- Configuración de Gemini ---
# Obtener la clave de la variable de entorno
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Error: No se encontró la GEMINI_API_KEY en las variables de entorno.")
else:
    genai.configure(api_key=gemini_api_key)

# --- Configuración de Google Sheets ---
try:
    google_credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(google_credentials_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    
    GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Sheet1")
    
    spreadsheet = gc.open_by_url(GOOGLE_SHEET_URL)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    
    SHEET_DATA_HEADERS = worksheet.row_values(1)
    SHEET_DATA_ROWS = worksheet.get_all_values()[1:]
    
    print("Datos de Google Sheet cargados exitosamente.")

except Exception as e:
    print(f"Error al cargar Google Sheet: {e}")
    SHEET_DATA_HEADERS = []
    SHEET_DATA_ROWS = []
    gc = None

# --- Rutas de la API ---
@app.route("/health", methods=["GET"])
def health():
    """Endpoint para verificar si el servicio está funcionando."""
    return jsonify({"ok": True})

@app.route("/summarize", methods=["POST"])
def summarize():
    """
    Endpoint principal para procesar tickets de Zendesk.
    Recibe el texto del ticket, lo analiza y devuelve sugerencias.
    """
    data = request.json
    ticket_text = data.get("ticket_text", "")
    
    # Obtener sugerencias de la hoja de cálculo
    field_suggestions = get_suggestions_from_sheet(ticket_text)
    
    # Generar la respuesta usando Gemini
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Basado en el siguiente texto, genera un resumen breve y una respuesta sugerida para un agente de soporte. \n\nTEXTO: {ticket_text}"
        response_gemini = model.generate_content(prompt)
        # Esto es un ejemplo, puedes ajustar el prompt para obtener los datos en formato JSON
        # o procesar el texto de forma más avanzada
        
        # Separar el resumen y la respuesta del texto de Gemini
        summary_gemini = f"Resumen: {response_gemini.text[:100]}..." 
        suggested_response_gemini = response_gemini.text
        
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        summary_gemini = "No se pudo generar un resumen."
        suggested_response_gemini = "No se pudo generar una respuesta sugerida."
    
    # Preparar la respuesta JSON para la app de Zendesk
    response_payload = {
        # Campos generados por Gemini
        "summary": summary_gemini,
        "suggested_response": suggested_response_gemini,
        
        # Campos obtenidos de la hoja de cálculo
        "formulario": field_suggestions.get("Formulario", "General"),
        "prioridad": field_suggestions.get("Prioridad", "Normal"),
        "tipo_asesoria": field_suggestions.get("Tipo de Asesoría", "No clasificado"),
        "dirigida_a": field_suggestions.get("Dirigida a", ""), # Vacío como lo solicitaste
        "titulo_ticket": field_suggestions.get("Etiqueta", "Ticket sin clasificar"), # Mapeado de 'Etiqueta'
        "tags": field_suggestions.get("Etiquetas", []), # Tomado de la hoja, si la tienes
        "macro": field_suggestions.get("Macro Sugerida", "Macro sugerida genérica")
    }

    print("Respuesta enviada a Zendesk:", json.dumps(response_payload, indent=2))

    res = jsonify(response_payload)
    res.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
    return res

# --- Funciones auxiliares (Lógica de Negocio) ---

def get_suggestions_from_sheet(ticket_text):
    """
    Busca en los datos de la hoja de cálculo (cargados al inicio)
    coincidencias con el texto del ticket y devuelve las sugerencias.
    """
    suggestions = {}
    if not SHEET_DATA_HEADERS or not SHEET_DATA_ROWS:
        print("Advertencia: No se cargaron los datos de Google Sheet.")
        return suggestions

    ticket_text_lower = ticket_text.lower()
    
    # Creamos un mapa de encabezados para fácil acceso
    headers_map = {header.lower().replace(" ", "_"): header for header in SHEET_DATA_HEADERS}
    
    for row_values in SHEET_DATA_ROWS:
        row_dict = dict(zip(SHEET_DATA_HEADERS, row_values))
        
        keywords_str = row_dict.get("Keywords", "").lower()
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        
        for keyword in keywords:
            if keyword in ticket_text_lower:
                suggestions = {
                    "Formulario": row_dict.get(headers_map.get("formulario"), ""),
                    "Prioridad": row_dict.get(headers_map.get("prioridad"), ""),
                    "Tipo de Asesoría": row_dict.get(headers_map.get("tipo_de_asesoria"), ""),
                    "Dirigida a": "",
                    "Etiqueta": row_dict.get(headers_map.get("etiqueta"), ""),
                    "Macro Sugerida": row_dict.get(headers_map.get("macro_sugerida"), ""),
                    "Etiquetas": [tag.strip() for tag in row_dict.get(headers_map.get("etiquetas"), "").split(',') if tag.strip()]
                }
                print(f"Coincidencia encontrada con palabra clave: '{keyword}'.")
                return suggestions
                
    print("No se encontraron coincidencias en la hoja de cálculo para el ticket.")
    return suggestions

# --- Punto de entrada principal para Render ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

