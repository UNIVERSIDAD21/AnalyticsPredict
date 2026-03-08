-- 01_dq_rule_results_ddl.sql
-- Bloque 08 - Persistencia de resultados de reglas de calidad
-- PostgreSQL 14+

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.dq_rule_results (
  id BIGSERIAL PRIMARY KEY,
  executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  periodo DATE NOT NULL,
  domain TEXT NOT NULL CHECK (domain IN ('NBA', 'FUTBOL')),
  rule_id TEXT NOT NULL,
  rule_name TEXT NOT NULL,
  category TEXT NOT NULL CHECK (
    category IN (
      'Completitud',
      'IntegridadLogica',
      'IntegridadTemporal',
      'RangosOutliers',
      'Freshness',
      'Coverage'
    )
  ),
  severity TEXT NOT NULL CHECK (severity IN ('Crítica', 'Alta', 'Media')),
  source_ref TEXT NOT NULL,
  failed_rows BIGINT NOT NULL DEFAULT 0 CHECK (failed_rows >= 0),
  total_rows BIGINT NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
  fail_rate NUMERIC(12, 8) NOT NULL DEFAULT 0,
  drift_signal_level TEXT NOT NULL DEFAULT 'none' CHECK (
    drift_signal_level IN ('none', 'yellow', 'orange', 'red')
  ),
  query_sql TEXT NOT NULL,
  UNIQUE (periodo, domain, rule_id)
);

CREATE INDEX IF NOT EXISTS idx_dq_rule_results_domain_periodo
  ON analytics.dq_rule_results (domain, periodo DESC);

CREATE INDEX IF NOT EXISTS idx_dq_rule_results_rule
  ON analytics.dq_rule_results (rule_id, domain, periodo DESC);

CREATE INDEX IF NOT EXISTS idx_dq_rule_results_severity
  ON analytics.dq_rule_results (severity, domain, periodo DESC);

CREATE INDEX IF NOT EXISTS idx_dq_rule_results_drift
  ON analytics.dq_rule_results (drift_signal_level, domain, periodo DESC);

CREATE TABLE IF NOT EXISTS analytics.dq_scorecard_daily (
  id BIGSERIAL PRIMARY KEY,
  calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  periodo DATE NOT NULL,
  domain TEXT NOT NULL CHECK (domain IN ('NBA', 'FUTBOL')),
  score_final NUMERIC(8, 4) NOT NULL,
  nivel TEXT NOT NULL CHECK (nivel IN ('A', 'B', 'C')),
  criticas_activas INT NOT NULL DEFAULT 0,
  drift_penalty NUMERIC(8, 4) NOT NULL DEFAULT 0,
  partial_penalty NUMERIC(8, 4) NOT NULL DEFAULT 0,
  componentes JSONB NOT NULL,
  overrides JSONB NOT NULL,
  UNIQUE (periodo, domain)
);

CREATE INDEX IF NOT EXISTS idx_dq_scorecard_daily_domain_periodo
  ON analytics.dq_scorecard_daily (domain, periodo DESC);
