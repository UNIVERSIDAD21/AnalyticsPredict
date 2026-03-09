-- 02_dq_alerts_incremental.sql
-- Incremental para trazabilidad de reincidencia/cooldown en alertas drift

ALTER TABLE analytics.dq_alerts
  ADD COLUMN IF NOT EXISTS alerta_reincidente BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE analytics.dq_alerts
  ADD COLUMN IF NOT EXISTS first_occurrence_at TIMESTAMPTZ;

UPDATE analytics.dq_alerts
SET first_occurrence_at = COALESCE(first_occurrence_at, created_at)
WHERE first_occurrence_at IS NULL;
