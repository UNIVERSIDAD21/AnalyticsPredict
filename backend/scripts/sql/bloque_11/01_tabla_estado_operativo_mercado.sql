-- BLOQUE 11
-- Tabla canónica de estado operativo por mercado (fútbol)
-- Permite override gobernado/auditable sobre estado calculado por scorecard.

CREATE TABLE IF NOT EXISTS futbol_estado_operativo_mercado (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mercado VARCHAR(64) NOT NULL,
  estado_operativo VARCHAR(20) NOT NULL CHECK (estado_operativo IN ('BLOQUEADO','LABORATORIO','VALIDACION','PROMOCIONABLE')),
  fuente VARCHAR(32) NOT NULL DEFAULT 'scorecard', -- scorecard|manual|incidente
  motivos JSONB NOT NULL DEFAULT '[]'::jsonb,
  vigente_desde TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  vigente_hasta TIMESTAMPTZ NULL,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_futbol_estado_operativo_activo UNIQUE (mercado, vigente_hasta)
);

CREATE INDEX IF NOT EXISTS idx_futbol_estado_operativo_mercado
  ON futbol_estado_operativo_mercado(mercado);

CREATE INDEX IF NOT EXISTS idx_futbol_estado_operativo_activo
  ON futbol_estado_operativo_mercado(mercado, vigente_hasta)
  WHERE vigente_hasta IS NULL;
