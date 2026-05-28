import json
import concurrent.futures
from openai import OpenAI
from config.settings import GROQ_API_KEY

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

def _analyze_single_chart(chart_name: str, data_context: str) -> str:
    system_prompt = (
        "Você é um Analista Econômico e de Ciência de Dados sênior avaliando os resultados "
        "de um pipeline de análise macro-financeira (focado no impacto no Dólar, Ibovespa e Selic).\n"
        "Com base nos dados numéricos exatos fornecidos sobre um gráfico específico, gere uma análise "
        "concisa em Markdown com foco nos impactos econômicos e na política monetária. Não invente dados. "
        "Use 2 ou 3 parágrafos curtos no máximo."
    )
    
    prompt = f"Gráfico: {chart_name}\n\nDados Subjacentes:\n{data_context}\n\nEscreva a sua análise para este gráfico."

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"*Não foi possível gerar a análise para este gráfico. Erro: {e}*"

def _json_default(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    # Para lidar com numpy floats, models, etc.
    return str(obj)

def generate_chart_analyses(payload: dict) -> dict:
    """
    Gera as análises textuais (via LLM) baseadas nos dados do results.json (payload).
    Retorna um dict com as análises por nome do gráfico.
    """
    print("\n[Analista IA] Gerando análises dos gráficos...")
    
    tasks = {}
    
    # 1. Heatmap de Correlação
    if "correlations" in payload:
        try:
            pearson = payload["correlations"]["pearson"].round(4)
            tasks["heatmap_correlacao.png"] = json.dumps({
                "pearson": pearson.to_dict(),
                "significance": payload["correlations"]["significance"].to_dict(orient="records")
            }, default=_json_default)
            
            # Gráficos de pares
            tasks["dual_line_ibovespa_dolar.png"] = json.dumps({
                "correlacao_ibovespa_dolar": pearson.loc["ibovespa", "dolar_brl"]
            }, default=_json_default)
            tasks["selic_vs_ibovespa.png"] = json.dumps({
                "correlacao_selic_ibovespa": pearson.loc["selic", "ibovespa"]
            }, default=_json_default)
            tasks["selic_vs_dolar_brl.png"] = json.dumps({
                "correlacao_selic_dolar": pearson.loc["selic", "dolar_brl"]
            }, default=_json_default)
            
            # Gráfico Rolling
            if "rolling" in payload["correlations"]:
                roll = payload["correlations"]["rolling"]
                tasks["rolling_correlation.png"] = json.dumps({
                    "correlacao_media_historica": roll.mean().to_dict(),
                    "correlacao_recente": roll.iloc[-1].to_dict(),
                    "minimo": roll.min().to_dict(),
                    "maximo": roll.max().to_dict()
                }, default=_json_default)
        except: pass
        
    # 2. SARIMAX
    if "models" in payload and "sarimax" in payload["models"]:
        try:
            sm = payload["models"]["sarimax"]
            tasks["forecast_sarimax.png"] = json.dumps({
                "aic": sm["aic"],
                "bic": sm["bic"],
                "forecast_tail": {str(k): float(v) for k, v in list(sm["forecast"].items())[:10]}
            }, default=_json_default)
        except: pass
        
    # 3. Random Forest (Feature Importance)
    if "models" in payload and "random_forest" in payload["models"]:
        try:
            rf = payload["models"]["random_forest"]
            tasks["feature_importance_rf.png"] = json.dumps({
                "metrics": {str(k): float(v) for k, v in rf["metrics"].items()},
                "feature_importance": rf["feature_importance"].round(4).to_dict()
            }, default=_json_default)
        except: pass

    analyses = {}
    
    # Executa as chamadas ao LLM em paralelo para economizar tempo
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chart = {
            executor.submit(_analyze_single_chart, chart, data): chart 
            for chart, data in tasks.items()
        }
        for future in concurrent.futures.as_completed(future_to_chart):
            chart = future_to_chart[future]
            analyses[chart] = future.result()
            
    print(f"[Analista IA] Concluído. {len(analyses)} análises geradas.")
    return analyses
