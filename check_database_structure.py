#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification de la structure de la base de données
Analyse les colonnes disponibles dans les tables
"""

import pyodbc
import pandas as pd

def check_database_structure():
    """Vérifie la structure de la base de données"""
    
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=(localdb)\\MSSQLLocalDB;"
        "DATABASE=SmartPromoDb_v2026_Fresh;"
        "Trusted_Connection=yes;"
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        print("✅ Connexion à la base de données établie")
        
        # Vérifier la table Stocks
        print("\n📋 Structure de la table Stocks:")
        stocks_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Stocks'
        ORDER BY ORDINAL_POSITION
        """
        
        stocks_df = pd.read_sql(stocks_query, conn)
        print(stocks_df.to_string(index=False))
        
        # Vérifier la table Ventes
        print("\n📋 Structure de la table Ventes:")
        ventes_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Ventes'
        ORDER BY ORDINAL_POSITION
        """
        
        ventes_df = pd.read_sql(ventes_query, conn)
        print(ventes_df.to_string(index=False))
        
        # Vérifier les données d'un stock
        print("\n📊 Exemple de données dans Stocks (5 premiers):")
        sample_query = "SELECT TOP 5 * FROM Stocks"
        sample_df = pd.read_sql(sample_query, conn)
        print(sample_df.to_string(index=False))
        
        conn.close()
        print("\n✅ Vérification terminée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    check_database_structure()
