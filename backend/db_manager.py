"""
db_manager.py — Camada de Modelo (MVC)
Responsabilidades:
  - Gerenciar conexões com o PostgreSQL via psycopg2
  - Cadastrar e buscar alunos com seus embeddings faciais
  - Identificar aluno por comparação de Distância Euclidiana
  - Registrar presença com regra de bloqueio de duplicidade (30 min)
  - Fornecer dados agregados para o dashboard
"""
import os
import numpy as np
import face_recognition
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Configurações ─────────────────────────────────────────────────────────────
URL_BANCO              = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/frequencia_escolar")
UNIDADE_ESCOLAR        = os.getenv("UNIDADE_ESCOLAR", "Escola Estadual Jardim Iguatemi")
INTERVALO_DUPLICIDADE  = int(os.getenv("INTERVALO_DUPLICIDADE_MINUTOS", "30"))
LIMIAR_RECONHECIMENTO  = 0.55  # Distância Euclidiana máxima para aceitar identidade


# ── Conexão ───────────────────────────────────────────────────────────────────

def obter_conexao() -> psycopg.Connection:
    """Abre e retorna uma conexão com o banco de dados PostgreSQL."""
    # No psycopg3, usamos row_factory=dict_row no lugar de cursor_factory
    conexao = psycopg.connect(URL_BANCO, row_factory=dict_row)
    return conexao

# ── Alunos ────────────────────────────────────────────────────────────────────

def cadastrar_aluno(
    nome: str,
    turma: str,
    telefone_responsavel: str,
    embedding_facial: list[float],
    canal_preferencial: str = "WHATSAPP",
    telegram_chat_id: str | None = None,
) -> dict:
    """
    Insere um novo aluno no banco de dados.

    Parâmetros:
        nome                 — Nome completo do aluno.
        turma                — Código/nome da turma.
        telefone_responsavel — Número no formato internacional (+55...).
        embedding_facial     — Lista de 128 floats gerada pelo face_recognition.
        canal_preferencial   — 'SMS', 'WHATSAPP' ou 'TELEGRAM'.
        telegram_chat_id     — Chat ID do Telegram (obrigatório se canal = TELEGRAM).

    Retorna:
        Dicionário com os dados do aluno recém-cadastrado.
    """
    sql = """
        INSERT INTO alunos
            (nome, turma, telefone_responsavel, embedding_facial, canal_preferencial, telegram_chat_id)
        VALUES
            (%s, %s, %s, %s::REAL[], %s, %s)
        RETURNING *;
    """
    with obter_conexao() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (
                nome,
                turma,
                telefone_responsavel,
                embedding_facial,
                canal_preferencial,
                telegram_chat_id,
            ))
            aluno = dict(cursor.fetchone())
            conexao.commit()
    return aluno


def listar_alunos() -> list[dict]:
    """Retorna todos os alunos cadastrados com seus embeddings."""
    sql = "SELECT * FROM alunos ORDER BY nome;"
    with obter_conexao() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql)
            alunos = [dict(linha) for linha in cursor.fetchall()]
    return alunos


def buscar_aluno_por_id(aluno_id: int) -> dict | None:
    """Busca um aluno pelo seu ID primário."""
    sql = "SELECT * FROM alunos WHERE id = %s;"
    with obter_conexao() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (aluno_id,))
            linha = cursor.fetchone()
    return dict(linha) if linha else None


# ── Reconhecimento via face_recognition.face_distance() ──────────────────────
# Referência: https://github.com/ageitgey/face_recognition
# face_distance() calcula a Distância Euclidiana entre embeddings — é a função
# nativa e vetorizada da biblioteca, equivalente ao cálculo manual com numpy.

def identificar_aluno(embedding_desconhecido: list[float]) -> dict | None:
    """
    Compara o embedding recebido com todos os embeddings cadastrados usando
    face_recognition.face_distance() — função oficial da biblioteca ageitgey.

    face_distance() retorna um array de distâncias Euclidianas entre o vetor
    desconhecido e cada vetor cadastrado. Distâncias menores = mais parecido.
    O limiar padrão da biblioteca é 0.6; usamos 0.55 para maior rigor.

    Retorna:
        Dicionário do aluno identificado ou None se nenhum corresponder.
    """
    todos_alunos = listar_alunos()
    if not todos_alunos:
        return None

    alunos_validos = [
        aluno for aluno in todos_alunos
        if aluno.get("embedding_facial") and len(aluno["embedding_facial"]) == 128
    ]

    if not alunos_validos:
        return None

    # Monta matriz de embeddings cadastrados (shape: N x 128)
    embeddings_cadastrados = np.array(
        [aluno["embedding_facial"] for aluno in alunos_validos], dtype=np.float64
    )
    vetor_desconhecido = np.array(embedding_desconhecido, dtype=np.float64)

    # face_distance() — função oficial; retorna array de N distâncias Euclidianas
    distancias = face_recognition.face_distance(embeddings_cadastrados, vetor_desconhecido)

    indice_melhor = int(np.argmin(distancias))
    menor_distancia = float(distancias[indice_melhor])

    if menor_distancia <= LIMIAR_RECONHECIMENTO:
        melhor_aluno = alunos_validos[indice_melhor]
        melhor_aluno["distancia_reconhecimento"] = round(menor_distancia, 4)
        return melhor_aluno

    return None


# ── Registro de Presença ──────────────────────────────────────────────────────

def _verificar_duplicidade(aluno_id: int) -> bool:
    """
    Verifica se o aluno já teve presença registrada nos últimos
    INTERVALO_DUPLICIDADE minutos.

    Retorna:
        True  — registro duplicado, deve ser bloqueado.
        False — pode registrar nova presença.
    """
    janela_inicio = datetime.now() - timedelta(minutes=INTERVALO_DUPLICIDADE)
    sql = """
        SELECT id FROM registro_presencas
        WHERE aluno_id = %s
          AND data_hora >= %s
        LIMIT 1;
    """
    with obter_conexao() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (aluno_id, janela_inicio))
            registro = cursor.fetchone()
    return registro is not None


def registrar_presenca(aluno_id: int) -> dict:
    """
    Registra a entrada do aluno na unidade escolar.

    Aplica a regra de bloqueio de duplicidade: se o aluno já entrou nos
    últimos INTERVALO_DUPLICIDADE minutos, lança ValueError.

    Retorna:
        Dicionário com os dados do registro recém-criado.

    Lança:
        ValueError — se o registro for duplicado dentro da janela de tempo.
    """
    if _verificar_duplicidade(aluno_id):
        raise ValueError(
            f"Presença do aluno {aluno_id} já registrada nos últimos "
            f"{INTERVALO_DUPLICIDADE} minutos."
        )

    sql = """
        INSERT INTO registro_presencas (aluno_id, unidade_escolar)
        VALUES (%s, %s)
        RETURNING *;
    """
    with obter_conexao() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (aluno_id, UNIDADE_ESCOLAR))
            registro = dict(cursor.fetchone())
            conexao.commit()
    return registro


# ── Dashboard ─────────────────────────────────────────────────────────────────

def obter_presencas_por_hora(data: datetime | None = None) -> list[dict]:
    """
    Retorna o total de presenças agrupadas por hora para uma data específica.

    Parâmetros:
        data — Data desejada; usa a data atual quando None.

    Retorna:
        Lista de dicionários: [{"hora": 7, "total": 42}, ...]
    """
    data_consulta = (data or datetime.now()).date()
    sql = """
        SELECT
            EXTRACT(HOUR FROM data_hora)::INTEGER AS hora,
            COUNT(*)                              AS total
        FROM registro_presencas
        WHERE data_hora::DATE = %s
        GROUP BY 1
        ORDER BY 1;
    """
    with obter_conexao() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (data_consulta,))
            resultado = [dict(linha) for linha in cursor.fetchall()]
    return resultado


def obter_presencas_recentes(limite: int = 20) -> list[dict]:
    """
    Retorna os registros de presença mais recentes com nome e turma do aluno.

    Parâmetros:
        limite — Quantidade máxima de registros retornados.

    Retorna:
        Lista de dicionários com dados do aluno e horário de entrada.
    """
    sql = """
        SELECT
            rp.id,
            a.nome,
            a.turma,
            rp.data_hora,
            rp.unidade_escolar
        FROM registro_presencas rp
        JOIN alunos a ON a.id = rp.aluno_id
        ORDER BY rp.data_hora DESC
        LIMIT %s;
    """
    with obter_conexao() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (limite,))
            registros = [dict(linha) for linha in cursor.fetchall()]
    return registros
