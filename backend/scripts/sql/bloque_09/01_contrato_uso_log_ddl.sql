-- 01_contrato_uso_log_ddl.sql
-- Telemetría de uso por versión de contrato (v1 vs legacy)
-- PostgreSQL 14+

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.contrato_uso_log (
  id BIGSERIAL PRIMARY KEY,
  fecha DATE NOT NULL,
  domain TEXT NOT NULL CHECK (domain IN ('NBA', 'FUTBOL')),
  total_llamadas_v1 BIGINT NOT NULL DEFAULT 0 CHECK (total_llamadas_v1 >= 0),
  total_llamadas_legacy BIGINT NOT NULL DEFAULT 0 CHECK (total_llamadas_legacy >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (fecha, domain)
);

CREATE INDEX IF NOT EXISTS idx_contrato_uso_log_fecha
  ON analytics.contrato_uso_log (fecha DESC);

CREATE INDEX IF NOT EXISTS idx_contrato_uso_log_domain_fecha
  ON analytics.contrato_uso_log (domain, fecha DESC);
