# Script PowerShell pour démarrer l'API Flask SmartPromo AI
Write-Host " Démarrage de l'API Flask SmartPromo AI..." -ForegroundColor Green

# Activer l'environnement virtuel Python si il existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host " Activation de l'environnement virtuel..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host " Aucun environnement virtuel trouvé, utilisation de Python global" -ForegroundColor Yellow
}

# Installer les dépendances si nécessaire
Write-Host " Vérification des dépendances..." -ForegroundColor Yellow
pip install flask flask-cors pandas numpy scikit-learn

# Démarrer le serveur Flask
Write-Host " Démarrage du serveur Flask sur http://localhost:5000..." -ForegroundColor Green
python flask_api_service.py
