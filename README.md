# SmartPromo AI Model - Guide d'Utilisation

## 🎯 Vue d'ensemble

Le **SmartPromo AI Model** est un modèle d'intelligence artificielle avancé conçu pour calculer automatiquement les pourcentages de promotion optimaux pour chaque article dans votre base de données SmartPromo.

## 🏗️ Architecture du Modèle

### Algorithme de Calcul Intelligent

Le modèle utilise une approche multi-critères pondérée basée sur 4 indicateurs clés :

1. **Rotation des stocks (35%)** - Analyse du taux de rotation et du niveau de stock
2. **Élasticité prix/demande (25%)** - Étudie la sensibilité de la demande aux variations de prix
3. **Historique des ventes (25%)** - Analyse les tendances de vente sur les 90 derniers jours
4. **Historique des promotions (15%)** - Prend en compte les promotions passées pour éviter la sur-promotion

### Formule de Calcul

```
Score Final = (Rotation × 0.35) + (Élasticité × 0.25) + (Ventes × 0.25) + (Promotions × 0.15)
Promotion % = Score Final × (Promotion Max - Promotion Min) + Promotion Min
```

## 📋 Prérequis

### Configuration Système
- **Python 3.8+**
- **SQL Server** avec la base de données SmartPromoDb_v2026_Fresh
- **Pilote ODBC** pour SQL Server

### Dépendances Python
```bash
pip install -r requirements.txt
```

## 🚀 Installation

1. **Cloner ou copier le dossier du modèle**
2. **Installer les dépendances**
   ```bash
   cd SmartPromo_AI_Model
   pip install -r requirements.txt
   ```
3. **Vérifier la connexion à la base de données**
   ```bash
   python test_model.py
   ```

## 💻 Utilisation

### Utilisation Simple (Mode Interactif)

```bash
python smartpromo_ai_model.py
```

Le script vous demandera :
- L'ID de la catégorie à analyser
- Affichera les résultats détaillés
- Générera un rapport de synthèse
- Sauvegardera les résultats en JSON

### Utilisation Avancée (Programmation)

```python
from smartpromo_ai_model import SmartPromoAIModel

# Configuration
CONNECTION_STRING = "Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;"

# Initialisation
model = SmartPromoAIModel(CONNECTION_STRING)

# Analyse d'une catégorie
results = model.analyze_category(category_id=1)

# Génération du rapport
report = model.generate_summary_report(results)
print(report)
```

## 📊 Interprétation des Résultats

### Scores d'Analyse (0.0 - 1.0)

- **Score Rotation** : Plus élevé = stock important nécessitant déstockage
- **Score Élasticité** : Plus élevé = produit sensible aux promotions
- **Score Ventes** : Plus élevé = tendance de vente défavorable
- **Score Promotions** : Plus élevé = peu de promotions récentes

### Pourcentages de Promotion

- **5-15%** : Promotion légère (produits performants, stock normal)
- **15-30%** : Promotion modérée (équilibre entre performance et déstockage)
- **30-70%** : Promotion forte (surstock, produits en difficulté)

### Prédictions d'Impact

- **Volume des ventes** : Estimation de l'augmentation des unités vendues
- **Revenu** : Impact financier prévu (peut être négatif si la remise est trop importante)
- **Recommandations** : Conseils automatiques basés sur l'analyse

## 🎯 Cas d'Usage Types

### 1. Campagne de Déstockage
```python
# Analyser tous les articles avec surstock
results = model.analyze_category(category_id)
high_stock_items = [r for r in results if r['current_stock'] > 100]
```

### 2. Optimisation du Chiffre d'Affaires
```python
# Identifier les opportunités de revenu
profitable_promos = [r for r in results if r['revenue_change_percentage'] > 0]
```

### 3. Gestion des Risques
```python
# Détecter les promotions risquées
risky_items = [r for r in results if r['current_stock'] < 10]
```

## ⚙️ Configuration Avancée

### Modification des Poids

```python
model.weights = {
    'stock_rotation': 0.40,      # Augmenter pour privilégier le déstockage
    'price_elasticity': 0.30,    # Augmenter pour des promotions plus ciblées
    'sales_history': 0.20,       # Réduire pour moins d'influence historique
    'promotion_history': 0.10    # Réduire pour permettre plus de promotions
}
```

### Modification des Seuils

```python
model.thresholds = {
    'min_promotion': 10,     # Promotion minimale plus élevée
    'max_promotion': 50,     # Promotion maximale plus conservatrice
    'stock_critical': 5,     # Seuil critique plus bas
    'stock_excess': 200      # Seuil de surstock plus élevé
}
```

## 📈 Métriques de Performance

### Indicateurs Clés

1. **Précision des Prédictions** : Comparaison avec les résultats réels
2. **ROI des Promotions** : Retour sur investissement des campagnes
3. **Réduction du Surstock** : Efficacité du déstockage
4. **Optimisation du Revenu** : Amélioration du chiffre d'affaires

### Suivi et Amélioration

- **Analyser les résultats** de campagnes précédentes
- **Ajuster les poids** selon les performances observées
- **Affiner les seuils** selon le secteur d'activité
- **Enrichir les données** avec plus d'historique

## 🔧 Dépannage

### Problèmes Courants

1. **Erreur de Connexion**
   - Vérifier la chaîne de connexion
   - S'assurer que SQL Server est démarré
   - Contrôler les permissions d'accès

2. **Pas de Données**
   - Vérifier que la catégorie existe
   - S'assurer que les articles sont actifs
   - Contrôler la présence d'historique

3. **Résultats Incohérents**
   - Vérifier la qualité des données d'entrée
   - Ajuster les poids du modèle
   - Examiner les seuils configurés

### Logs et Debug

Le modèle génère des logs détaillés pour faciliter le debug :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

### Structure des Fichiers

```
SmartPromo_AI_Model/
├── smartpromo_ai_model.py     # Modèle principal
├── test_model.py              # Tests de validation
├── requirements.txt           # Dépendances
└── README.md                  # Ce guide
```

### Points d'Extension

- **Nouveaux Indicateurs** : Ajouter d'autres critères d'analyse
- **Machine Learning** : Intégrer des algorithmes d'apprentissage
- **API REST** : Exposer le modèle via une API
- **Interface Graphique** : Créer une interface utilisateur

## 🎉 Conclusion

Le SmartPromo AI Model vous permet de :

✅ **Automatiser** le calcul des promotions optimales  
✅ **Maximiser** le retour sur investissement  
✅ **Réduire** les risques de surstock et rupture  
✅ **Prédire** l'impact des décisions commerciales  
✅ **Optimiser** les stratégies de pricing  

---

*Développé pour SmartPromo - Système Intelligent de Gestion des Promotions*
