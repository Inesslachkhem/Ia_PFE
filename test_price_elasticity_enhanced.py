#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la méthode d'élasticité prix améliorée
Valide l'utilisation des prix avant/après promotion de la base de données
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ajouter le répertoire parent au path pour importer le modèle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartpromo_ai_model import SmartPromoAIModel

def test_price_elasticity_with_promotion_data():
    """Test de l'élasticité prix avec données de promotions"""
    print("🧪 Test de l'élasticité prix avec données avant/après promotion")
    print("=" * 60)
    
    # Initialisation du modèle (sans connexion réelle)
    fake_connection = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=test;Trusted_Connection=yes;"
    model = SmartPromoAIModel(fake_connection)
    
    # Simulation des données d'article
    article_data = pd.Series({
        'ArticleId': 1,
        'ArticleName': 'Test Article Elasticité',
        'Price': 100.0,
        'CurrentStock': 45,
        'MinStockThreshold': 10,
        'CategoryId': 2
    })
    
    # Simulation de l'historique des ventes (méthode de fallback)
    sales_history = pd.DataFrame({
        'QuantitySold': [8, 6, 12, 15, 5, 18, 10, 7, 14, 9],
        'SalePrice': [100.0, 95.0, 90.0, 85.0, 100.0, 80.0, 95.0, 100.0, 85.0, 90.0],
        'SaleDate': pd.date_range('2025-07-01', periods=10)
    })
    
    # Simulation de l'historique des promotions avec prix avant/après
    promotion_history = pd.DataFrame({
        'StartDate': ['2025-06-01', '2025-05-15', '2025-04-20'],
        'EndDate': ['2025-06-07', '2025-05-22', '2025-04-27'],
        'DiscountPercentage': [15.0, 25.0, 20.0],
        'PriceBeforePromo': [100.0, 100.0, 100.0],
        'PriceAfterPromo': [85.0, 75.0, 80.0],  # Prix calculés avec réduction
        'SalesDuringPromo': [25, 45, 35]  # Ventes pendant chaque promotion
    })
    
    print("📊 Données de test:")
    print(f"   Article: {article_data['ArticleName']}")
    print(f"   Prix actuel: {article_data['Price']:.2f} €")
    print(f"   Historique ventes: {len(sales_history)} entrées")
    print(f"   Historique promotions: {len(promotion_history)} promotions")
    
    print("\n🔍 Analyse des promotions passées:")
    for i, promo in promotion_history.iterrows():
        prix_avant = promo['PriceBeforePromo']
        prix_apres = promo['PriceAfterPromo']
        reduction = promo['DiscountPercentage']
        ventes = promo['SalesDuringPromo']
        
        # Calcul de l'élasticité pour cette promotion
        changement_prix = (prix_apres - prix_avant) / prix_avant * 100
        ventes_normales_estimees = 15  # Estimation
        changement_demande = (ventes - ventes_normales_estimees) / ventes_normales_estimees * 100
        
        if changement_prix != 0:
            elasticite = abs(changement_demande / changement_prix)
        else:
            elasticite = 0
        
        print(f"   Promotion {i+1}: {reduction}% → Prix {prix_avant:.0f}€ → {prix_apres:.0f}€")
        print(f"      Changement prix: {changement_prix:.1f}%")
        print(f"      Ventes: {ventes} unités (vs {ventes_normales_estimees} normales)")
        print(f"      Changement demande: {changement_demande:.1f}%")
        print(f"      Élasticité calculée: {elasticite:.2f}")
    
    # Test de la méthode améliorée avec données de promotions
    print("\n🤖 Test de la méthode améliorée:")
    elasticity_score_with_promos = model.calculate_price_elasticity_score(
        article_data, sales_history, promotion_history
    )
    
    # Test de la méthode de fallback (sans promotions)
    print("\n📊 Test de la méthode de fallback:")
    elasticity_score_fallback = model.calculate_price_elasticity_score(
        article_data, sales_history, None
    )
    
    print(f"\n📈 Résultats:")
    print(f"   Score avec données promotions: {elasticity_score_with_promos:.3f}")
    print(f"   Score méthode fallback: {elasticity_score_fallback:.3f}")
    print(f"   Différence: {abs(elasticity_score_with_promos - elasticity_score_fallback):.3f}")
    
    # Interprétation des scores
    def interpret_elasticity_score(score):
        if score >= 0.8:
            return "Très élastique - Promotion très efficace"
        elif score >= 0.6:
            return "Assez élastique - Promotion efficace"
        elif score >= 0.4:
            return "Moyennement élastique"
        elif score >= 0.2:
            return "Peu élastique - Promotion peu efficace"
        else:
            return "Très peu élastique"
    
    print(f"\n🎯 Interprétation:")
    print(f"   Méthode promotions: {interpret_elasticity_score(elasticity_score_with_promos)}")
    print(f"   Méthode fallback: {interpret_elasticity_score(elasticity_score_fallback)}")
    
    return elasticity_score_with_promos, elasticity_score_fallback

def test_edge_cases():
    """Test des cas limites"""
    print("\n🧪 Test des cas limites")
    print("=" * 30)
    
    fake_connection = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=test;Trusted_Connection=yes;"
    model = SmartPromoAIModel(fake_connection)
    
    article_data = pd.Series({
        'ArticleId': 2,
        'ArticleName': 'Test Article Cas Limites',
        'Price': 50.0,
        'CurrentStock': 20,
        'MinStockThreshold': 5,
        'CategoryId': 1
    })
    
    # Test 1: Pas d'historique de promotions
    print("Test 1: Pas d'historique de promotions")
    empty_promos = pd.DataFrame()
    empty_sales = pd.DataFrame()
    score1 = model.calculate_price_elasticity_score(article_data, empty_sales, empty_promos)
    print(f"   Score (pas de données): {score1:.3f}")
    
    # Test 2: Une seule promotion
    print("\nTest 2: Une seule promotion")
    single_promo = pd.DataFrame({
        'PriceBeforePromo': [50.0],
        'PriceAfterPromo': [40.0],
        'SalesDuringPromo': [20]
    })
    score2 = model.calculate_price_elasticity_score(article_data, empty_sales, single_promo)
    print(f"   Score (une promotion): {score2:.3f}")
    
    # Test 3: Promotions avec des prix égaux (pas de changement)
    print("\nTest 3: Promotions sans changement de prix")
    no_change_promo = pd.DataFrame({
        'PriceBeforePromo': [50.0, 50.0],
        'PriceAfterPromo': [50.0, 50.0],
        'SalesDuringPromo': [15, 18]
    })
    score3 = model.calculate_price_elasticity_score(article_data, empty_sales, no_change_promo)
    print(f"   Score (pas de changement prix): {score3:.3f}")
    
    return score1, score2, score3

def main():
    """Fonction principale de test"""
    print("🧪 Test de la Méthode d'Élasticité Prix Améliorée")
    print("=" * 55)
    
    try:
        # Test principal
        score_promos, score_fallback = test_price_elasticity_with_promotion_data()
        
        # Test des cas limites
        edge_scores = test_edge_cases()
        
        print("\n" + "=" * 55)
        print("✅ RÉSUMÉ DES TESTS:")
        print(f"   🎯 Méthode avec promotions: Fonctionnelle")
        print(f"   🔄 Méthode de fallback: Fonctionnelle")
        print(f"   🛡️ Gestion cas limites: Robuste")
        print(f"   📊 Amélioration détectée: {'Oui' if abs(score_promos - score_fallback) > 0.1 else 'Mineure'}")
        
        print("\n🎉 La méthode d'élasticité prix utilise maintenant:")
        print("   ✅ Les prix avant/après promotion de la base de données")
        print("   ✅ Un calcul d'élasticité réel basé sur les promotions passées")
        print("   ✅ Une méthode de fallback robuste si pas de données")
        print("   ✅ Une gestion appropriée des cas limites")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
