import os
from dotenv import load_dotenv
import resend 

# Cargar variables del .env
load_dotenv()

api_key = os.getenv("RESEND_API_KEY")
frontend_url = os.getenv("FRONTEND_URL")

resend.api_key = api_key

def enviar_correo_recuperacion(destinatario: str, token: str):
    link = f"{frontend_url}/cambiar-contra?token={token}"

    with open("templates/recuperacion.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    # Reemplazar el link del botón por el dinámico
    html_content = html_content.replace(
        "{{ link }}",
        link
    )

    resend.Emails.send({
        "from": "grupo4PW@resend.dev",
        "to": destinatario,
        "subject": "Recuperación de contraseña",
        "html": html_content
    })

def enviar_correo_contraseña(destinatario: str, contra: str):
    with open("templates/nuevaContra.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    html_content = html_content.replace(
        "{{contraseña}}",
        contra
    )

    resend.Emails.send({
        "from": "grupo4PW@resend.dev",
        "to": destinatario,
        "subject": "Cambio de contraseña",
        "html": html_content
    })    