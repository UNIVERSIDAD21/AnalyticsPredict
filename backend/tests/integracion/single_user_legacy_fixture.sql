-- Esquema mínimo sintético que cubre las dependencias de la migración.
-- Exclusivo de una base PostgreSQL efímera; nunca restaurar sobre datos reales.
CREATE TABLE usuarios (
  id uuid PRIMARY KEY, preferencias jsonb, bankroll_inicial numeric,
  bankroll_actual numeric, perfil_riesgo_default varchar, config_sizing jsonb
);
CREATE TABLE apuestas (
  id uuid PRIMARY KEY, usuario_id uuid REFERENCES usuarios(id),
  equipo_local varchar, equipo_visitante varchar, fecha_partido timestamptz,
  mercado varchar, lado varchar, linea numeric, cuota numeric, stake numeric,
  probabilidad_sistema numeric, confianza_sistema numeric, valor_esperado numeric,
  resultado varchar, ganancia numeric, creado_en timestamptz,
  fecha_resolucion timestamptz, devig_overround numeric, devig_p_mkt_raw numeric,
  edge_real numeric, bankroll_momento numeric, score_total numeric
);
CREATE TABLE apuestas_futbol (
  id uuid PRIMARY KEY, usuario_id uuid REFERENCES usuarios(id),
  mercado varchar, resultado varchar, stake numeric, ganancia numeric
);
CREATE TABLE apuestas_combinadas (
  id uuid PRIMARY KEY, usuario_id uuid REFERENCES usuarios(id),
  cuota_total numeric, stake numeric, probabilidad_ajustada numeric,
  confianza_sistema numeric, valor_esperado numeric, resultado varchar,
  ganancia numeric, n_selecciones integer, selecciones_ganadas integer,
  selecciones_perdidas integer, tiene_mismo_partido boolean,
  creado_en timestamptz, fecha_resolucion timestamptz
);
CREATE TABLE selecciones_combinada (
  id uuid PRIMARY KEY, combinada_id uuid REFERENCES apuestas_combinadas(id),
  equipo_local varchar, equipo_visitante varchar, fecha_partido timestamptz
);
CREATE TABLE apuestas_analizadas (id integer PRIMARY KEY);
CREATE TABLE predicciones_registradas (id integer PRIMARY KEY);
CREATE TABLE predicciones_futbol (id integer PRIMARY KEY);
CREATE TABLE partidos_baloncesto (id integer PRIMARY KEY);
CREATE TABLE partidos_futbol (id integer PRIMARY KEY);
CREATE TABLE onboarding_events (id integer);
CREATE TABLE onboarding_profiles (id integer);
CREATE TABLE payment_events (id integer);
CREATE TABLE payment_intents (id integer);
CREATE TABLE subscriptions (id integer);
CREATE TABLE auth_reset_tokens_v2 (id integer);
CREATE TABLE auth_reset_tokens (id integer);
CREATE TABLE auth_revoked_tokens (id integer);
CREATE TABLE auth_users (id integer);
CREATE VIEW vista_resumen_por_tipo_apuesta AS SELECT id FROM apuestas;
CREATE VIEW vista_bitacora_unificada AS SELECT id FROM apuestas;
CREATE VIEW vista_analisis_apuestas AS SELECT id FROM apuestas;
CREATE VIEW vista_resumen_apuestas AS SELECT id FROM apuestas;
CREATE VIEW vista_resumen_apuestas_futbol AS SELECT id FROM apuestas_futbol;

INSERT INTO usuarios VALUES
  ('00000000-0000-0000-0000-000000000001', '{"locale":"es"}', 100, 110, 'moderado', '{}'),
  ('00000000-0000-0000-0000-000000000002', '{"locale":"en"}', 20, 20, 'bajo', '{}');
INSERT INTO apuestas (id, usuario_id, equipo_local, equipo_visitante, resultado, cuota, stake, probabilidad_sistema, confianza_sistema, creado_en)
VALUES
  ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'A', 'B', 'GANADA', 1.9, 10, 0.6, 0.7, now()),
  ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'C', 'D', 'PENDIENTE', 2.1, 10, 0.5, 0.6, now()),
  ('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000002', 'E', 'F', 'PERDIDA', 1.8, 5, 0.4, 0.5, now());
INSERT INTO apuestas_futbol (id, usuario_id, mercado, resultado) VALUES ('00000000-0000-0000-0000-000000000021', '00000000-0000-0000-0000-000000000001', 'GOLES_FT', 'GANADA');
INSERT INTO apuestas_combinadas (id, usuario_id, cuota_total, stake, probabilidad_ajustada, resultado, n_selecciones)
VALUES ('00000000-0000-0000-0000-000000000031', '00000000-0000-0000-0000-000000000001', 3.2, 5, 0.3, 'PENDIENTE', 1);
INSERT INTO selecciones_combinada VALUES ('00000000-0000-0000-0000-000000000041', '00000000-0000-0000-0000-000000000031', 'A', 'B', now());
INSERT INTO apuestas_analizadas VALUES (1);
INSERT INTO predicciones_registradas VALUES (1);
INSERT INTO predicciones_futbol VALUES (1);
INSERT INTO partidos_baloncesto VALUES (1);
INSERT INTO partidos_futbol VALUES (1);
