"""
face_engine.py — Serviço de IA (Visão Computacional)
Responsabilidades:
  - Decodificar imagens Base64 enviadas pelo front-end
  - Detectar rostos com OpenCV
  - Gerar embeddings de 128 dimensões com face_recognition (dlib)
  - Nunca salvar imagens originais em disco; trabalhar apenas em memória
"""

import base64
import logging

import cv2
import face_recognition
import numpy as np

logger = logging.getLogger(__name__)

# ── Parâmetros de Detecção ────────────────────────────────────────────────────
# Modelo de detecção: "hog" é mais rápido; "cnn" é mais preciso (requer GPU)
# Referência: https://github.com/ageitgey/face_recognition
MODELO_DETECCAO = "hog"

# num_jitters: quantas vezes re-amostrar o rosto ao calcular o encoding.
# Valores maiores = mais preciso mas mais lento. 100 = praticamente perfeito.
# Use 1 na catraca (velocidade) e 5+ no cadastro (precisão máxima).
NUM_JITTERS_CATRACA  = 1
NUM_JITTERS_CADASTRO = 5


# ── Decodificação da Imagem ───────────────────────────────────────────────────

def _base64_para_array_bgr(imagem_base64: str) -> np.ndarray:
    """
    Converte uma string Base64 (com ou sem cabeçalho data URI) em um
    array NumPy BGR (formato OpenCV).

    Parâmetros:
        imagem_base64 — String Base64 enviada pelo front-end via fetch.

    Retorna:
        Array NumPy com a imagem no espaço de cor BGR.

    Lança:
        ValueError — se a string não puder ser decodificada como imagem válida.
    """
    # Remove o cabeçalho "data:image/jpeg;base64," caso presente
    if "," in imagem_base64:
        imagem_base64 = imagem_base64.split(",", 1)[1]

    try:
        dados_binarios = base64.b64decode(imagem_base64)
    except Exception as erro:
        raise ValueError(f"Base64 inválido: {erro}") from erro

    array_bytes = np.frombuffer(dados_binarios, dtype=np.uint8)
    imagem_bgr  = cv2.imdecode(array_bytes, cv2.IMREAD_COLOR)

    if imagem_bgr is None:
        raise ValueError("Não foi possível decodificar a imagem. Verifique o formato Base64.")

    return imagem_bgr


def _bgr_para_rgb(imagem_bgr: np.ndarray) -> np.ndarray:
    """Converte BGR (OpenCV) para RGB (face_recognition)."""
    return cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2RGB)


# ── Geração de Embedding ──────────────────────────────────────────────────────

def gerar_embedding(imagem_base64: str) -> list[float]:
    """
    Processa uma imagem Base64 e retorna o embedding facial de 128 dimensões.

    Fluxo:
        1. Decodifica o Base64 → array BGR em memória (sem salvar em disco).
        2. Converte para RGB.
        3. Detecta localizações dos rostos via face_recognition.
        4. Gera o vetor de 128 floats para o primeiro rosto encontrado.

    Parâmetros:
        imagem_base64 — Frame capturado pelo navegador, codificado em Base64.

    Retorna:
        Lista de 128 floats representando o embedding facial.

    Lança:
        ValueError — se nenhum rosto for detectado na imagem.
    """
    imagem_bgr = _base64_para_array_bgr(imagem_base64)
    imagem_rgb = _bgr_para_rgb(imagem_bgr)

    localizacoes = face_recognition.face_locations(
        imagem_rgb, model=MODELO_DETECCAO
    )

    if not localizacoes:
        raise ValueError("Nenhum rosto detectado na imagem enviada.")

    # Usa apenas o primeiro rosto detectado (frame de catraca = 1 pessoa)
    # num_jitters=NUM_JITTERS_CATRACA — prioriza velocidade no reconhecimento em tempo real
    embeddings = face_recognition.face_encodings(
        imagem_rgb,
        known_face_locations=localizacoes,
        num_jitters=NUM_JITTERS_CATRACA,
    )

    if not embeddings:
        raise ValueError("Não foi possível gerar o embedding para o rosto detectado.")

    embedding_principal = embeddings[0].tolist()
    logger.debug("Embedding gerado com %d dimensões.", len(embedding_principal))

    # A imagem_bgr sai de escopo aqui; o GC Python libera a memória automaticamente.
    return embedding_principal


# ── Cadastro de Novo Aluno ────────────────────────────────────────────────────

def processar_cadastro(imagem_base64: str) -> list[float]:
    """
    Atalho semântico para o cadastro de alunos: valida e retorna o embedding.

    Idêntico a gerar_embedding, mas com nome mais expressivo para uso no
    endpoint de cadastro, diferenciando do fluxo de reconhecimento de entrada.

    Parâmetros:
        imagem_base64 — Foto do aluno enviada no momento do cadastro.

    Retorna:
        Lista de 128 floats pronta para ser salva no banco de dados.
    """
    imagem_bgr = _base64_para_array_bgr(imagem_base64)
    imagem_rgb = _bgr_para_rgb(imagem_bgr)

    localizacoes = face_recognition.face_locations(imagem_rgb, model=MODELO_DETECCAO)

    if not localizacoes:
        raise ValueError("Nenhum rosto detectado na imagem de cadastro.")

    # num_jitters=NUM_JITTERS_CADASTRO — prioriza precisão máxima no cadastro
    embeddings = face_recognition.face_encodings(
        imagem_rgb,
        known_face_locations=localizacoes,
        num_jitters=NUM_JITTERS_CADASTRO,
    )

    if not embeddings:
        raise ValueError("Não foi possível gerar o embedding para o rosto de cadastro.")

    return embeddings[0].tolist()


# ── Detecção de Múltiplos Rostos (utilitário) ─────────────────────────────────

def detectar_rostos(imagem_base64: str) -> int:
    """
    Retorna a quantidade de rostos detectados em uma imagem Base64.

    Útil para validação no momento do cadastro (deve haver exatamente 1 rosto).

    Parâmetros:
        imagem_base64 — Imagem codificada em Base64.

    Retorna:
        Inteiro com o número de rostos detectados.
    """
    imagem_bgr = _base64_para_array_bgr(imagem_base64)
    imagem_rgb = _bgr_para_rgb(imagem_bgr)

    localizacoes = face_recognition.face_locations(
        imagem_rgb, model=MODELO_DETECCAO
    )
    return len(localizacoes)
