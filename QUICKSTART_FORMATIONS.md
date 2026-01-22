# 🚀 Guide de Démarrage Rapide - Module Formations

## 📋 Prérequis

- Python 3.10+
- Node.js 18+
- MySQL 8.0+ (ou SQLite pour les tests)

## 🔧 Configuration Backend

### 1. Installer les dépendances

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Note:** Le package `google-generativeai` sera installé automatiquement pour le support Gemini.

### 2. Configurer la clé API Gemini (Optionnel)

Créez un fichier `.env` dans le dossier `backend/` ou ajoutez la variable d'environnement :

```env
GEMINI_API_KEY=votre_cle_api_gemini_ici
```

**Pour obtenir une clé Gemini:**
1. Allez sur https://makersuite.google.com/app/apikey
2. Créez une nouvelle clé API
3. Copiez-la dans votre `.env`

**Note:** Si vous n'avez pas de clé Gemini, le système utilisera Groq (si configuré) ou affichera un message d'erreur dans le chat.

### 3. Démarrer le Backend

**Option A: Utiliser le script batch (Windows)**
```powershell
.\start_backend.bat
```

**Option B: Manuellement**
```powershell
python main.py
```

**Option C: Avec uvicorn directement**
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le backend sera disponible sur: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**
- Health Check: **http://localhost:8000/api/health**

## 🎨 Configuration Frontend

### 1. Installer les dépendances

```powershell
cd frontend
npm install
```

### 2. Démarrer le serveur de développement

```powershell
ng serve
```

Ou pour ouvrir automatiquement le navigateur:

```powershell
ng serve --open
```

Le frontend sera disponible sur: **http://localhost:4200**

## 📚 Accéder au Module Formations

1. **Connectez-vous** à l'application (http://localhost:4200)
2. **Naviguez vers** `/formations` ou cliquez sur "Formations" dans le menu
3. **Sélectionnez une formation** pour commencer
4. **Utilisez le chat Gemini** pour poser des questions

## 🎯 Fonctionnalités Disponibles

### Pour les Utilisateurs:
- ✅ Voir toutes les formations disponibles
- ✅ Filtrer par niveau (Débutant/Intermédiaire/Avancé)
- ✅ Suivre sa progression
- ✅ Compléter des leçons
- ✅ Chat avec Gemini pour obtenir de l'aide
- ✅ Générer un certificat après complétion

### Pour les Admins:
- ✅ Créer de nouvelles formations
- ✅ Modifier les formations existantes
- ✅ Supprimer des formations
- ✅ Gérer le contenu des leçons

## 🧪 Tester l'API

### Créer une formation (Admin uniquement)

```bash
curl -X POST http://localhost:8000/api/formations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Introduction au Trading",
    "description": "Cours pour débutants",
    "level": "BEGINNER",
    "content_json": [
      {
        "id": "L1",
        "title": "Qu'est-ce que le trading?",
        "type": "TEXT",
        "data": "Le trading est l'achat et la vente d'actifs financiers...",
        "duration": 10
      }
    ]
  }'
```

### Tester le chat Gemini

```bash
curl -X POST http://localhost:8000/api/formations/gemini/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "question": "Qu'est-ce que le RSI?",
    "userId": 1,
    "context": "Formation en cours: Introduction au Trading"
  }'
```

## 🐛 Dépannage

### Erreur: "Gemini client not initialized"

**Solution:** Ajoutez `GEMINI_API_KEY` dans votre `.env` ou variables d'environnement.

### Erreur: "ModuleNotFoundError: No module named 'google.generativeai'"

**Solution:**
```powershell
pip install google-generativeai
```

### Erreur: "Table 'formations' doesn't exist"

**Solution:** La base de données sera créée automatiquement au démarrage. Si ce n'est pas le cas:

```powershell
python -c "from database import init_db; init_db()"
```

### Le chat ne fonctionne pas

**Vérifications:**
1. Vérifiez que `GEMINI_API_KEY` est configuré
2. Vérifiez les logs du backend pour les erreurs
3. Si Gemini n'est pas disponible, le système utilisera Groq (si configuré)

## 📝 Notes Importantes

- **SQLite par défaut:** Le projet utilise SQLite par défaut pour faciliter les tests
- **Gemini API:** Gratuite avec des limites de quota
- **Certificats:** La génération de certificats est simplifiée (URL fictive). Implémentez la génération PDF réelle si nécessaire

## 🎉 C'est prêt!

Vous pouvez maintenant:
1. Accéder à http://localhost:4200/formations
2. Explorer les formations
3. Utiliser le chat Gemini
4. Créer vos propres formations (si admin)

Bon apprentissage! 🚀

