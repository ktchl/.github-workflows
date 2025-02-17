import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime
import pandas as pd
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Paramètres de connexion depuis les variables d'environnement
username = os.getenv("EMAIL_USERNAME")  # Utilise la variable d'environnement
password = os.getenv("EMAIL_PASSWORD")  # Utilise la variable d'environnement
to_email = 'ktanchaleune@sgmfamily.com'  # Utilise la variable d'environnement

if not username or not password or not to_email:
    print("Les informations de connexion ne sont pas définies dans les variables d'environnement.")
    exit()

# Se connecter au serveur IMAP Gmail
print("Connexion au serveur IMAP...")
mail = imaplib.IMAP4_SSL("imap.gmail.com")

# Se connecter avec vos identifiants
try:
    mail.login(username, password)
    print("Connexion réussie!")
except Exception as e:
    print(f"Erreur de connexion : {e}")
    exit()

# Sélectionner la boîte de réception
print("Sélection de la boîte de réception...")
mail.select("inbox")

# Recherche des emails avec l'objet "monétique" (en utilisant un encodage sécurisé)
print('Recherche des emails avec l\'objet "monétique"...')

# Encoder "monétique" en UTF-8
subject_search = 'SUBJECT "monetique"'.encode('utf-8')

# Recherche des emails
status, messages = mail.search(None, subject_search.decode('utf-8'))

if status != "OK":
    print("Erreur lors de la recherche des emails")
    exit()

# Limiter à 10 premiers emails pour éviter de traiter tous les messages
messages = messages[0].split()[:10]  # Limiter à 10 emails pour tester

# Récupérer la date du jour
today_date = datetime.today().strftime('%d-%b-%Y')  # Format : 17-Feb-2025

print(f"Date d'aujourd'hui : {today_date}")
print(f"{len(messages)} email(s) trouvé(s) avec l'objet 'monétique'.")

def send_email_with_attachment(filename, attachment_data, to_email):
    """
    Envoie un email avec une pièce jointe.
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # Utilisé pour TLS
    smtp_user = username  # Votre adresse email (Gmail)
    smtp_password = password  # Mot de passe ou mot de passe d'application

    # Créer le message
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = "Pièce jointe CSV - Monétique"

    # Ajouter le corps de l'email
    msg.attach(MIMEText("Veuillez trouver ci-joint le fichier CSV.", "plain"))

    # Ajouter la pièce jointe (le fichier CSV)
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment_data)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", f"attachment; filename={filename}"
    )
    msg.attach(part)

    # Se connecter au serveur SMTP et envoyer l'email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Sécuriser la connexion
        server.login(smtp_user, smtp_password)  # Se connecter avec vos identifiants
        text = msg.as_string()  # Convertir le message en chaîne de caractères
        server.sendmail(smtp_user, to_email, text)  # Envoyer l'email
        print(f"Email envoyé avec succès à {to_email} !")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
    finally:
        server.quit()  # Toujours fermer la connexion SMTP

# Parcourir les messages
for mail_id in messages:
    print(f"Récupération de l'email {mail_id}...")
    # Récupérer l'email par ID
    status, msg_data = mail.fetch(mail_id, "(RFC822)")
    
    if status != "OK":
        print(f"Erreur lors de la récupération de l'email {mail_id}")
        continue

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            # Analyser l'email
            msg = email.message_from_bytes(response_part[1])

            # Décoder l'objet de l'email
            subject, encoding = decode_header(msg["Subject"])[0]
            
            try:
                if isinstance(subject, bytes):
                    # Si l'encodage est inconnu ou invalide, forcer à utf-8 ou ignorer les erreurs
                    subject = subject.decode(encoding if encoding and encoding != "unknown-8bit" else "utf-8", errors="ignore")
            except Exception as e:
                print(f"Erreur de décodage pour l'objet de l'email: {e}")
                subject = subject.decode("utf-8", errors="ignore")  # Au cas où il y a une autre erreur

            print(f"Objet de l'email: {subject}")

            # Vérifier si l'objet est "monétique"
            if subject.lower() == "monetique":
                # Récupérer la date de l'email et la comparer avec la date du jour
                email_date = msg["Date"]
                msg_date = email.utils.parsedate(email_date)
                email_date_str = datetime(*msg_date[:6]).strftime('%d-%b-%Y')

                print(f"Date de l'email : {email_date_str}")

                if email_date_str == today_date:
                    print(f"Email daté de {today_date} et objet 'monétique' trouvé.")

                    # Vérifier si l'email contient des pièces jointes
                    if msg.is_multipart():
                        for part in msg.walk():
                            # Si la partie est une pièce jointe
                            content_disposition = str(part.get("Content-Disposition"))
                            if "attachment" in content_disposition:
                                # Récupérer le nom du fichier de la pièce jointe
                                filename = part.get_filename()

                                # Vérifier si le fichier est un CSV
                                if filename and filename.endswith(".csv"):
                                    print(f"Pièce jointe CSV trouvée : {filename}")

                                    # Lire la pièce jointe CSV directement en mémoire avec Pandas
                                    csv_data = part.get_payload(decode=True)  # Récupérer le contenu de la pièce jointe
                                    df = pd.read_csv(BytesIO(csv_data))  # Lire le CSV en DataFrame depuis la mémoire

                                    # Afficher les premières lignes du DataFrame
                                    print("Voici les premières lignes du fichier CSV:")
                                    print(df.head())  # Affiche les 5 premières lignes du DataFrame

                                    # Envoi de l'email avec la pièce jointe CSV
                                    send_email_with_attachment(filename, csv_data, to_email)
                                else:
                                    print(f"Pièce jointe ignorée (non CSV) : {filename}")
                else:
                    print(f"Email daté de {email_date_str} mais pas aujourd'hui.")

# Déconnexion
print("Déconnexion...")
mail.logout()
print("Déconnexion réussie.")
