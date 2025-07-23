# SmartPromo AI Model - Script d'Installation et d'Exécution
# ============================================================

Write-Host "🤖 SmartPromo AI Model - Installation et Démarrage" -ForegroundColor Cyan
Write-Host "=" * 55 -ForegroundColor Cyan

# Configuration
$ModelPath = $PSScriptRoot
$PythonRequirements = Join-Path $ModelPath "requirements.txt"
$MainScript = Join-Path $ModelPath "smartpromo_ai_model.py"
$TestScript = Join-Path $ModelPath "test_model.py"

function Test-PythonInstallation {
    Write-Host "`n🔍 Vérification de l'installation Python..." -ForegroundColor Yellow
    
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.[8-9]|Python 3\.1[0-9]") {
            Write-Host "✅ Python détecté: $pythonVersion" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Version Python non compatible: $pythonVersion" -ForegroundColor Red
            Write-Host "   Veuillez installer Python 3.8 ou supérieur" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ Python non trouvé dans le PATH" -ForegroundColor Red
        Write-Host "   Veuillez installer Python 3.8+ et l'ajouter au PATH" -ForegroundColor Yellow
        return $false
    }
}

function Install-Requirements {
    Write-Host "`n📦 Installation des dépendances Python..." -ForegroundColor Yellow
    
    try {
        if (Test-Path $PythonRequirements) {
            pip install -r $PythonRequirements
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Dépendances installées avec succès" -ForegroundColor Green
                return $true
            } else {
                Write-Host "❌ Erreur lors de l'installation des dépendances" -ForegroundColor Red
                return $false
            }
        } else {
            Write-Host "❌ Fichier requirements.txt non trouvé" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Erreur lors de l'installation: $_" -ForegroundColor Red
        return $false
    }
}

function Test-DatabaseConnection {
    Write-Host "`n🔌 Test de connexion à la base de données..." -ForegroundColor Yellow
    
    try {
        if (Test-Path $TestScript) {
            python $TestScript
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Tests de connexion réussis" -ForegroundColor Green
                return $true
            } else {
                Write-Host "⚠️ Problème détecté lors des tests" -ForegroundColor Yellow
                return $false
            }
        } else {
            Write-Host "❌ Script de test non trouvé" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Erreur lors du test: $_" -ForegroundColor Red
        return $false
    }
}

function Start-AIModel {
    Write-Host "`n🚀 Démarrage du modèle d'IA..." -ForegroundColor Yellow
    
    try {
        if (Test-Path $MainScript) {
            Write-Host "🎯 Lancement de l'analyse intelligente des promotions" -ForegroundColor Cyan
            python $MainScript
        } else {
            Write-Host "❌ Script principal non trouvé: $MainScript" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Erreur lors du démarrage: $_" -ForegroundColor Red
    }
}

function Show-Menu {
    Write-Host "`n📋 Menu Principal - SmartPromo AI" -ForegroundColor Cyan
    Write-Host "1. Installation complète (Python + Dépendances)" -ForegroundColor White
    Write-Host "2. Test de connexion à la base de données" -ForegroundColor White
    Write-Host "3. Lancer l'analyse des promotions" -ForegroundColor White
    Write-Host "4. Installation des dépendances uniquement" -ForegroundColor White
    Write-Host "5. Afficher l'aide et la documentation" -ForegroundColor White
    Write-Host "6. Quitter" -ForegroundColor White
    Write-Host ""
}

function Show-Help {
    Write-Host "`n📖 Aide - SmartPromo AI Model" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎯 Objectif:" -ForegroundColor Yellow
    Write-Host "   Calculer automatiquement les pourcentages de promotion optimaux"
    Write-Host "   pour maximiser les ventes et optimiser la gestion des stocks."
    Write-Host ""
    Write-Host "🔧 Prérequis:" -ForegroundColor Yellow
    Write-Host "   • Python 3.8 ou supérieur"
    Write-Host "   • SQL Server avec SmartPromoDb_v2026_Fresh"
    Write-Host "   • Pilote ODBC pour SQL Server"
    Write-Host ""
    Write-Host "📊 Fonctionnalités:" -ForegroundColor Yellow
    Write-Host "   • Analyse de la rotation des stocks"
    Write-Host "   • Calcul de l'élasticité prix/demande"
    Write-Host "   • Étude de l'historique des ventes"
    Write-Host "   • Prédiction de l'impact des promotions"
    Write-Host ""
    Write-Host "🚀 Utilisation rapide:" -ForegroundColor Yellow
    Write-Host "   1. Choisir 'Installation complète' (première fois)"
    Write-Host "   2. Tester la connexion à la base"
    Write-Host "   3. Lancer l'analyse des promotions"
    Write-Host ""
    Write-Host "📁 Fichiers générés:" -ForegroundColor Yellow
    Write-Host "   • smartpromo_analysis_[ID]_[DATE].json - Résultats détaillés"
    Write-Host "   • Logs d'exécution avec historique complet"
    Write-Host ""
    Write-Host "Pour plus d'informations, consultez README.md" -ForegroundColor Green
}

# Script principal
function Main {
    do {
        Show-Menu
        $choice = Read-Host "Choisissez une option (1-6)"
        
        switch ($choice) {
            "1" {
                Write-Host "`n🔧 Installation complète..." -ForegroundColor Cyan
                if (Test-PythonInstallation) {
                    if (Install-Requirements) {
                        Test-DatabaseConnection
                        Write-Host "`n🎉 Installation terminée! Vous pouvez maintenant utiliser le modèle." -ForegroundColor Green
                    }
                }
            }
            "2" {
                Test-DatabaseConnection
            }
            "3" {
                Start-AIModel
            }
            "4" {
                Install-Requirements
            }
            "5" {
                Show-Help
            }
            "6" {
                Write-Host "`n👋 Au revoir! Merci d'avoir utilisé SmartPromo AI" -ForegroundColor Cyan
                break
            }
            default {
                Write-Host "`n❌ Option invalide. Veuillez choisir entre 1 et 6." -ForegroundColor Red
            }
        }
        
        if ($choice -ne "6") {
            Write-Host "`nAppuyez sur Entrée pour continuer..." -ForegroundColor Gray
            Read-Host
        }
        
    } while ($choice -ne "6")
}

# Vérification du répertoire de travail
if (-not (Test-Path $MainScript)) {
    Write-Host "❌ Erreur: Script principal non trouvé!" -ForegroundColor Red
    Write-Host "   Assurez-vous d'exécuter ce script depuis le dossier SmartPromo_AI_Model" -ForegroundColor Yellow
    Write-Host "   Chemin actuel: $ModelPath" -ForegroundColor Gray
    exit 1
}

# Lancement du menu principal
Main
