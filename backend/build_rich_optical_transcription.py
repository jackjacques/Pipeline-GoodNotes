import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.supabase_client import SupabaseHelper

db = SupabaseHelper()

GEO_RICH_TRANSCRIPTION = r"""# Optical Imaging for Biomedical Diagnosis
## Refresher: Geometrical Optics

---

### 1. Fundamental Postulates & Wave Equations

Light propagation is governed by Maxwell's equations. In an isotropic, homogeneous medium with refractive index $n = \frac{c}{v}$ :

- **Electric & Magnetic Fields :**
  $$\vec{E}(\vec{r}, t), \vec{B}(\vec{r}, t) \propto \cos(\vec{k} \cdot \vec{r} - \omega t)$$
  où le nombre d'onde $k = \frac{2\pi}{\lambda_0}$ et la longueur d'onde dans le milieu est $\lambda = \frac{\lambda_0}{n}$.

---

### 2. Geometrical Optics & Fermat's Principle

<div class="schema-box">
<div class="schema-title"><i data-lucide="compass"></i> Schéma Vectoriel : Réfraction à l'Interface (Snell-Descartes)</div>
<div class="schema-svg-container" style="text-align: center; margin: 16px 0;">
<svg viewBox="0 0 600 240" width="100%" height="220" style="background: rgba(15, 23, 42, 0.04); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
<rect x="0" y="0" width="600" height="120" fill="rgba(59, 130, 246, 0.06)" />
<rect x="0" y="120" width="600" height="120" fill="rgba(16, 185, 129, 0.08)" />
<line x1="0" y1="120" x2="600" y2="120" stroke="#3b82f6" stroke-width="2" />
<text x="20" y="35" fill="#2563eb" font-weight="bold" font-family="sans-serif" font-size="14">Milieu 1 (Indice n₁)</text>
<text x="20" y="155" fill="#059669" font-weight="bold" font-family="sans-serif" font-size="14">Milieu 2 (Indice n₂ > n₁)</text>
<line x1="300" y1="20" x2="300" y2="220" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="5,5" />
<text x="310" y="35" fill="#ef4444" font-size="12" font-family="sans-serif">Normale</text>
<line x1="120" y1="30" x2="300" y2="120" stroke="#2563eb" stroke-width="3" />
<polygon points="210,75 200,68 202,78" fill="#2563eb" />
<line x1="300" y1="120" x2="420" y2="220" stroke="#059669" stroke-width="3" />
<polygon points="360,170 352,160 362,160" fill="#059669" />
<line x1="300" y1="120" x2="480" y2="30" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4,4" />
<path d="M 300,80 A 40,40 0 0,0 240,90" fill="none" stroke="#2563eb" stroke-width="1.5" />
<text x="255" y="75" fill="#2563eb" font-weight="bold" font-family="sans-serif" font-size="13">θ₁</text>
<path d="M 300,160 A 40,40 0 0,0 348,160" fill="none" stroke="#059669" stroke-width="1.5" />
<text x="325" y="175" fill="#059669" font-weight="bold" font-family="sans-serif" font-size="13">θ₂</text>
</svg>
</div>
<p><strong>Loi fondamentale de la réfraction :</strong> $n_1 \sin \theta_1 = n_2 \sin \theta_2$</p>
<p><em>Principe de Fermat :</em> Le trajet optique $L = \int_A^B n(r) \, ds$ est extrémal ($\delta L = 0$).</p>
</div>

<div class="note-correction">
<div class="correction-title">⚠️ Note & Correctif Pédagogique (Démonstration de Fermat)</div>
<p><strong>Formule originale du manuscrit :</strong> $L(x) = n_1 \sqrt{x^2 + h_1^2} + n_2 \sqrt{(d-x)^2 + h_2^2}$</p>
<p><strong>Explication rigoureuse :</strong> En posant $\frac{dL}{dx} = 0$, on obtient $n_1 \frac{x}{\sqrt{x^2+h_1^2}} = n_2 \frac{d-x}{\sqrt{(d-x)^2+h_2^2}}$, soit précisément $n_1 \sin \theta_1 = n_2 \sin \theta_2$.</p>
</div>

---

### 3. Fibre Optique à Saut d'Indice & Angle Limite

<div class="schema-box">
<div class="schema-title"><i data-lucide="layers"></i> Schéma Vectoriel : Guidage par Réflexion Totale Interne dans une Fibre Optique</div>
<div class="schema-svg-container" style="text-align: center; margin: 16px 0;">
<svg viewBox="0 0 620 200" width="100%" height="180" style="background: rgba(15, 23, 42, 0.04); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
<rect x="80" y="10" width="520" height="40" fill="rgba(148, 163, 184, 0.25)" stroke="#64748b" stroke-width="1" />
<text x="300" y="35" fill="#475569" font-weight="bold" font-family="sans-serif" font-size="13">Gaine d'indice n₂</text>
<rect x="80" y="50" width="520" height="100" fill="rgba(59, 130, 246, 0.12)" stroke="#2563eb" stroke-width="1.5" />
<text x="300" y="105" fill="#1d4ed8" font-weight="bold" font-family="sans-serif" font-size="14">Cœur d'indice n₁ (n₁ > n₂)</text>
<rect x="80" y="150" width="520" height="40" fill="rgba(148, 163, 184, 0.25)" stroke="#64748b" stroke-width="1" />
<line x1="20" y1="100" x2="600" y2="100" stroke="#cbd5e1" stroke-dasharray="4,4" stroke-width="1.5" />
<polyline points="20,130 80,100 240,50 400,150 560,50" fill="none" stroke="#ed64a6" stroke-width="3" />
<circle cx="80" cy="100" r="4" fill="#ed64a6" />
<text x="25" y="120" fill="#ed64a6" font-weight="bold" font-family="sans-serif" font-size="12">θA</text>
</svg>
</div>
<ul>
<li><strong>Angle critique de réflexion totale interne :</strong> $\sin \theta_c = \frac{n_2}{n_1}$</li>
<li><strong>Ouverture Numérique (ON / NA) :</strong> $\sin \theta_A = \sqrt{n_1^2 - n_2^2} = NA$</li>
</ul>
</div>

---

### 4. Lentilles Minces & Formules de Conjugaison

Approximation paraxiale de Gauss :

<div class="schema-box">
<div class="schema-title"><i data-lucide="sun"></i> Schéma Vectoriel : Traacé des Rayons Principaux à travers une Lentille Mince Convergente</div>
<div class="schema-svg-container" style="text-align: center; margin: 16px 0;">
<svg viewBox="0 0 640 220" width="100%" height="200" style="background: rgba(15, 23, 42, 0.04); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
<line x1="20" y1="110" x2="620" y2="110" stroke="#64748b" stroke-width="1.5" />
<line x1="320" y1="20" x2="320" y2="200" stroke="#2563eb" stroke-width="3" />
<path d="M 310,30 L 320,15 L 330,30" fill="none" stroke="#2563eb" stroke-width="3" />
<path d="M 310,190 L 320,205 L 330,190" fill="none" stroke="#2563eb" stroke-width="3" />
<text x="330" y="30" fill="#2563eb" font-weight="bold" font-family="sans-serif" font-size="13">Lentille (O)</text>
<circle cx="180" cy="110" r="4" fill="#ef4444" />
<text x="175" y="130" fill="#ef4444" font-weight="bold" font-family="sans-serif" font-size="13">Foyer F</text>
<circle cx="460" cy="110" r="4" fill="#ef4444" />
<text x="455" y="130" fill="#ef4444" font-weight="bold" font-family="sans-serif" font-size="13">Foyer F'</text>
<line x1="100" y1="110" x2="100" y2="50" stroke="#7c3aed" stroke-width="3" />
<polygon points="100,45 94,57 106,57" fill="#7c3aed" />
<text x="85" y="45" fill="#7c3aed" font-weight="bold" font-family="sans-serif" font-size="14">B (Objet)</text>
<line x1="100" y1="50" x2="320" y2="50" stroke="#2563eb" stroke-width="2" />
<line x1="320" y1="50" x2="540" y2="170" stroke="#2563eb" stroke-width="2" />
<line x1="100" y1="50" x2="540" y2="170" stroke="#059669" stroke-width="2" />
<line x1="540" y1="110" x2="540" y2="170" stroke="#7c3aed" stroke-width="3" />
<polygon points="540,175 534,163 546,163" fill="#7c3aed" />
<text x="545" y="185" fill="#7c3aed" font-weight="bold" font-family="sans-serif" font-size="14">B' (Image)</text>
</svg>
</div>
</div>

- **Formule du tailleur de lentille (Lens Maker Equation) :**
  $$\varphi = \frac{1}{f'} = (n - 1) \left( \frac{1}{R_1} - \frac{1}{R_2} \right)$$
  - $\varphi > 0 \implies$ Lentille convergente
  - $\varphi < 0 \implies$ Lentille divergente

- **Formules de Conjugaison de Descartes (origine au centre $O$) :**
  $$\frac{1}{\overline{OA'}} - \frac{1}{\overline{OA}} = \frac{1}{f'}$$

- **Grandissement Transversal $\gamma$ :**
  $$\gamma = \frac{\overline{A'B'}}{\overline{AB}} = \frac{\overline{OA'}}{\overline{OA}} = \frac{f'}{\overline{FA}} = \frac{\overline{F'A'}}{f'}$$

---

### 5. Systèmes de Deux Lentilles & Lentilles Épaisses

- **Distance focale équivalente du doublet :**
  $$\frac{1}{f_{eq}'} = \frac{1}{f_1'} + \frac{1}{f_2'} - \frac{d}{f_1' f_2'}$$
- **Position du Foyer Image Principal ($z_{F'}$) :**
  $$z_{F'} = f_{eq}' \frac{(d - f_1')}{d - (f_1' + f_2')}$$

---

### 6. Formalisme Matriciel Ray-Transfer (Matrices ABCD)

Un rayon optique est représenté par le vecteur d'état $\begin{pmatrix} y \\ n \theta \end{pmatrix}$ :

- **Matrice de propagation en milieu homogène (distance $d$) :**
  $$T_d = \begin{pmatrix} 1 & d \\ 0 & 1 \end{pmatrix}$$
- **Matrice de réfraction d'une dioptre/lentille de puissance $\varphi$ :**
  $$R_\varphi = \begin{pmatrix} 1 & 0 \\ -\varphi & 1 \end{pmatrix}$$
- **Matrice Système Globale :**
  $$M = \begin{pmatrix} A & B \\ C & D \end{pmatrix} \quad \text{avec } \det(M) = 1$$
"""

def update_rich_transcription():
    res = db.client.table("notes").select("id, title").execute()
    notes = res.data or []

    for n in notes:
        title = n.get("title", "").strip().lower()
        if "refresher" in title and "geometric" in title:
            print(f"Updating unindented SVG transcription for '{n['title']}'...")
            db.client.table("notes").update({
                "full_transcription": GEO_RICH_TRANSCRIPTION,
                "content": GEO_RICH_TRANSCRIPTION
            }).eq("id", n["id"]).execute()

    print("🎉 Unindented SVG transcription successfully updated for all Geometric Refresher notes in Supabase!")

if __name__ == "__main__":
    update_rich_transcription()

