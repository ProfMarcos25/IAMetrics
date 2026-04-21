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

```powershell
# Conecte ao PostgreSQL como superusuário
psql -U postgres

# Dentro do psql, execute:
CREATE DATABASE frequencia_escolar ENCODING 'UTF8';
\q
```

### 2. Aplique o schema

```powershell
psql -U postgres -d frequencia_escolar -f database/schema.sql
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

### 2. Crie o ambiente virtual

```powershell
python -m venv .venv
```

### 3. Ative o ambiente virtual

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

> Após ativar, o prompt exibirá `(.venv)` no início.

### 4. Atualize o pip

```powershell
python -m pip install --upgrade pip
```

### 5. Instale as dependências

```powershell
pip install -r requirements.txt
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

# Linux / macOS
cp .env.example .env
```

### 2. Edite o arquivo `.env`

Abra `.env` em qualquer editor de texto e preencha:

```dotenv
# ── Banco de Dados ────────────────────────────────────────
# Substitua 'sua_senha' pela senha do seu usuário PostgreSQL
DB_URL=postgresql://postgres:sua_senha@localhost:5432/frequencia_escolar

# ── Twilio ────────────────────────────────────────────────
# Obtenha em: https://console.twilio.com/
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_NUMERO_ORIGEM=+5511999990000

# ── Telegram ──────────────────────────────────────────────
# Crie um bot via @BotFather no Telegram
TELEGRAM_BOT_TOKEN=0000000000:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

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
# Certifique-se de estar na raiz do projeto com o venv ativo
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Modo Produção

```powershell
cd backend
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
| `http://localhost:8000/app` | **Interface principal** (3 abas) |
| `http://localhost:8000/docs` | Documentação interativa **Swagger UI** |
| `http://localhost:8000/redoc` | Documentação **ReDoc** |
| `http://localhost:8000/` | Health-check da API |

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
