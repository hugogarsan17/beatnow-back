import smtplib
import ssl
from email.message import EmailMessage

from config.settings import SettingsError, get_settings

try:
    settings = get_settings()
except SettingsError as exc:
    raise RuntimeError("Failed to load mail configuration") from exc


def _get_email_credentials() -> tuple[str, str]:
    if not settings.email_sender or not settings.email_password:
        raise RuntimeError("Email credentials are not configured")
    return settings.email_sender, settings.email_password

def send_email(email_receiver: str, subject: str, body: str):
    try:
        print("Iniciando la creación del mensaje de correo electrónico.")
        em = EmailMessage()
        email_sender, email_password = _get_email_credentials()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.add_alternative(body, subtype='html')
        
        print("Mensaje de correo electrónico creado:")
        print(f"De: {em['From']}")
        print(f"Para: {em['To']}")
        print(f"Asunto: {em['Subject']}")
        
        context = ssl.create_default_context()
        
        print("Creando contexto SSL.")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            print("Conectando al servidor SMTP de Gmail.")
            smtp.login(email_sender, email_password)
            print("Inicio de sesión exitoso.")
            
            print("Enviando mensaje.")
            smtp.send_message(em)
            print("Correo enviado exitosamente.")
            
    except Exception as e:
        print(f"Error in send_email: {e}")