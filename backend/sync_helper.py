import os
import sys
import json
import argparse
import tempfile
import pymupdf

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gdrive_sync import GoogleDriveSync
from supabase_client import SupabaseHelper

def list_pending():
    """Lists files in Google Drive that have not yet been synced to Supabase."""
    g = GoogleDriveSync()
    s = SupabaseHelper()
    
    files = g.list_pdf_files()
    pending = []
    for f in files:
        if not s.is_file_processed(f["id"]):
            pending.append(f)
            
    print(json.dumps(pending, ensure_ascii=False, indent=2))
    return pending

def prepare_images(file_id: str, output_dir: str = None):
    """Downloads a PDF from Google Drive and renders each page to PNG."""
    g = GoogleDriveSync()
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix=f"note_{file_id}_")
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_path = os.path.join(output_dir, "document.pdf")
    if not g.download_file(file_id, pdf_path):
        print(json.dumps({"error": f"Failed to download file {file_id}"}))
        return []
    
    doc = pymupdf.open(pdf_path)
    page_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        img_path = os.path.join(output_dir, f"page_{i + 1}.png")
        pix.save(img_path)
        page_paths.append(img_path)
    doc.close()
    
    result = {
        "file_id": file_id,
        "output_dir": output_dir,
        "pdf_path": pdf_path,
        "page_count": len(page_paths),
        "page_paths": page_paths
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

def save_note_data(
    title: str,
    gdrive_file_id: str,
    school_name: str,
    year_name: str,
    subject_name: str,
    summary: str,
    full_transcription: str,
    pages_json_path: str
):
    """Saves note metadata, uploads page images, and inserts records into Supabase."""
    s = SupabaseHelper()
    
    with open(pages_json_path, "r", encoding="utf-8") as f:
        pages = json.load(f)
        
    # 1. Upload images
    for p in pages:
        img_path = p.get("image_path")
        if img_path and os.path.exists(img_path):
            storage_path = f"notes/{gdrive_file_id}/page_{p['page_number']}.png"
            p["image_url"] = s.upload_storage_file(img_path, storage_path)
            
    # 2. Save Note
    res = s.save_note(
        title=title,
        gdrive_file_id=gdrive_file_id,
        subject_name=subject_name,
        school_name=school_name,
        year_name=year_name,
        summary=summary,
        full_transcription=full_transcription,
        page_count=len(pages)
    )
    note_id = res.get("id") if res else None
    
    # 3. Save Pages
    if note_id:
        for p in pages:
            s.save_note_page(
                note_id=note_id,
                page_number=p["page_number"],
                transcription=p.get("transcription", ""),
                image_url=p.get("image_url")
            )
            
    print(json.dumps({"success": True, "note_id": note_id}))

def main():
    parser = argparse.ArgumentParser(description="GoodNotes Pipeline Sync Helper")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("list-pending", help="List all pending PDFs to transcribe")
    
    prep_p = subparsers.add_parser("prepare-images", help="Download PDF and slice to PNG")
    prep_p.add_argument("--file-id", required=True, help="Google Drive File ID")
    prep_p.add_argument("--output-dir", default=None, help="Directory to save PNGs")
    
    save_p = subparsers.add_parser("save-note", help="Save note and pages to Supabase")
    save_p.add_argument("--title", required=True)
    save_p.add_argument("--file-id", required=True)
    save_p.add_argument("--school", default="Général")
    save_p.add_argument("--year", default="3A")
    save_p.add_argument("--subject", default="Général")
    save_p.add_argument("--summary", required=True)
    save_p.add_argument("--transcription", required=True)
    save_p.add_argument("--pages-json", required=True)
    
    args = parser.parse_args()
    
    if args.command == "list-pending":
        list_pending()
    elif args.command == "prepare-images":
        prepare_images(args.file_id, args.output_dir)
    elif args.command == "save-note":
        save_note_data(
            title=args.title,
            gdrive_file_id=args.file_id,
            school_name=args.school,
            year_name=args.year,
            subject_name=args.subject,
            summary=args.summary,
            full_transcription=args.transcription,
            pages_json_path=args.pages_json
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
