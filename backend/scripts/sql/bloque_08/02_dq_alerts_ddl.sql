-- 02_dq_alerts_ddl.sql
-- Bloque 08 - Sistema operacional de alertas de calidad
-- PostgreSQL 14+

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.dq_alerts (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  periodo DATE NOT NULL,
  domain TEXT NOT NULL CHECK (domain IN ('NBA', 'FUTBOL')),
  alert_id TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('CRITICA', 'ALTA', 'MEDIA')),
  component TEXT NOT NULL,
  title TEXT NOT NULL,
  condition_text TEXT NOT NULL,
  incident_key TEXT NOT NULL,
  root_cause TEXT,
  status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'ACK', 'RESOLVED', 'SUPPRESSED')),
  emitted BOOLEAN NOT NULL DEFAULT TRUE,
  repeat_count INT NOT NULL DEFAULT 1,
  trigger_value NUMERIC,
  threshold_value NUMERIC,
  warning_type TEXT,
  warning_severity TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  resolved_at TIMESTAMPTZ,
  UNIQUE (periodo, domain, alert_id, incident_key)
);

CREATE INDEX IF NOT EXISTS idx_dq_alerts_active
  ON analytics.dq_alerts (domain, severity, status, periodo DESC)
  WHERE status IN ('OPEN', 'ACK');

CREATE INDEX IF NOT EXISTS idx_dq_alerts_alertid
  ON analytics.dq_alerts (alert_id, domain, periodo DESC);

CREATE INDEX IF NOT EXISTS idx_dq_alerts_incident
  ON analytics.dq_alerts (incident_key, domain, status, periodo DESC);
