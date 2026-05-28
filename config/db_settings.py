import sqlite3


def create_db():
    connection = sqlite3.connect("monetary_analysis.db")
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON; ")
    cursor.execute("PRAGMA journal_mode=WAL")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY,
            user_name VARCHAR(50)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            role VARCHAR(10),
            message TEXT,
            date TIMESTAMP
        )
    """
    )

    connection.commit()
    connection.close()
    print("Banco de dados e tabelas criadas com sucesso!")


def get_conversation_history(chat_id):
    connection = sqlite3.connect("monetary_analysis.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    sql = "SELECT role, message FROM messages WHERE chat_id = ? ORDER BY date DESC LIMIT 6"
    rows = cursor.execute(sql, (chat_id,)).fetchall()

    messages_history = []
    for row in rows:
        messages_history.append({"role": row["role"], "content": row["message"]})

    messages_history.reverse()  # Inverter para ordem cronológica (mais antigo primeiro)

    connection.close()
    return messages_history
