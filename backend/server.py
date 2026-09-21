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
