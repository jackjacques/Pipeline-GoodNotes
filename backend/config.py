import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from root or backend directory
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=env_path)

class Config:
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "notes-files")

    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Google Drive
    GDRIVE_FOLDER_ID: str = os.getenv("GDRIVE_FOLDER_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "backend/credentials.json")

    # Email
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "resend").lower()
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    NOTIFICATION_RECIPIENT_EMAIL: str = os.getenv("NOTIFICATION_RECIPIENT_EMAIL", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "notes@yourdomain.com")

    # SMTP Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "ssl0.ovh.net")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # Pipeline Settings
    CHECK_INTERVAL_SECONDS: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
    EXCLUDED_FOLDERS: list = ["Perso", "perso", "Personal", "Trash", "Archives", "1A", "2A", "1a", "2a"]

config = Config()
