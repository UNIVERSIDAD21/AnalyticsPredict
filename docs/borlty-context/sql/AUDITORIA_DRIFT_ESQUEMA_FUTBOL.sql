-- AUDITORIA_DRIFT_ESQUEMA_FUTBOL.sql
-- Consultas de auditoría para detectar drift y validar columnas canónicas.

-- 1) Columnas reales por tabla crítica fútbol
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='public'
  AND table_name IN ('apuestas_futbol','predicciones_futbol','calibradores_futbol','modelo_versiones_futbol')
ORDER BY table_name, ordinal_position;

-- 2) Verificar presencia de columnas canónicas esperadas en apuestas_futbol
SELECT
  EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='apuestas_futbol' AND column_name='cuota') AS tiene_cuota,
  EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='apuestas_futbol' AND column_name='probabilidad_sistema') AS tiene_probabilidad_sistema,
  EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='apuestas_futbol' AND column_name='confianza_sistema') AS tiene_confianza_sistema,
  EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='apuestas_futbol' AND column_name='ganancia') AS tiene_ganancia,
  EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='apuestas_futbol' AND column_name='resultado') AS tiene_resultado,
  EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='apuestas_futbol' AND column_name='casa_apuestas') AS tiene_casa_apuestas;

-- 3) Verificar columnas legacy conocidas
SELECT column_name
FROM information_schema.columns
WHERE table_schema='public'
  AND table_name='apuestas_futbol'
  AND column_name IN (
    'status','probabilidad','confianza','odds','cuota_decimal',
    'ganancia_real','ganancia_neta','beneficio_real','beneficio',
    'resultado_real','casa_apuesta'
  )
ORDER BY column_name;
