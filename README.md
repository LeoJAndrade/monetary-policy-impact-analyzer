# PI-V — Análise Quantitativa: Ibovespa, Dólar & Política Monetária

> Modelo quantitativo de relação entre política monetária (Selic/IPCA), mercado acionário (Ibovespa) e câmbio (USD/BRL) no Brasil.

---

## O que é o projeto

O **PI-V** é um pipeline de análise macro-financeira que:

- Coleta automaticamente dados históricos de **Ibovespa**, **Dólar (USD/BRL)** e **DXY** via `yfinance`, e de **Selic** e **IPCA** via a API pública do Banco Central do Brasil (SGS).
- Calcula a **correlação de Pearson** e **correlações rolling** (janelas de 30, 60 e 90 dias) entre os ativos.
- Treina três modelos preditivos para o câmbio (USD/BRL):
  - **Regressão Linear Múltipla** — interpretável e explicativa.
  - **ARIMA** — captura padrões temporais (tendência + sazonalidade).
  - **Random Forest** — captura não-linearidades entre as variáveis.
- Gera gráficos profissionais salvos na pasta `reports/`.
- (Opcional) Envia o relatório automaticamente por **e-mail** e/ou **Telegram**.

---

## Screenshots

![Ibovespa vs Dólar](reports/dual_line_ibovespa_dolar.png)
![Selic vs Ibovespa](reports/selic_vs_ibovespa.png)
![Selic vs Dólar](reports/selic_vs_dolar_brl.png)
![Matriz de Correlação](reports/heatmap_correlacao.png)
![Rolling Correlation](reports/rolling_correlation.png)
![Forecast ARIMA](reports/forecast_arima.png)
![Feature Importance (RF)](reports/feature_importance_rf.png)

---

## Estrutura do projeto

```
PI-V/
├── src/
│   ├── data/
│   │   ├── market_data.py       ← Ibovespa, Dólar, DXY via yfinance
│   │   └── bcb_data.py          ← Selic e IPCA via API SGS/BCB
│   ├── analysis/
│   │   ├── correlation.py       ← Pearson, rolling correlation, p-value
│   │   └── models.py            ← LinearRegression, ARIMA, RandomForest
│   ├── visualization/
│   │   └── charts.py            ← Geração e salvamento de gráficos
│   └── notifications/
│       ├── email_sender.py      ← Envio por SMTP
│       └── telegram_bot.py      ← Envio via Bot API do Telegram
├── config/
│   └── settings.py              ← Leitura do .env
├── reports/                     ← Gráficos e PDFs gerados (ignorado pelo git)
├── main.py                      ← Orquestra o pipeline completo
├── requirements.txt
├── .env.example                 ← Modelo de configuração
├── .gitignore
└── README.md
```

---

## O que cada módulo faz

| Módulo | Responsabilidade |
|---|---|
| `src/data/market_data.py` | Baixa preços de fechamento de `^BVSP`, `BRL=X` e `DX-Y.NYB` via `yfinance` |
| `src/data/bcb_data.py` | Consulta as séries 11 (Selic) e 13522 (IPCA 12m) na API pública do BCB |
| `src/analysis/correlation.py` | `pearson_matrix`, `rolling_correlation`, `correlation_significance` |
| `src/analysis/models.py` | `linear_regression_model`, `arima_model`, `random_forest_model` |
| `src/visualization/charts.py` | Gráfico duplo, heatmap, rolling, forecast ARIMA, feature importance |
| `src/notifications/email_sender.py` | Envia PDF + imagens via SMTP com TLS |
| `src/notifications/telegram_bot.py` | Envia mensagem, fotos e documentos via Telegram Bot API |
| `config/settings.py` | Carrega variáveis do `.env` (tokens, e-mails, período padrão) |
| `main.py` | Pipeline completo: coleta → análise → gráficos → modelos → (envio) |

---

## Instalação

### 1. Clone o repositório e entre na pasta

```bash
git clone <url-do-repositório>
cd PI-V
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

---

## Configuração

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
# Telegram Bot
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# E-mail SMTP (ex.: Gmail com App Password)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASS=sua_senha_de_app
EMAIL_TO=destinatario@email.com

# Período de coleta padrão
DEFAULT_START=2014-01-01
```

> As notificações são **opcionais** — o pipeline roda normalmente sem `.env` preenchido.

---

## Como executar

### Dashboard Web (recomendado)

```bash
source .venv/bin/activate
python3 app.py
# Abra http://localhost:5000
```

O dashboard permite:
- Definir período e executar o pipeline com um clique
- Ver todos os gráficos gerados
- Consultar a matriz de correlação de Pearson e significância estatística
- Ver métricas e previsões dos 3 modelos em tempo real
- Acompanhar logs ao vivo durante a execução

### CLI (linha de comando)

```bash
# pipeline completo (sem envio de notificações)
python3 main.py

# Período personalizado
python3 main.py --start 2018-01-01 --end 2024-12-31

# Com envio por e-mail
python3 main.py --email

# Com envio pelo Telegram
python3 main.py --telegram

# Ambos
python3 main.py --email --telegram
```

Os gráficos ficam salvos em `reports/`.

---

## Gráficos gerados

| Arquivo | Conteúdo |
|---|---|
| `dual_line_ibovespa_dolar.png` | Ibovespa vs Dólar — dois eixos Y |
| `selic_vs_ibovespa.png` | Selic vs Ibovespa |
| `selic_vs_dolar_brl.png` | Selic vs Dólar |
| `heatmap_correlacao.png` | Matriz de correlação de Pearson |
| `rolling_correlation.png` | Correlação rolling 30/60/90 dias |
| `forecast_arima.png` | Previsão ARIMA com IC 95% |
| `feature_importance_rf.png` | Importância de features (Random Forest) |

---

## Fundamentação teórica (resumo)

| Cenário | Efeito esperado |
|---|---|
| **Juros baixos** | Incentivo a risco → ↑ Ibovespa · ↓ Dólar |
| **Juros altos** | Migração para renda fixa → ↓ Ibovespa · ↑ Dólar |
| **Inflação alta** | Pressão cambial → ↑ Dólar |

Na prática, fatores externos (Fed, commodities, risco fiscal) podem distorcer essas relações — por isso o projeto mede a correlação empiricamente e não apenas teoricamente.

---

## Dependências principais

| Pacote | Uso |
|---|---|
| `yfinance` | Dados de mercado (Ibovespa, Dólar, DXY) |
| `pandas` / `numpy` | Manipulação de dados |
| `matplotlib` / `seaborn` | Visualização |
| `statsmodels` | Modelo ARIMA |
| `scikit-learn` | Regressão Linear + Random Forest |
| `scipy` | Teste de significância (p-value) |
| `requests` | API BCB + Telegram |
| `python-dotenv` | Leitura do `.env` |
| `reportlab` | Geração de PDF |

---

## Licença

MIT
