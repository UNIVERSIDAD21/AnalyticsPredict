-- Metadatos aditivos: no altera fechas canónicas ni pesos/modelos.
CREATE TABLE IF NOT EXISTS horarios_baloncesto (
 partido_id uuid PRIMARY KEY REFERENCES partidos_baloncesto(id),
 competicion_codigo text NOT NULL CHECK (competicion_codigo IN ('nba','euroleague')),
 proveedor text NOT NULL,
 id_fuente text NOT NULL,
 inicio_utc timestamptz,
 fecha_fuente date NOT NULL,
 zona_origen text NOT NULL,
 precision_fecha text NOT NULL CHECK (precision_fecha IN ('HORA','DIA')),
 estado text NOT NULL CHECK (estado IN ('PROGRAMADO','EN_VIVO','FINALIZADO','POSPUESTO','CANCELADO','SUSPENDIDO','DEMORADO')),
 observado_en timestamptz NOT NULL,
 revision_sha256 text NOT NULL CHECK (length(revision_sha256)=64),
 evidencia jsonb NOT NULL,
 actualizado_en timestamptz NOT NULL DEFAULT now(),
 UNIQUE(proveedor,competicion_codigo,id_fuente),
 CHECK ((precision_fecha='HORA') = (inicio_utc IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS horarios_baloncesto_inicio ON horarios_baloncesto(inicio_utc);
CREATE TABLE IF NOT EXISTS horarios_futbol (
 partido_id uuid PRIMARY KEY REFERENCES partidos_futbol(id),
 competicion_codigo text NOT NULL,
 proveedor text NOT NULL,
 id_fuente text NOT NULL,
 inicio_utc timestamptz,
 fecha_fuente date NOT NULL,
 zona_origen text NOT NULL,
 precision_fecha text NOT NULL CHECK (precision_fecha IN ('HORA','DIA')),
 estado text NOT NULL CHECK (estado IN ('PROGRAMADO','EN_VIVO','FINALIZADO','POSPUESTO','CANCELADO','SUSPENDIDO','DEMORADO')),
 observado_en timestamptz NOT NULL,
 revision_sha256 text NOT NULL CHECK(length(revision_sha256)=64),
 evidencia jsonb NOT NULL,
 actualizado_en timestamptz NOT NULL DEFAULT now(),
 UNIQUE(proveedor,competicion_codigo,id_fuente),
 CHECK ((precision_fecha='HORA') = (inicio_utc IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS revisiones_agenda (
 id uuid PRIMARY KEY,
 deporte text NOT NULL CHECK(deporte IN ('baloncesto','futbol','wnba')),
 partido_id uuid NOT NULL,
 competicion_codigo text NOT NULL,
 revision_sha256 text NOT NULL CHECK(length(revision_sha256)=64),
 antes jsonb,
 despues jsonb NOT NULL,
 observado_en timestamptz NOT NULL,
 procedencia jsonb NOT NULL,
 UNIQUE(deporte,partido_id,revision_sha256)
);
CREATE TABLE IF NOT EXISTS sincronizaciones_agenda (
 id uuid PRIMARY KEY,
 iniciado_en timestamptz NOT NULL,
 terminado_en timestamptz NOT NULL,
 estado text NOT NULL CHECK(estado IN ('COMPLETO','PARCIAL','ERROR')),
 informe jsonb NOT NULL
);
