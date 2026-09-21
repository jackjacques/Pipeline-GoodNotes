# 📚 Pipeline GoodNotes -> Supabase -> Gemini OCR -> Email

Pipeline backend complet d'ingestion et de retranscription automatique de notes manuscrites iPad / GoodNotes hébergé sur VPS OVH.

---

## 🛠️ Structure du Projet

```
Pipeline-goodnotes/
├── backend/
│   ├── config.py             # Gestion des variables d'environnement (.env)
│   ├── supabase_client.py    # Helper Supabase (base de données & storage)
│   ├── ocr_processor.py      # Traitement PDF -> Gemini 2.5 Flash Vision (OCR Manuscrit + LaTeX)
│   ├── gdrive_sync.py        # Ingestion Google Drive API
│   ├── email_notifier.py     # Notification récapitulatif par email (Resend / SMTP OVH)
│   ├── main.py               # Script principal (Daemon & mode CLI de test)
│   └── requirements.txt      # Dépendances Python
├── schema.sql                # Schéma SQL pour Supabase
└── .env.example              # Exemple de fichier d'environnement
```

---

## ⚡ Étape 1 : Configuration Supabase

1. Connecte-toi sur ton projet [Supabase](https://supabase.com/).
2. Ouvre le **SQL Editor** et exécute le contenu du fichier [`schema.sql`](file:///Users/jacques/PERSO/PersonalProjects/Pipeline-goodnotes/schema.sql).
3. Dans **Storage**, crée un bucket public nommé `notes-files`.

---

## 🔑 Étape 2 : Configuration du fichier `.env`

Copie `.env.example` en `.env` et renseigne tes clés API :

```bash
cp .env.example .env
```

Variables requises :
* `SUPABASE_URL` : URL de ton projet Supabase.
* `SUPABASE_SERVICE_ROLE_KEY` : Clé Service Role (pour écriture/stockage).
* `GEMINI_API_KEY` : Clé API Google Gemini (Vision).
* `GDRIVE_FOLDER_ID` : ID du dossier Google Drive d'export GoodNotes.
* `NOTIFICATION_RECIPIENT_EMAIL` : Ton adresse email personnelle qui recevra les récaps.
* `EMAIL_PROVIDER` : `resend` ou `smtp` (si tu utilises OVH Mail).

---

## 📦 Étape 3 : Installation & Test du Backend

### 1. Installation des dépendances
System requirements : `poppler` (nécessaire pour `pdf2image`).
* Sur macOS : `brew install poppler`
* Sur Ubuntu/VPS OVH : `sudo apt-get install -y poppler-utils`

Installe les paquets Python :
```bash
pip install -r backend/requirements.txt
```

### 2. Test rapide sur un fichier PDF local
Tu peux tester la chaîne OCR + Supabase + Email sur un fichier local :
```bash
python backend/main.py --test-file /chemin/vers/mon_cours.pdf --title "Chapitre 1 : Limites et Continuité" --subject "Mathématiques"
```

### 3. Lancement du Service Daemon (Sur VPS OVH)
Pour lancer la vérification automatique périodique sur Google Drive :
```bash
python backend/main.py
```
Pour le faire tourner en tâche de fond permanente sur ton VPS :
```bash
pm2 start backend/main.py --name goodnotes-pipeline --interpreter python3
```
