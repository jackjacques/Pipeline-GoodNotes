import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_client import SupabaseHelper

db = SupabaseHelper()
ct_note_id = "01611897-cb2c-4c99-96cc-4c7db4ba523e"
ct_file_id = "188z-jIuYGMyUVjIPUk3ZuOt8KxbtwIUU"

CT_PAGE_122 = r"""### Diapositive 122 : Data Storage and Exchange — The DICOM Format

---

#### 1. Encodage Numérique des Niveaux d'Atténuation (Pixels CT)
- **Représentation binaire :**
  - Dans la matrice de reconstruction tomodensitométrique, chaque coefficient d'atténuation (unité Hounsfield) est représenté sur **12 bits** effectifs, encapsulé dans un conteneur standard de **16 bits** (2 octets : $\text{lsB}$ et $\text{msB}$).
  - Dynamique de codage : $2^{12} = 4096$ niveaux discrets (permettant de couvrir la plage canonique $[-1024 \text{ HU}, +3071 \text{ HU}]$).

#### 2. Convention d'Organisation des Octets (*Endianness*)
Le standard DICOM (*Digital Imaging and Communications in Medicine*) gère deux ordres d'octets en mémoire :
- **Little-Endian (Architecture Intel x86, Pentium, PC / Windows) :**
  - L'octet de poids faible ($\text{lsB}$, *least significant Byte*) est stocké à l'adresse mémoire inférieure, suivi de l'octet de poids fort ($\text{msB}$, *most significant Byte*).
- **Big-Endian (Architectures Motorola 680x0, Sun Microsystems, Mac OS classique) :**
  - L'octet de poids fort ($\text{msB}$) est stocké en premier, suivi de l'octet de poids faible ($\text{lsB}$).

#### 3. Décodage et Conversion vers l'Échelle de Hounsfield (HU)
La valeur brute enregistrée dans le fichier DICOM ($\text{val}$) est convertie en unité Hounsfield radiologique ($\text{HU}$) via deux métadonnées obligatoires du tag DICOM :
- **$\text{RS}$ (*Rescale Slope*) :** Pente d'échelle.
- **$\text{RI}$ (*Rescale Intercept*) :** Constante d'origine (typiquement $\approx -1024$).

$$\boxed{\text{HU} = \text{RS} \times \text{val} + \text{RI}}$$
"""

CT_PAGE_123 = r"""### Diapositive 123 : Synthèse Générale & Récapitulatif du Cours Computed Tomography (CT)

---

#### Panorama Exhaustif du Module Tomodensitométrie (Catalin Fetita — DatSHealth)
Ce cours a couvert l'ensemble de la chaîne d'acquisition, de traitement mathématique et de reconstruction tomodensitométrique :

1. **CT Concept :** Fondements radiologiques, atténuation des rayons X selon la loi de Beer-Lambert $I = I_0 e^{-\int \mu(s) ds}$, définition de l'échelle des Unités Hounsfield (HU).
2. **Radon Transform :** Modélisation mathématique des projections radiologiques 2D en coordonnées polaires $(\rho, \theta)$, sinogramme.
3. **Image Reconstruction :** Théorème de la coupe centrale (Projection-Slice Theorem), Rétroprojection Filtrée (FBP / Filtered Backprojection avec filtre rampe de Ram-Lak/Shepp-Logan), et méthodes itératives algébriques (ART).
4. **Technical Aspects of CT :** Géométries de générations de scanners (du balayage 1ère génération aux détecteurs multibarrettes hélicoïdaux actuels), tube à rayons X et filtration spectrale.
5. **Acquisition Protocol in Spiral CT :** Définition du Pitch $p = \frac{d}{N \cdot \Delta z}$, interpolation z (180°LI / 360°LI).
6. **Volumetric Imaging in Spiral CT :** Reconstruction 3D, résolution isotrope, artéfacts de cône-beam (Feldkamp).
7. **Contrast Enhancement :** Produits de contraste iodés, cinétique vasculaire, scanner bi-énergie / spectral CT pour la séparation matière (eau/iode/calcium).
8. **Data Storage and Exchange :** Standard DICOM, formats d'encodage 16 bits, endianness et métadonnées de calibration $(\text{RS}, \text{RI})$.
"""

def main():
    print("Fetching existing CT note...")
    res = db.client.table("notes").select("id, full_transcription, page_count").eq("id", ct_note_id).execute()
    if not res.data:
        print("CT note not found.")
        return
    
    note = res.data[0]
    current_trans = note.get("full_transcription", "")
    
    # Append pages 122 and 123 if not already in full_transcription
    if "Diapositive 122" not in current_trans:
        new_trans = current_trans + "\n\n---\n\n## Page 122\n\n" + CT_PAGE_122 + "\n\n---\n\n## Page 123\n\n" + CT_PAGE_123
        db.client.table("notes").update({
            "full_transcription": new_trans,
            "page_count": 123
        }).eq("id", ct_note_id).execute()
        print("Updated CT note full_transcription & page_count to 123.")
    
    # Check note_pages for page 122 and 123
    for p_num, p_text in [(122, CT_PAGE_122), (123, CT_PAGE_123)]:
        p_res = db.client.table("note_pages").select("id").eq("note_id", ct_note_id).eq("page_number", p_num).execute()
        img_url = f"https://clpwmeooxkhpbeilsckh.supabase.co/storage/v1/object/public/notes-files/notes/{ct_file_id}/page_{p_num}.png"
        if p_res.data:
            db.client.table("note_pages").update({
                "transcription": p_text,
                "image_url": img_url
            }).eq("id", p_res.data[0]["id"]).execute()
            print(f"Updated CT page {p_num}")
        else:
            db.save_note_page(
                note_id=ct_note_id,
                page_number=p_num,
                transcription=p_text,
                image_url=img_url
            )
            print(f"Inserted CT page {p_num}")

    print("✅ CT notes successfully updated in Supabase!")

if __name__ == "__main__":
    main()
