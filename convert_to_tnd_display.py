"""
Conversion Affichage Dinars Tunisiens - Analyse SmartPromo AI
============================================================

Ce script convertit l'affichage des analyses existantes pour utiliser 
la devise tunisienne (DT) au lieu des euros (€).
"""

import json
import os
from datetime import datetime

def convert_analysis_to_tnd(json_file_path):
    """
    Convertit un fichier d'analyse JSON pour afficher les prix en dinars tunisiens
    
    Args:
        json_file_path (str): Chemin vers le fichier JSON d'analyse
    """
    
    print(f"🔄 Conversion du fichier: {os.path.basename(json_file_path)}")
    
    try:
        # Lecture du fichier JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        print(f"📊 {len(analysis_data)} articles trouvés dans l'analyse")
        
        # Mise à jour des recommandations pour inclure DT
        updated_count = 0
        for item in analysis_data:
            # Les prix sont déjà en TND dans la base, on met juste à jour l'affichage
            if 'recommendation' in item:
                # Mise à jour des recommandations pour mentionner TND
                old_rec = item['recommendation']
                
                # Remplacement de "€" par "DT" si présent
                if '€' in old_rec:
                    item['recommendation'] = old_rec.replace('€', 'DT')
                    updated_count += 1
                
                # Ajout d'informations de devise pour clarifier
                if 'current_price' in item:
                    item['currency'] = 'TND'
                    item['currency_symbol'] = 'DT'
        
        print(f"✅ {updated_count} recommandations mises à jour")
        
        # Création du nouveau fichier avec suffix TND
        base_name = os.path.splitext(json_file_path)[0]
        new_file_path = f"{base_name}_TND.json"
        
        # Sauvegarde du fichier converti
        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Fichier converti sauvegardé: {os.path.basename(new_file_path)}")
        
        return new_file_path
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion: {str(e)}")
        return None

def display_tnd_summary(json_file_path):
    """
    Affiche un résumé de l'analyse avec les prix en dinars tunisiens
    
    Args:
        json_file_path (str): Chemin vers le fichier JSON d'analyse
    """
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        print("\n🇹🇳 RÉSUMÉ DE L'ANALYSE EN DINARS TUNISIENS")
        print("=" * 50)
        
        # Calcul des statistiques
        total_articles = len(analysis_data)
        total_current_revenue = sum(item.get('current_monthly_revenue', 0) for item in analysis_data)
        total_predicted_revenue = sum(item.get('predicted_monthly_revenue', 0) for item in analysis_data)
        revenue_change = total_predicted_revenue - total_current_revenue
        
        avg_current_price = sum(item.get('current_price', 0) for item in analysis_data) / total_articles if total_articles > 0 else 0
        avg_promotion = sum(item.get('optimal_promotion_percentage', 0) for item in analysis_data) / total_articles if total_articles > 0 else 0
        
        print(f"📊 STATISTIQUES GÉNÉRALES:")
        print(f"   • Articles analysés: {total_articles}")
        print(f"   • Prix moyen: {avg_current_price:.2f} DT")
        print(f"   • Promotion moyenne recommandée: {avg_promotion:.1f}%")
        print(f"   • Revenu mensuel actuel: {total_current_revenue:,.2f} DT")
        print(f"   • Revenu mensuel prévu: {total_predicted_revenue:,.2f} DT")
        print(f"   • Impact total: {revenue_change:+,.2f} DT ({(revenue_change/total_current_revenue*100 if total_current_revenue > 0 else 0):+.1f}%)")
        
        # Top 3 des opportunités
        profitable_items = [item for item in analysis_data if item.get('revenue_change_percentage', 0) > 0]
        profitable_items.sort(key=lambda x: x.get('revenue_change_percentage', 0), reverse=True)
        
        print(f"\n🎯 TOP 3 DES OPPORTUNITÉS:")
        for i, item in enumerate(profitable_items[:3], 1):
            print(f"   {i}. {item.get('article_name', 'N/A')}")
            print(f"      Prix: {item.get('current_price', 0):.2f} DT → {item.get('discounted_price', 0):.2f} DT")
            print(f"      Impact: +{item.get('revenue_change_percentage', 0):.1f}% de revenu")
        
        print(f"\n💡 Toutes les valeurs sont exprimées en dinars tunisiens (DT)")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'affichage: {str(e)}")

def main():
    """Fonction principale"""
    
    print("🇹🇳 Conversion Affichage Dinars Tunisiens - SmartPromo AI")
    print("=" * 60)
    
    # Recherche du fichier d'analyse existant
    analysis_file = "smartpromo_analysis_2_20250723_061550.json"
    
    if os.path.exists(analysis_file):
        print(f"📁 Fichier d'analyse trouvé: {analysis_file}")
        
        # Conversion du fichier
        converted_file = convert_analysis_to_tnd(analysis_file)
        
        if converted_file:
            # Affichage du résumé en TND
            display_tnd_summary(converted_file)
        
    else:
        print(f"❌ Fichier d'analyse non trouvé: {analysis_file}")
        print("💡 Veuillez exécuter une analyse SmartPromo AI d'abord")
    
    print(f"\n✅ Conversion terminée!")
    print(f"📋 Les prix sont maintenant affichés en dinars tunisiens (DT)")

if __name__ == "__main__":
    main()
