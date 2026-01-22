# 🔑 Configuration de l'API Gemini

## Problème : "API key not valid"

Si vous voyez cette erreur, cela signifie que la clé API Gemini n'est pas correctement configurée.

## ✅ Solution 1 : Configurer Gemini API (Recommandé)

### Étape 1 : Obtenir une clé API Gemini

1. Allez sur [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Create API Key" ou "Get API Key"
4. Copiez la clé API générée

### Étape 2 : Configurer la clé dans le projet

**Option A : Fichier .env (Recommandé)**

Créez ou modifiez le fichier `backend/.env` :

```env
GEMINI_API_KEY=votre_cle_api_gemini_ici
```

**Option B : Variables d'environnement système**

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="votre_cle_api_gemini_ici"

# Linux/Mac
export GEMINI_API_KEY="votre_cle_api_gemini_ici"
```

### Étape 3 : Redémarrer le serveur

```powershell
# Arrêtez le serveur (Ctrl+C)
# Puis redémarrez
python main.py
```

## ✅ Solution 2 : Utiliser Groq comme alternative (Gratuit)

Si vous ne voulez pas utiliser Gemini, le système utilisera automatiquement Groq si configuré :

### Configurer Groq

1. Allez sur [Groq Console](https://console.groq.com/)
2. Créez un compte et obtenez votre clé API
3. Ajoutez dans `backend/.env` :

```env
GROQ_API_KEY=votre_cle_groq_ici
```

Le système utilisera automatiquement Groq si Gemini n'est pas disponible.

## 🔍 Vérification

Pour vérifier que la clé est bien configurée :

1. Vérifiez les logs du serveur au démarrage :
   ```
   ✅ "Gemini client initialized successfully"
   ```
   ou
   ```
   ✅ "Using Groq service as fallback"
   ```

2. Testez le chat dans l'interface formations

## 📝 Notes importantes

- **Gemini API** : Gratuite avec des limites de quota (généralement 60 requêtes/minute)
- **Groq API** : Gratuite et très rapide, bonne alternative
- Les deux services fonctionnent pour le chat des formations
- Si aucune clé n'est configurée, vous verrez un message d'erreur clair

## 🐛 Dépannage

### Erreur : "API key not valid"

**Causes possibles :**
1. La clé est incorrecte ou expirée
2. La clé n'est pas dans le bon format
3. Le fichier .env n'est pas lu correctement

**Solutions :**
1. Vérifiez que la clé est correctement copiée (sans espaces)
2. Vérifiez que le fichier `.env` est dans le dossier `backend/`
3. Redémarrez le serveur après modification du .env
4. Vérifiez les logs pour voir quelle clé est utilisée

### Erreur : "ModuleNotFoundError: No module named 'google.generativeai'"

**Solution :**
```bash
pip install google-generativeai
```

## 🎯 Recommandation

Pour un environnement de développement/test, **Groq est recommandé** car :
- ✅ Gratuit
- ✅ Très rapide
- ✅ Facile à configurer
- ✅ Pas de limite stricte de quota

Pour la production, Gemini peut être préféré selon vos besoins.

