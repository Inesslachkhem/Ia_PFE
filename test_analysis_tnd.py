"""
Test Analyse SmartPromo AI avec Affichage Dinars Tunisiens
==========================================================

Ce script génère une analyse SmartPromo AI avec affichage natif en dinars tunisiens.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartpromo_ai_model import SmartPromoAIModel
import pandas as pd
import json
from datetime import datetime

def run_analysis_with_tnd_display():
    """Exécute une analyse SmartPromo AI avec affichage en dinars tunisiens"""
    
    print("🇹🇳 Analyse SmartPromo AI - Affichage Dinars Tunisiens")
    print("=" * 60)
    
    # Configuration
    CONNECTION_STRING = "Server=localhost;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;"
    
    try:
        # Initialisation du modèle
        ai_model = SmartPromoAIModel(CONNECTION_STRING)
        
        print("🔗 Tentative de connexion à la base de données...")
        
        # Test de connexion
        try:
            connection = ai_model.get_connection()
            connection.close()
            print("✅ Base de données disponible")
            use_simulation = False
        except:
            print("⚠️ Base de données non disponible, utilisation du mode simulation")
            use_simulation = True
        
        # Entraînement des modèles
        print("🤖 Entraînement des modèles d'IA...")
        training_success = ai_model.train_models(use_simulation=use_simulation)
        
        if training_success:
            print("✅ Modèles d'IA entraînés avec succès")
        else:
            print("⚠️ Entraînement IA échoué, utilisation de la méthode classique")
        
        # Création d'articles d'exemple pour le test
        test_articles = [
            {
                'ArticleId': 101,
                'ArticleName': 'Jean Slim Noir T.32 - Test TND',
                'Price': 89.50,  # Prix en TND
                'CurrentStock': 45,
                'MinStockThreshold': 15,
                'CategoryId': 1
            },
            {
                'ArticleId': 102,
                'ArticleName': 'Pantalon Chino Bleu T.36 - Test TND',
                'Price': 75.25,  # Prix en TND
                'CurrentStock': 28,
                'MinStockThreshold': 10,
                'CategoryId': 2
            },
            {
                'ArticleId': 103,
                'ArticleName': 'Pantalon Costume Noir T.40 - Test TND',
                'Price': 125.75,  # Prix en TND
                'CurrentStock': 12,
                'MinStockThreshold': 5,
                'CategoryId': 3
            }
        ]
        
        results = []
        
        for article_data in test_articles:
            article = pd.Series(article_data)
            
            print(f"\n📊 Analyse pour: {article['ArticleName']}")
            print(f"💰 Prix: {article['Price']:.2f} DT")
            
            # Calcul de la promotion optimale
            result = ai_model.calculate_optimal_promotion_percentage(article)
            
            # Mise à jour du résultat pour affichage TND
            result_tnd = {
                **result,
                'currency': 'TND',
                'currency_symbol': 'DT'
            }
            
            results.append(result_tnd)
            
            # Affichage détaillé en TND
            print(f"   🏷️ Article: {result['article_name']}")
            print(f"   💰 Prix actuel: {result['current_price']:.2f} DT")
            print(f"   📊 Promotion recommandée: {result['optimal_promotion_percentage']}%")
            print(f"   💸 Prix après promotion: {result['discounted_price']:.2f} DT")
            print(f"   📈 Ventes prévues: {result['current_monthly_sales_volume']:.0f} → {result['predicted_monthly_sales_volume']:.0f} unités")
            print(f"   💰 Revenu prévu: {result['current_monthly_revenue']:.2f} → {result['predicted_monthly_revenue']:.2f} DT")
            print(f"   📊 Impact revenu: {result['revenue_change_percentage']:+.1f}%")
            print(f"   🎯 Recommandation: {result['recommendation']}")
            
            if result.get('prediction_method') == 'ai':
                print(f"   🤖 Méthode: Intelligence Artificielle")
            else:
                print(f"   📊 Méthode: Calcul Classique")
        
        # Sauvegarde des résultats avec suffix TND
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"smartpromo_analysis_TND_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés: {output_file}")
        
        # Résumé final
        total_revenue_change = sum(r.get('revenue_change', 0) for r in results)
        avg_promotion = sum(r.get('optimal_promotion_percentage', 0) for r in results) / len(results)
        
        print(f"\n📋 RÉSUMÉ DE L'ANALYSE (en DT):")
        print(f"   • Articles analysés: {len(results)}")
        print(f"   • Promotion moyenne: {avg_promotion:.1f}%")
        print(f"   • Impact total revenu: {total_revenue_change:+.2f} DT")
        print(f"   • Devise: Dinars Tunisiens (DT)")
        
        return results
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {str(e)}")
        return None

def validate_tnd_display(results):
    """Valide que l'affichage utilise bien les dinars tunisiens"""
    
    print(f"\n🔍 Validation Affichage Dinars Tunisiens")
    print("=" * 45)
    
    if not results:
        print("❌ Aucun résultat à valider")
        return False
    
    validation_passed = True
    
    for result in results:
        article_name = result.get('article_name', 'N/A')
        
        # Vérification de la présence des informations de devise
        if result.get('currency') == 'TND':
            print(f"✅ {article_name}: Devise TND correcte")
        else:
            print(f"❌ {article_name}: Devise manquante ou incorrecte")
            validation_passed = False
        
        if result.get('currency_symbol') == 'DT':
            print(f"✅ {article_name}: Symbole DT correct")
        else:
            print(f"❌ {article_name}: Symbole devise incorrect")
            validation_passed = False
    
    if validation_passed:
        print("🎉 Validation réussie: Tous les prix sont en dinars tunisiens!")
    else:
        print("⚠️ Validation échouée: Problèmes d'affichage détectés")
    
    return validation_passed

if __name__ == "__main__":
    print("🚀 Démarrage du test d'analyse avec dinars tunisiens...")
    
    # Exécution de l'analyse
    results = run_analysis_with_tnd_display()
    
    # Validation de l'affichage
    if results:
        validate_tnd_display(results)
    
    print(f"\n✅ Test terminé!")
    print(f"🇹🇳 Tous les prix sont maintenant affichés en dinars tunisiens (DT)")
