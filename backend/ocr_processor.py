import os
import tempfile
from typing import List, Dict, Tuple, Optional, Any
from PIL import Image
from pdf2image import convert_from_path
from config import config

try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False
    import google.generativeai as genai_legacy

class GeminiOCRProcessor:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        if self.api_key:
            if HAS_NEW_GENAI:
                self.client = genai.Client(api_key=self.api_key)
            else:
                genai_legacy.configure(api_key=self.api_key)
                self.model = genai_legacy.GenerativeModel('gemini-1.5-flash')
        else:
            print("[Warning] GEMINI_API_KEY missing. OCR processor running in mock mode.")
            self.client = None

    def convert_pdf_to_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """Converts each page of a PDF file into a high-res PNG image using PyMuPDF (fitz) or pdf2image."""
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []

        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=200)
                img_path = os.path.join(output_dir, f"page_{i + 1}.png")
                pix.save(img_path)
                image_paths.append(img_path)
            doc.close()
            return image_paths
        except Exception as e:
            print(f"[PDF Render] PyMuPDF conversion fallback to pdf2image: {e}")

        images = convert_from_path(pdf_path, dpi=200)
        for i, img in enumerate(images):
            img_path = os.path.join(output_dir, f"page_{i + 1}.png")
            img.save(img_path, "PNG")
            image_paths.append(img_path)
        return image_paths

    def transcribe_page_image(self, image_path: str, page_number: int) -> str:
        """Uses Gemini Vision to perform handwriting recognition and LaTeX formatting for a page image."""
        if not self.api_key:
            return f"### Page {page_number}\n\n[Mode Mock] Transcription automatique désactivée (clé API Gemini manquante)."

        prompt = (
            "Tu es un assistant expert en retranscription de notes de cours manuscrites (iPad / GoodNotes).\n"
            "Analyse minutieusement cette image de note manuscrite et effectue la retranscription exacte et complète en Markdown :\n"
            "1. Retranscris fidèlement l'ensemble des textes, titres, sous-titres, et listes à puces.\n"
            "2. Convertis TOUTES les formules et expressions mathématiques/physiques/chimiques au format LaTeX standard ($...$ pour inline, $$...$$ pour les blocs).\n"
            "3. Si la page comporte des schémas ou graphiques, ajoute un court extrait explicatif [Schéma Page manuscrite].\n"
            "4. Ne résume pas le contenu à cette étape : fais une transcription exhaustive et claire sans ommettre de détails."
        )

        max_retries = 4
        for attempt in range(max_retries):
            try:
                image = Image.open(image_path)
                if HAS_NEW_GENAI:
                    response = self.client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[image, prompt]
                    )
                    return response.text
                else:
                    response = self.model.generate_content([image, prompt])
                    return response.text
            except Exception as e:
                err_str = str(e)
                if ("RESOURCE_EXHAUSTED" in err_str or "429" in err_str) and attempt < max_retries - 1:
                    wait_time = 4 * (attempt + 1)
                    print(f"  [Rate Limit] Page {page_number}: Quota 429 atteint. Pause de {wait_time}s (essai {attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    print(f"[OCR Error] Failed to transcribe page {page_number}: {e}")
                    if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                        return f"### Page {page_number}\n\n⚠️ *(Quota API Gemini dépassé - Limite de requêtes/min atteinte)*"
                    return f"### Page {page_number}\n\n*(Erreur lors de la retranscription de la page)*"

    def generate_course_summary(self, full_transcription: str, title: str, subject_name: str) -> str:
        """Generates a structured executive summary of the entire lecture for the recap email & website."""
        if not self.api_key:
            return f"Résumé de la séance **{title}** ({subject_name}).\n\n- Cours synchronisé avec succès."

        prompt = f"""Tu es un assistant pédagogique. Voici la retranscription complète d'un cours manuscrit intitulé "{title}" pour la matière "{subject_name}".

Contenu du cours retranscrit :
{full_transcription}

Génère un résumé structuré et clair de la séance au format HTML/Markdown comprenant :
1. **Objectif principal & Sujet de la séance** (2-3 phrases clés).
2. **Notions clés abordées** (liste à puces concise des concepts importants).
3. **Formules & Théorèmes essentiels** (les équations canoniques et théorèmes fondamentaux de la matière en LaTeX. ATTENTION : N'inclus PAS les calculs numériques d'exercices ou valeurs particulières de TD !).
4. **Points d'attention & Devoirs** (si mentionnés).

Sois synthétique, clair et directement exploitable pour une révision rapide par email."""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if HAS_NEW_GENAI:
                    response = self.client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt]
                    )
                    return response.text
                else:
                    response = self.model.generate_content([prompt])
                    return response.text
            except Exception as e:
                err_str = str(e)
                if ("RESOURCE_EXHAUSTED" in err_str or "429" in err_str) and attempt < max_retries - 1:
                    print(f"  [Rate Limit Summary] Pause de 5s...")
                    time.sleep(5)
                else:
                    print(f"[Summary Error] Failed to generate summary: {e}")
                    return f"Résumé non disponible pour le cours **{title}**."

    def process_pdf(self, pdf_path: str, title: str, subject_name: str) -> Tuple[List[Dict[str, Any]], str, str, List[str]]:
        """
        Processes an entire PDF:
        - Renders pages to images
        - Transcribes each page
        - Aggregates full Markdown text
        - Generates course summary
        Returns: (pages_data, full_transcription, summary, image_paths)
        """
        temp_dir = tempfile.mkdtemp(prefix="goodnotes_ocr_")
        image_paths = self.convert_pdf_to_images(pdf_path, temp_dir)

        pages_data = []
        full_transcription_parts = []

        for i, img_path in enumerate(image_paths):
            page_num = i + 1
            print(f"  [OCR] Processing page {page_num}/{len(image_paths)}...")
            page_text = self.transcribe_page_image(img_path, page_num)
            
            pages_data.append({
                "page_number": page_num,
                "transcription": page_text,
                "image_path": img_path
            })

            full_transcription_parts.append(f"## Page {page_num}\n\n{page_text}\n\n---")
            time.sleep(2.5) # Pace requests to respect Free Tier 15 RPM limit

        full_transcription = "\n\n".join(full_transcription_parts)
        print("  [OCR] Generating full session summary...")
        summary = self.generate_course_summary(full_transcription, title, subject_name)

        return pages_data, full_transcription, summary, image_paths
