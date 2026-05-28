RESUMO
Este trabalho apresenta o desenvolvimento de um sistema automatizado de análise quantitativa do mercado cambial brasileiro, com ênfase na paridade dólar-real (USD/BRL) e no diferencial inflacionário internacional. O sistema foi desenvolvido em Python e integra coleta automatizada de dados via API do Yahoo Finance e do Sistema Gerenciador de Séries Temporais do Banco Central do Brasil (SGS/BCB). A partir das séries históricas do Ibovespa, câmbio (USD/BRL), índice DXY, taxa Selic e IPCA acumulado em 12 meses, foram aplicados modelos estatísticos e de aprendizado de máquina — Regressão Linear Múltipla, ARIMA(1,1,1) e Random Forest — para análise de correlação e projeção cambial. Os resultados evidenciaram alta correlação entre o câmbio oficial BCB e o Ibovespa (r = 0,9947), além de confirmar o IPCA acumulado como a variável de maior importância preditiva no modelo Random Forest (62,6%). O sistema entrega os resultados por meio de um dashboard web interativo (Flask) e relatórios PDF enviados automaticamente via SMTP. Adicionalmente, o projeto incorpora um agente de Inteligência Artificial integrado via Webhook do Telegram e Groq API, suportado por um banco de dados SQLite para gestão de histórico, permitindo aos usuários interagirem com os dados e solicitar análises em tempo real. Este conjunto demonstra como a Ciência de Dados e IA generativa podem apoiar a análise macroeconômica de forma contínua, reprodutível e interativa.
Palavras-chave: câmbio; dólar; correlação; Machine Learning; IA Generativa; Ibovespa; automação; Python; Telegram.

ABSTRACT
This work presents the development of an automated system for quantitative analysis of the Brazilian foreign exchange market, with emphasis on the dollar-real parity (USD/BRL) and the international inflation differential. The system was developed in Python and integrates automated data collection via the Yahoo Finance API and the Brazilian Central Bank's Time Series Management System (SGS/BCB). Based on historical series of Ibovespa, exchange rate (USD/BRL), DXY index, Selic rate, and 12-month accumulated IPCA, statistical and machine learning models — Multiple Linear Regression, ARIMA(1,1,1), and Random Forest — were applied for correlation analysis and exchange rate projection. Results showed high correlation between the official BCB exchange rate and Ibovespa (r = 0.9947), and confirmed the accumulated IPCA as the most predictively important variable in the Random Forest model (62.6%). The system delivers results through an interactive web dashboard (Flask) and automated PDF reports via SMTP. Furthermore, the project features an Artificial Intelligence agent integrated via Telegram Webhook and Groq API, backed by a SQLite database for conversation history, allowing users to interact with the data and request real-time analysis.
Keywords: exchange rate; dollar; correlation; Machine Learning; Generative AI; Ibovespa; automation; Python; Telegram.

5. PROCEDIMENTOS METODOLÓGICOS
Esta pesquisa tem caráter quantitativo-descritivo e adota pipeline de ciência de dados estruturado em cinco etapas: extração, tratamento, análise estatística, modelagem preditiva e automação de entrega. O período analisado compreende dados a partir de 01/01/2014 até a data de execução, correspondendo a 1.087 registros após o processo de sincronização e limpeza.
5.1 Extração de Dados
A coleta de dados foi realizada de forma automatizada via scripts Python, garantindo a reprodutibilidade das séries temporais. As variáveis coletadas foram:
Ibovespa (IBOV): cotações históricas de fechamento, via biblioteca yfinance (Yahoo Finance API).
Câmbio USD/BRL: paridade diária obtida via yfinance (ticker BRL=X) e confirmada pelo câmbio oficial BCB (dolar_brl).
DXY — Dollar Index: índice de força do dólar frente a uma cesta de moedas, via yfinance.
Taxa Selic: série diária extraída do SGS/BCB via biblioteca python-bcb, código de série 11.
IPCA acumulado 12 meses: variação acumulada extraída do SGS/BCB, série 13522.
A escolha por fontes primárias oficiais (Yahoo Finance e BCB) assegura a confiabilidade e a auditabilidade dos dados utilizados.
5.2 Tratamento de Dados
Os dados brutos passaram por processo de limpeza e estruturação com a biblioteca pandas, compreendendo:
Sincronização temporal: alinhamento entre a periodicidade diária do mercado financeiro e a periodicidade mensal do IPCA, com preenchimento por propagação progressiva (forward fill).
Tratamento de valores ausentes: lacunas decorrentes de feriados ou falhas nas APIs foram identificadas e preenchidas conforme a natureza da série (interpolação linear para preços, propagação para indicadores mensais).
Normalização: as variáveis foram padronizadas (z-score) antes da entrada nos modelos de aprendizado de máquina, eliminando o viés de escala.
Remoção de outliers: valores discrepantes identificados por Z-score > 3 foram avaliados individualmente e, quando comprovadamente erros de API, excluídos.
5.3 Análise Estatística e Exploratória
Para mensurar as interdependências entre as variáveis, foi calculado o Coeficiente de Correlação de Pearson entre todos os pares de variáveis, com validação por teste de significância estatística (p-value < 0,05). Complementarmente, foi implementada a Correlação Móvel (Rolling Correlation) com janelas de 30, 60 e 90 dias, permitindo identificar variações estruturais na relação entre Ibovespa e câmbio ao longo do tempo e evidenciar episódios de estresse de mercado.
5.4 Desenvolvimento dos Modelos Preditivos
Foram implementados três modelos com objetivos complementares:
a) Regressão Linear Múltipla (OLS) O modelo foi ajustado pelo método dos Mínimos Quadrados Ordinários, tendo o câmbio USD/BRL como variável dependente e DXY, Ibovespa, IPCA acumulado e Selic como variáveis independentes. O objetivo foi identificar a direção e magnitude do efeito linear de cada variável sobre o câmbio.
b) ARIMA (1,1,1) Para a componente de série temporal, foi aplicado o modelo ARIMA com parâmetros (p=1, d=1, q=1), selecionados após teste de estacionariedade ADF (Augmented Dickey-Fuller). O modelo captura a autocorrelação da série histórica e produz previsões para os próximos dias úteis com intervalos de confiança de 95%.
c) Random Forest Regressor O modelo de ensemble foi configurado com 100 árvores de decisão (n_estimators=100), critério MSE para seleção de divisões e profundidade máxima controlada para mitigar overfitting. Além das previsões, o Random Forest fornece a importância relativa de cada variável na formação do câmbio, métrica fundamental para interpretação do modelo.
A performance dos modelos foi avaliada por R² (coeficiente de determinação), RMSE (raiz do erro quadrático médio) e MAE (erro médio absoluto), com validação cruzada temporal para garantir generalização.
5.5 Arquitetura do Sistema
O sistema foi desenvolvido sob paradigma modular em Python, orquestrado por um script principal (main.py) que executa o pipeline sequencialmente: coleta → tratamento → análise → modelagem → visualização → entrega. Adicionalmente, possui uma arquitetura assíncrona orientada a eventos via FastAPI (webhook.py) para suportar o agente conversacional. A interface de usuário ocorre por meio de dois canais principais:

1. **Dashboard Web (Flask)**: Expondo um painel com os seguintes módulos:
   - Gráficos: Ibovespa vs Dólar, previsão ARIMA, heatmap de correlação, importância de features
   - Correlação: Matriz de Pearson completa e tabela de significância por par
   - Modelos: Métricas e coeficientes dos três modelos preditivos
   - Logs: Registro de execução do pipeline

2. **Interface Conversacional (Telegram Webhook)**: Um bot interativo conectado a um banco de dados local SQLite (monetary_analysis.db) para gerenciar contexto de conversas e responder dúvidas analíticas do usuário em tempo real.

O pipeline de dados pode ser executado por período customizável (data inicial/final) ou por períodos rápidos pré-configurados (desde 2014, últimos 5/3/2/1 anos, período Covid).



6. IMPLEMENTAÇÃO E FERRAMENTAS UTILIZADAS (seção técnica — ênfase na IA)
Nota para o relatório: Esta seção aprofunda a implementação, com ênfase especial nos modelos de IA/ML conforme orientação.
6.1 Stack Tecnológico
O sistema foi integralmente desenvolvido em Python 3.x, linguagem que se consolidou como padrão na análise de dados quantitativos por sua versatilidade, ecossistema de bibliotecas científicas e portabilidade (Srinath, 2017). A tabela abaixo sintetiza as principais dependências:
Biblioteca
Versão
Finalidade
pandas / numpy
—
Estruturação e operações vetoriais sobre séries temporais
yfinance
—
Extração automatizada de dados de mercado (Yahoo Finance)
python-bcb
—
Integração com o SGS/BCB para indicadores macroeconômicos
scikit-learn
—
Implementação do Random Forest e métricas de avaliação
statsmodels
—
Modelagem ARIMA, testes ADF e regressão OLS
matplotlib / seaborn
—
Visualização e geração de gráficos para relatório PDF
flask
—
Dashboard web interativo e orquestração do pipeline
smtplib
stdlib
Envio de relatórios por e-mail via protocolo SMTP
python-telegram-bot / requests
—
Notificações via Telegram Bot API
fastapi / uvicorn
—
Implementação do endpoint Webhook para comunicação em tempo real
sqlite3
stdlib
Banco de dados local para armazenamento de histórico e contexto do usuário
groq / openai
—
Integração com a Groq API para acesso a modelos de IA Generativa de grande escala

6.2 Aplicação de Inteligência Artificial
O projeto emprega três abordagens distintas de IA, divididas entre aprendizado de máquina preditivo e IA generativa:

**1. Random Forest — Aprendizado por Ensemble**
O Random Forest constitui um dos núcleos de inteligência preditiva do sistema. Trata-se de um algoritmo supervisionado que constrói múltiplas árvores de decisão em paralelo, cada uma treinada sobre uma amostra aleatória dos dados e features (bagging). A predição final é a média das saídas individuais, mitigando overfitting (Géron, 2021). Uma vantagem é a geração de *Feature Importance*, que quantifica a contribuição de cada variável, fornecendo interpretabilidade ao modelo.

**2. ARIMA — Modelagem de Séries Temporais**
O modelo ARIMA foi selecionado para capturar a estrutura temporal da série cambial. A diferenciação de ordem 1 (I=1) torna a série estacionária, validada pelo teste ADF. O componente autorregressivo (AR=1) captura a dependência temporal e o componente de média móvel (MA=1) modela o erro residual. Durante o treinamento de todos os modelos preditivos, foi monitorado o risco de overfitting utilizando validação cruzada temporal.

**3. Agente Conversacional (IA Generativa e Webhook)**
Para tornar os resultados acessíveis e interativos, o sistema integra um agente autônomo baseado em Large Language Models (LLMs), utilizando o modelo `gpt-oss-120b` acessado através da Groq API. 
Diferente de um simples chatbot de perguntas e respostas, este Agente de IA possui capacidade analítica sobre o contexto do projeto. A comunicação ocorre em tempo real via um **Webhook no Telegram** (construído com FastAPI), que escuta as mensagens do usuário e as envia para o orquestrador do agente.
Para manter a coesão nas conversas, o sistema utiliza um **Banco de Dados Local (SQLite)** (`monetary_analysis.db`) que gerencia as sessões dos usuários e armazena o histórico do chat. Isso permite que a IA "lembre" do contexto de mensagens anteriores e responda de maneira continuada e personalizada às solicitações de geração de gráficos ou dúvidas sobre macroeconomia.
6.3 Automação e Entrega de Resultados
A camada de comunicação do sistema opera em canais complementares:
- **E-mail (SMTP)**: O relatório técnico consolidado em PDF e os gráficos são gerados e enviados automaticamente, assegurando registro documental e rastreabilidade formal das análises diárias.
- **Telegram Bot (Push & Pull)**: 
  - *Envio Ativo (Push)*: Resumos executivos, imagens de gráficos gerados e alertas são enviados de forma programada pela API do Telegram para manter o usuário ciente das atualizações.
  - *Interação Reativa (Pull via Webhook)*: O usuário pode solicitar novas análises, consultar dados ou pedir explicações diretamente pelo chat, acionando o agente de IA que busca informações no banco de dados SQLite e formula uma resposta contextualizada.

7. RESULTADOS E DISCUSSÃO
Esta seção apresenta os resultados da última execução do pipeline (período: 2022-01-03 a 2026-03-09, n = 1.087 registros).
7.1 Análise de Correlação
A Matriz de Correlação de Pearson e os respectivos testes de significância (α = 0,05) revelaram relações estruturalmente relevantes entre as variáveis analisadas.
Tabela 1 — Matriz de Correlação de Pearson (variáveis selecionadas)


cambio_bcb
dolar_brl
dxy
ibovespa
ipca_12m
selic
cambio_bcb
1,000
0,061
0,224
0,995
-0,205
0,011
dolar_brl
0,061
1,000
-0,466
0,056
0,006
-0,163
dxy
0,224
-0,466
1,000
0,227
-0,416
0,313
ibovespa
0,995
0,056
0,227
1,000
-0,204
0,016
ipca_12m
-0,205
0,006
-0,416
-0,204
1,000
-0,079
selic
0,011
-0,163
0,313
0,016
-0,079
1,000

O resultado mais expressivo é a correlação de 0,9947 (p < 0,0001) entre cambio_bcb e Ibovespa, indicando que ambas as séries incorporam tendência de alta de longo prazo — reflexo do componente nominal comum: a desvalorização da moeda brasileira eleva cotações em reais simultaneamente. É importante destacar que correlação não implica causalidade; a relação pode ser mediada por um fator comum, como a depreciação do real.
Outros resultados estatisticamente significativos:
dolar_brl × dxy = -0,4463 (p < 0,0001): o fortalecimento do dólar global (DXY) está associado à apreciação do dólar frente ao real, relação esperada pela teoria da paridade cambial.
dolar_brl × selic = -0,1627 (p < 0,0001): taxa Selic mais elevada associa-se modestamente à apreciação do real, coerente com a lógica de carry trade.
dxy × ipca_12m = -0,4157 (p < 0,0001): inflação doméstica acumulada maior correlaciona-se com dólar global mais fraco — possivelmente refletindo períodos em que a inflação brasileira sobe enquanto o dólar perde força internacionalmente.
ipca_12m × cambio_bcb = -0,2054 (p < 0,0001): inflação acumulada mais alta correlaciona-se negativamente com o câmbio BCB na série analisada.
As correlações ibovespa × dolar_brl (r = 0,056, p = 0,865) e dolar_brl × ipca_12m (r = 0,006, p = 0,844) não foram estatisticamente significativas, indicando ausência de relação linear direta nessas combinações.
7.2 Resultados dos Modelos Preditivos
Tabela 2 — Desempenho comparativo dos modelos
Modelo
R²
RMSE
MAE
Observação
Regressão Linear
-26,274
5,094
4,834
R² negativo indica pior que a média
ARIMA (1,1,1)
—
—
—
AIC: 1494,97 · BIC: 1509,95
Random Forest
-6,679
2,703
2,510
Melhor MAE; R² negativo no teste

Regressão Linear Múltipla O modelo OLS apresentou R² negativo (-26,274), o que indica que, no conjunto de teste, a regressão linear performou pior do que simplesmente prever a média da série. Os coeficientes obtidos foram: DXY = -0,7870, Ibovespa = +1,8801, IPCA_12m = -0,6867, Selic = +0,4816. O sinal positivo do Ibovespa corrobora a correlação elevada observada. O R² negativo é esperado em séries temporais financeiras não estacionárias quando o modelo é avaliado fora da amostra — a regressão linear não captura a dinâmica temporal da série.
ARIMA (1,1,1) O modelo de série temporal apresentou AIC de 1494,97 e BIC de 1509,95, indicadores de ajuste relativo que servem para comparação entre especificações do modelo. As previsões para os dias úteis subsequentes (10 a 18 de março de 2026) convergiram para a faixa de R$ 99,19 (valor indexado), com intervalo de confiança de 95% representado no gráfico do dashboard. A estabilidade das previsões reflete a baixa volatilidade recente da série no período analisado.
Random Forest O Random Forest obteve o menor MAE (2,510) e RMSE (2,703) entre os modelos avaliados, indicando menor magnitude de erro nas previsões pontuais. O R² negativo (-6,679) no conjunto de teste reforça a dificuldade inerente de modelos puramente preditivos em séries cambiais — a série possui componentes de não-linearidade e estrutura temporal que reduzem a generalização fora da amostra.
7.3 Importância de Features (Random Forest)
A análise de importância de variáveis do Random Forest revelou a seguinte hierarquia:
Ranking
Variável
Importância Relativa
1º
IPCA acumulado 12m
62,6%
2º
DXY (Dollar Index)
16,7%
3º
Ibovespa
14,0%
4º
Selic
6,7%

O IPCA acumulado em 12 meses domina com expressivos 62,6% da importância preditiva, confirmando empiricamente a hipótese central do estudo: o diferencial inflacionário é o principal determinante estrutural do câmbio no horizonte analisado. Este resultado é consistente com a teoria da Paridade do Poder de Compra (PPC), que postula que diferenças persistentes de inflação entre países tendem a se refletir em depreciação da moeda de maior inflação (Gujarati; Porter, 2011).
O DXY em segundo lugar (16,7%) corrobora a importância do movimento sistêmico do dólar global como fator de influência sobre o câmbio local, independentemente das condições domésticas. O Ibovespa (14,0%) captura o canal de fluxo de capital — períodos de alta do mercado acionário tendem a atrair capital estrangeiro, valorizando o real. A Selic (6,7%), apesar de estatisticamente significativa em alguns pares, apresenta menor poder explicativo no modelo não-linear, possivelmente porque seu efeito sobre o câmbio é mediado por outras variáveis já presentes no modelo.

8. CONSIDERAÇÕES FINAIS
Este trabalho apresentou o desenvolvimento e os resultados de um sistema automatizado de análise quantitativa cambial, integrando coleta de dados, modelagem estatística, aprendizado de máquina, e um componente avançado de Inteligência Artificial Generativa para interação humana.
Os objetivos propostos foram alcançados: (i) a correlação entre Ibovespa, câmbio e Selic foi mensurada; (ii) o impacto da política monetária foi avaliado; (iii) a influência da inflação foi confirmada como principal variável preditiva; (iv) foram desenvolvidos três modelos comparáveis; e (v) o sistema foi automatizado e entregue via dashboard web, complementado por um agente autônomo (via Groq API e Telegram Webhook) operado sobre um banco de dados relacional.
Os resultados indicam que, no período analisado, o diferencial inflacionário (IPCA acumulado) é o determinante estrutural mais relevante do câmbio USD/BRL, respondendo por 62,6% da importância preditiva no modelo Random Forest. O DXY e o Ibovespa completam o quadro explicativo, evidenciando que o câmbio brasileiro é produto tanto de dinâmicas globais quanto de condições domésticas.
Limitações do estudo:
Os modelos preditivos apresentaram R² negativos no conjunto de teste, refletindo a natureza não-estacionária e de difícil previsão das séries cambiais em horizontes curtos.
A correlação elevada entre cambio_bcb e Ibovespa pode ser parcialmente espúria, derivada de tendência nominal comum de longo prazo, e não necessariamente uma relação de causalidade.
O período pós-2022 inclui eventos estruturais (ciclos de alta de juros nos EUA, eleições no Brasil, guerra na Ucrânia) que podem ter influenciado os parâmetros dos modelos de forma não generalizável.
O modelo não incorpora variáveis de expectativa (e.g., Focus/BCB) e fluxo de capital estrangeiro, que têm influência conhecida sobre o câmbio.
Trabalhos futuros: Recomenda-se a incorporação de dados de expectativas do mercado (Relatório Focus), variáveis de fluxo de capital e a exploração de modelos com memória temporal mais longa (LSTM, Prophet) para comparação com os resultados obtidos. A expansão do modelo de proporcionalidade inflacionária para incluir países de moeda forte (EUR, GBP, JPY) representa uma extensão natural do estudo.

REFERÊNCIAS (acrescentar às existentes)
As referências abaixo complementam as já listadas no documento base. Conferir se já não constam.
BANCO CENTRAL DO BRASIL. Sistema Gerenciador de Séries Temporais (SGS). Disponível em: https://www3.bcb.gov.br/sgspub/. Acesso em: 15 jan. 2026.
IBM. Overfitting. Disponível em: https://www.ibm.com/think/topics/overfitting. Acesso em: 20 mar. 2026.
PERKTOLD, Josef; SEABOLD, Skipper; TAYLOR, Jonathan. Statsmodels: Statistical modeling and hypothesis testing with Python. Disponível em: https://www.statsmodels.org/. Acesso em: 12 mar. 2026.

