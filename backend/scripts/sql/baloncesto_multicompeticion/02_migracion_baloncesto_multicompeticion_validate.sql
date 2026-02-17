-- ============================================================================
-- VALIDACION POST-MIGRACION: BALONCESTO MULTI-COMPETICION
-- ============================================================================
-- Esta validacion verifica:
-- - Competiciones NBA y Euroliga.
-- - Migracion de 30 equipos NBA.
-- - Integridad referencial en temporadas/partidos/predicciones/apuestas.
-- - Reglas de IDs Sofascore (NBA NULL, Euroliga=138).
-- - Planes de consulta para casos de uso comunes.
-- ============================================================================

BEGIN;

-- --------------------------------------------------------------------------
-- 0) Presencia de tablas clave
-- --------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.competiciones_baloncesto') IS NULL THEN
        RAISE EXCEPTION 'Falta tabla public.competiciones_baloncesto';
    END IF;
    IF to_regclass('public.equipos_baloncesto') IS NULL THEN
        RAISE EXCEPTION 'Falta tabla public.equipos_baloncesto';
    END IF;
    IF to_regclass('public.temporadas_baloncesto') IS NULL THEN
        RAISE EXCEPTION 'Falta tabla public.temporadas_baloncesto';
    END IF;
    IF to_regclass('public.partidos_baloncesto') IS NULL THEN
        RAISE EXCEPTION 'Falta tabla public.partidos_baloncesto';
    END IF;
    IF to_regclass('public.ingestion_state_baloncesto') IS NULL THEN
        RAISE EXCEPTION 'Falta tabla public.ingestion_state_baloncesto';
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 1) Validaciones duras de competiciones
-- --------------------------------------------------------------------------
DO $$
DECLARE
    v_nba_count integer;
    v_euro_count integer;
    v_euro_sofa integer;
    v_nba_sofa integer;
BEGIN
    SELECT COUNT(*)
      INTO v_nba_count
      FROM public.competiciones_baloncesto
     WHERE codigo = 'nba';

    IF v_nba_count <> 1 THEN
        RAISE EXCEPTION 'Se esperaba exactamente 1 competicion NBA, encontrado=%', v_nba_count;
    END IF;

    SELECT COUNT(*), max(sofascore_id)
      INTO v_euro_count, v_euro_sofa
      FROM public.competiciones_baloncesto
     WHERE codigo = 'euroleague';

    IF v_euro_count <> 1 THEN
        RAISE EXCEPTION 'Se esperaba exactamente 1 competicion Euroleague, encontrado=%', v_euro_count;
    END IF;

    IF v_euro_sofa <> 138 THEN
        RAISE EXCEPTION 'Euroliga debe tener sofascore_id=138. Valor actual=%', v_euro_sofa;
    END IF;

    SELECT max(sofascore_id)
      INTO v_nba_sofa
      FROM public.competiciones_baloncesto
     WHERE codigo = 'nba';

    IF v_nba_sofa IS NOT NULL THEN
        RAISE EXCEPTION 'NBA debe mantener sofascore_id NULL. Valor actual=%', v_nba_sofa;
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 2) Validaciones duras de migracion NBA (30 equipos)
-- --------------------------------------------------------------------------
DO $$
DECLARE
    v_nba_id uuid;
    v_equipos_nba integer;
    v_equipos_nba_sofa integer;
BEGIN
    SELECT id INTO v_nba_id
    FROM public.competiciones_baloncesto
    WHERE codigo = 'nba'
    LIMIT 1;

    SELECT COUNT(*)
      INTO v_equipos_nba
      FROM public.equipos_baloncesto
     WHERE competicion_principal_id = v_nba_id;

    IF v_equipos_nba <> 30 THEN
        RAISE EXCEPTION 'Se esperaban 30 equipos NBA migrados en equipos_baloncesto, encontrado=%', v_equipos_nba;
    END IF;

    SELECT COUNT(*)
      INTO v_equipos_nba_sofa
      FROM public.equipos_baloncesto
     WHERE competicion_principal_id = v_nba_id
       AND sofascore_id IS NOT NULL;

    IF v_equipos_nba_sofa <> 0 THEN
        RAISE EXCEPTION 'Equipos NBA deben tener sofascore_id NULL en equipos_baloncesto. Filas invalidas=%', v_equipos_nba_sofa;
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 3) Integridad en temporadas / partidos / predicciones / apuestas
-- --------------------------------------------------------------------------
DO $$
DECLARE
    v_temporadas_null integer;
    v_partidos_null integer;
    v_pred_null integer;
    v_partidos_fk_local integer;
    v_partidos_fk_visitante integer;
    v_pred_fk_partido integer;
    v_pred_fk_comp integer;
BEGIN
    SELECT COUNT(*) INTO v_temporadas_null
    FROM public.temporadas_baloncesto
    WHERE competicion_id IS NULL;

    IF v_temporadas_null <> 0 THEN
        RAISE EXCEPTION 'Hay temporadas_baloncesto sin competicion_id: %', v_temporadas_null;
    END IF;

    SELECT COUNT(*) INTO v_partidos_null
    FROM public.partidos_baloncesto
    WHERE competicion_id IS NULL;

    IF v_partidos_null <> 0 THEN
        RAISE EXCEPTION 'Hay partidos_baloncesto sin competicion_id: %', v_partidos_null;
    END IF;

    SELECT COUNT(*) INTO v_pred_null
    FROM public.predicciones_registradas
    WHERE competicion_id IS NULL;

    IF v_pred_null <> 0 THEN
        RAISE EXCEPTION 'Hay predicciones_registradas sin competicion_id: %', v_pred_null;
    END IF;

    SELECT COUNT(*)
      INTO v_partidos_fk_local
      FROM public.partidos_baloncesto p
 LEFT JOIN public.equipos e ON e.id = p.equipo_local_id
     WHERE e.id IS NULL;

    IF v_partidos_fk_local <> 0 THEN
        RAISE EXCEPTION 'Hay partidos con equipo_local_id huerfano: %', v_partidos_fk_local;
    END IF;

    SELECT COUNT(*)
      INTO v_partidos_fk_visitante
      FROM public.partidos_baloncesto p
 LEFT JOIN public.equipos e ON e.id = p.equipo_visitante_id
     WHERE e.id IS NULL;

    IF v_partidos_fk_visitante <> 0 THEN
        RAISE EXCEPTION 'Hay partidos con equipo_visitante_id huerfano: %', v_partidos_fk_visitante;
    END IF;

    SELECT COUNT(*)
      INTO v_pred_fk_partido
      FROM public.predicciones_registradas pr
 LEFT JOIN public.partidos_baloncesto p ON p.id = pr.partido_id
     WHERE p.id IS NULL;

    IF v_pred_fk_partido <> 0 THEN
        RAISE EXCEPTION 'Hay predicciones con partido_id huerfano: %', v_pred_fk_partido;
    END IF;

    SELECT COUNT(*)
      INTO v_pred_fk_comp
      FROM public.predicciones_registradas pr
 LEFT JOIN public.competiciones_baloncesto c ON c.id = pr.competicion_id
     WHERE c.id IS NULL;

    IF v_pred_fk_comp <> 0 THEN
        RAISE EXCEPTION 'Hay predicciones con competicion_id huerfano: %', v_pred_fk_comp;
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 4) Reglas de fuente por competicion
-- --------------------------------------------------------------------------
DO $$
DECLARE
    v_nba_con_sofa integer;
BEGIN
    SELECT COUNT(*)
      INTO v_nba_con_sofa
      FROM public.partidos_baloncesto p
      JOIN public.competiciones_baloncesto c ON c.id = p.competicion_id
     WHERE c.codigo = 'nba'
       AND p.sofascore_match_id IS NOT NULL;

    IF v_nba_con_sofa <> 0 THEN
        RAISE EXCEPTION 'NBA no debe usar sofascore_match_id. Filas invalidas=%', v_nba_con_sofa;
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 5) Reporte resumido
-- --------------------------------------------------------------------------
SELECT
    c.codigo,
    c.nombre,
    c.sofascore_id,
    COUNT(DISTINCT t.id) AS temporadas,
    COUNT(DISTINCT e.id) AS equipos_catalogo,
    COUNT(DISTINCT p.id) AS partidos
FROM public.competiciones_baloncesto c
LEFT JOIN public.temporadas_baloncesto t
       ON t.competicion_id = c.id
LEFT JOIN public.equipos_baloncesto e
       ON e.competicion_principal_id = c.id
LEFT JOIN public.partidos_baloncesto p
       ON p.competicion_id = c.id
GROUP BY c.codigo, c.nombre, c.sofascore_id
ORDER BY c.codigo;

SELECT
    COUNT(*) AS apuestas_sin_competicion
FROM public.apuestas
WHERE competicion_id IS NULL;

SELECT
    clave,
    ultima_sincronizacion,
    ultima_exito,
    ultimo_insertados,
    ultimo_actualizados,
    cursor_fecha
FROM public.ingestion_state_baloncesto
ORDER BY clave;

-- --------------------------------------------------------------------------
-- 6) Checks de performance (consultas comunes)
-- --------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.fecha_partido, p.source, p.source_game_id
FROM public.partidos_baloncesto p
JOIN public.competiciones_baloncesto c ON c.id = p.competicion_id
WHERE c.codigo = 'nba'
  AND p.fecha_partido >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY p.fecha_partido DESC
LIMIT 50;

EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id
FROM public.partidos_baloncesto p
WHERE p.source = 'ESPN'
  AND p.source_game_id IS NOT NULL
ORDER BY p.actualizado_en DESC
LIMIT 20;

EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id
FROM public.partidos_baloncesto p
JOIN public.competiciones_baloncesto c ON c.id = p.competicion_id
WHERE c.codigo = 'euroleague'
  AND p.sofascore_match_id IS NOT NULL
ORDER BY p.fecha_partido DESC
LIMIT 20;

COMMIT;

