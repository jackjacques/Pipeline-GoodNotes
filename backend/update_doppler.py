import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_client import SupabaseHelper

db = SupabaseHelper()
note_id = "45b10312-3c7b-4956-8b7f-a4ac508ac112"
file_id = "1avRp7QHSVsSCU4QQPurkpZgUyYvJy8xg"

PAGES = {
    1: r"""# Doppler Imaging : Principes Fondamentaux de l'Effet Doppler Ultrasonore

---

### 1. Phénomène Physique de l'Effet Doppler Acoustique

L'effet Doppler acoustique repose sur le décalage en fréquence observé entre une onde émise et l'onde rétrodiffusée par une cible en mouvement (principalement les globules rouges / hématies dans le flux sanguin) :

- **Source & Détecteur :**
  - La sonde ultrasonore (transducteur piézoélectrique) émet une onde acoustique de fréquence porteuse $f_0$ (ou $f_s$).
  - Les hématies en mouvement à la vitesse $\vec{v}$ agissent d'abord comme des récepteurs en mouvement (premier décalage Doppler), puis réémettent/rétrodiffusent l'onde acoustique vers la sonde immobile (second décalage Doppler).

<div class="schema-box">
  <div class="schema-title"><i data-lucide="waves"></i> Schéma : Géométrie de l'Effet Doppler & Angle d'Insonation</div>
  <div class="schema-svg-container" style="text-align: center; margin: 16px 0;">
    <svg viewBox="0 0 650 260" width="100%" height="240" style="background: rgba(15, 23, 42, 0.04); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.25);">
      <!-- Sonde ultrasonore -->
      <rect x="40" y="170" width="100" height="45" rx="8" fill="#1e293b" stroke="#3b82f6" stroke-width="2" />
      <text x="90" y="198" fill="#f8fafc" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Sonde US (f₀)</text>
      
      <!-- Faisceau ultrasonore -->
      <line x1="140" y1="180" x2="380" y2="80" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="6,4" />
      <path d="M 180,165 A 60,60 0 0,0 200,195" fill="none" stroke="#60a5fa" stroke-width="2" />
      <path d="M 230,145 A 90,90 0 0,0 260,190" fill="none" stroke="#60a5fa" stroke-width="2" />
      
      <!-- Vaisseau sanguin -->
      <rect x="250" y="50" width="370" height="60" rx="12" fill="rgba(239, 68, 68, 0.12)" stroke="#ef4444" stroke-width="2" />
      <text x="590" y="42" fill="#ef4444" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="end">Vaisseau Sanguin</text>
      
      <!-- Vecteur vitesse flux -->
      <line x1="330" y1="80" x2="490" y2="80" stroke="#dc2626" stroke-width="3.5" />
      <polygon points="490,75 502,80 490,85" fill="#dc2626" />
      <text x="510" y="85" fill="#dc2626" font-family="sans-serif" font-size="14" font-weight="bold">v</text>
      
      <!-- Angle thêta -->
      <line x1="380" y1="80" x2="470" y2="80" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3" />
      <path d="M 430,80 A 50,50 0 0,1 410,68" fill="none" stroke="#f59e0b" stroke-width="2" />
      <text x="445" y="98" fill="#d97706" font-family="sans-serif" font-size="14" font-weight="bold">θ</text>
    </svg>
  </div>
  <p><strong>Formule de l'effet Doppler ultrasonore :</strong></p>
  $$\Delta f = f_d - f_0 = \frac{2 v \cos\theta}{c} f_0$$
</div>

---

### 2. Équation Fondamentale et Dépendance Angulaire

- **Formule Canonique :**
  $$\Delta f = \frac{2 v f_0 \cos\theta}{c}$$
  où :
  - $\Delta f$ est le décalage Doppler mesuré ($\text{Hz}$),
  - $f_0$ est la fréquence d'émission ultrasonore ($\text{Hz}$),
  - $v$ est la vitesse de déplacement des hématies ($\text{m/s}$),
  - $\theta$ est l'angle d'insonation (angle entre le faisceau ultrasonore et l'axe d'écoulement sanguin),
  - $c \approx 1540\text{ m/s}$ est la vitesse de propagation du son dans les tissus mous humains.

- **Influence Critique de l'Angle Doppler $\theta$ :**
  - **Incidence Perpendiculaire ($\theta = 90^\circ$) :**
    $$\cos(90^\circ) = 0 \implies \Delta f = 0$$
    Même en présence d'un flux sanguin rapide ($v \gg 0$), aucun décalage fréquentiel n'est détecté si le faisceau est rigoureusement perpendiculaire au vaisseau.
  - **Sensibilité & Direction du flux :**
    - Si $\theta < 90^\circ$, $\cos\theta > 0 \implies \Delta f > 0$ : le sang s'approche de la sonde (fréquence reçue augmentée).
    - Si $\theta > 90^\circ$, $\cos\theta < 0 \implies \Delta f < 0$ : le sang s'éloigne de la sonde (fréquence reçue diminuée).
  - **Plage angulaire recommandée en pratique clinique :**
    L'angle d'insonation $\theta$ doit idéalement être compris entre **$30^\circ$ et $60^\circ$**. Au-delà de $60^\circ$, la dérivée $\frac{d(\cos\theta)}{d\theta} = -\sin\theta$ devient importante, ce qui amplifie considérablement l'erreur d'estimation de la vitesse $v$ pour une petite imprécision d'alignement angulaire.""",

    2: r"""# Ultrasound Investigation : Continuous-Wave Doppler (Doppler Continu - CW)

---

### 1. Principe Technique du Doppler Continu (CW)

- **Architecture à double transducteur :**
  - Utilise **2 cristaux piézoélectriques distincts** :
    1. Un cristal émetteur fonctionnant en continu à haute fréquence $f_0$.
    2. Un cristal récepteur captant continuellement les échos rétrodiffusés par les cibles mobiles.
  
- **Extraction du profil vélocimétrique :**
  - *"We seek speed over time"* : Le signal résultant est démodulé et analysé par transformée de Fourier à court terme (STFT) pour fournir en temps réel le spectrogramme (vitesse en fonction du temps).

<div class="schema-box">
  <div class="schema-title"><i data-lucide="activity"></i> Schéma : Spectrogramme Vélocimétrique Doppler (Vitesse en fonction du Temps)</div>
  <div class="schema-svg-container" style="text-align: center; margin: 16px 0;">
    <svg viewBox="0 0 650 240" width="100%" height="220" style="background: rgba(15, 23, 42, 0.04); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.25);">
      <!-- Axes -->
      <line x1="50" y1="120" x2="610" y2="120" stroke="#94a3b8" stroke-width="1.5" />
      <text x="615" y="125" fill="#64748b" font-family="sans-serif" font-size="12">Temps (t)</text>
      <line x1="80" y1="20" x2="80" y2="220" stroke="#94a3b8" stroke-width="1.5" />
      <text x="85" y="30" fill="#64748b" font-family="sans-serif" font-size="12">Vitesse (v)</text>
      
      <!-- Ligne de base (zéro flux) -->
      <line x1="80" y1="120" x2="610" y2="120" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4,4" />
      <text x="45" y="124" fill="#94a3b8" font-family="sans-serif" font-size="11">0</text>
      
      <!-- Onde pulsatile 1 -->
      <path d="M 100,120 Q 140,25 180,60 T 260,120 Q 280,135 310,120" fill="rgba(59, 130, 246, 0.2)" stroke="#2563eb" stroke-width="2.5" />
      <!-- Onde pulsatile 2 -->
      <path d="M 330,120 Q 370,25 410,60 T 490,120 Q 510,135 540,120" fill="rgba(59, 130, 246, 0.2)" stroke="#2563eb" stroke-width="2.5" />
      
      <!-- Hachures spectral broadening -->
      <line x1="160" y1="50" x2="160" y2="115" stroke="rgba(37, 99, 235, 0.5)" stroke-width="1.5" />
      <line x1="180" y1="65" x2="180" y2="115" stroke="rgba(37, 99, 235, 0.5)" stroke-width="1.5" />
      <line x1="200" y1="80" x2="200" y2="115" stroke="rgba(37, 99, 235, 0.5)" stroke-width="1.5" />
      <line x1="390" y1="50" x2="390" y2="115" stroke="rgba(37, 99, 235, 0.5)" stroke-width="1.5" />
      <line x1="410" y1="65" x2="410" y2="115" stroke="rgba(37, 99, 235, 0.5)" stroke-width="1.5" />
      
      <!-- Légendes cliniques -->
      <text x="180" y="20" fill="#2563eb" font-family="sans-serif" font-size="12" font-weight="bold">Pic Systolique</text>
      <text x="260" y="105" fill="#64748b" font-family="sans-serif" font-size="11">Flux Diastolique</text>
      <text x="200" y="180" fill="#dc2626" font-family="sans-serif" font-size="12" font-weight="bold">Direction du flux (Flow)</text>
    </svg>
  </div>
  <p>Spectrogramme Doppler typique montrant le profil pulsatile avec pic systolique, encoche dicrote et élargissement spectral (<em>spectral broadening</em>).</p>
</div>

---

### 2. Avantages & Limites Fondamentales du CW Doppler

- **Avantage Majeur : Mesure de Vitesses Arbitrairement Élevées**
  - Comme l'émission et la détection sont ininterrompues, il n'existe **aucune contrainte d'échantillonnage temporel**. Le système ne souffre d'**aucun repliement spectral (aliasing)**.
  - C'est l'outil de référence en cardiologie pour quantifier les sténoses aortiques sévères et les régurgitations de haute vélocité ($v > 4\text{ à }6\text{ m/s}$).

- **Limite Majeure : Absence Totale de Résolution en Profondeur (<em>Range Ambiguity</em>)**
  - *"Where is the vessel flow, give an ID of where place the probe"* :
  - Le signal acoustique reçu correspond à la somme intégrée de tous les réflecteurs en mouvement situés tout au long de la ligne de visée acoustique.
  - Il est impossible de discriminer si un signal provient d'un vaisseau superficiel ou d'un vaisseau profond situé sur la même trajectoire. Une sonde d'imagerie 2D mode B combinée (Doppler Duplex) est indispensable pour guider le placement de la sonde.""",

    3: r"""# Pulsed-Wave Doppler (Doppler Pulsé - PW) & Color Doppler

---

### 1. Doppler Pulsé (Pulsed-Wave - PW Doppler)

Le Doppler pulsé utilise un transducteur unique qui alterne émission d'un court train d'ondes acoustiques et écoute des échos. Il permet une sélection spatiale rigoureuse (*porte d'échantillonnage* / *sample volume*) à une profondeur $r$ précise grâce au temps de vol aller-retour $t = \frac{2r}{c}$.

- **Flux Lents (<em>Slow Flow</em>) vs Flux Rapides :**
  - *"Slow flow : fixed frequency due to repetition gives a hard time for fast flows"*
  - La fréquence de répétition des impulsions ($PRF$, *Pulse Repetition Frequency*) impose une fréquence d'échantillonnage finie. D'après le critère de Shannon-Nyquist :
    $$f_{Doppler, max} = \frac{PRF}{2}$$
  - Par conséquent, la vitesse maximale mesurable sans aliasing (vitesse de Nyquist) est bornée par :
    $$v_{max} = \frac{c \cdot PRF}{4 f_0 \cos\theta}$$
  - Si la vitesse du flux dépasse $v_{max}$, le signal subit un **repliement spectral (aliasing)**.

---

### 2. Réglage de la Profondeur de Champ & Explication du point vert

- **Formule de Profondeur Maximale :**
  $$r_{max} = \frac{c}{2 \cdot PRF}$$

<div class="note-correction">
  <div class="correction-title">⚠️ Clarification Pédagogique sur l'annotation verte (* where ?) : Profondeur Maximale et Dilemme de Nyquist</div>
  <p>L'annotation manuscrite en vert <strong>"* where ?"</strong> posée sous la relation $r_{max} = \frac{c}{2 PRF}$ souligne une interrogation fondamentale sur l'origine physique et les conséquences de cette équation :</p>
  <ol>
    <li><strong>D'où vient cette formule (Origine physique du facteur 2) ?</strong><br />
    Pour éviter toute ambiguïté de distance (<em>range ambiguity</em>), l'onde émise doit voyager jusqu'à la profondeur maximale $r_{max}$ et revenir au transducteur avant que l'impulsion suivante ne soit tirée :
    $$t_{aller-retour} = \frac{2 r_{max}}{c} \le T_{PRF} = \frac{1}{PRF} \implies r_{max} \le \frac{c}{2 \cdot PRF}$$
    </li>
    <li><strong>Le Dilemme Infranchissable du Doppler Pulsé (Limite Profondeur × Vitesse) :</strong><br />
    Pour explorer un vaisseau situé en profondeur ($r_{max}$ grand), il est impératif de diminuer la cadence de tir ($PRF \le \frac{c}{2 r_{max}}$).<br />
    Mais une $PRF$ faible abaisse directement la vitesse maximale détectable sans aliasing :
    $$v_{max} = \frac{c \cdot PRF}{4 f_0 \cos\theta} \le \frac{c^2}{8 f_0 r_{max} \cos\theta}$$
    En multipliant ces deux grandeurs limites, on obtient la contrainte fondamentale :
    $$r_{max} \cdot v_{max} \le \frac{c^2}{8 f_0 \cos\theta}$$
    <strong>Conclusion :</strong> On ne peut pas mesurer simultanément des vitesses très élevées ($v_{max}$) à grande profondeur ($r_{max}$). C'est pourquoi pour des flux cardiaques profonds et très rapides, on doit basculer en Doppler Continu (CW).
    </li>
  </ol>
</div>

---

### 3. Doppler Couleur (Color Doppler)

- **Principe :**
  - Superposition d'une cartographie couleur bidimensionnelle de l'écoulement sanguin sur l'image anatomique en mode B.
  - La vitesse moyenne et le sens d'écoulement sont estimés en temps réel (souvent via l'autocorrélation de Kasai).

- **Convention de Codage Couleur :**
  - *"Flow towards the probe / going with the probe"* :
  - **Rouge (Warm Colors / Red) :** Flux se déplaçant **vers** la sonde ($\Delta f > 0$, $\theta < 90^\circ$).
  - **Bleu (Cold Colors / Blue) :** Flux s'éloignant **de** la sonde ($\Delta f < 0$, $\theta > 90^\circ$).
  - *(Règle mnémotechnique internationale : **BART** — **B**lue **A**way, **R**ed **T**owards)*.
  - **Mosaïque / Vert / Jaune :** Zones de forte variance spectrale ou d'écoulement turbulent (sténoses, tourbillons post-valvulaires).""",

    4: r"""# Analyse Spectrale d'une Impulsion Doppler : Démonstration Mathématique de la Transformée de Fourier

---

### 1. Modélisation Mathématique de l'Impulsion Émise

En échographie Doppler pulsée, l'émission ultrasonore n'est pas une onde sinusoïdale pure et continue, mais un paquet d'ondes (impulsion) de durée finie $\Delta t$ centrée en $t=0$, modulée à la fréquence porteuse $f_c$ :

$$s(t) = \Pi\left(\frac{t}{\Delta t}\right) \cos(2\pi f_c t) = \begin{cases} \cos(2\pi f_c t) & \text{si } -\frac{\Delta t}{2} \le t \le \frac{\Delta t}{2} \\[6pt] 0 & \text{sinon} \end{cases}$$

---

### 2. Démonstration Étape par Étape de la Transformée de Fourier

La transformée de Fourier du signal s'écrit par définition :

$$S(f) = \int_{-\infty}^{+\infty} s(t) e^{-i 2\pi f t} \, dt = \int_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} \cos(2\pi f_c t) e^{-i 2\pi f t} \, dt$$

#### Étape 1 : Décomposition d'Euler du Cosinus
En utilisant la formule d'Euler $\cos(2\pi f_c t) = \frac{e^{i 2\pi f_c t} + e^{-i 2\pi f_c t}}{2}$ :

$$S(f) = \frac{1}{2} \int_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} \left( e^{i 2\pi f_c t} + e^{-i 2\pi f_c t} \right) e^{-i 2\pi f t} \, dt$$

$$S(f) = \frac{\displaystyle \int_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} e^{i 2\pi (f_c - f) t} \, dt + \int_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} e^{-i 2\pi (f_c + f) t} \, dt}{2}$$

#### Étape 2 : Intégration des Exponentielles Complexes
Calculons la primitive de chaque terme exponentiel :

$$\int_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} e^{i 2\pi (f_c - f) t} \, dt = \left[ \frac{e^{i 2\pi (f_c - f) t}}{i 2\pi (f_c - f)} \right]_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} = \frac{e^{i \pi (f_c - f) \Delta t} - e^{-i \pi (f_c - f) \Delta t}}{i 2\pi (f_c - f)}$$

Sachant que $e^{i X} - e^{-i X} = 2i \sin(X)$ en posant $X = \pi (f_c - f) \Delta t = 2\pi (f_c - f) \frac{\Delta t}{2}$ :

$$\int_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} e^{i 2\pi (f_c - f) t} \, dt = \frac{2 i \sin\left(2\pi (f_c - f) \frac{\Delta t}{2}\right)}{i 2\pi (f_c - f)}$$

De manière parfaitement analogue pour le second terme (avec $- (f_c + f)$) :

$$\int_{-\frac{\Delta t}{2}}^{\frac{\Delta t}{2}} e^{-i 2\pi (f_c + f) t} \, dt = \frac{2 i \sin\left(2\pi (f_c + f) \frac{\Delta t}{2}\right)}{i 2\pi (f_c + f)}$$

En réinjectant dans l'expression globale avec le facteur $\frac{1}{2}$ :

$$S(f) = \frac{1}{2} \left[ \frac{2 i \sin\left(2\pi (f_c - f) \frac{\Delta t}{2}\right)}{i 2\pi (f_c - f)} + \frac{2 i \sin\left(2\pi (f_c + f) \frac{\Delta t}{2}\right)}{i 2\pi (f_c + f)} \right]$$

#### Étape 3 : Simplification et Passage au Sinus Cardinal
Les termes $2i$ au numérateur et au dénominateur se simplifient ($\frac{2i}{i 2\pi} = \frac{1}{\pi}$) :

$$S(f) = \frac{1}{2} \left[ \frac{\sin\left(\pi (f_c - f) \Delta t\right)}{\pi (f_c - f)} + \frac{\sin\left(\pi (f_c + f) \Delta t\right)}{\pi (f_c + f)} \right]$$

Multiplions et divisons chaque terme par la durée $\Delta t$ pour faire émerger la fonction sinus cardinal $\text{sinc}(u) = \frac{\sin(u)}{u}$ :

$$S(f) = \frac{\Delta t}{2} \frac{\sin\left(\pi (f_c - f) \Delta t\right)}{\pi (f_c - f) \Delta t} + \frac{\Delta t}{2} \frac{\sin\left(\pi (f_c + f) \Delta t\right)}{\pi (f_c + f) \Delta t}$$

On aboutit à l'expression canonique finale :

$$\boxed{S(f) = \frac{\Delta t}{2} \, \text{sinc}\left[\pi (f_c - f) \Delta t\right] + \frac{\Delta t}{2} \, \text{sinc}\left[\pi (f_c + f) \Delta t\right]}$$

---

### 3. Interprétation Physique : Le Compromis Temps-Fréquence en Doppler

<div class="schema-box">
  <div class="schema-title"><i data-lucide="bar-chart-2"></i> Spectre Fréquentiel de l'Impulsion Ultrasonore</div>
  <p>Le spectre est composé de deux lobes principaux de sinus cardinal centrés sur les fréquences porteuses $+f_c$ et $-f_c$.</p>
  <ul>
    <li><strong>Largeur du lobe principal (entre les premiers zéros) :</strong> $$\Delta f_{lobe} = \frac{2}{\Delta t}$$</li>
    <li><strong>Largeur à mi-hauteur (FWHM) :</strong> $$\delta f \approx \frac{1}{\Delta t}$$</li>
  </ul>
</div>

<div class="note-correction">
  <div class="correction-title">⚠️ Conséquence Fondamentale sur l'Imagerie Médicale</div>
  <p>Cette relation démontre le <strong>compromis fondamental d'incertitude temps-fréquence</strong> :</p>
  <ul>
    <li><strong>Pour une résolution vélocimétrique précise (mesure fine de vitesse) :</strong><br />
    Il faut une bande passante fréquentielle la plus étroite possible ($\Delta f \to 0$), ce qui impose une durée d'impulsion longue ($\Delta t$ grand).</li>
    <li><strong>Pour une résolution spatiale axiale fine (localisation spatiale) :</strong><br />
    La résolution axiale vaut $\Delta z = \frac{c \Delta t}{2}$. Une bonne résolution axiale exige donc une impulsion très brève ($\Delta t \to 0$).</li>
  </ul>
  <p><strong>En échographie clinique :</strong> Le mode B morphologique utilise des impulsions très courtes (1 à 3 cycles, $\Delta t$ faible) pour maximiser la netteté spatiale, tandis que le mode Doppler pulsé utilise des impulsions plus longues (4 à 16 cycles, $\Delta t$ élevé) pour mesurer précisément la fréquence Doppler et la vitesse d'écoulement.</p>
</div>"""
}

SUMMARY = r"""# 🌊 Résumé Exécutif : Doppler Imaging & Analyse Spectrale Ultrasonore
## Cours : Advanced Imaging (MDC_53602_EP - Master BME / 3A)

---

### 1. Objectif Principal & Notions Clés
Cette séance de cours approfondit les **principes physiques, technologiques et mathématiques de l'imagerie Doppler ultrasonore** pour l'exploration hémodynamique cardiovasculaire :
- **Effet Doppler acoustique :** Décalage fréquentiel $\Delta f = \frac{2 v \cos\theta}{c} f_0$ induit par le mouvement des globules rouges (hématies).
- **Doppler Continu (CW) :** Deux transducteurs distincts (émission / réception continues) permettant la mesure sans limitation de vitesses sanguines très élevées, mais sans aucune discrimination spatiale en profondeur (*range ambiguity*).
- **Doppler Pulsé (PW) :** Émission par impulsions à cadence $PRF$, permettant de choisir précisément la profondeur d'échantillonnage mais limité par le repliement spectral (*aliasing*) au-delà de la vitesse de Nyquist $v_{max} = \frac{c \cdot PRF}{4 f_0 \cos\theta}$.
- **Doppler Couleur (Color Doppler) :** Cartographie bidimensionnelle superposée au mode B selon la convention BART (Red = flux s'approchant de la sonde, Blue = flux s'éloignant).

---

### 2. Formules Canoniques & Théorèmes Fondamentaux
1. **Équation Doppler Cardiovasculaire :**
   $$\Delta f = \frac{2 v f_0 \cos\theta}{c}$$
2. **Profondeur Maximale sans Ambiguïté de Distance :**
   $$r_{max} = \frac{c}{2 \cdot PRF}$$
3. **Limite Fondamentale Profondeur × Vitesse (Dilemme de Nyquist) :**
   $$r_{max} \cdot v_{max} \le \frac{c^2}{8 f_0 \cos\theta}$$
4. **Spectre de l'Impulsion Troncée (Transformée de Fourier) :**
   $$S(f) = \frac{\Delta t}{2} \, \text{sinc}\left[\pi (f_c - f) \Delta t\right] + \frac{\Delta t}{2} \, \text{sinc}\left[\pi (f_c + f) \Delta t\right]$$
5. **Compromis Temps-Fréquence (Résolution Axiale vs Résolution Vélocimétrique) :**
   $$\Delta z = \frac{c \Delta t}{2} \quad \longleftrightarrow \quad \Delta f \approx \frac{1}{\Delta t}$$

---

### 3. Points d'Attention & Éclaircissement Pédagogique
- **Angle Doppler optimal :** Toujours maintenir l'angle d'insonation $\theta$ entre $30^\circ$ et $60^\circ$ pour éviter une perte totale de signal à $90^\circ$ ($\cos 90^\circ = 0$) ou une explosion des erreurs de mesure à $\theta > 60^\circ$.
- **Résolution du questionnement (* where ?) :** La limitation $r_{max} = \frac{c}{2 PRF}$ découle strictement du temps de vol aller-retour des ondes acoustiques, imposant un arbitrage physique direct avec la vitesse maximale mesurable."""

def main():
    full_transcription = "\n\n---\n\n".join([f"## Page {p}\n\n{PAGES[p]}" for p in sorted(PAGES.keys())])

    # 1. Update note record in Supabase
    print("Updating note record in Supabase...")
    db.client.table("notes").update({
        "title": "Doppler Imaging & Ultrasound Flow Analysis",
        "summary": SUMMARY,
        "full_transcription": full_transcription,
        "page_count": 4
    }).eq("id", note_id).execute()

    # 2. Clean old pages and insert new pages
    print("Replacing pages in note_pages table...")
    db.client.table("note_pages").delete().eq("note_id", note_id).execute()

    for p in sorted(PAGES.keys()):
        img_url = f"https://clpwmeooxkhpbeilsckh.supabase.co/storage/v1/object/public/notes-files/notes/{file_id}/page_{p}.png"
        db.save_note_page(
            note_id=note_id,
            page_number=p,
            transcription=PAGES[p],
            image_url=img_url
        )

    print("✅ Ultrasounds Imaging successfully transcribed and saved in Supabase!")

if __name__ == "__main__":
    main()
