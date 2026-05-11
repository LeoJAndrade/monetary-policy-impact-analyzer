from datetime import datetime
import uvicorn
import sqlite3
from fastapi import FastAPI, Request
from orchestrator.ai_agent import process_message
from src.notifications.telegram_bot import send_message
from config.db_settings import create_db, get_conversation_history
import uvicorn

app = FastAPI()


@app.post("/webhook/telegram")
async def recebei_webhook(request: Request):

    # Criando tabelas
    create_db()

    data = await request.json()
    print("Nova mensagem recebida: ", data)

    # 1. Mensagem do usuário, Chat ID e Data recebidos do telegram
    message_data = data.get("message", {})
    user_message = message_data.get("text", "")
    user_name = message_data.get("chat", {}).get("first_name", {})
    chat_id = message_data.get("chat", {}).get("id")
    message_date_seconds = message_data.get("date", 0)

    # 0. Salva o chat na tabela 'chat' se ainda não existir
    with sqlite3.connect("monetary_analysis.db", timeout=10.0) as connection:
        cursor = connection.cursor()
        # INSERT OR IGNORE: insere se não existir, ignora se o ID já estiver lá
        sql_chat = "INSERT OR IGNORE INTO chat (id, user_name) VALUES (?, ?)"
        cursor.execute(sql_chat, (chat_id, user_name))
        connection.commit()

    # 2. Verifica se a mensagem é antiga (mais de 30 segundos)
    import time

    if time.time() - message_date_seconds > 30:
        return {"status": "200"}

    # Guarda a mensagem do usuário no banco
    with sqlite3.connect("monetary_analysis.db", timeout=10.0) as connection:
        cursor = connection.cursor()
        sql = "INSERT INTO messages(chat_id, role, message, date) VALUES (?, ?, ?, ?)"
        cursor.execute(sql, (chat_id, "user", user_message, datetime.now().isoformat()))
        connection.commit()

    print(f"Mensagem do usuário: {user_message} (Chat ID: {chat_id})")

    # 3. Envia mensagem do usuário para IA
    messages_history = get_conversation_history(chat_id)
    ai_response = process_message(user_message, messages_history, chat_id)

    # Guarda a resposta da IA no banco
    with sqlite3.connect("monetary_analysis.db", timeout=10.0) as connection:
        cursor = connection.cursor()
        sql_ai = "INSERT INTO messages(chat_id, role, message, date) VALUES(?, ?, ?, ?)"
        cursor.execute(
            sql_ai, (chat_id, "assistant", ai_response, datetime.now().isoformat())
        )
        connection.commit()

    # 4. Enviar mensagem de volta para o chat_id específico
    send_message(text=ai_response, chat_id=chat_id)

    return {"status": "200"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
