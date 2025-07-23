"""
SmartPromo AI Model - Modèle d'Intelligence Artificielle pour le Calcul Optimal des Promotions
=========================================================================================

Ce modèle calcule le pourcentage de promotion optimal pour chaque article en se basant sur :
- Rotation des stocks
- Élasticité prix/demande
- Historique des ventes
- Historique des promotions

Et prédit l'impact sur le revenu et le volume des ventes.
"""

import pyodbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import logging
from typing import Dict, List, Tuple, Optional
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os

warnings.filterwarnings('ignore')

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartPromoAIModel:
    """
    Modèle d'IA pour calculer les pourcentages de promotion optimaux
    """
    
    def __init__(self, connection_string: str):
        """
        Initialise le modèle avec la chaîne de connexion à la base de données
        
        Args:
            connection_string (str): Chaîne de connexion SQL Server
        """
        self.connection_string = connection_string
        self.connection = None
        
        # Poids pour la formule de calcul (pondération selon l'importance)
        self.weights = {
            'stock_rotation': 0.35,      # 35% - Rotation des stocks
            'price_elasticity': 0.25,    # 25% - Élasticité prix/demande
            'sales_history': 0.25,       # 25% - Historique des ventes
            'promotion_history': 0.15    # 15% - Historique des promotions
        }
        
        # Paramètres de seuils
        self.thresholds = {
            'min_promotion': 5,     # Promotion minimale de 5%
            'max_promotion': 50,    # Promotion maximale de 50%
            'stock_critical': 10,   # Seuil critique de stock
            'stock_excess': 100     # Seuil de surstock
        }
        
        # Modèles d'IA
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression()
        }
        self.best_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_metrics = {}
        
    def connect_database(self) -> bool:
        """
        Établit la connexion à la base de données avec gestion robuste des pilotes ODBC
        
        Returns:
            bool: True si connexion réussie, False sinon
        """
        try:
            # Liste des chaînes de connexion à essayer (dans l'ordre de préférence)
            connection_strings = [
                # Pilote ODBC Driver 17 (fonctionne selon le diagnostic)
                "DRIVER={ODBC Driver 17 for SQL Server};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;",
                
                # Pilote SQL Server standard (fonctionne aussi)
                "DRIVER={SQL Server};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;",
                
                # Pilote ODBC Driver 18 avec certificat
                "DRIVER={ODBC Driver 18 for SQL Server};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;TrustServerCertificate=yes;",
                
                # Chaîne originale
                self.connection_string,
                
                # SQL Server Native Client
                "DRIVER={SQL Server Native Client 11.0};Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=yes;"
            ]
            
            for i, conn_str in enumerate(connection_strings, 1):
                try:
                    logger.info(f"Tentative de connexion {i}/5...")
                    self.connection = pyodbc.connect(conn_str, timeout=10)
                    logger.info("✅ Connexion à la base de données établie avec succès")
                    return True
                except Exception as conn_error:
                    logger.warning(f"❌ Tentative {i} échouée: {str(conn_error)[:100]}...")
                    continue
            
            logger.error("🚫 Toutes les tentatives de connexion ont échoué")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur générale de connexion à la base de données: {e}")
            return False
    
    def disconnect_database(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            logger.info("Connexion à la base de données fermée")
    
    def extract_articles_by_category(self, category_id: int) -> pd.DataFrame:
        """
        Extrait les articles d'une catégorie spécifique
        
        Args:
            category_id (int): ID de la catégorie
            
        Returns:
            pd.DataFrame: DataFrame contenant les articles
        """
        query = """
        SELECT 
            a.Id as ArticleId,
            a.Libelle as ArticleName,
            a.Prix_Vente_TND as Price,
            ISNULL(s.QuantitePhysique, 0) as CurrentStock,
            ISNULL(s.StockMin, 5) as MinStockThreshold,
            a.IdCategorie as CategoryId,
            c.Nom as CategoryName,
            a.CodeArticle
        FROM Articles a
        LEFT JOIN Categories c ON a.IdCategorie = c.IdCategorie
        LEFT JOIN Stocks s ON a.Id = s.ArticleId
        WHERE a.IdCategorie = ?
        AND a.Prix_Vente_TND > 0
        """
        
        try:
            df = pd.read_sql(query, self.connection, params=[str(category_id)])
            logger.info(f"Extraction de {len(df)} articles pour la catégorie {category_id}")
            return df
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des articles: {e}")
            return pd.DataFrame()
    
    def get_sales_history(self, article_id: int, days: int = 90) -> pd.DataFrame:
        """
        Récupère l'historique des ventes d'un article
        
        Args:
            article_id (int): ID de l'article
            days (int): Nombre de jours d'historique
            
        Returns:
            pd.DataFrame: Historique des ventes
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            v.Date as SaleDate,
            v.QuantiteFacturee as QuantitySold,
            v.Prix_Vente_TND as SalePrice,
            s.ArticleId,
            s.QuantitePhysique as CurrentStock,
            ISNULL(s.QuantitePhysique, 0) as QuantityInjected
        FROM Ventes v
        JOIN Stocks s ON v.StockId = s.Id
        WHERE s.ArticleId = ?
        AND v.Date >= ?
        AND v.Date <= ?
        ORDER BY v.Date
        """
        
        try:
            df = pd.read_sql(query, self.connection, 
                           params=[article_id, start_date, end_date])
            return df
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique des ventes: {e}")
            return pd.DataFrame()
    
    def get_promotion_history(self, article_id: int, days: int = 180) -> pd.DataFrame:
        """
        Récupère l'historique des promotions d'un article avec prix avant/après
        
        Args:
            article_id (int): ID de l'article
            days (int): Nombre de jours d'historique
            
        Returns:
            pd.DataFrame: Historique des promotions avec prix
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            p.DateDebut as StartDate,
            p.DateFin as EndDate,
            p.TauxReduction as DiscountPercentage,
            p.CodeArticle,
            a.Id as ArticleId,
            a.Prix_Vente_TND as PriceBeforePromo,
            (a.Prix_Vente_TND * (1 - p.TauxReduction / 100.0)) as PriceAfterPromo,
            -- Calcul des ventes pendant cette promotion
            (SELECT SUM(v.QuantiteFacturee)
             FROM Ventes v
             JOIN Stocks s ON v.StockId = s.Id
             WHERE s.ArticleId = a.Id
             AND v.Date BETWEEN p.DateDebut AND p.DateFin
            ) as SalesDuringPromo
        FROM Promotions p
        JOIN Articles a ON p.CodeArticle = a.CodeArticle
        WHERE a.Id = ?
        AND p.DateDebut >= ?
        AND p.DateFin <= ?
        ORDER BY p.DateDebut
        """
        
        try:
            df = pd.read_sql(query, self.connection, 
                           params=[article_id, start_date, end_date])
            return df
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique des promotions: {e}")
            return pd.DataFrame()
    
    def calculate_stock_rotation_score(self, article_row: pd.Series, sales_history: pd.DataFrame) -> float:
        """
        Calcule le score de rotation des stocks selon la formule correcte:
        Rotation = Quantité vendue / Quantité injectée
        
        Args:
            article_row (pd.Series): Données de l'article
            sales_history (pd.DataFrame): Historique des ventes
            
        Returns:
            float: Score de rotation (0-1)
        """
        current_stock = article_row['CurrentStock']
        min_threshold = article_row['MinStockThreshold']
        
        if sales_history.empty:
            return 0.5  # Score neutre si pas d'historique
        
        # Calcul de la rotation correcte : Quantité vendue / Quantité injectée
        total_sales = sales_history['QuantitySold'].sum()
        total_injected = sales_history['QuantityInjected'].sum()
        
        if total_injected == 0:
            return 0.5  # Score neutre si pas d'injection
        
        # Calcul du taux de rotation réel
        rotation_rate = total_sales / total_injected
        
        if current_stock == 0:
            return 1.0  # Stock critique - promotion maximale
        
        # Normalisation du score basé sur la rotation
        if current_stock <= min_threshold:
            # Stock faible mais on regarde la rotation
            return min(0.8, rotation_rate)  # Max 0.8 pour stock faible
        elif current_stock >= self.thresholds['stock_excess']:
            return 0.9  # Surstock - promotion élevée
        else:
            # Score proportionnel à la rotation
            # Une rotation élevée (>1) indique un bon écoulement
            # Une rotation faible (<0.5) indique des difficultés de vente
            if rotation_rate > 1.0:
                return 0.3  # Bon écoulement - promotion faible
            elif rotation_rate > 0.7:
                return 0.5  # Écoulement moyen
            elif rotation_rate > 0.4:
                return 0.7  # Écoulement lent - promotion modérée
            else:
                return 0.9  # Écoulement très lent - promotion forte
    
    def calculate_price_elasticity_score(self, article_row: pd.Series, sales_history: pd.DataFrame, promotion_history: pd.DataFrame = None) -> float:
        """
        Calcule le score d'élasticité prix/demande en utilisant les prix avant et après promotion
        
        Args:
            article_row (pd.Series): Données de l'article
            sales_history (pd.DataFrame): Historique des ventes
            promotion_history (pd.DataFrame): Historique des promotions avec prix avant/après
            
        Returns:
            float: Score d'élasticité (0-1)
        """
        # Si on a l'historique des promotions avec les prix, on l'utilise
        if promotion_history is not None and not promotion_history.empty and len(promotion_history) >= 2:
            try:
                # Calcul de l'élasticité basée sur les promotions passées
                elasticity_scores = []
                
                for _, promo in promotion_history.iterrows():
                    price_before = promo['PriceBeforePromo']
                    price_after = promo['PriceAfterPromo']
                    sales_during = promo.get('SalesDuringPromo', 0)
                    
                    if price_before > 0 and price_after > 0 and sales_during > 0:
                        # Calcul du changement de prix en pourcentage
                        price_change_pct = (price_after - price_before) / price_before
                        
                        # Estimation des ventes avant promotion (basée sur historique)
                        if not sales_history.empty:
                            avg_sales_before = sales_history['QuantitySold'].mean()
                        else:
                            avg_sales_before = sales_during * 0.7  # Estimation conservatrice
                        
                        if avg_sales_before > 0:
                            # Calcul du changement de quantité en pourcentage
                            quantity_change_pct = (sales_during - avg_sales_before) / avg_sales_before
                            
                            # Calcul de l'élasticité: variation demande / variation prix
                            if price_change_pct != 0:
                                elasticity = abs(quantity_change_pct / price_change_pct)
                                elasticity_scores.append(elasticity)
                
                if elasticity_scores:
                    # Moyenne des élasticités calculées
                    avg_elasticity = np.mean(elasticity_scores)
                    
                    # Normalisation du score d'élasticité
                    # Élasticité élevée (> 2) = très sensible au prix = score élevé pour promotion
                    # Élasticité faible (< 0.5) = peu sensible au prix = score faible pour promotion
                    if avg_elasticity > 2.0:
                        return 0.9  # Très élastique - promotion très efficace
                    elif avg_elasticity > 1.5:
                        return 0.8  # Assez élastique - promotion efficace
                    elif avg_elasticity > 1.0:
                        return 0.6  # Moyennement élastique
                    elif avg_elasticity > 0.5:
                        return 0.4  # Peu élastique
                    else:
                        return 0.2  # Très peu élastique - promotion peu efficace
                        
            except Exception as e:
                logger.warning(f"Erreur dans le calcul d'élasticité avec promotions: {e}")
        
        # Méthode de fallback basée sur l'historique des ventes (méthode originale)
        if sales_history.empty or len(sales_history) < 10:
            return 0.5  # Score neutre si données insuffisantes
        
        current_price = article_row['Price']
        
        # Calcul de la corrélation prix/quantité dans l'historique des ventes
        price_changes = sales_history['SalePrice'].pct_change().dropna()
        quantity_changes = sales_history['QuantitySold'].pct_change().dropna()
        
        if len(price_changes) < 5 or len(quantity_changes) < 5:
            return 0.5
        
        # Élasticité = variation relative de la demande / variation relative du prix
        correlation = np.corrcoef(price_changes, quantity_changes)[0, 1]
        
        if np.isnan(correlation):
            return 0.5
        
        # Conversion en score (plus la corrélation est négative, plus l'élasticité est forte)
        elasticity_score = min(0.9, max(0.1, (1 - correlation) / 2))
        
        return elasticity_score
    
    def calculate_sales_history_score(self, sales_history: pd.DataFrame) -> float:
        """
        Calcule le score basé sur l'historique des ventes
        
        Args:
            sales_history (pd.DataFrame): Historique des ventes
            
        Returns:
            float: Score des ventes (0-1)
        """
        if sales_history.empty:
            return 0.3  # Score faible si pas d'historique
        
        # Tendance des ventes (croissante/décroissante)
        sales_by_week = sales_history.groupby(
            sales_history['SaleDate'].dt.isocalendar().week
        )['QuantitySold'].sum()
        
        if len(sales_by_week) < 2:
            return 0.5
        
        # Calcul de la tendance
        trend = np.polyfit(range(len(sales_by_week)), sales_by_week.values, 1)[0]
        
        # Score basé sur la tendance
        if trend > 0:  # Tendance croissante - promotion modérée
            return 0.3
        elif trend < -0.5:  # Tendance très décroissante - promotion forte
            return 0.8
        else:  # Tendance stable ou légèrement décroissante
            return 0.6
    
    def calculate_promotion_history_score(self, promotion_history: pd.DataFrame) -> float:
        """
        Calcule le score basé sur l'historique des promotions
        
        Args:
            promotion_history (pd.DataFrame): Historique des promotions
            
        Returns:
            float: Score des promotions (0-1)
        """
        if promotion_history.empty:
            return 0.7  # Score élevé si jamais promu
        
        # Fréquence des promotions
        recent_promotions = promotion_history[
            promotion_history['EndDate'] >= datetime.now() - timedelta(days=60)
        ]
        
        if len(recent_promotions) > 2:
            return 0.2  # Trop de promotions récentes - réduire
        elif len(recent_promotions) == 0:
            return 0.8  # Pas de promotion récente - augmenter
        else:
            return 0.5  # Équilibré
    
    def extract_training_data(self) -> pd.DataFrame:
        """
        Extrait les données d'entraînement à partir de l'historique des promotions et ventes
        
        Returns:
            pd.DataFrame: Données d'entraînement avec features et target
        """
        query = """
        SELECT 
            a.Id as ArticleId,
            a.Prix_Vente_TND as Price,
            a.IdCategorie as CategoryId,
            ISNULL(s.QuantitePhysique, 0) as CurrentStock,
            ISNULL(s.StockMin, 5) as MinStockThreshold,
            ISNULL(s.QuantitePhysique, 0) as QuantityInjected,
            p.TauxReduction as PromotionPercentage,
            p.DateDebut,
            p.DateFin,
            -- Calcul des ventes avant promotion (30 jours avant)
            (SELECT SUM(v1.QuantiteFacturee) 
             FROM Ventes v1 
             JOIN Stocks s1 ON v1.StockId = s1.Id 
             WHERE s1.ArticleId = a.Id 
             AND v1.Date BETWEEN DATEADD(day, -60, p.DateDebut) AND DATEADD(day, -30, p.DateDebut)
            ) as SalesBeforePromo,
            -- Calcul des ventes pendant promotion
            (SELECT SUM(v2.QuantiteFacturee) 
             FROM Ventes v2 
             JOIN Stocks s2 ON v2.StockId = s2.Id 
             WHERE s2.ArticleId = a.Id 
             AND v2.Date BETWEEN p.DateDebut AND p.DateFin
            ) as SalesDuringPromo,
            -- Calcul des revenus avant promotion
            (SELECT SUM(v3.QuantiteFacturee * v3.Prix_Vente_TND) 
             FROM Ventes v3 
             JOIN Stocks s3 ON v3.StockId = s3.Id 
             WHERE s3.ArticleId = a.Id 
             AND v3.Date BETWEEN DATEADD(day, -60, p.DateDebut) AND DATEADD(day, -30, p.DateDebut)
            ) as RevenueBeforePromo,
            -- Calcul des revenus pendant promotion
            (SELECT SUM(v4.QuantiteFacturee * v4.Prix_Vente_TND) 
             FROM Ventes v4 
             JOIN Stocks s4 ON v4.StockId = s4.Id 
             WHERE s4.ArticleId = a.Id 
             AND v4.Date BETWEEN p.DateDebut AND p.DateFin
            ) as RevenueDuringPromo
        FROM Articles a
        LEFT JOIN Stocks s ON a.Id = s.ArticleId
        JOIN Promotions p ON a.CodeArticle = p.CodeArticle
        WHERE p.DateFin < GETDATE()
        AND a.Prix_Vente_TND > 0
        """
        
        try:
            df = pd.read_sql(query, self.connection)
            
            # Nettoyage et calcul des features
            df = df.dropna(subset=['SalesBeforePromo', 'SalesDuringPromo'])
            
            # Calcul de la rotation
            df['RotationRate'] = df['SalesBeforePromo'] / df['QuantityInjected'].replace(0, 1)
            
            # Calcul de l'efficacité de la promotion (target)
            df['PromotionEffectiveness'] = (df['SalesDuringPromo'] / (df['SalesBeforePromo'].replace(0, 1))) - 1
            
            # Calcul du changement de revenus
            df['RevenueChange'] = (df['RevenueDuringPromo'] / df['RevenueBeforePromo'].replace(0, 1)) - 1
            
            # Seuil de stock
            df['StockLevel'] = df['CurrentStock'] / df['MinStockThreshold'].replace(0, 1)
            
            # Niveau de prix (comparé à la moyenne de la catégorie)
            avg_price_by_category = df.groupby('CategoryId')['Price'].mean()
            df['PriceLevel'] = df.apply(lambda row: row['Price'] / avg_price_by_category[row['CategoryId']], axis=1)
            
            logger.info(f"Données d'entraînement extraites: {len(df)} échantillons")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des données d'entraînement: {e}")
            return pd.DataFrame()
    
    def generate_simulated_training_data(self, n_samples: int = 200) -> pd.DataFrame:
        """
        Génère des données d'entraînement simulées pour l'IA
        
        Args:
            n_samples (int): Nombre d'échantillons à générer
            
        Returns:
            pd.DataFrame: Données simulées pour l'entraînement
        """
        np.random.seed(42)  # Pour la reproductibilité
        
        # Simulation de différents types d'articles et promotions
        data = {
            'ArticleId': range(1, n_samples + 1),
            'Price': np.random.uniform(20, 300, n_samples),
            'CategoryId': np.random.choice([1, 2, 3, 4, 5], n_samples),
            'CurrentStock': np.random.randint(0, 150, n_samples),
            'MinStockThreshold': np.random.randint(5, 25, n_samples),
            'QuantityInjected': np.random.randint(50, 800, n_samples),
            'PromotionPercentage': np.random.uniform(5, 45, n_samples),
        }
        
        # Calculs des ventes basés sur des facteurs réalistes
        base_sales = np.random.randint(10, 80, n_samples)
        promotion_effect = 1 + (data['PromotionPercentage'] / 100) * np.random.uniform(1.5, 3.0, n_samples)
        
        # Ventes avant promotion (baseline)
        data['SalesBeforePromo'] = base_sales
        
        # Ventes pendant promotion (augmentées selon l'effet promotion)
        data['SalesDuringPromo'] = np.round(base_sales * promotion_effect).astype(int)
        
        # Simulation des revenus
        base_revenue = data['Price'] * np.array(data['SalesBeforePromo'])
        promo_price = np.array(data['Price']) * (1 - np.array(data['PromotionPercentage']) / 100)
        promo_revenue = promo_price * data['SalesDuringPromo']
        
        data['RevenueBeforePromo'] = base_revenue
        data['RevenueDuringPromo'] = promo_revenue
        
        df = pd.DataFrame(data)
        
        # Calcul des features dérivées (comme dans la méthode réelle)
        df['RotationRate'] = df['SalesBeforePromo'] / df['QuantityInjected'].replace(0, 1)
        df['PromotionEffectiveness'] = (df['SalesDuringPromo'] / df['SalesBeforePromo'].replace(0, 1)) - 1
        df['RevenueChange'] = (df['RevenueDuringPromo'] / df['RevenueBeforePromo'].replace(0, 1)) - 1
        df['StockLevel'] = df['CurrentStock'] / df['MinStockThreshold'].replace(0, 1)
        
        # Niveau de prix par catégorie
        avg_price_by_category = df.groupby('CategoryId')['Price'].mean()
        df['PriceLevel'] = df.apply(lambda row: row['Price'] / avg_price_by_category[row['CategoryId']], axis=1)
        
        logger.info(f"✅ Données simulées générées: {len(df)} échantillons")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prépare les features et target pour l'entraînement
        
        Args:
            df (pd.DataFrame): Données brutes
            
        Returns:
            Tuple[pd.DataFrame, pd.Series]: Features (X) et target (y)
        """
        # Sélection des features
        feature_columns = [
            'Price', 'CurrentStock', 'MinStockThreshold', 'QuantityInjected',
            'RotationRate', 'StockLevel', 'PriceLevel', 'CategoryId'
        ]
        
        X = df[feature_columns].copy()
        
        # Target: combinaison d'efficacité ventes et revenus
        # Plus le score est élevé, plus la promotion devrait être importante
        y = (df['PromotionEffectiveness'] * 0.6 + df['RevenueChange'] * 0.4) * 100
        
        # Nettoyage des valeurs aberrantes
        X = X.fillna(X.median())
        y = y.fillna(y.median())
        
        # Limitation des valeurs extrêmes du target
        y = np.clip(y, -50, 200)  # Entre -50% et +200% d'efficacité
        
        return X, y
    
    def train_models(self, use_simulation: bool = False) -> bool:
        """
        Entraîne les modèles d'IA avec les données historiques ou simulées
        
        Args:
            use_simulation (bool): Utiliser des données simulées si True
        
        Returns:
            bool: True si l'entraînement a réussi
        """
        logger.info("🤖 Début de l'entraînement des modèles d'IA...")
        
        training_data = pd.DataFrame()
        
        if use_simulation:
            logger.info("📊 Utilisation de données simulées pour l'entraînement...")
            training_data = self.generate_simulated_training_data()
        else:
            if not self.connect_database():
                logger.warning("❌ Connexion échouée, basculement vers données simulées...")
                training_data = self.generate_simulated_training_data()
                use_simulation = True
            else:
                try:
                    # Extraction des données d'entraînement réelles
                    training_data = self.extract_training_data()
                finally:
                    self.disconnect_database()
        
        if training_data.empty or len(training_data) < 50:
            if not use_simulation:
                logger.warning("Données réelles insuffisantes, génération de données simulées...")
                training_data = self.generate_simulated_training_data()
            else:
                logger.error("Impossible de générer suffisamment de données d'entraînement")
                return False
        
        try:
            # Préparation des features
            X, y = self.prepare_features(training_data)
            
            # Division train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Normalisation
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            best_score = -np.inf
            
            # Entraînement de chaque modèle
            for name, model in self.models.items():
                logger.info(f"Entraînement du modèle: {name}")
                
                # Entraînement
                if name == 'linear_regression':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                # Évaluation
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                
                # Stockage des métriques
                self.model_metrics[name] = {
                    'mse': mse,
                    'r2': r2,
                    'mae': mae,
                    'rmse': np.sqrt(mse)
                }
                
                logger.info(f"  {name}: R² = {r2:.3f}, RMSE = {np.sqrt(mse):.3f}")
                
                # Sélection du meilleur modèle
                if r2 > best_score:
                    best_score = r2
                    self.best_model = model
                    self.best_model_name = name
            
            self.is_trained = True
            data_source = "simulées" if use_simulation or not self.connection else "réelles"
            logger.info(f"✅ Entraînement terminé avec données {data_source}. Meilleur modèle: {self.best_model_name} (R² = {best_score:.3f})")
            
            # Sauvegarde du modèle
            self.save_model()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'entraînement: {e}")
            return False
    
    def save_model(self):
        """Sauvegarde le modèle entraîné"""
        try:
            model_dir = "trained_models"
            os.makedirs(model_dir, exist_ok=True)
            
            # Sauvegarde du meilleur modèle
            joblib.dump(self.best_model, f"{model_dir}/best_model.pkl")
            joblib.dump(self.scaler, f"{model_dir}/scaler.pkl")
            
            # Sauvegarde des métriques
            with open(f"{model_dir}/metrics.json", 'w') as f:
                json.dump(self.model_metrics, f, indent=2)
                
            logger.info(f"📁 Modèle sauvegardé dans {model_dir}/")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def load_model(self) -> bool:
        """Charge un modèle pré-entraîné"""
        try:
            model_dir = "trained_models"
            
            if not os.path.exists(f"{model_dir}/best_model.pkl"):
                return False
            
            self.best_model = joblib.load(f"{model_dir}/best_model.pkl")
            self.scaler = joblib.load(f"{model_dir}/scaler.pkl")
            
            with open(f"{model_dir}/metrics.json", 'r') as f:
                self.model_metrics = json.load(f)
            
            self.is_trained = True
            logger.info("✅ Modèle pré-entraîné chargé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            return False
    
    def calculate_optimal_promotion_percentage(self, article_row: pd.Series) -> Dict:
        """
        Calcule le pourcentage de promotion optimal pour un article en utilisant l'IA
        
        Args:
            article_row (pd.Series): Données de l'article
            
        Returns:
            Dict: Résultats du calcul
        """
        article_id = article_row['ArticleId']
        
        # Récupération des historiques
        sales_history = self.get_sales_history(article_id)
        promotion_history = self.get_promotion_history(article_id)
        
        # Calcul des scores individuels (pour compatibilité et transparence)
        stock_score = self.calculate_stock_rotation_score(article_row, sales_history)
        elasticity_score = self.calculate_price_elasticity_score(article_row, sales_history, promotion_history)
        sales_score = self.calculate_sales_history_score(sales_history)
        promotion_score = self.calculate_promotion_history_score(promotion_history)
        
        # Calcul du score final pondéré (méthode classique)
        final_score = (
            stock_score * self.weights['stock_rotation'] +
            elasticity_score * self.weights['price_elasticity'] +
            sales_score * self.weights['sales_history'] +
            promotion_score * self.weights['promotion_history']
        )
        
        # Promotion par méthode classique
        classic_promotion_percentage = (
            self.thresholds['min_promotion'] + 
            (self.thresholds['max_promotion'] - self.thresholds['min_promotion']) * final_score
        )
        
        # Prédiction par IA si le modèle est entraîné
        ai_promotion_percentage = classic_promotion_percentage
        prediction_method = "classic"
        
        if self.is_trained and self.best_model is not None:
            try:
                # Préparation des features pour l'IA
                total_injected = sales_history['QuantityInjected'].sum() if not sales_history.empty else article_row['CurrentStock']
                rotation_rate = sales_history['QuantitySold'].sum() / total_injected if total_injected > 0 else 0
                stock_level = article_row['CurrentStock'] / article_row['MinStockThreshold'] if article_row['MinStockThreshold'] > 0 else 1
                
                # Calcul du prix relatif (approximation)
                price_level = 1.0  # Valeur par défaut si pas de données de catégorie
                
                features = pd.DataFrame({
                    'Price': [article_row['Price']],
                    'CurrentStock': [article_row['CurrentStock']],
                    'MinStockThreshold': [article_row['MinStockThreshold']],
                    'QuantityInjected': [total_injected],
                    'RotationRate': [rotation_rate],
                    'StockLevel': [stock_level],
                    'PriceLevel': [price_level],
                    'CategoryId': [article_row.get('CategoryId', 1)]
                })
                
                # Prédiction
                if hasattr(self, 'best_model_name') and self.best_model_name == 'linear_regression':
                    features_scaled = self.scaler.transform(features)
                    ai_effectiveness = self.best_model.predict(features_scaled)[0]
                else:
                    ai_effectiveness = self.best_model.predict(features)[0]
                
                # Conversion de l'efficacité prédite en pourcentage de promotion
                # Plus l'efficacité prédite est faible, plus la promotion doit être élevée
                if ai_effectiveness < 0:  # Efficacité négative = besoin de promotion
                    ai_promotion_percentage = min(self.thresholds['max_promotion'], 
                                                abs(ai_effectiveness) * 0.5 + self.thresholds['min_promotion'])
                else:  # Efficacité positive = promotion modérée
                    ai_promotion_percentage = max(self.thresholds['min_promotion'],
                                                self.thresholds['max_promotion'] - (ai_effectiveness * 0.3))
                
                prediction_method = "ai"
                
            except Exception as e:
                logger.warning(f"Erreur lors de la prédiction IA: {e}, utilisation méthode classique")
                ai_promotion_percentage = classic_promotion_percentage
                prediction_method = "classic_fallback"
        
        # Arrondi à l'entier le plus proche
        final_promotion_percentage = round(ai_promotion_percentage)
        
        # Création des données de base pour l'impact
        basic_result = {
            'article_id': article_id,
            'article_name': article_row['ArticleName'],
            'current_price': article_row['Price'],
            'current_stock': article_row['CurrentStock'],
            'stock_score': round(stock_score, 3),
            'elasticity_score': round(elasticity_score, 3),
            'sales_score': round(sales_score, 3),
            'promotion_score': round(promotion_score, 3),
            'final_score': round(final_score, 3),
            'classic_promotion_percentage': round(classic_promotion_percentage),
            'optimal_promotion_percentage': final_promotion_percentage,
            'prediction_method': prediction_method,
            'discounted_price': round(article_row['Price'] * (1 - final_promotion_percentage/100), 2)
        }
        
        # Calcul de l'impact prévu
        impact_data = self.predict_impact(basic_result, sales_history)
        
        # Fusion des résultats
        complete_result = {**basic_result, **impact_data}
        
        return complete_result
    
    def predict_impact(self, article_data: Dict, sales_history: pd.DataFrame) -> Dict:
        """
        Prédit l'impact de la promotion sur le revenu et le volume des ventes
        
        Args:
            article_data (Dict): Données de l'article avec promotion
            sales_history (pd.DataFrame): Historique des ventes
            
        Returns:
            Dict: Prédictions d'impact
        """
        promotion_percentage = article_data['optimal_promotion_percentage']
        current_price = article_data['current_price']
        discounted_price = article_data['discounted_price']
        
        # Calcul des métriques de base
        if sales_history.empty:
            avg_daily_sales = 1
            avg_daily_revenue = current_price
        else:
            avg_daily_sales = sales_history['QuantitySold'].mean()
            avg_daily_revenue = (sales_history['QuantitySold'] * sales_history['SalePrice']).mean()
        
        # Estimation de l'augmentation des ventes basée sur l'élasticité
        # Plus la promotion est importante, plus l'augmentation est significative
        sales_increase_factor = 1 + (promotion_percentage / 100) * 2  # Facteur d'augmentation
        
        predicted_daily_sales = avg_daily_sales * sales_increase_factor
        predicted_daily_revenue = predicted_daily_sales * discounted_price
        
        # Calcul de l'impact sur 30 jours
        monthly_current_revenue = avg_daily_revenue * 30
        monthly_predicted_revenue = predicted_daily_revenue * 30
        monthly_current_sales = avg_daily_sales * 30
        monthly_predicted_sales = predicted_daily_sales * 30
        
        revenue_change = monthly_predicted_revenue - monthly_current_revenue
        revenue_change_percentage = (revenue_change / monthly_current_revenue) * 100 if monthly_current_revenue > 0 else 0
        
        sales_change = monthly_predicted_sales - monthly_current_sales
        sales_change_percentage = (sales_change / monthly_current_sales) * 100 if monthly_current_sales > 0 else 0
        
        return {
            'current_monthly_sales_volume': round(monthly_current_sales, 2),
            'predicted_monthly_sales_volume': round(monthly_predicted_sales, 2),
            'sales_volume_change': round(sales_change, 2),
            'sales_volume_change_percentage': round(sales_change_percentage, 2),
            'current_monthly_revenue': round(monthly_current_revenue, 2),
            'predicted_monthly_revenue': round(monthly_predicted_revenue, 2),
            'revenue_change': round(revenue_change, 2),
            'revenue_change_percentage': round(revenue_change_percentage, 2),
            'recommendation': self.get_recommendation(article_data, revenue_change_percentage, sales_change_percentage)
        }
    
    def get_recommendation(self, article_data: Dict, revenue_change: float, sales_change: float) -> str:
        """
        Génère une recommandation basée sur les prédictions
        
        Args:
            article_data (Dict): Données de l'article
            revenue_change (float): Changement de revenu prédit
            sales_change (float): Changement de volume prédit
            
        Returns:
            str: Recommandation
        """
        stock = article_data['current_stock']
        promotion = article_data['optimal_promotion_percentage']
        
        if stock <= self.thresholds['stock_critical']:
            return f"⚠️ STOCK CRITIQUE: Éviter la promotion ({promotion}%) pour éviter la rupture de stock"
        elif stock >= self.thresholds['stock_excess']:
            return f"📈 SURSTOCK: Promotion recommandée ({promotion}%) pour écouler le stock"
        elif revenue_change > 0 and sales_change > 20:
            return f"✅ PROMOTION RENTABLE: Augmentation prévue du revenu ({revenue_change:.1f}%) et des ventes ({sales_change:.1f}%)"
        elif revenue_change < -10:
            return f"❌ RISQUE: La promotion pourrait réduire significativement le revenu ({revenue_change:.1f}%)"
        else:
            return f"⚖️ NEUTRE: Impact modéré prévu. Promotion de {promotion}% acceptable"
    
    def analyze_category(self, category_id: int) -> List[Dict]:
        """
        Analyse complète d'une catégorie d'articles
        
        Args:
            category_id (int): ID de la catégorie
            
        Returns:
            List[Dict]: Analyses complètes de tous les articles
        """
        if not self.connect_database():
            return []
        
        try:
            # Extraction des articles
            articles_df = self.extract_articles_by_category(category_id)
            
            if articles_df.empty:
                logger.warning(f"Aucun article trouvé pour la catégorie {category_id}")
                return []
            
            results = []
            
            for _, article_row in articles_df.iterrows():
                logger.info(f"Analyse de l'article: {article_row['ArticleName']}")
                
                # Calcul de la promotion optimale avec impact inclus
                complete_analysis = self.calculate_optimal_promotion_percentage(article_row)
                results.append(complete_analysis)
            
            logger.info(f"Analyse terminée pour {len(results)} articles")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la catégorie: {e}")
            return []
        finally:
            self.disconnect_database()
    
    def generate_summary_report(self, analysis_results: List[Dict]) -> str:
        """
        Génère un rapport de synthèse
        
        Args:
            analysis_results (List[Dict]): Résultats d'analyse
            
        Returns:
            str: Rapport de synthèse
        """
        if not analysis_results:
            return "Aucune donnée à analyser"
        
        df = pd.DataFrame(analysis_results)
        
        # Statistiques générales
        avg_promotion = df['optimal_promotion_percentage'].mean()
        total_potential_revenue_change = df['revenue_change'].sum()
        total_potential_sales_change = df['sales_volume_change'].sum()
        
        # Articles par catégorie de recommandation
        high_promotion = len(df[df['optimal_promotion_percentage'] > 30])
        medium_promotion = len(df[(df['optimal_promotion_percentage'] >= 15) & (df['optimal_promotion_percentage'] <= 30)])
        low_promotion = len(df[df['optimal_promotion_percentage'] < 15])
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                            RAPPORT DE SYNTHÈSE SMARTPROMO AI                     ║
║                              {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}                              ║
╚══════════════════════════════════════════════════════════════════════════════════╝

📊 STATISTIQUES GÉNÉRALES:
   • Nombre d'articles analysés: {len(analysis_results)}
   • Promotion moyenne recommandée: {avg_promotion:.1f}%
   • Impact total prévu sur le revenu: {total_potential_revenue_change:,.2f} DT
   • Impact total prévu sur les ventes: {total_potential_sales_change:,.0f} unités

📈 RÉPARTITION DES PROMOTIONS:
   • Promotions élevées (>30%): {high_promotion} articles
   • Promotions moyennes (15-30%): {medium_promotion} articles  
   • Promotions faibles (<15%): {low_promotion} articles

🎯 TOP 5 DES OPPORTUNITÉS:
"""
        
        # Top 5 des meilleures opportunités
        top_opportunities = df.nlargest(5, 'revenue_change_percentage')
        for i, (_, row) in enumerate(top_opportunities.iterrows(), 1):
            report += f"   {i}. {row['article_name'][:30]:<30} | Promotion: {row['optimal_promotion_percentage']:>3}% | Impact: +{row['revenue_change_percentage']:>6.1f}%\n"
        
        report += f"\n⚠️  ALERTES STOCK:\n"
        
        # Alertes stock critique
        critical_stock = df[df['current_stock'] <= self.thresholds['stock_critical']]
        if not critical_stock.empty:
            for _, row in critical_stock.iterrows():
                report += f"   • {row['article_name'][:40]:<40} | Stock: {row['current_stock']:>3} unités (CRITIQUE)\n"
        else:
            report += "   • Aucune alerte stock critique\n"
        
        report += f"\n📋 RECOMMANDATIONS GLOBALES:\n"
        if total_potential_revenue_change > 0:
            report += f"   ✅ Les promotions recommandées devraient augmenter le revenu global\n"
        else:
            report += f"   ⚠️ Attention: impact négatif potentiel sur le revenu global\n"
            
        if high_promotion > len(analysis_results) * 0.3:
            report += f"   📦 Nombreux articles en surstock - campagne de déstockage recommandée\n"
            
        report += f"\n{'='*80}\n"
        
        return report


def main():
    """
    Fonction principale pour tester le modèle
    """
    # Configuration de la base de données
    CONNECTION_STRING = "Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;"
    
    # Initialisation du modèle
    ai_model = SmartPromoAIModel(CONNECTION_STRING)
    
    print("🤖 SmartPromo AI Model - Calcul Intelligent des Promotions avec IA")
    print("=" * 70)
    
    try:
        # Tentative de chargement d'un modèle pré-entraîné
        if not ai_model.load_model():
            print("📚 Aucun modèle pré-entraîné trouvé.")
            choice = input("Voulez-vous entraîner un nouveau modèle ? (o/n): ").strip().lower()
            
            if choice == 'o':
                print("\n🔄 Entraînement du modèle d'IA en cours...")
                
                # Demander le mode d'entraînement
                mode_choice = input("Mode d'entraînement: (1) Données réelles, (2) Données simulées, (3) Auto (défaut): ").strip()
                
                use_simulation = False
                if mode_choice == '2':
                    use_simulation = True
                    print("📊 Utilisation de données simulées pour l'entraînement...")
                elif mode_choice == '1':
                    print("🗄️ Tentative d'utilisation des données réelles...")
                else:
                    print("🔄 Mode automatique: données réelles si possible, sinon simulées...")
                
                if ai_model.train_models(use_simulation=(mode_choice == '2')):
                    print("✅ Modèle entraîné avec succès !")
                    print("\n📊 Métriques des modèles:")
                    for name, metrics in ai_model.model_metrics.items():
                        print(f"  {name}:")
                        print(f"    R² Score: {metrics['r2']:.3f}")
                        print(f"    RMSE: {metrics['rmse']:.3f}")
                        print(f"    MAE: {metrics['mae']:.3f}")
                else:
                    print("❌ Échec de l'entraînement. Utilisation de la méthode classique.")
            else:
                print("📊 Utilisation de la méthode de calcul classique (sans IA)")
        else:
            print("✅ Modèle pré-entraîné chargé avec succès !")
            print("📊 Métriques du modèle:")
            for name, metrics in ai_model.model_metrics.items():
                print(f"  {name}: R² = {metrics['r2']:.3f}, RMSE = {metrics['rmse']:.3f}")
        
        # Demande de la catégorie à analyser
        category_id = input("\nEntrez l'ID de la catégorie à analyser (ou 1 par défaut): ").strip()
        category_id = int(category_id) if category_id.isdigit() else 1
        
        print(f"\n🔍 Analyse de la catégorie {category_id} en cours...")
        if ai_model.is_trained:
            print("🤖 Utilisation de l'IA pour les prédictions")
        else:
            print("📊 Utilisation de la méthode algorithmique classique")
        
        # Analyse de la catégorie
        results = ai_model.analyze_category(category_id)
        
        if results:
            # Affichage des résultats détaillés
            print(f"\n📋 RÉSULTATS DÉTAILLÉS:")
            print("-" * 120)
            
            for result in results:
                method_icon = "🤖" if result.get('prediction_method') == 'ai' else "📊"
                print(f"""
🏷️  Article: {result['article_name']}
   💰 Prix actuel: {result['current_price']:.2f} DT → Prix promo: {result['discounted_price']:.2f} DT
   📊 Promotion recommandée: {result['optimal_promotion_percentage']}% {method_icon}
   📦 Stock actuel: {result['current_stock']} unités
   
   📈 Scores d'analyse:
      • Rotation stock: {result['stock_score']:.2f}
      • Élasticité prix: {result['elasticity_score']:.2f}  
      • Historique ventes: {result['sales_score']:.2f}
      • Historique promos: {result['promotion_score']:.2f}
      • Score final: {result['final_score']:.2f}
      • Méthode: {result.get('prediction_method', 'classic')}
   
   🎯 Impact prévu (30 jours):
      • Ventes: {result['current_monthly_sales_volume']:.0f} → {result['predicted_monthly_sales_volume']:.0f} unités ({result['sales_volume_change_percentage']:+.1f}%)
      • Revenu: {result['current_monthly_revenue']:.2f} → {result['predicted_monthly_revenue']:.2f} DT ({result['revenue_change_percentage']:+.1f}%)
   
   💡 {result['recommendation']}
""")
                print("-" * 120)
            
            # Statistiques sur les méthodes utilisées
            ai_predictions = sum(1 for r in results if r.get('prediction_method') == 'ai')
            classic_predictions = len(results) - ai_predictions
            
            print(f"\n📊 STATISTIQUES DES PRÉDICTIONS:")
            print(f"   🤖 Prédictions IA: {ai_predictions}")
            print(f"   📊 Prédictions classiques: {classic_predictions}")
            
            # Génération et affichage du rapport de synthèse
            summary_report = ai_model.generate_summary_report(results)
            print(summary_report)
            
            # Sauvegarde des résultats en JSON
            output_file = f"smartpromo_analysis_{category_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"📁 Résultats sauvegardés dans: {output_file}")
            
        else:
            print("❌ Aucun résultat trouvé pour cette catégorie")
            
    except KeyboardInterrupt:
        print("\n⏹️ Analyse interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        logger.error(f"Erreur principale: {e}")


if __name__ == "__main__":
    main()
