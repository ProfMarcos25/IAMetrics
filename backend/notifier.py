"""
notifier.py — Serviço de Notificação
Responsabilidades:
  - Enviar mensagens de confirmação de presença ao responsável do aluno
  - Suportar três canais: SMS (Twilio), WhatsApp (Twilio) e Telegram Bot
  - Selecionar o canal correto com base no campo `canal_preferencial` do aluno
"""

import os
import logging
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configurações Twilio ──────────────────────────────────────────────────────
TWILIO_SID             = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN           = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_NUMERO_ORIGEM   = os.getenv("TWILIO_NUMERO_ORIGEM", "")

# ── Configurações Telegram ────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN", "")


# ── Montagem da Mensagem ──────────────────────────────────────────────────────

def _montar_mensagem(nome_aluno: str, turma: str, data_hora: datetime) -> str:
    """
    Formata a mensagem padrão enviada ao responsável.

    Parâmetros:
        nome_aluno — Nome completo do aluno.
        turma      — Turma do aluno.
        data_hora  — Momento do registro de presença.

    Retorna:
        String com a mensagem formatada.
    """
    horario = data_hora.strftime("%d/%m/%Y às %H:%M")
    return (
        f"✅ *Presença registrada!*\n"
        f"Aluno: {nome_aluno}\n"
        f"Turma: {turma}\n"
        f"Entrada: {horario}\n\n"
        f"_Sistema de Frequência Escolar_"
    )


# ── Canal: SMS (Twilio) ───────────────────────────────────────────────────────

def _enviar_sms(telefone_destino: str, mensagem: str) -> bool:
    """
    Envia uma mensagem SMS via Twilio.

    Parâmetros:
        telefone_destino — Número do responsável no formato internacional (+55...).
        mensagem         — Texto da mensagem.

    Retorna:
        True em caso de sucesso; False em caso de falha.
    """
    try:
        from twilio.rest import Client  # importação lazy para não bloquear outros canais

        cliente = Client(TWILIO_SID, TWILIO_TOKEN)
        mensagem_enviada = cliente.messages.create(
            body=mensagem,
            from_=TWILIO_NUMERO_ORIGEM,
            to=telefone_destino,
        )
        logger.info("SMS enviado. SID: %s", mensagem_enviada.sid)
        return True
    except Exception as erro:
        logger.error("Falha ao enviar SMS para %s: %s", telefone_destino, erro)
        return False


# ── Canal: WhatsApp (Twilio) ──────────────────────────────────────────────────

def _enviar_whatsapp(telefone_destino: str, mensagem: str) -> bool:
    """
    Envia uma mensagem via WhatsApp usando o canal Twilio Sandbox/Business.

    O prefixo 'whatsapp:' é exigido pela API Twilio para roteamento correto.

    Parâmetros:
        telefone_destino — Número do responsável no formato internacional (+55...).
        mensagem         — Texto da mensagem.

    Retorna:
        True em caso de sucesso; False em caso de falha.
    """
    try:
        from twilio.rest import Client

        cliente = Client(TWILIO_SID, TWILIO_TOKEN)
        mensagem_enviada = cliente.messages.create(
            body=mensagem,
            from_=f"whatsapp:{TWILIO_NUMERO_ORIGEM}",
            to=f"whatsapp:{telefone_destino}",
        )
        logger.info("WhatsApp enviado. SID: %s", mensagem_enviada.sid)
        return True
    except Exception as erro:
        logger.error("Falha ao enviar WhatsApp para %s: %s", telefone_destino, erro)
        return False


# ── Canal: Telegram Bot ───────────────────────────────────────────────────────

def _enviar_telegram(chat_id: str, mensagem: str) -> bool:
    """
    Envia uma mensagem via Telegram Bot API usando python-telegram-bot.

    Parâmetros:
        chat_id  — Chat ID do responsável obtido previamente via o bot.
        mensagem — Texto da mensagem (suporta Markdown).

    Retorna:
        True em caso de sucesso; False em caso de falha.
    """
    try:
        import asyncio
        from telegram import Bot

        async def _disparar():
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=chat_id,
                text=mensagem,
                parse_mode="Markdown",
            )

        asyncio.run(_disparar())
        logger.info("Telegram enviado para chat_id: %s", chat_id)
        return True
    except Exception as erro:
        logger.error("Falha ao enviar Telegram para chat_id %s: %s", chat_id, erro)
        return False


# ── Ponto de Entrada Principal ────────────────────────────────────────────────

def notificar_responsavel(aluno: dict, data_hora: datetime) -> bool:
    """
    Seleciona o canal preferencial do aluno e dispara a notificação.

    Parâmetros:
        aluno     — Dicionário com os dados do aluno (nome, turma, canal,
                    telefone_responsavel, telegram_chat_id).
        data_hora — Momento exato do registro de presença.

    Retorna:
        True se a mensagem foi enviada com sucesso; False caso contrário.
    """
    nome_aluno  = aluno.get("nome", "")
    turma       = aluno.get("turma", "")
    canal       = aluno.get("canal_preferencial", "WHATSAPP").upper()
    telefone    = aluno.get("telefone_responsavel", "")
    chat_id     = aluno.get("telegram_chat_id", "")

    mensagem = _montar_mensagem(nome_aluno, turma, data_hora)

    if canal == "SMS":
        return _enviar_sms(telefone, mensagem)

    if canal == "TELEGRAM":
        if not chat_id:
            logger.warning("Canal TELEGRAM selecionado mas telegram_chat_id está vazio para aluno %s.", aluno.get("id"))
            return False
        return _enviar_telegram(chat_id, mensagem)

    # Padrão: WHATSAPP
    return _enviar_whatsapp(telefone, mensagem)
