import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from config import config

try:
    import resend
    HAS_RESEND = True
except ImportError:
    HAS_RESEND = False

class EmailNotifier:
    def __init__(self):
        self.provider = config.EMAIL_PROVIDER
        self.recipient = config.NOTIFICATION_RECIPIENT_EMAIL
        self.sender = config.SENDER_EMAIL
        
        if HAS_RESEND and config.RESEND_API_KEY:
            resend.api_key = config.RESEND_API_KEY

    def render_email_html(self, title: str, subject_name: str, summary_html: str, website_url: Optional[str] = None) -> str:
        """Constructs a responsive modern HTML email template for lecture recaps."""
        view_link = website_url or "#"
        
        return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Récap de cours - {title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f6f8;
            color: #1e293b;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: #ffffff;
            padding: 24px;
            text-align: left;
        }}
        .badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .title {{
            font-size: 22px;
            font-weight: 700;
            margin: 0;
        }}
        .content {{
            padding: 24px;
            line-height: 1.6;
        }}
        .button-container {{
            text-align: center;
            margin-top: 30px;
            margin-bottom: 10px;
        }}
        .button {{
            display: inline-block;
            background-color: #2563eb;
            color: #ffffff;
            text-decoration: none;
            padding: 12px 28px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 15px;
        }}
        .footer {{
            background-color: #f8fafc;
            border-top: 1px solid #e2e8f0;
            padding: 16px;
            text-align: center;
            font-size: 12px;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">{subject_name}</span>
            <h1 class="title">📚 Récapitulatif : {title}</h1>
        </div>
        <div class="content">
            {summary_html}
            
            <div class="button-container">
                <a href="{view_link}" class="button">Voir le cours complet & notes originales</a>
            </div>
        </div>
        <div class="footer">
            Pipeline GoodNotes • Retranscription automatique par Gemini OCR
        </div>
    </div>
</body>
</html>
"""

    def send_recap_email(self, title: str, subject_name: str, summary_markdown: str, note_id: Optional[str] = None) -> bool:
        """Sends the recap email to the configured recipient email address."""
        if not self.recipient:
            print("[Warning] NOTIFICATION_RECIPIENT_EMAIL not configured. Email notification skipped.")
            return False

        # Convert simple markdown linebreaks to basic HTML for email body
        summary_html = summary_markdown.replace("\n", "<br>").replace("**", "<b>").replace("<b>", "<b>", 1)

        html_body = self.render_email_html(title, subject_name, summary_html)
        subject_line = f"📚 Récap de cours [{subject_name}] - {title}"

        if self.provider == "resend" and HAS_RESEND and config.RESEND_API_KEY:
            try:
                resend.Emails.send({
                    "from": self.sender,
                    "to": self.recipient,
                    "subject": subject_line,
                    "html": html_body
                })
                print(f"[Email] Recap email sent successfully via Resend to {self.recipient}.")
                return True
            except Exception as e:
                print(f"[Email Error] Resend failed: {e}")
                return False

        elif self.provider == "smtp":
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject_line
                msg["From"] = self.sender
                msg["To"] = self.recipient

                part = MIMEText(html_body, "html")
                msg.attach(part)

                if config.SMTP_PORT == 465:
                    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as server:
                        if config.SMTP_USER and config.SMTP_PASSWORD:
                            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                        server.sendmail(self.sender, self.recipient, msg.as_string())
                else:
                    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
                        server.starttls()
                        if config.SMTP_USER and config.SMTP_PASSWORD:
                            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                        server.sendmail(self.sender, self.recipient, msg.as_string())

                print(f"[Email] Recap email sent successfully via SMTP to {self.recipient}.")
                return True
            except Exception as e:
                print(f"[Email Error] SMTP failed: {e}")
                return False
        else:
            print(f"[Mock Email] Simulated sending recap email for '{title}' to {self.recipient}.")
            return True
