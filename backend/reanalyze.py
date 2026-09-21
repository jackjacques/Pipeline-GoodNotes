import os
import sys
import tempfile
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from supabase_client import SupabaseHelper
from ocr_processor import GeminiOCRProcessor
from gdrive_sync import GoogleDriveSync
from main import log_msg

def reanalyze_note_by_id(note_id: str) -> bool:
    """Force re-analysis of a single note by note_id using original PDF from Google Drive."""
    supabase = SupabaseHelper()
    ocr = GeminiOCRProcessor()
    gdrive = GoogleDriveSync()
    
    # 1. Fetch note from Supabase
    res = supabase.client.table("notes").select("*").eq("id", note_id).execute()
    if not res.data:
        log_msg(f"❌ Note with ID '{note_id}' not found in Supabase.")
        return False
        
    note = res.data[0]
    gdrive_file_id = note.get("gdrive_file_id")
    title = note.get("title", "Sans titre")
    subject_name = note.get("subject_name", "Général")

    log_msg(f"⚡ Launching AI Re-Analysis for Note '{title}' (ID: {note_id}, Drive ID: {gdrive_file_id})...")

    if not gdrive_file_id or gdrive_file_id.startswith("mock-") or gdrive_file_id.startswith("local-"):
        log_msg(f"⚠️ Note '{title}' does not have a valid Google Drive file ID for re-analysis.")
        return False

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        temp_pdf_path = tmp.name

    try:
        log_msg(f"📥 Downloading original PDF from Google Drive...")
        if gdrive.download_file(gdrive_file_id, temp_pdf_path):
            # Process OCR with Gemini
            pages_data, full_transcription, summary, image_paths = ocr.process_pdf(
                pdf_path=temp_pdf_path,
                title=title,
                subject_name=subject_name
            )

            # Update Supabase note record
            supabase.client.table("notes").update({
                "full_transcription": full_transcription,
                "summary": summary
            }).eq("id", note_id).execute()

            # Update pages
            for page in pages_data:
                page_num = page["page_number"]
                transcription = page["transcription"]
                supabase.client.table("note_pages").upsert({
                    "note_id": note_id,
                    "page_number": page_num,
                    "transcription": transcription
                }).execute()

            log_msg(f"✅ AI Re-Analysis successfully completed for '{title}'!")
            return True
        else:
            log_msg(f"❌ Failed to download file from Google Drive (ID: {gdrive_file_id})")
            return False
    except Exception as e:
        log_msg(f"❌ Error during AI re-analysis: {e}")
        return False
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

def reanalyze_all_notes() -> bool:
    """Force re-analysis of all PDF notes in Google Drive."""
    supabase = SupabaseHelper()
    ocr = GeminiOCRProcessor()
    gdrive = GoogleDriveSync()

    log_msg("⚡ Launching AI Re-Analysis for ALL documents in Google Drive...")
    pdf_files = gdrive.list_pdf_files()

    if not pdf_files:
        log_msg("⚠️ No PDF files found in Google Drive.")
        return False

    count = 0
    for pdf_info in pdf_files:
        try:
            file_id = pdf_info["id"]
            title = pdf_info["title"]
            subject_name = pdf_info.get("subject", "Général")
            school_name = pdf_info.get("school", "Général")
            year_name = pdf_info.get("year", "Général")

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf_path = tmp.name

            log_msg(f"📥 Downloading & Re-analyzing '{title}'...")
            if gdrive.download_file(file_id, temp_pdf_path):
                pages_data, full_transcription, summary, image_paths = ocr.process_pdf(
                    pdf_path=temp_pdf_path,
                    title=title,
                    subject_name=subject_name
                )

                supabase.save_note(
                    title=title,
                    gdrive_file_id=file_id,
                    subject_name=subject_name,
                    school_name=school_name,
                    year_name=year_name,
                    summary=summary,
                    full_transcription=full_transcription,
                    page_count=len(pages_data)
                )

                count += 1
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

        except Exception as err:
            log_msg(f"❌ Error re-analyzing file '{pdf_info.get('name')}': {err}")

    log_msg(f"✅ Finished AI Re-Analysis of {count} documents!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Force AI Re-Analysis of original GoodNotes PDFs")
    parser.add_argument("--note-id", type=str, help="ID of specific note in Supabase to re-analyze")
    parser.add_argument("--all", action="store_true", help="Re-analyze all PDF notes in Google Drive")

    args = parser.parse_args()

    if args.note_id:
        reanalyze_note_by_id(args.note_id)
    elif args.all:
        reanalyze_all_notes()
    else:
        print("Please specify --note-id <ID> or --all")
