-- ============================================================
-- SCHEMA DO BANCO DE DADOS — SISTEMA DE FREQUÊNCIA ESCOLAR
-- PostgreSQL 14+
-- Execute: psql -U postgres -d frequencia_escolar -f schema.sql
-- ============================================================

-- Cria o banco caso não exista (executar separadamente se necessário)
-- CREATE DATABASE frequencia_escolar ENCODING 'UTF8';

-- ── Tabela de Alunos ──────────────────────────────────────────────────────────
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
