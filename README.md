# Zendesk AI Backend

Este backend sirve para tu app de Zendesk privada.

Endpoints:
- /health → verificar backend activo
- /summarize → recibe ticket_text y devuelve resumen, etiquetas y macro sugerida

Despliegue:
1. Subir a GitHub (archivos descomprimidos)
2. Render:
   - Python 3
   - Build: pip install -r requirements.txt
   - Start: gunicorn app:app --bind 0.0.0.0:
3. Variables de entorno: OPENAI_API_KEY, ALLOWED_ORIGIN
4. Prueba: /health → {"ok": true}
5. Conecta tu app de Zendesk: BACKEND_BASE_URL = URL pública de Render
