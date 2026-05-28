"""
app.py  —  PI-V Web Dashboard (Flask)

Rotas:
    GET  /                         → Dashboard principal
    GET  /api/run                  → Executa pipeline via SSE (stream de logs)
    GET  /api/results              → Últimos resultados (results.json)
    GET  /api/charts               → Lista de gráficos gerados
    GET  /reports/<filename>       → Serve arquivos da pasta reports/
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory

from orchestrator.ai_agent import process_message
from config.db_settings import create_db, get_conversation_history

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_SORT_KEYS"] = False

# Fila global de logs da última execução
_log_queue: queue.Queue[str | None] = queue.Queue()
_pipeline_running = threading.Event()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_pipeline_thread(start: str, end: str | None) -> None:
    """Executa main.py como subprocesso e enfileira as linhas de log."""
    _pipeline_running.set()
    cmd = [sys.executable, str(BASE_DIR / "main.py"), "--start", start]
    if end:
        cmd += ["--end", end]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(BASE_DIR),
        )
        for line in proc.stdout:  # type: ignore[union-attr]
            _log_queue.put(line.rstrip())
        proc.wait()
        status = "success" if proc.returncode == 0 else "error"
        _log_queue.put(f"__STATUS__{status}")
    except Exception as exc:
        _log_queue.put(f"[ERRO] {exc}")
        _log_queue.put("__STATUS__error")
    finally:
        _log_queue.put(None)  # sentinel
        _pipeline_running.clear()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run")
def run_pipeline():
    """SSE: executa o pipeline e faz stream das linhas de log."""
    if _pipeline_running.is_set():
        return Response(
            "data: [Pipeline já em execução. Aguarde.]\n\n",
            mimetype="text/event-stream",
        )

    start = request.args.get("start", "2014-01-01")
    end = request.args.get("end") or None

    # Limpa fila anterior
    while not _log_queue.empty():
        _log_queue.get_nowait()

    t = threading.Thread(target=_run_pipeline_thread, args=(start, end), daemon=True)
    t.start()

    def generate():
        yield "data: [Pipeline iniciado]\n\n"
        while True:
            try:
                line = _log_queue.get(timeout=120)
            except queue.Empty:
                yield "data: [Timeout]\n\nevent: end\ndata: error\n\n"
                break

            if line is None:
                yield "event: end\ndata: done\n\n"
                break

            if line.startswith("__STATUS__"):
                status = line.replace("__STATUS__", "")
                yield f"event: end\ndata: {status}\n\n"
                break

            # Escapa quebras de linha internas
            yield f"data: {line}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


@app.route("/api/results")
def api_results():
    """Retorna o último results.json gerado pelo pipeline."""
    results_path = REPORTS_DIR / "results.json"
    if not results_path.exists():
        return jsonify({"error": "Nenhum resultado disponível. Execute o pipeline primeiro."}), 404
    return jsonify(json.loads(results_path.read_text(encoding="utf-8")))


@app.route("/api/charts")
def api_charts():
    """Lista imagens disponíveis em reports/."""
    imgs = sorted(p.name for p in REPORTS_DIR.glob("*.png"))
    return jsonify(imgs)


@app.route("/reports/<path:filename>")
def serve_report(filename: str):
    return send_from_directory(REPORTS_DIR, filename)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Recebe mensagem do frontend e responde via AI Agent, salvando no banco local."""
    create_db()
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    user_message = data.get("message", "")
    chat_id = data.get("chat_id", 999999) # Default local chat ID
    user_name = data.get("user_name", "LocalUser")
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # 0. Salva o chat na tabela 'chat' se ainda não existir
    with sqlite3.connect("monetary_analysis.db", timeout=10.0) as connection:
        cursor = connection.cursor()
        sql_chat = "INSERT OR IGNORE INTO chat (id, user_name) VALUES (?, ?)"
        cursor.execute(sql_chat, (chat_id, user_name))
        connection.commit()

    # Guarda a mensagem do usuário no banco
    with sqlite3.connect("monetary_analysis.db", timeout=10.0) as connection:
        cursor = connection.cursor()
        sql = "INSERT INTO messages(chat_id, role, message, date) VALUES (?, ?, ?, ?)"
        cursor.execute(sql, (chat_id, "user", user_message, datetime.now().isoformat()))
        connection.commit()

    # 3. Envia mensagem do usuário para IA
    messages_history = get_conversation_history(chat_id)
    ai_response = process_message(user_message, messages_history, chat_id)

    # Guarda a resposta da IA no banco
    with sqlite3.connect("monetary_analysis.db", timeout=10.0) as connection:
        cursor = connection.cursor()
        sql_ai = "INSERT INTO messages(chat_id, role, message, date) VALUES(?, ?, ?, ?)"
        cursor.execute(sql_ai, (chat_id, "assistant", ai_response, datetime.now().isoformat()))
        connection.commit()

    return jsonify({"response": ai_response})


@app.route("/api/chat/history", methods=["GET"])
def api_chat_history():
    """Retorna o histórico de conversas do usuário local."""
    chat_id = request.args.get("chat_id", 999999, type=int)
    history = get_conversation_history(chat_id)
    return jsonify(history)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n  PI-V Dashboard → http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
