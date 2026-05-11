import json
import inspect
from orchestrator.tools import (
    model_market_indicators,
    model_ibovespa_dolar_heatmap,
    get_market_indicators,
    get_correlation_heatmap,
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
}


def process_message(message: str, messages_history: list, chat_id: int = None):

    system_prompt = "Você é uma IA especialista em responder apenas sobre politica monetária. Não responda sobre coisas que não sejam sobre finanças e ciência de dados. Responda de forma curta e direta"
    messages = (
        [{"role": "system", "content": system_prompt}]
        + messages_history
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
            model="openai/gpt-oss-120b", messages=messages
        )

        return second_response.choices[0].message.content

    return response_message.content
