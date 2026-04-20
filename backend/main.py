"""
main.py — Controller / API (FastAPI)
Endpoints:
  POST /cadastrar        — Cadastra novo aluno com foto
  POST /reconhecer       — Reconhece aluno e registra presença
  GET  /alunos           — Lista todos os alunos
  GET  /presencas/hoje   — Lista presenças do dia
  GET  /dashboard/fluxo  — Retorna total de presenças por hora (para Chart.js)
"""

import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import db_manager
import face_engine
import notifier

# ── Inicialização ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(aplicacao: FastAPI):
    """
    Evento de startup: valida os modelos .dat do face_recognition_models
    antes de aceitar requisições.
    Ref: https://github.com/ageitgey/face_recognition_models
    """
    logger.info("Iniciando validação dos modelos face_recognition_models...")
    face_engine.validar_modelos()
    logger.info("Todos os modelos validados. API pronta.")
    yield

app = FastAPI(
    title="Sistema de Frequência Escolar — IA",
    description="API REST para controle de presença via reconhecimento facial.",
    version="1.0.0",
    lifespan=lifespan,
)

# Permite requisições do front-end (mesmo domínio ou localhost de dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve os arquivos estáticos do front-end em /app
app.mount("/app", StaticFiles(directory="../frontend", html=True), name="frontend")


# ── Schemas (Pydantic) ────────────────────────────────────────────────────────

class SchemaCadastroAluno(BaseModel):
    nome:                 str = Field(..., min_length=3, max_length=150, example="João da Silva")
    turma:                str = Field(..., min_length=1, max_length=20,  example="3A")
    telefone_responsavel: str = Field(..., min_length=8, max_length=20,  example="+5511999990000")
    imagem_base64:        str = Field(..., description="Foto do aluno em Base64 (JPEG/PNG)")
    canal_preferencial:   str = Field(default="WHATSAPP", pattern="^(SMS|WHATSAPP|TELEGRAM)$")
    telegram_chat_id:     str | None = Field(default=None)


class SchemaReconhecimento(BaseModel):
    imagem_base64: str = Field(..., description="Frame da câmera em Base64 (JPEG)")


class SchemaRespostaReconhecimento(BaseModel):
    reconhecido:    bool
    aluno_id:       int | None
    nome:           str | None
    turma:          str | None
    data_hora:      str | None
    mensagem:       str


class SchemaFluxoHora(BaseModel):
    hora:  int
    total: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Sistema"])
def raiz():
    """Health-check básico da API."""
    return {"status": "online", "sistema": "Frequência Escolar IA", "versao": "1.0.0"}


@app.post(
    "/cadastrar",
    status_code=status.HTTP_201_CREATED,
    tags=["Alunos"],
    summary="Cadastra novo aluno com embedding facial",
)
def cadastrar_aluno(payload: SchemaCadastroAluno):
    """
    Recebe os dados do aluno e sua foto em Base64.
    Gera o embedding facial e salva tudo no banco de dados.
    A imagem original NÃO é armazenada.
    """
    # Valida que há exatamente 1 rosto na foto
    quantidade_rostos = face_engine.detectar_rostos(payload.imagem_base64)
    if quantidade_rostos == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nenhum rosto detectado na imagem. Tente uma foto mais nítida.",
        )
    if quantidade_rostos > 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Detectados {quantidade_rostos} rostos. Envie uma foto individual.",
        )

    try:
        embedding = face_engine.processar_cadastro(payload.imagem_base64)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro))

    aluno = db_manager.cadastrar_aluno(
        nome                 = payload.nome,
        turma                = payload.turma,
        telefone_responsavel = payload.telefone_responsavel,
        embedding_facial     = embedding,
        canal_preferencial   = payload.canal_preferencial,
        telegram_chat_id     = payload.telegram_chat_id,
    )

    logger.info("Aluno cadastrado: %s (id=%s)", aluno["nome"], aluno["id"])
    # Remove embedding da resposta para não trafegar 128 floats desnecessariamente
    aluno.pop("embedding_facial", None)
    return {"mensagem": "Aluno cadastrado com sucesso!", "aluno": aluno}


@app.post(
    "/reconhecer",
    response_model=SchemaRespostaReconhecimento,
    tags=["Catraca"],
    summary="Reconhece aluno pelo rosto e registra presença",
)
def reconhecer_aluno(payload: SchemaReconhecimento):
    """
    Processa um frame da câmera:
    1. Gera embedding do rosto.
    2. Compara com os embeddings cadastrados (Distância Euclidiana).
    3. Registra presença se identificado e dentro da janela permitida.
    4. Dispara notificação assíncrona ao responsável.
    """
    # Gera embedding do frame recebido
    try:
        embedding_capturado = face_engine.gerar_embedding(payload.imagem_base64)
    except ValueError as erro:
        return SchemaRespostaReconhecimento(
            reconhecido=False,
            aluno_id=None,
            nome=None,
            turma=None,
            data_hora=None,
            mensagem=str(erro),
        )

    # Identifica o aluno
    aluno = db_manager.identificar_aluno(embedding_capturado)
    if not aluno:
        return SchemaRespostaReconhecimento(
            reconhecido=False,
            aluno_id=None,
            nome=None,
            turma=None,
            data_hora=None,
            mensagem="Rosto não reconhecido.",
        )

    # Registra a presença (pode ser bloqueada por duplicidade)
    try:
        registro = db_manager.registrar_presenca(aluno["id"])
    except ValueError as erro:
        return SchemaRespostaReconhecimento(
            reconhecido=True,
            aluno_id=aluno["id"],
            nome=aluno["nome"],
            turma=aluno["turma"],
            data_hora=None,
            mensagem=str(erro),
        )

    data_hora_registro = registro["data_hora"]

    # Notifica o responsável (falha silenciosa: não bloqueia a catraca)
    try:
        notifier.notificar_responsavel(aluno, data_hora_registro)
    except Exception as erro_notif:
        logger.warning("Falha na notificação do aluno %s: %s", aluno["id"], erro_notif)

    logger.info("Presença registrada — aluno: %s, horário: %s", aluno["nome"], data_hora_registro)

    return SchemaRespostaReconhecimento(
        reconhecido=True,
        aluno_id=aluno["id"],
        nome=aluno["nome"],
        turma=aluno["turma"],
        data_hora=data_hora_registro.isoformat(),
        mensagem=f"Bem-vindo(a), {aluno['nome']}! Presença registrada.",
    )


@app.get(
    "/alunos",
    tags=["Alunos"],
    summary="Lista todos os alunos cadastrados",
)
def listar_alunos():
    """Retorna a lista completa de alunos sem os embeddings faciais."""
    alunos = db_manager.listar_alunos()
    for aluno in alunos:
        aluno.pop("embedding_facial", None)
    return {"total": len(alunos), "alunos": alunos}


@app.get(
    "/presencas/hoje",
    tags=["Presenças"],
    summary="Lista as presenças registradas no dia atual",
)
def presencas_hoje():
    """Retorna os registros mais recentes do dia (máx. 200 registros)."""
    registros = db_manager.obter_presencas_recentes(limite=200)
    return {"total": len(registros), "registros": registros}


@app.get(
    "/dashboard/fluxo",
    response_model=list[SchemaFluxoHora],
    tags=["Dashboard"],
    summary="Total de presenças por hora para gráfico",
)
def fluxo_por_hora(data: str | None = None):
    """
    Retorna o total de presenças agrupadas por hora.

    Parâmetros de query:
        data — Data no formato YYYY-MM-DD (opcional; padrão = hoje).

    Retorna:
        Lista de objetos {hora: int, total: int} para alimentar o Chart.js.
    """
    data_obj = None
    if data:
        try:
            data_obj = datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data inválido. Use YYYY-MM-DD.",
            )

    resultado = db_manager.obter_presencas_por_hora(data_obj)
    return resultado
