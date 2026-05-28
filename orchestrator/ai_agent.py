import json
import inspect
import datetime
from orchestrator.tools import (
    model_market_indicators,
    model_ibovespa_dolar_heatmap,
    model_dual_line_chart,
    model_selic_vs_asset_chart,
    model_rolling_correlation_chart,
    model_forecast_chart,
    model_feature_importance_chart,
    get_market_indicators,
    get_correlation_heatmap,
    get_dual_line_chart,
    get_selic_vs_asset_chart,
    get_rolling_correlation_chart,
    get_forecast_chart,
    get_feature_importance_chart,
    model_get_pdf_report,
    get_pdf_report,
)
from openai import OpenAI
from config.settings import GROQ_API_KEY

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_market_indicators",
            "description": "Obtém indicadores econômicos (Selic, IPCA, etc) do Banco Central para um período.",
            "parameters": model_market_indicators.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_correlation_heatmap",
            "description": "Utilizado para gerar um gráfico de correlação (heatmap) entre o índice Ibovespa e a taxa de câmbio do Dólar.",
            "parameters": model_ibovespa_dolar_heatmap.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dual_line_chart",
            "description": "Gera um gráfico de linha dupla comparando dois ativos (ex: Ibovespa e Dólar) no mesmo período.",
            "parameters": model_dual_line_chart.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_selic_vs_asset_chart",
            "description": "Gera um gráfico comparando a taxa Selic com um ativo específico.",
            "parameters": model_selic_vs_asset_chart.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rolling_correlation_chart",
            "description": "Gera um gráfico de correlação móvel (rolling correlation) entre dois ativos.",
            "parameters": model_rolling_correlation_chart.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast_chart",
            "description": "Gera um gráfico com a série histórica e a previsão (forecast) utilizando modelo SARIMAX.",
            "parameters": model_forecast_chart.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_feature_importance_chart",
            "description": "Gera um gráfico de importância de features utilizando modelo Random Forest.",
            "parameters": model_feature_importance_chart.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pdf_report",
            "description": "Gera um relatório completo em PDF contendo todas as análises, gráficos e modelos preditivos e o envia para o usuário.",
            "parameters": model_get_pdf_report.model_json_schema(),
        },
    },
]

TOOL_REGISTRY = {
    "get_market_indicators": {
        "function": get_market_indicators,
        "model": model_market_indicators,
    },
    "get_correlation_heatmap": {
        "function": get_correlation_heatmap,
        "model": model_ibovespa_dolar_heatmap,
    },
    "get_dual_line_chart": {
        "function": get_dual_line_chart,
        "model": model_dual_line_chart,
    },
    "get_selic_vs_asset_chart": {
        "function": get_selic_vs_asset_chart,
        "model": model_selic_vs_asset_chart,
    },
    "get_rolling_correlation_chart": {
        "function": get_rolling_correlation_chart,
        "model": model_rolling_correlation_chart,
    },
    "get_forecast_chart": {
        "function": get_forecast_chart,
        "model": model_forecast_chart,
    },
    "get_feature_importance_chart": {
        "function": get_feature_importance_chart,
        "model": model_feature_importance_chart,
    },
    "get_pdf_report": {
        "function": get_pdf_report,
        "model": model_get_pdf_report,
    },
}


def process_message(message: str, messages_history: list, chat_id: int = None):

    system_prompt = """
    Você é uma IA especialista em responder apenas sobre politica monetária. Não responda sobre coisas que não sejam sobre finanças e ciência de dados. Responda de forma curta e direta.

    Ativos e códigos disponíveis para consulta (BCB/SGS):
    - "selic": 11 (Taxa Selic Diária)
    - "ipca_12m": 13522 (IPCA Acumulado 12 meses)
    - "cambio_bcb": 1 (Taxa de Câmbio USD/BRL)

    Ativos de mercado disponíveis (Colunas):
    - "ibovespa"
    - "dolar_brl"
    - "dxy"
    """
    messages = (
        [{"role": "system", "content": system_prompt}]
        + messages_history
        + [{"role": "system", "content": f"Data de Hoje: {datetime.datetime.now()}"}]
        + [{"role": "user", "content": message}]
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b", messages=messages, tools=tools
    )

    response_message = response.choices[0].message
    print(f"Estrutura de response_message: {response_message}")

    tool_calls = response_message.tool_calls

    if tool_calls:
        messages.append(response_message)

        for tool_call in tool_calls:
            tool_name = tool_call.function.name

            if tool_name in TOOL_REGISTRY:
                registry_item = TOOL_REGISTRY[tool_name]

                ToolModel = registry_item["model"]
                tool_function = registry_item["function"]

                # Validação dos argumentos
                args_json = json.loads(tool_call.function.arguments)
                args_obj = ToolModel(**args_json)

                # Transforma argumentos válidos em um dicionário
                kwargs_to_function = args_obj.model_dump()

                # Inspeciona a função e vê se precisa do chat_id
                signature = inspect.signature(tool_function)
                if "chat_id" in signature.parameters:
                    kwargs_to_function["chat_id"] = chat_id

                result = tool_function(**kwargs_to_function)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": str(result),
                    }
                )

        second_response = client.chat.completions.create(
            model="openai/gpt-oss-120b", messages=messages, tools=tools
        )

        return second_response.choices[0].message.content

    return response_message.content
