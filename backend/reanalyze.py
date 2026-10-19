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

            # Upload images to Supabase storage
            for page in pages_data:
                img_path = page["image_path"]
                storage_dest = f"notes/{gdrive_file_id}/page_{page['page_number']}.png"
                public_url = supabase.upload_storage_file(img_path, storage_dest)
                page["image_url"] = public_url

            # Generate course quiz (15 questions)
            log_msg(f"🎯 Generating AI Course Quiz for '{title}' (15 questions)...")
            quiz = ocr.generate_course_quiz(full_transcription, title, subject_name, num_questions=15)

            # Update Supabase note record
            update_data = {
                "full_transcription": full_transcription,
                "summary": summary,
                "page_count": len(pages_data),
                "quiz": quiz
            }
            try:
                supabase.client.table("notes").update(update_data).eq("id", note_id).execute()
            except Exception as e_quiz:
                if "notes.quiz" in str(e_quiz):
                    del update_data["quiz"]
                    supabase.client.table("notes").update(update_data).eq("id", note_id).execute()
                else:
                    raise e_quiz

            # Clean and re-insert pages
            supabase.client.table("note_pages").delete().eq("note_id", note_id).execute()
            for page in pages_data:
                supabase.save_note_page(
                    note_id=note_id,
                    page_number=page["page_number"],
                    transcription=page["transcription"],
                    image_url=page.get("image_url")
                )

            log_msg(f"✅ AI Re-Analysis successfully completed for '{title}' ({len(pages_data)} pages)!")
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

def reanalyze_all_notes(subject_filter: Optional[str] = None) -> bool:
    """Force re-analysis of PDF notes in Google Drive, optionally filtered by subject/folder name."""
    supabase = SupabaseHelper()
    ocr = GeminiOCRProcessor()
    gdrive = GoogleDriveSync()

    log_msg(f"⚡ Launching AI Re-Analysis (filter: {subject_filter or 'ALL'})...")
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

            if subject_filter:
                filter_lower = subject_filter.lower()
                subj_match = filter_lower in subject_name.lower() or filter_lower in title.lower()
                if not subj_match:
                    continue

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf_path = tmp.name

            log_msg(f"📥 Downloading & Re-analyzing '{title}' ({subject_name})...")
            if gdrive.download_file(file_id, temp_pdf_path):
                pages_data, full_transcription, summary, image_paths = ocr.process_pdf(
                    pdf_path=temp_pdf_path,
                    title=title,
                    subject_name=subject_name
                )

                # Upload page images
                for page in pages_data:
                    img_path = page["image_path"]
                    storage_dest = f"notes/{file_id}/page_{page['page_number']}.png"
                    public_url = supabase.upload_storage_file(img_path, storage_dest)
                    page["image_url"] = public_url

                saved_note = supabase.save_note(
                    title=title,
                    gdrive_file_id=file_id,
                    subject_name=subject_name,
                    school_name=school_name,
                    year_name=year_name,
                    summary=summary,
                    full_transcription=full_transcription,
                    page_count=len(pages_data)
                )

                note_id = saved_note.get("id") if saved_note else None
                if note_id:
                    supabase.client.table("note_pages").delete().eq("note_id", note_id).execute()
                    for page in pages_data:
                        supabase.save_note_page(
                            note_id=note_id,
                            page_number=page["page_number"],
                            transcription=page["transcription"],
                            image_url=page.get("image_url")
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
    parser.add_argument("--subject", type=str, help="Filter by subject / folder name (e.g. 'Advanced Imaging')")
    parser.add_argument("--all", action="store_true", help="Re-analyze all PDF notes in Google Drive")

    args = parser.parse_args()

    if args.note_id:
        reanalyze_note_by_id(args.note_id)
    elif args.subject:
        reanalyze_all_notes(subject_filter=args.subject)
    elif args.all:
        reanalyze_all_notes()
    else:
        print("Please specify --note-id <ID>, --subject <NAME>, or --all")
