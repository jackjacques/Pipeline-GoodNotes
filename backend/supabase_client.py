import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from config import config

class SupabaseHelper:
    def __init__(self):
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
            print("[Warning] Supabase URL or Service Role Key missing in environment.")
            self.client: Optional[Client] = None
        else:
            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

    def is_file_processed(self, gdrive_file_id: str) -> bool:
        if not self.client:
            return False
        response = self.client.table("notes").select("id").eq("gdrive_file_id", gdrive_file_id).execute()
        return len(response.data) > 0

    def get_or_create_subject(self, subject_name: str) -> Optional[str]:
        if not self.client or not subject_name:
            return None
        
        # Check if subject exists
        res = self.client.table("subjects").select("id").eq("name", subject_name).execute()
        if res.data:
            return res.data[0]["id"]
        
        # Create subject if missing
        insert_res = self.client.table("subjects").insert({"name": subject_name}).execute()
        if insert_res.data:
            return insert_res.data[0]["id"]
        return None

    def save_note(
        self,
        title: str,
        gdrive_file_id: str,
        subject_name: Optional[str] = None,
        school_name: Optional[str] = None,
        year_name: Optional[str] = None,
        summary: Optional[str] = None,
        full_transcription: Optional[str] = None,
        pdf_url: Optional[str] = None,
        page_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        if not self.client:
            print("[Mock] Saving note to Supabase (Supabase not configured)")
            return {"id": "mock-note-id", "title": title}

        # 1. Normalize clean subject name
        raw_sub = (subject_name or "Général").strip()
        clean_sub = raw_sub
        school = (school_name or "").strip()
        year = (year_name or "").strip()

        if raw_sub.startswith("["):
            import re
            m = re.match(r'^\[(.*?)\s*/\s*(.*?)\]\s*(.*)$', raw_sub)
            if m:
                if not school or school == "Général": school = m.group(1).strip()
                if not year or year == "Général": year = m.group(2).strip()
                clean_sub = m.group(3).strip()
            else:
                m2 = re.match(r'^\[(.*?)\]\s*(.*)$', raw_sub)
                if m2:
                    clean_sub = m2.group(2).strip()

        # 2. Infer school if missing or "Général"
        # 2. Strict Drive path classification (BME is 3A)
        full_text = f"{clean_sub} {title} {school} {year}".lower()
        if 'bme' in full_text:
            school = "Master BME"
            year = "3A"
        else:
            if not school or school == "Général":
                school = "TSP"
            if not year or year == "Général":
                if '1a' in full_text: year = "1A"
                elif '3a' in full_text or 'vap' in full_text: year = "3A"
                else: year = "2A"

        formatted_subject = f"[{school} / {year}] {clean_sub}"
        subject_id = self.get_or_create_subject(clean_sub)

        # Upsert note record
        data = {
            "title": title,
            "gdrive_file_id": gdrive_file_id,
            "subject_id": subject_id,
            "subject_name": formatted_subject,
            "summary": summary or "",
            "full_transcription": full_transcription or "",
            "pdf_url": pdf_url or "",
            "page_count": page_count
        }

        try:
            existing = self.client.table("notes").select("id").eq("gdrive_file_id", gdrive_file_id).execute()
            if existing.data:
                note_id = existing.data[0]["id"]
                res = self.client.table("notes").update(data).eq("id", note_id).execute()
            else:
                res = self.client.table("notes").insert(data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"[Supabase Error] Failed to save note record ({e})")
            return None

    def save_note_page(self, note_id: str, page_number: int, transcription: str, image_url: Optional[str] = None):
        if not self.client:
            return
        data = {
            "note_id": note_id,
            "page_number": page_number,
            "transcription": transcription,
            "image_url": image_url or ""
        }
        self.client.table("note_pages").insert(data).execute()

    def upload_storage_file(self, local_file_path: str, storage_path: str) -> Optional[str]:
        """Uploads a file to Supabase Storage bucket and returns public URL."""
        if not self.client:
            return None
        bucket = config.SUPABASE_STORAGE_BUCKET
        try:
            with open(local_file_path, "rb") as f:
                file_bytes = f.read()
            self.client.storage.from_(bucket).upload(storage_path, file_bytes, file_options={"upsert": "true"})
            url_res = self.client.storage.from_(bucket).get_public_url(storage_path)
            return url_res
        except Exception as e:
            print(f"[Supabase Storage Error] Failed to upload {local_file_path}: {e}")
            return None
