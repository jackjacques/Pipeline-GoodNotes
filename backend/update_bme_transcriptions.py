import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.supabase_client import SupabaseHelper

db = SupabaseHelper()

GEO_TRANSCRIPTION = r"""# Optical Imaging for Biomedical Diagnosis
## Refresher: Geometrical Optics

---

### 1. Fundamental Postulates & Wave Equations
Light propagation is governed by Maxwell's equations. In an isotropic, homogeneous medium with refractive index $n = \frac{c}{v}$ :

- **Electric & Magnetic Fields :**
  $$\vec{E}(\vec{r}, t), \vec{B}(\vec{r}, t) \propto \cos(\vec{k} \cdot \vec{r} - \omega t)$$
  où $k = \frac{2\pi}{\lambda_0}$ et la longueur d'onde dans le milieu est $\lambda = \frac{\lambda_0}{n}$.

---

### 2. Geometrical Optics & Fermat's Principle

<div class="schema-box">
  <div class="schema-title"><i data-lucide="compass"></i> Schéma : Réfraction à l'interface & Principe de Fermat</div>
  <p>Rayon lumineux traversant une surface plane séparant deux milieux d'indices $n_1$ et $n_2$.</p>
  <p><em>Trajet optique :</em> $L = \int_A^B n(r) \, ds = n_1 \sqrt{x^2 + h_1^2} + n_2 \sqrt{(d-x)^2 + h_2^2}$</p>
</div>

Le principe de Fermat stipule que le chemin optique suivi par la lumière entre deux points $A$ et $B$ est extrémal ($\delta L = 0$) :

- **Loi de Réflexion :** $\theta_i = \theta_r$
- **Loi de Snell-Descartes pour la réfraction :**
  $$n_1 \sin \theta_1 = n_2 \sin \theta_2$$

<div class="note-correction">
  <div class="correction-title">⚠️ Note sur la dérivation de Fermat</div>
  <p><strong>Remarque :</strong> En minimisant $L(x)$ par rapport à $x$, $\frac{dL}{dx} = n_1 \frac{x}{\sqrt{x^2+h_1^2}} - n_2 \frac{d-x}{\sqrt{(d-x)^2+h_2^2}} = 0$, ce qui redémontre rigoureusement la loi en sinus $n_1 \sin \theta_1 = n_2 \sin \theta_2$.</p>
</div>

---

### 3. Fibre Optique à Saut d'Indice & Angle Limite

<div class="schema-box">
  <div class="schema-title"><i data-lucide="layers"></i> Schéma : Guidage par Réflexion Totale Interne dans une Fibre Optique</div>
  <p>Cœur d'indice $n_1$, gaine d'indice $n_2$ (avec $n_1 > n_2$).</p>
</div>

- **Angle critique de réflexion totale interne :**
  $$\sin \theta_c = \frac{n_2}{n_1}$$
- **Ouverture Numérique (ON / NA) & Angle d'acceptation $\theta_A$ :**
  $$\sin \theta_A = \sqrt{n_1^2 - n_2^2} = NA$$

---

### 4. Lentilles Minces & Formules de Conjugaison

Approximation paraxiale de Gauss :
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

<div class="schema-box">
  <div class="schema-title"><i data-lucide="sliders"></i> Schéma : Association de 2 Lentilles Minces séparées par une distance $d$</div>
  <p>Calcul des foyers principaux $F, F'$ et de la distance focale équivalente $f_{eq}'$.</p>
</div>

- **Distance focale équivalente :**
  $$\frac{1}{f_{eq}'} = \frac{1}{f_1'} + \frac{1}{f_2'} - \frac{d}{f_1' f_2'}$$
- **Position du Foyer Image Principal ($z_{F'}$) :**
  $$z_{F'} = f' \frac{(d - f_1)}{d - (f_1 + f_2)}$$

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

EM_TRANSCRIPTION = r"""# Optical Imaging for Biomedical Diagnosis
## Refresher: Electromagnetism & Maxwell Equations

---

### 1. Les Équations de Maxwell dans le Vide

$$\begin{cases}
\vec{\nabla} \cdot \vec{E} = \frac{\rho}{\varepsilon_0} & \text{(Loi de Gauss pour l'électricité)} \\[8pt]
\vec{\nabla} \cdot \vec{B} = 0 & \text{(Loi de Gauss pour le magnétisme)} \\[8pt]
\vec{\nabla} \times \vec{E} = -\frac{\partial \vec{B}}{\partial t} & \text{(Loi d'Induction de Faraday)} \\[8pt]
\vec{\nabla} \times \vec{B} = \mu_0 \left( \vec{J} + \varepsilon_0 \frac{\partial \vec{E}}{\partial t} \right) & \text{(Loi d'Ampère-Maxwell)}
\end{cases}$$

Relation avec la vitesse de la lumière dans le vide :
$$\frac{1}{c^2} = \mu_0 \varepsilon_0$$

- $\rho(\vec{r}, t)$ : Densité volumique de charge ($\text{C} \cdot \text{m}^{-3}$)
- $\vec{J}(\vec{r}, t)$ : Densité volumique de courant ($\text{A} \cdot \text{m}^{-2}$)
- $\varepsilon_0$ : Permittivité diélectrique du vide ($8.854 \times 10^{-12} \text{ F/m}$)
- $\mu_0$ : Perméabilité magnétique du vide ($4\pi \times 10^{-7} \text{ H/m}$)

---

### 2. Équation d'Onde Électromagnétique

En utilisant l'identité vectorielle sur le double rotatif :
$$\vec{\nabla} \times (\vec{\nabla} \times \vec{E}) = \vec{\nabla} (\vec{\nabla} \cdot \vec{E}) - \vec{\nabla}^2 \vec{E}$$

Dans un milieu isolant, linéaire, homogène et isotrope sans charges libres ($\rho = 0, \vec{J} = 0$) :
$$\vec{\nabla}^2 \vec{E} - \frac{1}{v^2} \frac{\partial^2 \vec{E}}{\partial t^2} = 0 \quad \text{avec } v = \frac{c}{n}$$
"""

def update_transcriptions():
    res = db.client.table("notes").select("id, title").execute()
    notes = res.data or []

    for n in notes:
        title = n.get("title", "").strip().lower()
        if title == "refreshers - geometric":
            print(f"Updating exact PDF transcription for '{n['title']}'...")
            db.client.table("notes").update({"full_transcription": GEO_TRANSCRIPTION}).eq("id", n["id"]).execute()
        elif title == "refreshers - em":
            print(f"Updating exact PDF transcription for '{n['title']}'...")
            db.client.table("notes").update({"full_transcription": EM_TRANSCRIPTION}).eq("id", n["id"]).execute()

    print("🎉 Exact BME transcriptions updated in Supabase!")

if __name__ == "__main__":
    update_transcriptions()
