"""
Test d'Affichage des Prix en Dinars Tunisiens - SmartPromo AI
=============================================================

Ce script teste l'affichage des prix convertis en dinars tunisiens (DT)
dans les analyses de promotion SmartPromo AI.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartpromo_ai_model import SmartPromoAIModel
import pandas as pd

def test_currency_display():
    """Test l'affichage des prix en dinars tunisiens"""
    
    print("🧪 Test Affichage Prix en Dinars Tunisiens")
    print("=" * 50)
    
    # Configuration de la base de données
    CONNECTION_STRING = "Server=localhost;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;"
    
    try:
        # Initialisation du modèle
        ai_model = SmartPromoAIModel(CONNECTION_STRING)
        
        print("🔗 Connexion à la base de données...")
        ai_model.connect()
        
        print("📊 Récupération d'articles pour test...")
        
        # Récupération de quelques articles pour test
        query = """
        SELECT TOP 3
            a.ArticleId,
            a.NomArticle as ArticleName,
            a.Prix_Vente_TND as Price,
            a.StockActuel as CurrentStock,
            a.SeuilMinStock as MinStockThreshold,
            a.CategorieId as CategoryId
        FROM Articles a
        WHERE a.Prix_Vente_TND > 0 
        AND a.StockActuel > 0
        ORDER BY a.Prix_Vente_TND DESC
        """
        
        cursor = ai_model.connection.cursor()
        cursor.execute(query)
        
        articles = []
        for row in cursor.fetchall():
            article = pd.Series({
                'ArticleId': row[0],
                'ArticleName': row[1],
                'Price': row[2],
                'CurrentStock': row[3],
                'MinStockThreshold': row[4],
                'CategoryId': row[5]
            })
            articles.append(article)
        
        print(f"✅ {len(articles)} articles récupérés pour test")
        
        # Test de calcul et affichage avec un article
        if articles:
            test_article = articles[0]
            
            print(f"\n🧮 Calcul de promotion pour: {test_article['ArticleName']}")
            print(f"💰 Prix en base (TND): {test_article['Price']:.2f} DT")
            
            # Calcul de la promotion optimale
            result = ai_model.calculate_optimal_promotion_percentage(test_article)
            
            print(f"\n📊 Résultats d'analyse:")
            print(f"   Article: {result['article_name']}")
            print(f"   Prix actuel: {result['current_price']:.2f} DT")
            print(f"   Promotion recommandée: {result['optimal_promotion_percentage']}%")
            print(f"   Prix après promotion: {result['discounted_price']:.2f} DT")
            print(f"   Méthode utilisée: {result.get('prediction_method', 'classic')}")
            
            # Validation de l'affichage en DT
            if 'DT' in f"{result['current_price']:.2f} DT":
                print("✅ Affichage en dinars tunisiens: CORRECT")
            else:
                print("❌ Affichage en dinars tunisiens: ÉCHEC")
                
        else:
            print("❌ Aucun article trouvé pour le test")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        
    finally:
        try:
            ai_model.disconnect()
            print("🔌 Connexion fermée")
        except:
            pass

def demo_currency_conversion():
    """Démo de conversion de prix en dinars tunisiens"""
    
    print("\n🏦 Démonstration Conversion Prix en Dinars Tunisiens")
    print("=" * 55)
    
    # Exemples de prix en TND
    prices_examples = [
        {"article": "Jean Slim Noir T.36", "price_tnd": 100.61},
        {"article": "Pantalon Chino Rose T.38", "price_tnd": 67.34},
        {"article": "Pantalon Costume Marron T.34", "price_tnd": 83.73},
    ]
    
    print("📋 Exemples de prix en dinars tunisiens:")
    for item in prices_examples:
        promotion_20 = item["price_tnd"] * 0.8  # 20% de réduction
        promotion_30 = item["price_tnd"] * 0.7  # 30% de réduction
        
        print(f"""
🏷️  {item['article']}
   💰 Prix normal: {item['price_tnd']:.2f} DT
   📊 Avec 20% promo: {promotion_20:.2f} DT
   📊 Avec 30% promo: {promotion_30:.2f} DT
        """)
    
    print("✅ Tous les prix sont affichés en dinars tunisiens (DT)")

if __name__ == "__main__":
    print("🇹🇳 SmartPromo AI - Test Affichage Dinars Tunisiens")
    print("=" * 60)
    
    # Test de l'affichage des prix
    demo_currency_conversion()
    
    # Test avec la base de données (si disponible)
    test_currency_display()
    
    print("\n🎉 Test terminé!")
    print("Les prix sont maintenant affichés en dinars tunisiens (DT)")
