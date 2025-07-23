"""
Intégration SmartPromo AI avec ASP.NET Backend
=============================================

Ce script montre comment intégrer le modèle IA avec le backend ASP.NET Core
via des appels Python ou une API REST.
"""

import sys
import json
import argparse
from smartpromo_ai_model import SmartPromoAIModel

def analyze_category_for_api(category_id: int, connection_string: str) -> str:
    """
    Analyse une catégorie et retourne les résultats au format JSON
    pour l'intégration avec l'API ASP.NET
    
    Args:
        category_id (int): ID de la catégorie
        connection_string (str): Chaîne de connexion
        
    Returns:
        str: JSON des résultats
    """
    try:
        model = SmartPromoAIModel(connection_string)
        results = model.analyze_category(category_id)
        
        if results:
            # Format de sortie pour l'API
            api_response = {
                "success": True,
                "message": f"Analyse réussie pour {len(results)} articles",
                "category_id": category_id,
                "analysis_date": model.datetime.now().isoformat(),
                "total_articles": len(results),
                "data": results,
                "summary": {
                    "average_promotion": sum(r['optimal_promotion_percentage'] for r in results) / len(results),
                    "total_revenue_impact": sum(r['revenue_change'] for r in results),
                    "high_promotion_count": len([r for r in results if r['optimal_promotion_percentage'] > 30]),
                    "critical_stock_count": len([r for r in results if r['current_stock'] <= 10])
                }
            }
        else:
            api_response = {
                "success": False,
                "message": f"Aucun article trouvé pour la catégorie {category_id}",
                "category_id": category_id,
                "data": [],
                "summary": {}
            }
            
        return json.dumps(api_response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_response = {
            "success": False,
            "message": f"Erreur lors de l'analyse: {str(e)}",
            "category_id": category_id,
            "data": [],
            "summary": {}
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)

def analyze_single_article(article_id: int, connection_string: str) -> str:
    """
    Analyse un article spécifique
    
    Args:
        article_id (int): ID de l'article
        connection_string (str): Chaîne de connexion
        
    Returns:
        str: JSON du résultat
    """
    try:
        model = SmartPromoAIModel(connection_string)
        
        if not model.connect_database():
            raise Exception("Impossible de se connecter à la base de données")
        
        # Récupération des données de l'article
        query = """
        SELECT 
            a.Id as ArticleId,
            a.Nom as ArticleName,
            a.Prix as Price,
            a.StockDisponible as CurrentStock,
            a.SeuilMinStock as MinStockThreshold,
            a.CategoryId,
            c.Nom as CategoryName
        FROM Articles a
        JOIN Categories c ON a.CategoryId = c.Id
        WHERE a.Id = ? AND a.IsActive = 1
        """
        
        import pandas as pd
        article_df = pd.read_sql(query, model.connection, params=[article_id])
        model.disconnect_database()
        
        if article_df.empty:
            raise Exception(f"Article {article_id} non trouvé ou inactif")
        
        article_row = article_df.iloc[0]
        
        # Calcul pour cet article
        model = SmartPromoAIModel(connection_string)
        if model.connect_database():
            promotion_data = model.calculate_optimal_promotion_percentage(article_row)
            sales_history = model.get_sales_history(article_id)
            impact_prediction = model.predict_impact(promotion_data, sales_history)
            model.disconnect_database()
            
            result = {**promotion_data, **impact_prediction}
            
            api_response = {
                "success": True,
                "message": f"Analyse réussie pour l'article {article_id}",
                "article_id": article_id,
                "analysis_date": model.datetime.now().isoformat(),
                "data": result
            }
        else:
            raise Exception("Connexion à la base de données échouée")
            
        return json.dumps(api_response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_response = {
            "success": False,
            "message": f"Erreur lors de l'analyse de l'article: {str(e)}",
            "article_id": article_id,
            "data": {}
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)

def main():
    """
    Point d'entrée principal pour l'intégration API
    """
    parser = argparse.ArgumentParser(description='SmartPromo AI API Integration')
    parser.add_argument('--mode', choices=['category', 'article'], required=True,
                       help='Mode d\'analyse: category ou article')
    parser.add_argument('--id', type=int, required=True,
                       help='ID de la catégorie ou de l\'article')
    parser.add_argument('--connection', type=str, 
                       default="Server=DESKTOP-S22JEMV\\SQLEXPRESS;Database=SmartPromoDb_v2026_Fresh;Trusted_Connection=True;",
                       help='Chaîne de connexion à la base de données')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'category':
            result = analyze_category_for_api(args.id, args.connection)
        elif args.mode == 'article':
            result = analyze_single_article(args.id, args.connection)
        
        print(result)
        sys.exit(0)
        
    except Exception as e:
        error_response = {
            "success": False,
            "message": f"Erreur système: {str(e)}",
            "data": {}
        }
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()

# Exemples d'utilisation depuis ASP.NET:
#
# 1. Analyse d'une catégorie:
#    python api_integration.py --mode category --id 1
#
# 2. Analyse d'un article:
#    python api_integration.py --mode article --id 123
#
# 3. Avec chaîne de connexion personnalisée:
#    python api_integration.py --mode category --id 1 --connection "Server=...;Database=...;..."

"""
Exemple d'intégration dans le contrôleur ASP.NET Core:

[ApiController]
[Route("api/[controller]")]
public class PromotionAIController : ControllerBase
{
    private readonly string _connectionString;
    
    public PromotionAIController(IConfiguration configuration)
    {
        _connectionString = configuration.GetConnectionString("DefaultConnection");
    }
    
    [HttpGet("analyze-category/{categoryId}")]
    public async Task<IActionResult> AnalyzeCategory(int categoryId)
    {
        try
        {
            var processInfo = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"SmartPromo_AI_Model/api_integration.py --mode category --id {categoryId} --connection \"{_connectionString}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            
            using var process = Process.Start(processInfo);
            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            
            await process.WaitForExitAsync();
            
            if (process.ExitCode == 0)
            {
                var result = JsonSerializer.Deserialize<object>(output);
                return Ok(result);
            }
            else
            {
                return BadRequest(new { error = error, output = output });
            }
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { error = ex.Message });
        }
    }
    
    [HttpGet("analyze-article/{articleId}")]
    public async Task<IActionResult> AnalyzeArticle(int articleId)
    {
        try
        {
            var processInfo = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"SmartPromo_AI_Model/api_integration.py --mode article --id {articleId} --connection \"{_connectionString}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            
            using var process = Process.Start(processInfo);
            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            
            await process.WaitForExitAsync();
            
            if (process.ExitCode == 0)
            {
                var result = JsonSerializer.Deserialize<object>(output);
                return Ok(result);
            }
            else
            {
                return BadRequest(new { error = error, output = output });
            }
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { error = ex.Message });
        }
    }
}
"""
