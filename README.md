# 🎓 FrequêncIA — Sistema de Controle de Presença Escolar com IA

> Reconhecimento facial em tempo real para registro automático de frequência, notificação de responsáveis e dashboard de fluxo diário.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue?logo=postgresql)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-red?logo=opencv)
![License](https://img.shields.io/badge/Licença-MIT-lightgrey)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Projeto](#arquitetura-do-projeto)
3. [Pré-requisitos](#pré-requisitos)
4. [Instalação das Dependências do Sistema](#instalação-das-dependências-do-sistema)
5. [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
6. [Configuração do Ambiente Python](#configuração-do-ambiente-python)
7. [Variáveis de Ambiente (.env)](#variáveis-de-ambiente-env)
8. [Configuração dos Serviços de Notificação](#configuração-dos-serviços-de-notificação)
9. [Executando o Servidor](#executando-o-servidor)
10. [Acessando o Front-End](#acessando-o-front-end)
11. [Endpoints da API](#endpoints-da-api)
12. [Fluxo de Uso do Sistema](#fluxo-de-uso-do-sistema)
13. [Solução de Problemas](#solução-de-problemas)
14. [Considerações de Segurança](#considerações-de-segurança)

---

## Visão Geral

O **FrequêncIA** é um sistema escolar que substitui o controle manual de chamada por reconhecimento facial automatizado. Ao entrar na escola, o aluno passa diante de uma câmera; o sistema:

1. **Detecta** o rosto via OpenCV
2. **Gera** um vetor de 128 dimensões (embedding) com `face_recognition` (dlib)
3. **Compara** o vetor com os cadastrados no banco via Distância Euclidiana
4. **Registra** a presença no PostgreSQL (com bloqueio de duplicidade de 30 min)
5. **Notifica** o responsável via WhatsApp, SMS ou Telegram

---

## Arquitetura do Projeto


<img width="451" height="382" alt="image" src="https://github.com/user-attachments/assets/099f4cf9-1fb9-4075-8b3f-7a9a86af8b91" />


## Descrição da aquitetura

```
IAMetrics/
├── requirements.txt          # Dependências Python
├── .env.example              # Template de variáveis de ambiente
├── database/
│   └── schema.sql            # Tabelas, índices e views PostgreSQL
├── backend/                  # Camada Back-End (MVC)
│   ├── main.py               # Controller — API FastAPI (5 endpoints)
│   ├── db_manager.py         # Model — Banco de dados e lógica de negócio
│   ├── face_engine.py        # Serviço de IA — OpenCV + face_recognition
│   └── notifier.py           # Serviço de Notificação — Twilio / Telegram
└── frontend/                 # Camada Front-End (View)
    ├── index.html             # Interface com 3 abas
    ├── style.css              # Design institucional responsivo
    └── app.js                 # Câmera, reconhecimento e Chart.js
```

### Padrão MVC

| Camada | Arquivo | Responsabilidade |
|--------|---------|-----------------|
| **Model** | `db_manager.py` | Persistência, comparação vetorial, regra de duplicidade |
| **View** | `frontend/` | Interface do usuário, câmera, gráficos |
| **Controller** | `main.py` | Roteamento HTTP, orquestração dos serviços |
| **IA Service** | `face_engine.py` | Decodificação Base64, geração de embeddings |
| **Notif. Service** | `notifier.py` | Envio de mensagens por canal preferencial |

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

| Software | Versão Mínima | Download |
|----------|--------------|---------|
| Python | 3.10 | https://www.python.org/downloads/ |
| PostgreSQL | 14 | https://www.postgresql.org/download/ |
| CMake | 3.20+ | https://cmake.org/download/ *(necessário para dlib)* |
| Visual C++ Build Tools | 2019+ | https://visualstudio.microsoft.com/visual-cpp-build-tools/ *(Windows)* |
| Git | qualquer | https://git-scm.com/ |

> **Atenção (Windows):** A biblioteca `face_recognition` depende do `dlib`, que precisa ser compilada. O CMake e o Visual C++ Build Tools são **obrigatórios** no Windows antes de instalar.

---

## Instalação das Dependências do Sistema

### Windows

```powershell
# 1. Instale o CMake (marque "Add CMake to PATH" no instalador)
# 2. Instale o Visual C++ Build Tools
# 3. Verifique as instalações:
cmake --version
python --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y build-essential cmake libopenblas-dev liblapack-dev \
                   libx11-dev libgtk-3-dev python3-dev python3-pip
```

### macOS

```bash
brew install cmake
brew install python@3.11
```

---

## Configuração do Banco de Dados

### 1. Crie o banco de dados



### 3. Criar o banco de dados

--> No PostegreSql , Abra o pgadmin
1. Procure PgAdmin no Computador

<img width="865" height="757" alt="image" src="https://github.com/user-attachments/assets/60715683-6f2b-435d-867a-9f6f1f606a9e" />


1.1 
<img width="749" height="595" alt="image" src="https://github.com/user-attachments/assets/f44364b4-8911-45a8-9c51-194cd4dd117f" />



2. Acesse o Postegree recente a senha de acesso é 1234

   <img width="545" height="399" alt="image" src="https://github.com/user-attachments/assets/fe86c4c6-49f0-4932-b8fc-d6998dce5c0e" />

2.1 clique com o Botao direito em Database


   <img width="638" height="377" alt="image" src="https://github.com/user-attachments/assets/62061b60-2cbd-49ff-98b2-f1d043e11f5d" />

   
2.2 Insira o nome do seu Database


   <img width="696" height="550" alt="image" src="https://github.com/user-attachments/assets/b95ea6fd-6112-490c-8301-d194cf949cb5" />

   
2.2 Clique em Save


   <img width="698" height="552" alt="image" src="https://github.com/user-attachments/assets/1144808f-394d-42c4-9e41-a82883f7d965" />

   
3. Clique no Database Criado com o botao direito:


<img width="495" height="498" alt="image" src="https://github.com/user-attachments/assets/eba19eae-3018-4632-9540-bcfa390dacdd" />


3.1 Clique no Database Criado com o botao direito e selecione QueryTols:

   <img width="413" height="486" alt="image" src="https://github.com/user-attachments/assets/2b56cb1a-6711-4f28-8e47-f2738072c6cc" />

### 2. Aplique o schema

```powershell
CREATE TABLE IF NOT EXISTS alunos (
    id                    SERIAL PRIMARY KEY,
    nome                  VARCHAR(150)    NOT NULL,
    turma                 VARCHAR(20)     NOT NULL,
    telefone_responsavel  VARCHAR(20)     NOT NULL,
    -- Vetor de 128 dimensões gerado pelo face_recognition (dlib)
    embedding_facial      REAL[]          NOT NULL,
    -- Canal preferencial de notificação: 'SMS', 'WHATSAPP' ou 'TELEGRAM'
    canal_preferencial    VARCHAR(10)     NOT NULL DEFAULT 'WHATSAPP'
                              CHECK (canal_preferencial IN ('SMS', 'WHATSAPP', 'TELEGRAM')),
    -- Chat ID do Telegram, preenchido quando canal_preferencial = 'TELEGRAM'
    telegram_chat_id      VARCHAR(50),
    criado_em             TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Comentários descritivos para documentação
COMMENT ON TABLE  alunos                        IS 'Cadastro de alunos com dados de contato e vetor facial';
COMMENT ON COLUMN alunos.embedding_facial       IS 'Array de 128 floats gerado pelo dlib/face_recognition';
COMMENT ON COLUMN alunos.canal_preferencial     IS 'Canal de envio da notificação ao responsável';

-- ── Tabela de Registros de Presença ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registro_presencas (
    id               SERIAL PRIMARY KEY,
    aluno_id         INTEGER     NOT NULL
                         REFERENCES alunos (id) ON DELETE CASCADE,
    data_hora        TIMESTAMP   NOT NULL DEFAULT NOW(),
    unidade_escolar  VARCHAR(100) NOT NULL
);

COMMENT ON TABLE  registro_presencas              IS 'Log de entradas reconhecidas pela câmera';
COMMENT ON COLUMN registro_presencas.data_hora    IS 'Momento exato do reconhecimento facial';

-- ── Índices para Consultas Frequentes ────────────────────────────────────────
-- Busca de presenças por aluno (verificação de duplicidade e relatórios)
CREATE INDEX IF NOT EXISTS idx_presencas_aluno_id
    ON registro_presencas (aluno_id);

-- Busca por período (dashboard diário / por hora)
CREATE INDEX IF NOT EXISTS idx_presencas_data_hora
    ON registro_presencas (data_hora);

-- Busca combinada: aluno + período (verificação de duplicidade de 30 min)
CREATE INDEX IF NOT EXISTS idx_presencas_aluno_data
    ON registro_presencas (aluno_id, data_hora DESC);

-- ── View: Presenças por Hora (usada pelo endpoint do dashboard) ───────────────
CREATE OR REPLACE VIEW vw_presencas_por_hora AS
SELECT
    DATE_TRUNC('hour', data_hora)                   AS hora,
    EXTRACT(HOUR FROM data_hora)::INTEGER           AS hora_numero,
    COUNT(*)                                        AS total_presencas
FROM registro_presencas
WHERE data_hora::DATE = CURRENT_DATE
GROUP BY 1, 2
ORDER BY 1;

COMMENT ON VIEW vw_presencas_por_hora IS 'Agregação diária de entradas por hora para o dashboard';

```

Esse script criará:

- **Tabela `alunos`** — dados cadastrais + embedding facial (128 floats)
- **Tabela `registro_presencas`** — log de entradas com timestamp
- **Índices** de performance para consultas por aluno e período
- **View `vw_presencas_por_hora`** — agregação para o dashboard

### 3. Verifique as tabelas

```powershell
psql -U postgres -d frequencia_escolar -c "\dt"
```

Saída esperada:
```
          List of relations
 Schema |        Name         | Type  
--------+---------------------+-------
 public | alunos              | table 
 public | registro_presencas  | table 
```

---

## Configuração do Ambiente Python

### 1. Clone o repositório (se ainda não o fez)

```powershell
git clone https://github.com/ProfMarcos25/IAMetrics.git
cd IAMetrics
```

```powershell
cd IAMetrics
```

### 2. Crie o ambiente virtual

```powershell
py -m venv .venv
```

### 3. Ative o ambiente virtual

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

```powershell
# Windows (CMD)
.venv\Scripts\activate.bat
```

> Após ativar, o prompt exibirá `(.venv)` no início.

### 4. Atualize o pip

```powershell
py -m pip install --upgrade pip
```

### 5. Instale as dependências

```powershell
py -m pip install -r requirements.txt
```

> ⏳ A instalação do `dlib` (compilação nativa) pode levar de **5 a 15 minutos**. Isso é normal.


### 6. Verifique a instalação

```powershell
python -c "import face_recognition; import cv2; import fastapi; print('OK — todas as bibliotecas carregadas!')"
```

---

## Variáveis de Ambiente (.env)

### 1. Copie o arquivo de exemplo

```powershell
# Windows
copy .env.example .env
```

### 2. Edite o arquivo `.env`

Abra `.env` em qualquer editor de texto e preencha:

```dotenv
# ── Banco de Dados ────────────────────────────────────────
# Substitua 'sua_senha' pela senha do seu usuário PostgreSQL
DB_URL=postgresql://postgres:1234@localhost:5432/frequencia_escolar

# ── Twilio ────────────────────────────────────────────────
# Obtenha em: https://console.twilio.com/
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_NUMERO_ORIGEM=+5511999990000

# ── Telegram ──────────────────────────────────────────────
# Crie um bot via @BotFather no Telegram
TELEGRAM_BOT_TOKEN=8756218296:AAGjYY8tCs0rmFY0d_4dNsixZxWIL-ffIwQ
TELEGRAM_CHAT_ID=634033523

# ── Sistema ───────────────────────────────────────────────
UNIDADE_ESCOLAR=Escola Estadual Jardim Iguatemi
INTERVALO_DUPLICIDADE_MINUTOS=30
```

> ⚠️ **Nunca** commite o arquivo `.env` no repositório. Ele já está no `.gitignore`.

---

## Configuração dos Serviços de Notificação

### Opção A — WhatsApp / SMS via Twilio

1. Acesse [console.twilio.com](https://console.twilio.com/) e crie uma conta gratuita
2. Ative o **Twilio Sandbox for WhatsApp** (em Messaging → Try it out)
3. Cada responsável deve enviar a mensagem de adesão ao sandbox uma vez
4. Copie o **Account SID**, **Auth Token** e o número Twilio para o `.env`

### Opção B — Telegram Bot

1. Abra o Telegram e pesquise por **@BotFather**
2. Envie `/newbot`, escolha nome e username para o bot
3. Copie o token fornecido para `TELEGRAM_BOT_TOKEN` no `.env`
4. Para obter o **Chat ID** de cada responsável:
   - O responsável envia qualquer mensagem para o bot
   - Acesse: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - O `chat.id` aparecerá no JSON — preencha no campo `telegram_chat_id` ao cadastrar o aluno

---

## Executando o Servidor

### Modo Desenvolvimento (com hot-reload)

```powershell
cd backend
```

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Modo Produção

```powershell
cd backend
```

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Saída esperada no terminal:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX]
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Acessando o Front-End

Com o servidor rodando, abra no navegador:

| URL | Descrição |
|-----|-----------|
| `http://localhost:8000/app`   | **Interface principal** (3 abas) |
| `http://localhost:8000/docs`  | Documentação interativa **Swagger UI** |
| `http://localhost:8000/redoc` | Documentação **ReDoc** |
| `http://localhost:8000/`      | Health-check da API |

### Abas da Interface

| Aba | Função |
|-----|--------|
| �� **Catraca Virtual** | Câmera ao vivo, reconhecimento automático a cada 2,5s, feed de entradas recentes |
| 📊 **Dashboard de Gestão** | Gráfico de fluxo por hora (Chart.js), métricas de total e hora de pico |
| ➕ **Cadastrar Aluno** | Formulário + captura de foto para registrar novo aluno |

---

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Health-check |
| `POST` | `/cadastrar` | Cadastra aluno com embedding facial |
| `POST` | `/reconhecer` | Reconhece rosto e registra presença |
| `GET` | `/alunos` | Lista todos os alunos |
| `GET` | `/presencas/hoje` | Presenças do dia (máx. 200) |
| `GET` | `/dashboard/fluxo` | Total por hora (`?data=YYYY-MM-DD`) |

### Exemplo — Cadastrar Aluno (curl)

```bash
curl -X POST http://localhost:8000/cadastrar \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Maria da Silva",
    "turma": "5A",
    "telefone_responsavel": "+5511999990000",
    "imagem_base64": "<BASE64_DA_FOTO>",
    "canal_preferencial": "WHATSAPP"
  }'
```

### Exemplo — Reconhecer (curl)

```bash
curl -X POST http://localhost:8000/reconhecer \
  -H "Content-Type: application/json" \
  -d '{"imagem_base64": "<BASE64_DO_FRAME>"}'
```

---

## Fluxo de Uso do Sistema

```
1. CADASTRO
   └─ Acesse a aba "Cadastrar Aluno"
   └─ Preencha nome, turma, telefone e canal de notificação
   └─ Clique em "Abrir Câmera" → "Capturar Foto" → "Cadastrar Aluno"
   └─ O embedding é gerado e salvo; a foto NÃO é armazenada

2. OPERAÇÃO DIÁRIA (Catraca)
   └─ Acesse a aba "Catraca Virtual"
   └─ Clique em "Iniciar Câmera"
   └─ O sistema captura frames a cada 2,5 segundos automaticamente
   └─ Ao reconhecer: registra presença + notifica responsável
   └─ Duplicidade bloqueada por 30 minutos por aluno

3. ACOMPANHAMENTO (Dashboard)
   └─ Acesse a aba "Dashboard de Gestão"
   └─ Selecione a data desejada e clique em "Atualizar"
   └─ Visualize o gráfico de barras com entradas por hora
```

---

* --------------------------------------------------------------------------- *
*                           COMANDOS - SQL                                    *  
* --------------------------------------------------------------------------- *



UPDATE public.alunos 
SET telefone_responsavel = '+551199999999999' 
WHERE id = 1;


SELECT id, nome, turma, telefone_responsavel, embedding_facial, canal_preferencial, telegram_chat_id, criado_em
	FROM public.alunos;

DELETE FROM nome_da_tabela WHERE id = 1;
	

## Solução de Problemas

### ❌ `dlib` falha na instalação (Windows)

```powershell
# Instale manualmente a wheel pré-compilada
pip install dlib==19.24.2
# Se ainda falhar, instale via conda:
conda install -c conda-forge dlib
```

### ❌ `face_recognition` não encontra rostos

- Garanta boa iluminação no ambiente
- Use fotos frontais e nítidas no cadastro
- O parâmetro `MODELO_DETECCAO` em `face_engine.py` pode ser alterado de `"hog"` para `"cnn"` para maior precisão (requer GPU)

### ❌ Erro de conexão com PostgreSQL

```powershell
# Verifique se o serviço está rodando (Windows)
Get-Service postgresql*

# Linux / macOS
sudo systemctl status postgresql
```

Confirme que `DB_URL` no `.env` contém a senha correta e o banco `frequencia_escolar` existe.

### ❌ Câmera não abre no navegador

- O navegador exige **HTTPS** para `getUserMedia` em produção
- Em desenvolvimento (`localhost`), HTTP é permitido
- Verifique se outra aplicação não está usando a câmera

### ❌ Notificação Twilio não enviada

- Confirme que o número de destino está no formato `+55XXXXXXXXXXX`
- No plano trial do Twilio, apenas números verificados recebem mensagens
- Verifique os logs em: https://console.twilio.com/us1/monitor/logs/sms

---

## Considerações de Segurança

| Aspecto | Implementação |
|---------|--------------|
| **Privacidade** | Imagens originais nunca são salvas em disco; apenas vetores numéricos |
| **Variáveis sensíveis** | Tokens e senhas ficam exclusivamente no `.env` (fora do Git) |
| **Anti-duplicidade** | Janela de 30 min configurável impede registros repetidos acidentais |
| **CORS** | Configure `allow_origins` em `main.py` para o domínio real em produção |
| **Banco de dados** | Use um usuário PostgreSQL dedicado com permissões mínimas (não `postgres`) |

---

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais no contexto do **Programa de Modernização Escolar — Jardim Iguatemi, 2026**.

---

*Desenvolvido com ❤️ por **ProfMarcos25** ·  v1.0.0 · Abril/2026*
