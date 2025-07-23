"""
Script de Test Rapide - SmartPromo AI Model
===========================================

Ce script teste rapidement les fonctionnalités principales du modèle IA
"""

from smartpromo_ai_model import SmartPromoAIModel
import logging

# Configuration de base
CONNECTION_STRING = "Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;"

def test_connection():
    """Test de connexion à la base de données"""
    print("🔌 Test de connexion à la base de données...")
    
    model = SmartPromoAIModel(CONNECTION_STRING)
    
    if model.connect_database():
        print("✅ Connexion réussie!")
        model.disconnect_database()
        return True
    else:
        print("❌ Échec de la connexion!")
        return False

def test_quick_analysis():
    """Test d'analyse rapide sur la catégorie 1"""
    print("\n🧪 Test d'analyse rapide (Catégorie 1)...")
    
    model = SmartPromoAIModel(CONNECTION_STRING)
    
    try:
        results = model.analyze_category(1)
        
        if results:
            print(f"✅ Analyse réussie! {len(results)} articles analysés")
            
            # Affichage du premier résultat
            if len(results) > 0:
                first_result = results[0]
                print(f"\n📊 Exemple de résultat:")
                print(f"   Article: {first_result['article_name']}")
                print(f"   Promotion recommandée: {first_result['optimal_promotion_percentage']}%")
                print(f"   Impact revenu: {first_result['revenue_change_percentage']:+.1f}%")
            
            return True
        else:
            print("⚠️ Aucun résultat (catégorie vide ou inexistante)")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def run_all_tests():
    """Exécute tous les tests"""
    print("🚀 SmartPromo AI Model - Tests de Validation")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Connexion
    if test_connection():
        tests_passed += 1
    
    # Test 2: Analyse rapide
    if test_quick_analysis():
        tests_passed += 1
    
    # Résultats
    print(f"\n📋 Résultats des tests: {tests_passed}/{total_tests} réussis")
    
    if tests_passed == total_tests:
        print("🎉 Tous les tests sont passés! Le modèle est prêt à être utilisé.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    run_all_tests()
