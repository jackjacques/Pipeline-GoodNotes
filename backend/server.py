import os
import sys
import json
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8080
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEBSITE_DIR = os.path.join(PROJECT_ROOT, "website")

class PipelineHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBSITE_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/scan":
            print("\n🚀 Web request received: Triggering Google Drive scan pass...", flush=True)
            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = f"backend:{PROJECT_ROOT}"
                
                subprocess.Popen(
                    [sys.executable, "backend/main.py", "--once"],
                    cwd=PROJECT_ROOT,
                    env=env
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "started", "message": "Scan Google Drive lancé avec succès !"}).encode("utf-8"))
            except Exception as e:
                print(f"❌ Error triggering scan from web: {e}", flush=True)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/reanalyze":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(post_body.decode("utf-8"))
            except Exception:
                data = {}

            note_id = data.get("note_id")
            reanalyze_all = data.get("all", False)

            print(f"\n⚡ Web request received: Triggering AI re-analysis (note_id: {note_id}, all: {reanalyze_all})...", flush=True)

            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = f"backend:{PROJECT_ROOT}"

                cmd = [sys.executable, "backend/reanalyze.py"]
                if note_id:
                    cmd.extend(["--note-id", note_id])
                elif reanalyze_all:
                    cmd.append("--all")
                else:
                    cmd.append("--all")

                subprocess.Popen(cmd, cwd=PROJECT_ROOT, env=env)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "started",
                    "message": "Analyse IA relancée avec succès sur le document d'origine !"
                }).encode("utf-8"))
            except Exception as e:
                print(f"❌ Error triggering AI re-analysis: {e}", flush=True)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/generate_quiz":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(post_body.decode("utf-8"))
            except Exception:
                data = {}

            note_id = data.get("note_id")
            num_questions = int(data.get("num_questions", 15))
            if num_questions not in [10, 15, 20]:
                num_questions = 15

            if not note_id:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "note_id is required"}).encode("utf-8"))
                return

            print(f"\n🎯 Web request: Generating {num_questions} quiz questions for note {note_id}...", flush=True)

            try:
                sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
                from supabase_client import SupabaseHelper
                from ocr_processor import GeminiOCRProcessor

                sb = SupabaseHelper()
                res = sb.client.table("notes").select("id, title, subject_name, full_transcription").eq("id", note_id).execute()
                if not res.data:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Note not found"}).encode("utf-8"))
                    return

                note = res.data[0]
                transcription = note.get("full_transcription", "")
                title = note.get("title", "Cours")
                subject = note.get("subject_name", "Général")

                if not transcription or len(transcription.strip()) < 20:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Retranscription insuffisante pour générer un quiz"}).encode("utf-8"))
                    return

                ocr = GeminiOCRProcessor()
                quiz = ocr.generate_course_quiz(transcription, title, subject, num_questions=num_questions)

                if quiz:
                    sb.save_quiz(note_id, quiz)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok", "quiz": quiz, "count": len(quiz)}).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Échec de génération du quiz par l'IA"}).encode("utf-8"))
            except Exception as e:
                print(f"❌ Error generating quiz: {e}", flush=True)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

def run_server():
    print(f"🌐 Pipeline Web Server running on http://localhost:{PORT}", flush=True)
    httpd = HTTPServer(("0.0.0.0", PORT), PipelineHTTPHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server.", flush=True)
        httpd.server_close()


if __name__ == "__main__":
    run_server()
