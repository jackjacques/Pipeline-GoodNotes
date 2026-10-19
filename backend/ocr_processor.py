import os
import time
import json
import re
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

    def transcribe_page_image(self, image_path: str, page_number: int, global_notes: str = "", specific_notes: str = "") -> str:
        """Uses Gemini Vision to perform handwriting recognition and LaTeX formatting for a page image."""
        if not self.api_key:
            return f"### Page {page_number}\n\n[Mode Mock] Transcription automatique désactivée (clé API Gemini manquante)."

        prompt = (
            "Tu es un assistant expert en retranscription de notes de cours manuscrites (iPad / GoodNotes).\n"
            "Analyse minutieusement cette image de note manuscrite et effectue la retranscription exacte et complète en Markdown :\n"
            "1. Retranscris fidèlement l'ensemble des textes, titres, sous-titres, et listes à puces.\n"
            "2. Convertis TOUTES les formules et expressions mathématiques/physiques/chimiques au format LaTeX standard ($...$ pour inline, $$...$$ pour les blocs).\n"
            "3. Si la page comporte des schémas ou graphiques, ajoute un court extrait explicatif [Schéma Page manuscrite].\n"
            "4. Dans ce cas, détaille la notion particulièrement.\n"
            "5. Si sur une slide ou une page, il y a un astérisque ou une annotation manuscrite en vert, détaille particulièrement et explique le cours et la formule en profondeur.\n"
            "6. Dans ce cas, il est souvent marqué à côté ce qui n'est pas clair et pas compris : réponds précisément à la question ou clarifie le point d'incompréhension.\n"
        )

        if global_notes:
            prompt += f"\n--- DIRECTIVES GENERALES ---\n{global_notes}\n"
        if specific_notes:
            prompt += f"\n--- DIRECTIVES SPECIFIQUES POUR CE DOCUMENT ---\n{specific_notes}\n"

        models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
        max_retries = 3

        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    image = Image.open(image_path)
                    if HAS_NEW_GENAI:
                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=[image, prompt]
                        )
                        if response and response.text:
                            return response.text
                    else:
                        response = self.model.generate_content([image, prompt])
                        if response and response.text:
                            return response.text
                except Exception as e:
                    err_str = str(e)
                    is_transient = any(code in err_str for code in ["503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "429", "500", "INTERNAL"])
                    if is_transient and attempt < max_retries - 1:
                        wait_time = 3 * (attempt + 1)
                        print(f"  [Retry {model_name}] Page {page_number}: temporairement indisponible ({err_str[:60]}...). Attente {wait_time}s (essai {attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        # Try next fallback model
                        break

        print(f"[OCR Error] All models failed to transcribe page {page_number}")
        return f"### Page {page_number}\n\n*(Transcription temporairement indisponible pour cette page)*"

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

        models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
        max_retries = 3

        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    if HAS_NEW_GENAI:
                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=[prompt]
                        )
                        if response and response.text:
                            return response.text
                    else:
                        response = self.model.generate_content([prompt])
                        if response and response.text:
                            return response.text
                except Exception as e:
                    err_str = str(e)
                    is_transient = any(code in err_str for code in ["503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "429", "500", "INTERNAL"])
                    if is_transient and attempt < max_retries - 1:
                        wait_time = 3 * (attempt + 1)
                        print(f"  [Retry {model_name} Summary]: Attente {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        break

        print(f"[Summary Error] All models failed to generate summary for '{title}'")
        return f"Résumé non disponible pour le cours **{title}**."

    def generate_course_quiz(self, full_transcription: str, title: str, subject_name: str, num_questions: int = 15) -> List[Dict[str, Any]]:
        """
        Generates an extensive educational multiple-choice quiz (QCM) specifically based on the course notes.
        Supports 10, 15, or 20 questions with LaTeX math formatting ($...$), clear options, and pedagogical explanations.
        """
        if not self.api_key:
            return []

        # Validate question count
        if num_questions not in [10, 15, 20]:
            num_questions = 15

        prompt = f"""Tu es un enseignant universitaire expert et pédagogue.
Voici la retranscription d'un cours intitulé "{title}" pour la matière "{subject_name}".

--- CONTENU DU COURS ---
{full_transcription[:18000]}
--- FIN DU CONTENU DU COURS ---

CONSIGNE :
Génère un questionnaire à choix multiples (QCM) d'entraînement et d'évaluation composé de très exactement {num_questions} questions de haute qualité pédagogique portant SPÉCIFIQUEMENT sur le contenu de ce cours.

DIRECTIVES PÉDAGOGIQUES :
1. Répartition variée des questions :
   - Définitions clés et concepts fondamentaux abordés dans ce cours.
   - Formules et équations essentielles (écris TOUTES les formules mathématiques/physiques en KaTeX standard entre dollars : $...$ pour l'inline, $$...$$ pour les blocs).
   - Pièges classiques, cas limites, propriétés et théorèmes.
   - Raisonnements et applications directes.
2. Chaque question doit comporter EXACTEMENT 4 propositions de réponse plausibles.
3. Il y a STRICTEMENT UNE SEULE réponse correcte par question.
4. "correct" doit être l'index entier de la bonne réponse (0 pour la 1ère option, 1 pour la 2e, 2 pour la 3e, 3 pour la 4e).
5. "explanation" doit être une explication détaillée et pédagogique qui clarifie pourquoi cette réponse est exacte et pourquoi les autres options sont incorrectes.

FORMAT DE SORTIE STRICT :
Réponds UNIQUEMENT par un tableau JSON valide sans aucun texte d'accompagnement ni balises superflues.
Exemple :
[
  {{
    "question": "Quelle est l'unité Hounsfield pour l'eau en tomodensitométrie (CT) ?",
    "options": ["-1000 HU", "0 HU", "+1000 HU", "+40 HU"],
    "correct": 1,
    "explanation": "Par convention, le coefficient d'atténuation linéaire de l'eau correspond à 0 HU."
  }}
]
"""

        models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
        max_retries = 3

        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    raw_text = None
                    if HAS_NEW_GENAI:
                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=[prompt]
                        )
                        if response and response.text:
                            raw_text = response.text
                    else:
                        response = self.model.generate_content([prompt])
                        if response and response.text:
                            raw_text = response.text

                    if raw_text:
                        cleaned = raw_text.strip()
                        if cleaned.startswith("```json"):
                            cleaned = cleaned[7:]
                        elif cleaned.startswith("```"):
                            cleaned = cleaned[3:]
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3]
                        cleaned = cleaned.strip()

                        parsed = json.loads(cleaned)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            validated = []
                            for item in parsed:
                                if isinstance(item, dict) and "question" in item and "options" in item and "correct" in item:
                                    try:
                                        correct_idx = int(item["correct"])
                                    except (ValueError, TypeError):
                                        correct_idx = 0
                                    options = [str(opt) for opt in item["options"]]
                                    if len(options) >= 2:
                                        if correct_idx < 0 or correct_idx >= len(options):
                                            correct_idx = 0
                                        validated.append({
                                            "question": str(item["question"]),
                                            "options": options,
                                            "correct": correct_idx,
                                            "explanation": str(item.get("explanation", ""))
                                        })
                            if len(validated) >= 5:
                                print(f"  [AI Quiz] Successfully generated {len(validated)} questions for '{title}'.")
                                return validated
                except Exception as e:
                    err_str = str(e)
                    is_transient = any(code in err_str for code in ["503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "429", "500", "INTERNAL"])
                    if is_transient and attempt < max_retries - 1:
                        wait_time = 3 * (attempt + 1)
                        print(f"  [Retry {model_name} Quiz]: Attente {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        break

        print(f"[Quiz Error] All models failed to generate quiz for '{title}'")
        return []

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

        try:
            from prompt_manager import PromptManager
            pm = PromptManager()
            global_notes, specific_notes = pm.get_instructions(doc_name=title)
            if global_notes or specific_notes:
                print(f"  [OCR] Loaded custom prompt instructions (global: {bool(global_notes)}, specific: {bool(specific_notes)})")
        except Exception as e:
            print(f"  [PromptManager Warning] Could not load instructions: {e}")
            global_notes, specific_notes = "", ""

        pages_data = []
        full_transcription_parts = []

        for i, img_path in enumerate(image_paths):
            page_num = i + 1
            print(f"  [OCR] Processing page {page_num}/{len(image_paths)}...")
            page_text = self.transcribe_page_image(
                img_path,
                page_num,
                global_notes=global_notes,
                specific_notes=specific_notes
            )
            
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
