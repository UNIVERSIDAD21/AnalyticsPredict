-- Esquema sintético mínimo para la suite global en PostgreSQL desechable.
-- Sin datos de Neon ni credenciales. No ejecutar en una base persistente.

CREATE TABLE predicciones_registradas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    partido_id uuid,
    mercado text,
    linea numeric,
    lado text,
    origen text,
    p_raw numeric,
    p_calibrada numeric,
    calibrador_id uuid,
    outcome_binario boolean,
    resuelto boolean,
    timestamp_generacion timestamptz,
    timestamp_resolucion timestamptz,
    creado_en timestamptz,
    actualizado_en timestamptz
);

CREATE TABLE predicciones_futbol (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    mercado text,
    linea numeric,
    fecha_partido timestamptz,
    prob_over numeric,
    prob_over_raw numeric,
    prob_over_calibrada numeric,
    calibrador_id uuid,
    outcome_binario boolean,
    resuelto boolean,
    timestamp_generacion timestamptz,
    timestamp_resolucion timestamptz,
    creado_en timestamptz,
    actualizado_en timestamptz
);

CREATE TABLE modelo_versiones (
    version text,
    fecha_entrenamiento timestamptz,
    partidos_entrenamiento integer
);

CREATE TABLE modelo_versiones_futbol (
    version text,
    fecha_entrenamiento timestamptz,
    partidos_entrenamiento integer,
    creado_en timestamptz
);

CREATE TABLE partidos_futbol (
    id uuid PRIMARY KEY,
    fecha_partido timestamptz
);

CREATE TABLE equipos (
    id uuid PRIMARY KEY,
    nombre text
);

CREATE TABLE partidos_baloncesto (
    id uuid PRIMARY KEY,
    fecha_partido timestamptz,
    equipo_local_id uuid,
    equipo_visitante_id uuid
);

CREATE TABLE apuestas_analizadas (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    deporte text NOT NULL,
    partido_id uuid NOT NULL,
    mercado text,
    lado text,
    linea numeric,
    probabilidad_sistema numeric,
    confianza text,
    estado text,
    resultado_outcome text,
    valor_real numeric,
    resultado_resumen text,
    creado_en timestamptz DEFAULT now(),
    actualizado_en timestamptz DEFAULT now(),
    decision_p_raw numeric,
    decision_p_calibrada numeric,
    decision_edge_real numeric,
    decision_score numeric,
    decision_sizing numeric,
    decision_valor_esperado numeric,
    decision_calibrador_id text,
    decision_modelo_version_id text,
    decision_fuente text,
    decision_devig_metodo text,
    decision_devig_overround numeric,
    decision_devig_p_mkt_fair numeric,
    decision_cuota numeric,
    decision_cuota_over numeric,
    decision_cuota_under numeric
);

CREATE SCHEMA analytics;
CREATE TABLE analytics.dq_alerts (
    id bigint,
    periodo date,
    domain text,
    alert_id text,
    severity text,
    component text,
    title text,
    condition_text text,
    incident_key text,
    status text,
    emitted boolean,
    repeat_count integer,
    trigger_value numeric,
    threshold_value numeric,
    warning_type text,
    warning_severity text,
    payload jsonb,
    created_at timestamptz,
    updated_at timestamptz,
    alerta_reincidente boolean,
    first_occurrence_at timestamptz
);
