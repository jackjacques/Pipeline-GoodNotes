import os
import sys
import time
import argparse
import tempfile
from typing import Optional

# Ensure backend module directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from supabase_client import SupabaseHelper
from ocr_processor import GeminiOCRProcessor
from gdrive_sync import GoogleDriveSync
from email_notifier import EmailNotifier

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline_daemon.log")

def log_msg(msg: str):
    print(msg, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

def process_single_pdf(
    pdf_path: str,
    title: str,
    subject_name: str,
    gdrive_file_id: str,
    supabase: SupabaseHelper,
    ocr: GeminiOCRProcessor,
    email: EmailNotifier,
    school_name: str = "Général",
    year_name: str = "Général"
):
    """Processes a single PDF file through the complete pipeline."""
    print(f"\n==========================================")
    print(f"🚀 Processing: {title} (École: {school_name} | Année: {year_name} | Matière: {subject_name})")
    print(f"==========================================")

    # 1. OCR & Transcription via Gemini Vision
    pages_data, full_transcription, summary, image_paths = ocr.process_pdf(
        pdf_path=pdf_path,
        title=title,
        subject_name=subject_name
    )

    # 2. Upload images to Supabase Storage if configured
    page_urls = []
    for i, page in enumerate(pages_data):
        img_path = page["image_path"]
        storage_dest = f"notes/{gdrive_file_id}/page_{page['page_number']}.png"
        public_url = supabase.upload_storage_file(img_path, storage_dest)
        page_urls.append(public_url)
        page["image_url"] = public_url

    # 3. Save Note metadata & transcription to Supabase Database
    print("  [Supabase] Saving note & transcription record...")
    saved_note = supabase.save_note(
        title=title,
        gdrive_file_id=gdrive_file_id,
        subject_name=subject_name,
        school_name=school_name,
        year_name=year_name,
        summary=summary,
        full_transcription=full_transcription,
        page_count=len(pages_data)
    )

    note_id = saved_note.get("id") if saved_note else "mock-id"

    # Save pages
    for page in pages_data:
        supabase.save_note_page(
            note_id=note_id,
            page_number=page["page_number"],
            transcription=page["transcription"],
            image_url=page.get("image_url")
        )

    # 4. Send Email Recap
    print("  [Email] Sending session recap notification...")
    email.send_recap_email(
        title=title,
        subject_name=f"[{school_name}] {subject_name}",
        summary_markdown=summary,
        note_id=note_id
    )

    print(f"✅ Successfully processed {title}!")

def run_pipeline_step(once: bool = False):
    """Executes a scan pass over Google Drive."""
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    
    log_msg("\n-------------------------------------------------")
    log_msg("🔄 Starting GoodNotes Pipeline Google Drive Scan...")
    log_msg("-------------------------------------------------\n")

    supabase = SupabaseHelper()
    ocr = GeminiOCRProcessor()
    gdrive = GoogleDriveSync()
    email = EmailNotifier()

    while True:
        try:
            log_msg("🔍 Checking Google Drive for PDF exports...")
            pdf_files = gdrive.list_pdf_files()

            if not pdf_files:
                log_msg("  No PDF files found or Google Drive API credentials not set.")
            else:
                log_msg(f"  Found {len(pdf_files)} PDF files in Google Drive.")
                new_count = 0
                for pdf_info in pdf_files:
                    try:
                        file_id = pdf_info["id"]
                        title = pdf_info["title"]
                        subject_name = pdf_info.get("subject", "Général")
                        school_name = pdf_info.get("school", "Général")
                        year_name = pdf_info.get("year", "Général")

                        # Process if file not in database
                        if not supabase.is_file_processed(file_id):
                            new_count += 1
                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                                temp_pdf_path = tmp.name

                            log_msg(f"📥 Downloading new file '{pdf_info['name']}' ({school_name} / {year_name} / {subject_name})...")
                            if gdrive.download_file(file_id, temp_pdf_path):
                                process_single_pdf(
                                    pdf_path=temp_pdf_path,
                                    title=title,
                                    subject_name=subject_name,
                                    school_name=school_name,
                                    year_name=year_name,
                                    gdrive_file_id=file_id,
                                    supabase=supabase,
                                    ocr=ocr,
                                    email=email
                                )
                                if os.path.exists(temp_pdf_path):
                                    os.remove(temp_pdf_path)

                    except Exception as file_err:
                        log_msg(f"❌ Error processing file '{pdf_info.get('name')}': {file_err}")
                
                if new_count == 0:
                    log_msg("  All PDF files are up to date in Supabase.")

        except Exception as e:
            log_msg(f"❌ Error in pipeline step: {e}")

        if once:
            log_msg("✅ Scan pass finished.")
            break

        time.sleep(config.CHECK_INTERVAL_SECONDS)

def main():
    parser = argparse.ArgumentParser(description="GoodNotes PDF OCR Pipeline & Supabase Sync")
    parser.add_argument("--test-file", type=str, help="Path to a local PDF file for testing")
    parser.add_argument("--title", type=str, default="Cours de Test", help="Title of the test lecture")
    parser.add_argument("--subject", type=str, default="Mathématiques", help="Subject name of the test lecture")
    parser.add_argument("--once", action="store_true", help="Run a single scan pass on Google Drive and exit")

    args = parser.parse_args()

    if args.test_file:
        if not os.path.exists(args.test_file):
            print(f"Error: Specified test file '{args.test_file}' does not exist.")
            sys.exit(1)
            
        print("Running pipeline in test mode on local PDF file...")
        supabase = SupabaseHelper()
        ocr = GeminiOCRProcessor()
        email = EmailNotifier()

        process_single_pdf(
            pdf_path=args.test_file,
            title=args.title,
            subject_name=args.subject,
            gdrive_file_id=f"local-test-{int(time.time())}",
            supabase=supabase,
            ocr=ocr,
            email=email
        )
    else:
        run_pipeline_step(once=args.once)

if __name__ == "__main__":
    main()
