# Especificações Técnicas e Arquitetura

Este documento detalha os componentes técnicos integrados ao pipeline de análise macro-financeira, focando na integração com o Agente de IA, no banco de dados local e na arquitetura do Webhook do Telegram.

## 1. Banco de Dados Local (SQLite)

Para que a Inteligência Artificial consiga manter o contexto das conversas e lembrar do que o usuário disse anteriormente, foi implementado um banco de dados local utilizando SQLite (`monetary_analysis.db`). A arquitetura foi dividida em duas tabelas principais.

### Esquema de Tabelas

**Tabela `chat`**
Armazena a identificação única das pessoas que interagem com o bot.
- `id` (INTEGER PRIMARY KEY): ID numérico único do chat gerado pelo Telegram.
- `user_name` (TEXT): Nome ou primeiro nome do usuário no Telegram.

**Tabela `messages`**
Mantém o registro completo (log) de todas as interações.
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT): Identificador sequencial da mensagem no banco.
- `chat_id` (INTEGER): Chave estrangeira ligando a mensagem ao `chat` específico.
- `role` (TEXT): Identifica o emissor da mensagem. Pode ser `"user"` (usuário) ou `"assistant"` (IA).
- `message` (TEXT): O texto completo da mensagem enviada ou recebida.
- `date` (TEXT): Timestamp (ISO) exato de quando a mensagem foi processada.

> **Regra de Negócio:** Na hora de enviar mensagens à IA, o sistema consulta apenas o histórico recente para não estourar o limite de tokens permitidos pela API.

---

## 2. Webhook e Integração com o Telegram

Diferente do método tradicional de *Long Polling* (onde o bot fica perguntando à rede se há mensagens novas infinitamente), a comunicação foi otimizada usando **Webhooks**. Assim, a própria API do Telegram notifica passivamente a aplicação assim que um evento ocorre (mensagem recebida).

### Fluxo de Comunicação

1. O servidor local (`webhook.py`) é iniciado usando o framework **FastAPI** e escuta requisições na porta `8000` (rota `/webhook/telegram`).
2. Como o Telegram não consegue enviar pacotes diretamente para o `localhost`, a ferramenta **Ngrok** é utilizada para criar um túnel seguro, gerando uma URL pública HTTPS dinâmica (ex: `https://exemplo.ngrok-free.app`).
3. O vínculo é feito cadastrando a URL do Ngrok no servidor do Telegram através do endpoint oficial:
   `https://api.telegram.org/bot<TOKEN_DO_BOT>/setWebhook?url=<URL_NGROK>/webhook/telegram`
4. Quando uma mensagem é disparada pelo usuário:
   - O Telegram faz um `POST` no FastAPI.
   - O Python extrai o texto e ID, salvando a mensagem no SQLite (`user`).
   - O histórico é consultado e enviado à IA (Groq).
   - O retorno da IA é salvo no SQLite (`assistant`).
   - A resposta final é devolvida ao usuário via POST para a API do Telegram.

> **Mecanismo de Segurança:** Existe um filtro (`time.time() - message_date_seconds > 30`) que previne que mensagens travadas com mais de 30 segundos entrem em loop e sobrecarreguem a API.

---

## 3. Agente de Inteligência Artificial (Groq API)

O agente orquestrador (`orchestrator/ai_agent.py`) foi desenhado para atuar como um especialista técnico focado exclusivamente no escopo do PI-V: macroeconomia, política monetária e ciência de dados.

### Arquitetura de Conexão

Para maximizar a velocidade de inferência (tokens por segundo) e minimizar custos operacionais, o sistema não utiliza a infraestrutura padrão da OpenAI. Em vez disso, utiliza a provedora **Groq**, famosa por sua tecnologia de hardware LPU (Language Processing Units).

Para manter compatibilidade absoluta de código, a biblioteca nativa `openai` para Python foi utilizada, bastando sobrescrever a URL base da API:

```python
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)
```

### Prompt Engineering e Configurações

- **Modelo Inferido:** O sistema aponta para o modelo `gpt-oss-120b` (uma estrutura open-source de alto parâmetro hospedada na Groq).
- **System Prompt (Injeção de Personalidade):** Foi adicionado um `role: system` invisível ao usuário com a instrução: *"Você é uma IA especialista em responder apenas sobre politica monetária. Não responda sobre coisas que não sejam sobre finanças e ciência de dados. Responda de forma curta e direta"*.
- **Estruturação de Contexto:** A montagem final da requisição enviada à rede neural neural contém sempre a estrutura tríplice:
  `[Prompt de Sistema] + [Array do Histórico do SQLite] + [Mensagem Atual do Usuário]`.
