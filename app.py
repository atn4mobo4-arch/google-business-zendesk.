import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Configuración de la API de Gemini ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Definimos el modelo generativo
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# --- Configuración de Flask ---
app = Flask(__name__)
CORS(app)

# --- Base de conocimiento para la IA ---
# Aquí es donde le damos el contexto a la IA sobre tus macros de Zendesk
contexto_macros = """
Eres un asistente de servicio al cliente. Tu trabajo es leer la descripción de un ticket de Zendesk y sugerir la macro más adecuada para responder. 
Debes ser conciso y solo devolver el nombre de la macro. Si no encuentras una coincidencia, devuelve "No se encontró una macro adecuada".

Aquí tienes una lista de macros y para qué se usan:
- Macro_Garantia: Para tickets que mencionan problemas de producto, fallos, reparaciones o defectos. Palabras clave: garantía, falla, producto, no funciona, roto.
- Macro_Facturacion: Para tickets relacionados con facturas, pagos, cargos, o montos. Palabras clave: factura, pago, monto, cargo, recibo.
- Macro_Asesoria: Para tickets que solicitan ayuda general o información sobre un producto. Palabras clave: ayuda, información, cómo, para qué sirve, asesoría.
- Macro_Envio: Para tickets sobre el estado de un pedido, demoras o problemas de entrega. Palabras clave: envío, entrega, rastreo, pedido, dónde está.
"""

# --- Rutas de la API ---

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route("/suggest", methods=["POST"])
def suggest_macro():
    try:
        data = request.get_json()
        issue_description = data.get("issue_description", "")

        if not issue_description:
            return jsonify({"error": "issue_description es requerido"}), 400

        # Conectamos con la IA de Gemini
        prompt = f"{contexto_macros}\n\nDescripción del ticket: {issue_description}"
        
        response = model.generate_content(prompt)
        macro_sugerida = response.text.strip()
        
        # Devolvemos la sugerencia a Zendesk
        return jsonify({
            "suggestions": {
                "macros": [macro_sugerida]
            }
        })

    except Exception as e:
        print(f"Error al procesar la solicitud: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Punto de entrada de la aplicación
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
