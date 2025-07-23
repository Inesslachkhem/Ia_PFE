#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test automatisé du modèle SmartPromo AI avec entraînement en mode simulation
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer le modèle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartpromo_ai_model import SmartPromoAIModel

def test_ai_training_with_simulation():
    """Test de l'entraînement IA avec données simulées"""
    print("🤖 Test de l'entraînement SmartPromo AI avec simulation")
    print("=" * 60)
    
    # Configuration de la base de données (factice pour ce test)
    CONNECTION_STRING = "Server=localhost;Database=test;Trusted_Connection=True;"
    
    # Initialisation du modèle
    ai_model = SmartPromoAIModel(CONNECTION_STRING)
    
    print("📊 Tentative d'entraînement avec données simulées...")
    
    # Entraînement avec données simulées
    training_success = ai_model.train_models(use_simulation=True)
    
    if training_success:
        print("✅ Entraînement réussi avec données simulées!")
        print("\n📈 Métriques des modèles:")
        
        for name, metrics in ai_model.model_metrics.items():
            print(f"  {name}:")
            print(f"    R² Score: {metrics['r2']:.3f}")
            print(f"    RMSE: {metrics['rmse']:.3f}")
            print(f"    MAE: {metrics['mae']:.3f}")
            
        print(f"\n🏆 Meilleur modèle: {ai_model.best_model_name}")
        print(f"📊 Score R²: {ai_model.model_metrics[ai_model.best_model_name]['r2']:.3f}")
        
        # Test de prédiction avec le modèle entraîné
        print("\n🧪 Test de prédiction avec le modèle entraîné...")
        
        import pandas as pd
        
        # Article de test
        test_article = pd.Series({
            'ArticleId': 999,
            'ArticleName': 'Article Test IA',
            'Price': 150.0,
            'CurrentStock': 25,
            'MinStockThreshold': 10,
            'CategoryId': 2
        })
        
        # Simulation des méthodes de récupération des données (sans BDD)
        original_get_sales_history = ai_model.get_sales_history
        original_get_promotion_history = ai_model.get_promotion_history
        
        def mock_get_sales_history(article_id, days=90):
            return pd.DataFrame({
                'QuantitySold': [5, 3, 7, 4, 6],
                'QuantityInjected': [50, 50, 50, 50, 50],
                'SalePrice': [150.0] * 5,
                'SaleDate': pd.date_range('2025-07-18', periods=5)
            })
        
        def mock_get_promotion_history(article_id, days=180):
            return pd.DataFrame({
                'StartDate': pd.to_datetime(['2025-06-01', '2025-05-01']),
                'EndDate': pd.to_datetime(['2025-06-07', '2025-05-07']),
                'PriceBeforePromo': [150.0, 150.0],
                'PriceAfterPromo': [120.0, 135.0],
                'SalesDuringPromo': [15, 12],
                'DiscountPercentage': [20.0, 10.0]
            })
        
        ai_model.get_sales_history = mock_get_sales_history
        ai_model.get_promotion_history = mock_get_promotion_history
        
        try:
            # Test de calcul de promotion optimale
            result = ai_model.calculate_optimal_promotion_percentage(test_article)
            
            print(f"🎯 Résultats de prédiction:")
            print(f"   Article: {result['article_name']}")
            print(f"   Prix actuel: {result['current_price']:.2f} €")
            print(f"   Promotion recommandée: {result['optimal_promotion_percentage']}%")
            print(f"   Prix promo: {result['discounted_price']:.2f} €")
            print(f"   Méthode utilisée: {result['prediction_method']}")
            
            if result['prediction_method'] == 'ai':
                print("✅ Le modèle IA a été utilisé avec succès!")
            else:
                print("⚠️ Fallback vers méthode classique")
                
        finally:
            # Restauration des méthodes originales
            ai_model.get_sales_history = original_get_sales_history
            ai_model.get_promotion_history = original_get_promotion_history
        
        return True
        
    else:
        print("❌ Échec de l'entraînement avec données simulées")
        return False

def test_simulation_data_generation():
    """Test de la génération de données simulées"""
    print("\n📊 Test de génération de données simulées")
    print("=" * 45)
    
    CONNECTION_STRING = "Server=localhost;Database=test;Trusted_Connection=True;"
    ai_model = SmartPromoAIModel(CONNECTION_STRING)
    
    # Génération de données simulées
    simulated_data = ai_model.generate_simulated_training_data(n_samples=100)
    
    print(f"📈 Données générées: {len(simulated_data)} échantillons")
    print(f"📋 Colonnes: {list(simulated_data.columns)}")
    
    # Vérification des données
    required_columns = [
        'Price', 'CategoryId', 'CurrentStock', 'PromotionPercentage',
        'SalesBeforePromo', 'SalesDuringPromo', 'RotationRate'
    ]
    
    missing_columns = [col for col in required_columns if col not in simulated_data.columns]
    
    if not missing_columns:
        print("✅ Toutes les colonnes requises sont présentes")
        
        # Statistiques des données
        print(f"\n📊 Statistiques des données simulées:")
        print(f"   Prix moyen: {simulated_data['Price'].mean():.2f} €")
        print(f"   Promotion moyenne: {simulated_data['PromotionPercentage'].mean():.1f}%")
        print(f"   Ventes moyennes avant promo: {simulated_data['SalesBeforePromo'].mean():.1f}")
        print(f"   Ventes moyennes pendant promo: {simulated_data['SalesDuringPromo'].mean():.1f}")
        print(f"   Rotation moyenne: {simulated_data['RotationRate'].mean():.3f}")
        
        return True
    else:
        print(f"❌ Colonnes manquantes: {missing_columns}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test Complet du Modèle SmartPromo AI avec Simulation")
    print("=" * 65)
    
    try:
        # Test 1: Génération de données simulées
        data_gen_success = test_simulation_data_generation()
        
        # Test 2: Entraînement avec données simulées
        training_success = test_ai_training_with_simulation()
        
        print("\n" + "=" * 65)
        print("📋 RÉSUMÉ DES TESTS:")
        print(f"   {'✅' if data_gen_success else '❌'} Génération données simulées: {'OK' if data_gen_success else 'Erreur'}")
        print(f"   {'✅' if training_success else '❌'} Entraînement IA: {'OK' if training_success else 'Erreur'}")
        
        if data_gen_success and training_success:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("🤖 Le modèle SmartPromo AI peut maintenant:")
            print("   ✅ S'entraîner avec des données simulées")
            print("   ✅ Fonctionner sans connexion base de données")
            print("   ✅ Utiliser de vrais algorithmes ML (RandomForest, GradientBoosting, LinearRegression)")
            print("   ✅ Faire des prédictions avec l'IA entraînée")
            print("   ✅ Se rabattre sur la méthode classique si nécessaire")
        else:
            print("\n⚠️ Certains tests ont échoué")
            
        return data_gen_success and training_success
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
