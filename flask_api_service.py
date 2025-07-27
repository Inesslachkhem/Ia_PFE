"""
SmartPromo AI Flask API Service
==============================

Service Flask pour l'intégration de l'IA SmartPromo avec le frontend Angular.
Fournit des endpoints REST pour la génération de promotions intelligentes.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging
from datetime import datetime
import traceback

# Ajout du chemin pour importer le modèle IA
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from smartpromo_ai_model import SmartPromoAIModel
except ImportError as e:
    print(f"❌ Erreur d'import du modèle IA: {e}")
    SmartPromoAIModel = None

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)  # Permet les requêtes cross-origin depuis Angular

# Configuration
app.config['JSON_AS_ASCII'] = False  # Support des caractères UTF-8

# Configuration de la base de données
# Essayons plusieurs drivers ODBC possibles
POSSIBLE_CONNECTION_STRINGS = [
    "DRIVER={ODBC Driver 17 for SQL Server};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;",
  ]

CONNECTION_STRING = None

def test_database_connection():
    """Teste différentes chaînes de connexion pour trouver la bonne"""
    global CONNECTION_STRING
    import pyodbc
    
    for conn_str in POSSIBLE_CONNECTION_STRINGS:
        try:
            logger.info(f"🔍 Test de connexion avec: {conn_str[:50]}...")
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            CONNECTION_STRING = conn_str
            logger.info(f"✅ Connexion réussie avec: {conn_str[:50]}...")
            return True
            
        except Exception as e:
            logger.warning(f"❌ Échec avec ce driver: {str(e)[:100]}...")
            continue
    
    logger.error("❌ Aucune connexion de base de données n'a fonctionné")
    return False

# Test de la connexion au démarrage
test_database_connection()

# Instance globale du modèle IA
ai_model = None
model_status = {
    'initialized': False,
    'trained': False,
    'last_error': None,
    'last_update': None
}

def initialize_ai_model():
    """Initialise le modèle d'IA"""
    global ai_model, model_status
    
    try:
        if SmartPromoAIModel is None:
            raise ImportError("Module SmartPromoAIModel non disponible")
            
        logger.info("🤖 Initialisation du modèle IA...")
        ai_model = SmartPromoAIModel(CONNECTION_STRING)
        
        # Tentative de chargement d'un modèle pré-entraîné
        if ai_model.load_model():
            logger.info("✅ Modèle pré-entraîné chargé")
            model_status['trained'] = True
        else:
            logger.info("📚 Entraînement d'un nouveau modèle...")
            if ai_model.train_models(use_simulation=False):
                logger.info("✅ Modèle entraîné avec succès")
                model_status['trained'] = True
            else:
                logger.warning("⚠️ Utilisation du mode simulation")
                ai_model.train_models(use_simulation=True)
                model_status['trained'] = True
        
        model_status['initialized'] = True
        model_status['last_update'] = datetime.now().isoformat()
        model_status['last_error'] = None
        
        logger.info("🎯 Modèle IA prêt à utiliser")
        
    except Exception as e:
        error_msg = f"Erreur d'initialisation du modèle IA: {e}"
        logger.error(error_msg)
        model_status['last_error'] = error_msg
        model_status['initialized'] = False

# Initialisation au démarrage
initialize_ai_model()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de vérification de l'état de l'API"""
    return jsonify({
        'status': 'healthy',
        'service': 'SmartPromo AI API',
        'timestamp': datetime.now().isoformat(),
        'model_status': model_status
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Récupère la liste des catégories depuis la base de données"""
    try:
        import pyodbc
        
        if not CONNECTION_STRING:
            logger.warning("⚠️ Aucune connexion DB disponible, utilisation des données fallback")
            raise Exception("Pas de connexion DB")
        
        logger.info("🔍 Récupération des catégories depuis la base de données...")
        
        # Connexion à la base de données
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Requête pour récupérer les catégories
        # D'abord, testons la structure de la table
        try:
            cursor.execute("SELECT TOP 1 * FROM Categories")
            columns = [column[0] for column in cursor.description]
            logger.info(f"🔍 Colonnes disponibles dans Categories: {columns}")
        except Exception as e:
            logger.warning(f"Impossible de récupérer la structure: {e}")
        
        # Requête adaptée avec les vrais noms de colonnes
        query = """
        SELECT IdCategorie, Nom, Description 
        FROM Categories 
        ORDER BY Nom
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        categories = []
        for row in rows:
            categories.append({
                'id': row.IdCategorie,
                'name': row.Nom,
                'description': row.Description or ''
            })
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ {len(categories)} catégories récupérées depuis la DB")
        
        return jsonify({
            'success': True,
            'categories': categories,
            'count': len(categories),
            'source': 'database'
        })
        
    except Exception as e:
        logger.warning(f"⚠️ Erreur DB (utilisation fallback): {str(e)[:100]}...")
        
        # Fallback sur des catégories simulées si erreur DB
        categories = [
            {'id': 1, 'name': 'Électronique', 'description': 'Appareils électroniques'},
            {'id': 2, 'name': 'Vêtements', 'description': 'Vêtements et accessoires'},
            {'id': 3, 'name': 'Alimentation', 'description': 'Produits alimentaires'},
            {'id': 4, 'name': 'Maison & Jardin', 'description': 'Articles pour la maison'},
            {'id': 5, 'name': 'Sport & Loisirs', 'description': 'Équipements sportifs'},
            {'id': 6, 'name': 'Beauté & Santé', 'description': 'Produits de beauté et santé'},
            {'id': 7, 'name': 'Automobile', 'description': 'Accessoires auto et moto'},
            {'id': 8, 'name': 'Livres & Media', 'description': 'Livres, films et musique'}
        ]
        
        return jsonify({
            'success': True,
            'categories': categories,
            'count': len(categories),
            'source': 'fallback'
        })

@app.route('/api/test/promotions', methods=['GET'])
def test_promotions_table():
    """Endpoint de test pour vérifier la structure de la table Promotions"""
    try:
        import pyodbc
        
        if not CONNECTION_STRING:
            return jsonify({
                'success': False,
                'message': 'Aucune connexion DB configurée'
            }), 503
        
        logger.info("🧪 Test de la structure de la table Promotions...")
        
        # Connexion à la base de données
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Test de la table Promotions
        try:
            cursor.execute("SELECT TOP 3 * FROM Promotions ORDER BY Id DESC")
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            promotions_data = []
            for row in rows:
                row_data = {}
                for i, column in enumerate(columns):
                    row_data[column] = row[i] if len(row) > i else None
                promotions_data.append(row_data)
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'table': 'Promotions',
                'columns': columns,
                'sample_data': promotions_data,
                'total_records': len(promotions_data),
                'connection_string': CONNECTION_STRING[:50] + "..."
            })
            
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Erreur lors du test de Promotions: {str(e)}',
                'connection_string': CONNECTION_STRING[:50] + "..."
            }), 500
        
    except Exception as e:
        logger.error(f"Erreur lors du test DB: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur de connexion: {str(e)}'
        }), 500

@app.route('/api/debug/save-test', methods=['POST'])
def debug_save_test():
    """Endpoint de debug pour tester la sauvegarde avec des données simplifiées"""
    try:
        logger.info("🐛 Test de debug de la sauvegarde...")
        
        # Données de test simplifiées
        test_data = {
            'promotions': [{
                'article_id': 999,
                'article_name': 'Test Debug Product',
                'current_price': 100.0,
                'promotional_price': 80.0,
                'promotion_percentage': 20.0,
                'risk_level': 'low',
                'recommendation': 'Test de debug',
                'impact': {
                    'revenue_change_percentage': 10.0,
                    'volume_change_percentage': 15.0
                },
                'scores': {
                    'final_score': 0.85,
                    'sales_score': 0.7,
                    'elasticity_score': 0.8
                }
            }],
            'start_date': '2025-01-27',
            'end_date': '2025-02-27'
        }
        
        # Utiliser la même logique que save_promotions
        promotions = test_data['promotions']
        
        import pyodbc
        
        if not CONNECTION_STRING:
            return jsonify({
                'success': False,
                'message': 'Base de données non disponible',
                'debug': True
            }), 503
        
        logger.info(f"🐛 Test sauvegarde de {len(promotions)} promotions...")
        
        # Connexion à la base de données
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for promo in promotions:
            try:
                current_price = promo.get('current_price', 0)
                promotional_price = promo.get('promotional_price', 0)
                promotion_percentage = promo.get('promotion_percentage', 0)
                article_id = promo.get('article_id', 0)
                
                code_article = f"DBG{article_id:06d}"  # Debug prefix
                
                impact_data = promo.get('impact', {})
                scores_data = promo.get('scores', {})
                
                expected_revenue_impact = impact_data.get('revenue_change_percentage', 0) / 100.0
                expected_volume_impact = impact_data.get('volume_change_percentage', 0) / 100.0
                prediction_confidence = scores_data.get('final_score', 0.85)
                seasonal_adjustment = scores_data.get('sales_score', 0) * 0.1
                temporal_adjustment = scores_data.get('elasticity_score', 0) * 0.1
                
                insert_query = """
                INSERT INTO Promotions 
                (CodeArticle, Prix_Vente_TND_Avant, Prix_Vente_TND_Apres, TauxReduction, 
                 DateDebut, DateFin, IsAccepted, DateCreation, PredictionConfidence, 
                 ExpectedRevenueImpact, ExpectedVolumeImpact, SeasonalAdjustment, 
                 TemporalAdjustment, ReminderEmailSent)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_query, 
                    code_article,
                    float(current_price),
                    float(promotional_price),
                    float(promotion_percentage),
                    test_data.get('start_date'),
                    test_data.get('end_date'),
                    0,
                    float(prediction_confidence),
                    float(expected_revenue_impact),
                    float(expected_volume_impact),
                    float(seasonal_adjustment),
                    float(temporal_adjustment),
                    0
                )
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"🐛 Erreur lors de la sauvegarde debug: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🐛 Debug: {saved_count} promotions sauvegardées")
        
        return jsonify({
            'success': True,
            'message': f'Debug: {saved_count} promotions sauvegardées avec succès',
            'debug': True,
            'saved_count': saved_count,
            'test_data': test_data
        })
        
    except Exception as e:
        logger.error(f"🐛 Erreur debug sauvegarde: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur debug: {str(e)}',
            'debug': True
        }), 500

@app.route('/api/test/database', methods=['GET'])
def test_database():
    """Endpoint de test pour vérifier la structure de la base de données"""
    try:
        import pyodbc
        
        if not CONNECTION_STRING:
            return jsonify({
                'success': False,
                'message': 'Aucune connexion DB configurée'
            }), 503
        
        logger.info("🧪 Test de la structure de la base de données...")
        
        # Connexion à la base de données
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Test de la table Categories
        try:
            cursor.execute("SELECT TOP 3 * FROM Categories")
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            categories_data = []
            for row in rows:
                row_data = {}
                for i, column in enumerate(columns):
                    row_data[column] = row[i] if len(row) > i else None
                categories_data.append(row_data)
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'table': 'Categories',
                'columns': columns,
                'sample_data': categories_data,
                'connection_string': CONNECTION_STRING[:50] + "..."
            })
            
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Erreur lors du test de Categories: {str(e)}',
                'connection_string': CONNECTION_STRING[:50] + "..."
            }), 500
        
    except Exception as e:
        logger.error(f"Erreur lors du test DB: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur de connexion: {str(e)}'
        }), 500

@app.route('/api/promotions/generate', methods=['POST'])
def generate_promotions():
    """Génère des promotions IA pour une catégorie"""
    try:
        if not model_status['initialized']:
            return jsonify({
                'success': False,
                'message': 'Modèle IA non initialisé'
            }), 503
            
        data = request.get_json()
        category_id = data.get('category_id', 1)
        
        logger.info(f"🔍 Génération de promotions pour la catégorie {category_id}")
        
        # Utilisation du modèle IA pour analyser la catégorie
        if ai_model:
            results = ai_model.analyze_category(category_id)
        else:
            # Données simulées si le modèle n'est pas disponible
            results = generate_simulated_promotions(category_id)
        
        if not results:
            return jsonify({
                'success': False,
                'message': 'Aucune promotion générée pour cette catégorie'
            }), 404
        
        # Transformation des résultats pour l'interface
        promotions = []
        for result in results:
            promotion = {
                'article_id': result.get('article_id'),
                'article_name': result.get('article_name'),
                'current_price': result.get('current_price'),
                'promotional_price': result.get('discounted_price'),
                'promotion_percentage': result.get('optimal_promotion_percentage'),
                'current_stock': result.get('current_stock', 0),
                'prediction_method': result.get('prediction_method', 'ai'),
                'scores': {
                    'stock_score': result.get('stock_score', 0),
                    'elasticity_score': result.get('elasticity_score', 0),
                    'sales_score': result.get('sales_score', 0),
                    'promotion_score': result.get('promotion_score', 0),
                    'final_score': result.get('final_score', 0)
                },
                'impact': {
                    'current_monthly_sales_volume': result.get('current_monthly_sales_volume', 0),
                    'predicted_monthly_sales_volume': result.get('predicted_monthly_sales_volume', 0),
                    'volume_change_percentage': result.get('sales_volume_change_percentage', 0),
                    'current_monthly_revenue': result.get('current_monthly_revenue', 0),
                    'predicted_monthly_revenue': result.get('predicted_monthly_revenue', 0),
                    'revenue_change_percentage': result.get('revenue_change_percentage', 0),
                    'profit_change_percentage': result.get('revenue_change_percentage', 0) * 0.7  # Estimation
                },
                'recommendation': result.get('recommendation', ''),
                'risk_level': calculate_risk_level(result),
                'created_at': datetime.now().isoformat()
            }
            promotions.append(promotion)
        
        # Calcul des statistiques
        statistics = calculate_statistics(promotions)
        
        logger.info(f"✅ {len(promotions)} promotions générées avec succès")
        
        return jsonify({
            'success': True,
            'message': f'{len(promotions)} promotions générées avec succès',
            'data': {
                'promotions': promotions,
                'statistics': statistics,
                'category_id': category_id,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la génération: {str(e)}'
        }), 500

def generate_simulated_promotions(category_id):
    """Génère des promotions simulées pour les tests"""
    import random
    
    simulated_articles = [
        {'name': 'Smartphone Galaxy', 'base_price': 599.99},
        {'name': 'Laptop Dell', 'base_price': 899.99},
        {'name': 'Écouteurs Bluetooth', 'base_price': 79.99},
        {'name': 'Montre Connectée', 'base_price': 199.99},
        {'name': 'Tablette iPad', 'base_price': 449.99}
    ]
    
    results = []
    for i, article in enumerate(simulated_articles):
        promotion_pct = random.uniform(10, 40)
        discounted_price = article['base_price'] * (1 - promotion_pct/100)
        
        result = {
            'article_id': i + 1,
            'article_name': article['name'],
            'current_price': article['base_price'],
            'discounted_price': discounted_price,
            'optimal_promotion_percentage': promotion_pct,
            'current_stock': random.randint(5, 100),
            'stock_score': random.uniform(0.2, 0.9),
            'elasticity_score': random.uniform(0.3, 0.8),
            'sales_score': random.uniform(0.4, 0.9),
            'promotion_score': random.uniform(0.2, 0.7),
            'final_score': random.uniform(0.3, 0.8),
            'prediction_method': 'simulation',
            'current_monthly_sales_volume': random.uniform(10, 50),
            'predicted_monthly_sales_volume': random.uniform(15, 80),
            'sales_volume_change_percentage': random.uniform(5, 60),
            'current_monthly_revenue': article['base_price'] * random.uniform(10, 50),
            'predicted_monthly_revenue': discounted_price * random.uniform(15, 80),
            'revenue_change_percentage': random.uniform(10, 40),
            'recommendation': f'Promotion recommandée de {promotion_pct:.1f}%'
        }
        results.append(result)
    
    return results

def calculate_risk_level(result):
    """Calcule le niveau de risque d'une promotion"""
    revenue_change = result.get('revenue_change_percentage', 0)
    promotion_pct = result.get('optimal_promotion_percentage', 0)
    stock = result.get('current_stock', 0)
    
    if revenue_change < -15 or stock < 5:
        return 'high'
    elif revenue_change < 5 or promotion_pct > 35:
        return 'medium'
    else:
        return 'low'

def calculate_statistics(promotions):
    """Calcule les statistiques globales"""
    if not promotions:
        return {}
    
    total_promotions = len(promotions)
    avg_promotion = sum(p['promotion_percentage'] for p in promotions) / total_promotions
    total_revenue_impact = sum(p['impact']['revenue_change_percentage'] for p in promotions)
    
    # Distribution par méthode
    ai_count = sum(1 for p in promotions if p['prediction_method'] == 'ai')
    classic_count = total_promotions - ai_count
    
    # Distribution par risque
    risk_distribution = {
        'low': sum(1 for p in promotions if p['risk_level'] == 'low'),
        'medium': sum(1 for p in promotions if p['risk_level'] == 'medium'),
        'high': sum(1 for p in promotions if p['risk_level'] == 'high')
    }
    
    return {
        'total_promotions': total_promotions,
        'average_promotion': round(avg_promotion, 2),
        'total_revenue_impact': round(total_revenue_impact, 2),
        'method_distribution': {
            'ai': ai_count,
            'classic': classic_count
        },
        'risk_distribution': risk_distribution
    }

@app.route('/api/promotions/history', methods=['GET'])
def get_promotions_history():
    """Récupère l'historique des promotions générées"""
    try:
        # Simulation d'historique (remplacez par votre logique de DB)
        history = [
            {
                'id': 1,
                'category_id': 1,
                'generated_at': '2025-07-20T10:30:00',
                'promotions_count': 5,
                'avg_promotion_percentage': 22.5
            },
            {
                'id': 2,
                'category_id': 2,
                'generated_at': '2025-07-19T15:45:00',
                'promotions_count': 8,
                'avg_promotion_percentage': 18.7
            }
        ]
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/model/status', methods=['GET'])
def get_model_status():
    """Récupère l'état du modèle IA"""
    try:
        status_info = {
            **model_status,
            'model_name': 'SmartPromo AI',
            'version': '1.0.0',
            'accuracy': 0.85 if model_status['trained'] else 0.0,
            'last_updated': model_status.get('last_update'),
            'features_count': 8,
            'model_ready': model_status['initialized'] and model_status['trained']
        }
        
        return jsonify({
            'success': True,
            'model_status': status_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/model/retrain', methods=['POST'])
def retrain_model():
    """Réentraîne le modèle IA"""
    try:
        data = request.get_json() or {}
        force_retrain = data.get('force', False)
        
        if not ai_model:
            return jsonify({
                'success': False,
                'message': 'Modèle IA non disponible'
            }), 503
        
        logger.info("🔄 Début du réentraînement du modèle...")
        
        success = ai_model.train_models(use_simulation=not force_retrain)
        
        if success:
            model_status['trained'] = True
            model_status['last_update'] = datetime.now().isoformat()
            model_status['last_error'] = None
            
            return jsonify({
                'success': True,
                'message': 'Modèle réentraîné avec succès',
                'retrained_at': model_status['last_update']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Échec du réentraînement'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur lors du réentraînement: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404"""
    return jsonify({
        'success': False,
        'message': 'Endpoint non trouvé'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    return jsonify({
        'success': False,
        'message': 'Erreur interne du serveur'
    }), 500

@app.route('/api/promotions/save', methods=['POST'])
def save_promotions():
    """Sauvegarde les promotions générées par l'IA dans la base de données"""
    try:
        data = request.get_json()
        
        if not data or 'promotions' not in data:
            return jsonify({
                'success': False,
                'message': 'Aucune promotion fournie'
            }), 400
        
        promotions = data['promotions']
        
        import pyodbc
        
        if not CONNECTION_STRING:
            logger.warning("⚠️ Aucune connexion DB disponible pour la sauvegarde")
            return jsonify({
                'success': False,
                'message': 'Base de données non disponible'
            }), 503
        
        logger.info(f"💾 Sauvegarde de {len(promotions)} promotions dans la base de données...")
        
        # Connexion à la base de données
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        saved_promotions = []
        
        for promo in promotions:
            try:
                # Récupération des vraies données des promotions IA
                current_price = promo.get('current_price', 0)
                promotional_price = promo.get('promotional_price', 0)
                promotion_percentage = promo.get('promotion_percentage', 0)
                article_id = promo.get('article_id', 0)
                
                # Conversion de article_id en CodeArticle format
                code_article = f"ART{article_id:06d}"  # Format: ART000001
                
                # Extraction des données du modèle IA pour les colonnes enrichies
                impact_data = promo.get('impact', {})
                scores_data = promo.get('scores', {})
                
                # Calculs pour les colonnes du modèle IA
                expected_revenue_impact = impact_data.get('revenue_change_percentage', 0) / 100.0
                expected_volume_impact = impact_data.get('volume_change_percentage', 0) / 100.0
                prediction_confidence = scores_data.get('final_score', 0.85)
                seasonal_adjustment = scores_data.get('sales_score', 0) * 0.1  # Ajustement saisonnier basé sur les ventes
                temporal_adjustment = scores_data.get('elasticity_score', 0) * 0.1  # Ajustement temporel basé sur l'élasticité
                
                # Insertion avec TOUTES les colonnes disponibles dans la DB
                insert_query = """
                INSERT INTO Promotions 
                (CodeArticle, Prix_Vente_TND_Avant, Prix_Vente_TND_Apres, TauxReduction, 
                 DateDebut, DateFin, IsAccepted, DateCreation, PredictionConfidence, 
                 ExpectedRevenueImpact, ExpectedVolumeImpact, SeasonalAdjustment, 
                 TemporalAdjustment, ReminderEmailSent)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_query, 
                    code_article,                    # CodeArticle
                    float(current_price),           # Prix_Vente_TND_Avant
                    float(promotional_price),       # Prix_Vente_TND_Apres
                    float(promotion_percentage),    # TauxReduction
                    data.get('start_date'),         # DateDebut
                    data.get('end_date'),           # DateFin
                    0,                              # IsAccepted (False par défaut)
                    # DateCreation est géré par GETDATE() dans la requête SQL
                    float(prediction_confidence),   # PredictionConfidence
                    float(expected_revenue_impact), # ExpectedRevenueImpact
                    float(expected_volume_impact),  # ExpectedVolumeImpact
                    float(seasonal_adjustment),     # SeasonalAdjustment
                    float(temporal_adjustment),     # TemporalAdjustment
                    0                               # ReminderEmailSent (False par défaut)
                )
                
                # Récupération de l'ID de la promotion créée
                cursor.execute("SELECT @@IDENTITY")
                promotion_id = cursor.fetchone()[0]
                
                saved_promotions.append({
                    'id': promotion_id,
                    'code_article': code_article,
                    'article_id': article_id,
                    'article_name': promo.get('article_name', ''),
                    'prix_avant': current_price,
                    'prix_apres': promotional_price,
                    'taux_reduction': promotion_percentage,
                    'prediction_confidence': prediction_confidence,
                    'expected_revenue_impact': expected_revenue_impact,
                    'expected_volume_impact': expected_volume_impact,
                    'seasonal_adjustment': seasonal_adjustment,
                    'temporal_adjustment': temporal_adjustment,
                    'risk_level': promo.get('risk_level', 'medium'),
                    'recommendation': promo.get('recommendation', ''),
                    'status': 'En attente d\'approbation',
                    'date_debut': data.get('start_date'),
                    'date_fin': data.get('end_date')
                })
                
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de la promotion {promo.get('article_id')}: {e}")
                continue
        
        # Validation des changements
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ {len(saved_promotions)} promotions sauvegardées avec succès")
        
        return jsonify({
            'success': True,
            'message': f'{len(saved_promotions)} promotions sauvegardées avec succès dans la table Promotions',
            'promotions': saved_promotions,
            'count': len(saved_promotions),
            'table_structure': 'Colonnes utilisées: CodeArticle, Prix_Vente_TND_Avant, Prix_Vente_TND_Apres, TauxReduction, DateDebut, DateFin, IsAccepted, PredictionConfidence, ExpectedRevenueImpact, ExpectedVolumeImpact, SeasonalAdjustment, TemporalAdjustment, ReminderEmailSent',
            'model_integration': {
                'ai_predictions': True,
                'confidence_scores': True,
                'impact_analysis': True,
                'seasonal_temporal_adjustments': True
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des promotions: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la sauvegarde: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Démarrage de SmartPromo AI Flask API...")
    print("📡 API disponible sur: http://localhost:5000")
    print("🔗 Health check: http://localhost:5000/api/health")
    print("⚡ Endpoints disponibles:")
    print("   GET  /api/health")
    print("   GET  /api/categories")
    print("   POST /api/promotions/generate")
    print("   POST /api/promotions/save")
    print("   GET  /api/promotions/history")
    print("   GET  /api/model/status")
    print("   POST /api/model/retrain")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
