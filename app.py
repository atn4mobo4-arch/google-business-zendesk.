from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import json

# Carga variables de entorno desde .env
load_dotenv()

# Crear la app Flask
app = Flask(__name__)

# Origen permitido para CORS (tu Zendesk)
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")

# ====================
# Rutas
# ====================

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

# Endpoint principal para resumir tickets
@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    ticket_text = data.get("ticket_text", "")
    
    # Detectar idioma
    language = detect_language(ticket_text)
    
    # Generar resumen
    summary = summarize_ticket(ticket_text, language)
    
    # Sugerir etiquetas
    tags = suggest_tags(ticket_text)
    
    # Sugerir macro
    macro = suggest_macro(ticket_text)
    
    response = {
        "summary": summary,
        "tags": tags,
        "macro": macro,
        "language": language
    }

    # Agregar CORS
    res = jsonify(response)
    res.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
    return res

# ====================
# Funciones auxiliares (reemplaza con tu lógica real)
# ====================

def detect_language(text):
    # Dummy: detecta español si hay acentos, inglés si no
    return "es" if any(c in "áéíóú" for c in text) else "en"

def summarize_ticket(text, language):
    # Aquí podrías conectar con OpenAI
    return "Resumen breve del ticket"

def suggest_tags(text):
    # Aquí podrías usar Google Sheets o un set básico
    basic_tags = ["billing", "warranty", "shipping", "account", "technical"]
    return basic_tags[:3]

def suggest_macro(text):
    # Selecciona la macro sugerida
    return "Macro sugerida"

# ====================
# Main
# ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

