# Chatbot Ads Manager (WhatsApp + Google Ads Automation)

Backend desarrollado en Flask que recibe mensajes de WhatsApp vía webhooks e integra Google Ads, Google Sheets y Firestore para gestionar flujos de chatbot, registro de usuarios y estados operativos de campañas.

## Prop�sito del proyecto

Automatizar la atención y el seguimiento de usuarios interesados en publicidad digital, reduciendo fricción operativa y dependencia de procesos manuales.  
El sistema centraliza el control de flujos para asegurar coherencia, trazabilidad y continuidad en cada interacción, facilitando la ejecución de campañas y garantizando una experiencia uniforme tanto para el usuario final como para el equipo operativo.

## Alcance y funcionalidades
- Recepción y validación de webhooks de WhatsApp, con envío de respuestas vía Graph API.
- Respuestas conversacionales con OpenAI y detección de intenciones predefinidas.
- Registro y lectura de historial de conversación en Firestore (con alternativa local si se desactiva).
- Registro de usuarios y actualización de campos operativos en Google Sheets.
- Agente conversacional que recopila datos de campaña (nombre, títulos, descripciones, keywords, presupuesto) y los guarda en la hoja.
- Scripts para crear campañas y anuncios en Google Ads.
- Monitores que procesan estados en Google Sheets y sincronizan datos con Google Ads.

## Arquitectura general / flujo de trabajo
Flujo principal (aplicación):
1. WhatsApp envía eventos al endpoint `/webhook` (Flask).
2. El backend valida el token, guarda el mensaje y recupera historial desde Firestore.
3. Si el usuario no completó datos de campaña, se activa el agente que pregunta y completa campos en Google Sheets.
4. Si ya hay datos suficientes, se responde con intenciones predefinidas o con OpenAI según el caso.
5. Monitores de Google Sheets detectan estados y ejecutan scripts:
   - `incomplete` ? crea campaña en Google Ads.
   - `campaign processing` ? recupera y guarda detalles de campaña.
   - `campaign ready` ? crea anuncios/grupos y actualiza estado.
   - `ad processing` ? consulta grupos de anuncios y actualiza la hoja.

Infraestructura operativa en GCP (configurada externamente, no incluida en el repo):
- Cloud Run (ejecución del servicio).
- Cloud Scheduler (ejecución periódica de monitores).
- Artifact Registry (almacenamiento de imágenes/artefactos).
- Firestore (persistencia del historial).

## Estructura del proyecto
```
/ (raíz)
+- src/                      # Código fuente principal
�  +- server.py              # App Flask y rutas base
�  +- routes.py              # Webhook de WhatsApp
�  +- config.py              # Configuración y variables de entorno
�  +- chatbot.py             # Orquestación de respuestas
�  +- data/                  # Persistencia (Firestore / local) y conectores
�  +- services/              # Lógica de intenciones, agentes y respuestas
�  +- google_ads/            # Scripts y helpers de Google Ads
�  +- google_sheets/         # Monitores de Google Sheets
+- app.yaml                  # Config App Engine
+- app-monitors.yaml         # Config App Engine para monitores
+- requirements.txt          # Dependencias Python
+- Dockerfile                # Contenedor (si aplica)
+- start_monitors.sh         # Script de arranque de monitores
+- google-ads.yaml           # Configuración SDK Google Ads (sin secretos en README)
+- .env                      # Variables de entorno (no versionar)
+- Credentials*.json         # Credenciales de servicios (no versionar)
```

## Requisitos previos
- Python 3.10+ (recomendado).
- OpenAI API Key (para respuestas conversacionales).
- Cuenta y proyecto en Google Cloud con Firestore habilitado.
- Credenciales de servicio para Google Sheets y Firestore.
- Acceso aprobado a Google Ads API (restringida; requiere aprobaci�n previa).
- Acceso a WhatsApp Business API (Meta) y sus credenciales.

## Configuraci�n (variables de entorno y credenciales, sin exponer secretos)
### Variables de entorno
Crea un archivo `.env` con las siguientes variables (no las publiques):

- `VERIFY_TOKEN` (token de verificación para el webhook de WhatsApp)
- `ACCESS_TOKEN` (token de acceso de WhatsApp Business API)
- `PHONE_NUMBER_ID` (ID del número de WhatsApp Business)
- `OPENAI_API_KEY` (API key de OpenAI)

### Credenciales y archivos sensibles
- `CredentialsGoogleFirestore.json` (service account para Firestore).
- `CredentialsGoogleSheets.json` (service account para Google Sheets).
- `CredentialsGoogleAds.json` / `CredentialsBusinessProfile.json` (según integraciones activas).
- `google-ads.yaml` (configuración del SDK de Google Ads).

Recomendación: mantén estos archivos fuera del repositorio y usa `.gitignore`.

## Instalación
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Ejecución local
1. Asegura que `.env` y las credenciales están configuradas localmente.
2. Inicia el servidor Flask:

```bash
python src/server.py
```

Opcional: iniciar monitores de Google Sheets (si est�n configurados):

```bash
./start_monitors.sh
```

## Despliegue (App Engine / Docker)
### App Engine
El repositorio incluye configuraciones listas para App Engine:
- `app.yaml` (servicio principal con `gunicorn`).
- `app-monitors.yaml` (servicio separado para ejecutar los monitores de Google Sheets).

Ejemplo de despliegue:
```bash
gcloud app deploy app.yaml
gcloud app deploy app-monitors.yaml
```

### Docker + Artifact Registry + Cloud Run + Cloud Scheduler
El `Dockerfile` permite contenerizar el servicio para publicarlo en Artifact Registry y ejecutarlo en Cloud Run. Cloud Scheduler puede invocar el servicio periódicamente (por ejemplo, cada minuto) para revisar Google Sheets y disparar la creación de campañas/anuncios en Google Ads.

## Contribución
Las contribuciones son bienvenidas. Por favor:
1. Abre un issue para discutir cambios mayores.
2. Crea un fork y una rama con un nombre descriptivo.
3. Envía un pull request con una descripción clara del cambio y su objetivo.

## Licencia
Este proyecto es propietario (All rights reserved). Se permite usar la lógica y técnicas con atribución explícita al autor, pero está prohibido presentar este proyecto con otro nombre sin autorización expresa.

