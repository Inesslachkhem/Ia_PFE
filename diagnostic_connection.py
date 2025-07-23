"""
Test de Connexion et Diagnostic - SmartPromo AI Model
===================================================

Ce script teste et diagnostique les problèmes de connexion à la base de données
"""

import pyodbc
import sys
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_odbc_drivers():
    """Test et affichage des pilotes ODBC disponibles"""
    print("🔍 Pilotes ODBC disponibles:")
    print("-" * 40)
    
    drivers = pyodbc.drivers()
    for i, driver in enumerate(drivers, 1):
        print(f"   {i}. {driver}")
    
    return drivers

def test_database_connections():
    """Test de différentes chaînes de connexion"""
    print("\n🔌 Test des connexions à la base de données:")
    print("-" * 50)
    
    # Chaînes de connexion à tester
    connection_strings = [
        # Chaîne de base (originale)
        "Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;",
        
        # Avec ODBC Driver 17
        "DRIVER={ODBC Driver 17 for SQL Server};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;",
        
        # Avec ODBC Driver 18 et TrustServerCertificate
        "DRIVER={ODBC Driver 18 for SQL Server};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;TrustServerCertificate=yes;",
        
        # Avec SQL Server Driver
        "DRIVER={SQL Server};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;",
        
        # Avec SQL Server Native Client
        "DRIVER={SQL Server Native Client 11.0};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;",
    ]
    
    successful_connection = None
    
    for i, conn_str in enumerate(connection_strings, 1):
        print(f"\n   Test {i}: {conn_str[:60]}...")
        
        try:
            conn = pyodbc.connect(conn_str, timeout=10)
            print(f"   ✅ SUCCÈS - Connexion établie!")
            
            # Test d'une requête simple
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM Articles")
            result = cursor.fetchone()
            print(f"   📊 Articles dans la base: {result[0]}")
            
            cursor.close()
            conn.close()
            
            if not successful_connection:
                successful_connection = conn_str
                
        except Exception as e:
            print(f"   ❌ ÉCHEC: {str(e)}")
    
    return successful_connection

def test_table_structure():
    """Test de la structure des tables"""
    print("\n📋 Vérification de la structure des tables:")
    print("-" * 45)
    
    # Utiliser sqlcmd pour vérifier la structure
    import subprocess
    
    tables = ['Articles', 'Categories', 'Stocks', 'Ventes', 'Promotions']
    
    for table in tables:
        try:
            cmd = f'sqlcmd -S "DESKTOP-S22JEMV\\SQLEXPRESS" -d "SmartPromoDb_v2026_Fresh" -E -Q "SELECT TOP 1 * FROM {table}" -h -1'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"   ✅ Table {table}: Accessible")
            else:
                print(f"   ❌ Table {table}: Erreur - {result.stderr}")
                
        except Exception as e:
            print(f"   ⚠️ Table {table}: Impossible de tester - {e}")

def test_smartpromo_model():
    """Test du modèle SmartPromo avec les corrections"""
    print("\n🧠 Test du modèle SmartPromo AI:")
    print("-" * 35)
    
    try:
        from smartpromo_ai_model import SmartPromoAIModel
        
        # Utiliser la chaîne de connexion qui fonctionne
        connection_string = "Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;"
        
        model = SmartPromoAIModel(connection_string)
        
        if model.connect_database():
            print("   ✅ Connexion du modèle réussie!")
            
            # Test d'extraction d'articles
            try:
                articles = model.extract_articles_by_category(1)
                print(f"   📊 Articles extraits (catégorie 1): {len(articles)}")
                
                if len(articles) > 0:
                    print(f"   📝 Premier article: {articles.iloc[0]['ArticleName']}")
                    print("   🎯 Modèle prêt pour l'analyse!")
                else:
                    print("   ⚠️ Aucun article trouvé dans la catégorie 1")
                    
            except Exception as e:
                print(f"   ❌ Erreur lors de l'extraction: {e}")
            
            model.disconnect_database()
            return True
        else:
            print("   ❌ Échec de connexion du modèle")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test du modèle: {e}")
        return False

def main():
    """Fonction principale de diagnostic"""
    print("🚀 SmartPromo AI - Diagnostic de Connexion")
    print("=" * 55)
    
    # Test 1: Pilotes ODBC
    drivers = test_odbc_drivers()
    
    # Test 2: Connexions à la base
    successful_conn = test_database_connections()
    
    # Test 3: Structure des tables
    test_table_structure()
    
    # Test 4: Modèle SmartPromo
    model_ok = test_smartpromo_model()
    
    # Résumé final
    print("\n" + "=" * 55)
    print("📋 RÉSUMÉ DU DIAGNOSTIC:")
    print("-" * 25)
    
    if successful_conn:
        print("✅ Connexion à la base de données: OK")
        print(f"   Chaîne recommandée: {successful_conn[:60]}...")
    else:
        print("❌ Connexion à la base de données: ÉCHEC")
        
    if model_ok:
        print("✅ Modèle SmartPromo AI: FONCTIONNEL")
        print("\n🎉 Vous pouvez maintenant utiliser le modèle:")
        print("   python smartpromo_ai_model.py")
    else:
        print("❌ Modèle SmartPromo AI: PROBLÈME")
        print("\n🔧 Actions recommandées:")
        print("   1. Vérifiez que SQL Server Express est démarré")
        print("   2. Installez le pilote ODBC pour SQL Server")
        print("   3. Vérifiez les permissions d'accès à la base")

if __name__ == "__main__":
    main()
