import os                                                                
import re                                                                
from typing import Dict, Optional, Tuple                                 
                                                                     
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))                                                                       
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")                      
 
class PromptManager:                                                     
    def __init__(self, global_prompt_path: Optional[str] = None):        
        self.prompts_dir = PROMPTS_DIR                                   
        os.makedirs(self.prompts_dir, exist_ok=True)                                                                     
        root_global = os.path.join(PROJECT_ROOT, "global_prompt.txt")
        default_global = root_global if os.path.exists(root_global) else os.path.join(self.prompts_dir, "global_prompt.txt")                                                                      
        self.global_path = global_prompt_path if (global_prompt_path and os.path.exists(global_prompt_path)) else default_global 

    def read_prompt(self, path: Optional[str]) -> str:
        if not path or not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"[PromptManager] Erreur lecture {path}: {e}")
            return ""

    def get_instructions(self, specific_path: Optional[str] = None, doc_name: Optional[str] = None) -> Tuple[str, str]:
        """Retourne (global_text, specific_text). Détecte automatiquement prompts/<nom>.txt si non spécifié."""
        global_text = self.read_prompt(self.global_path)

        specific_text = ""
        if specific_path and os.path.exists(specific_path):
            specific_text = self.read_prompt(specific_path)
        elif doc_name:
            base_name = os.path.splitext(os.path.basename(doc_name))[0]
            auto_path = os.path.join(self.prompts_dir, f"{base_name}.txt")
            if os.path.exists(auto_path):
                print(f"[PromptManager] Fichier de prompt spécifique trouvé automatiquement : {auto_path}")
                specific_text = self.read_prompt(auto_path)
        return global_text, specific_text

    ger_instructions = get_instructions
