from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import json

load_dotenv()

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    ticket_text = data.get("ticket_text", "")
    language = detect_language(ticket_text)
    summary = summarize_ticket(ticket_text, language)
    tags = suggest_tags(ticket_text)
    macro = suggest_macro(ticket_text)
    
    response = {
        "summary": summary,
        "tags": tags,
        "macro": macro,
        "language": language
    }

    res = jsonify(response)
    res.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
    return res

def detect_language(text):
    return "es" if any(c in "áéíóú" for c in text) else "en"

def summarize_ticket(text, language):
    return "Resumen breve del ticket"

def suggest_tags(text):
    basic_tags = ["billing", "warranty", "shipping", "account", "technical"]
    return basic_tags[:3]

def suggest_macro(text):
    return "Macro sugerida"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
