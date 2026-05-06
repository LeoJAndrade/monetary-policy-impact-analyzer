from openai import OpenAI
from config.settings import GROQ_API_KEY

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

tools = {}

def process_message(message: str, messages_history: list):
    
    system_prompt = "Você é uma IA especialista em responder apenas sobre politica monetária. Não responda sobre coisas que não sejam sobre finanças e ciência de dados. Responda de forma curta e direta"
    messages = [{"role": "system", "content": system_prompt}] + messages_history + [{"role": "user", "content": message}]

    ai_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages
    )

    return ai_response.choices[0].message.content