import smtplib
import ssl
from email.message import EmailMessage

EMAIL_SENDER = 'beatnowinfo@gmail.com'
EMAIL_PASSWORD = 'qowkdxcphexfjjyr'


def send_email(email_receiver: str, subject: str, body: str):
    try:
        print("Iniciando la creación del mensaje de correo electrónico.")
        em = EmailMessage()
        em['From'] = EMAIL_SENDER
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
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            print("Inicio de sesión exitoso.")
            
            print("Enviando mensaje.")
            smtp.send_message(em)
            print("Correo enviado exitosamente.")
            
    except Exception as e:
        print(f"Error in send_email: {e}")