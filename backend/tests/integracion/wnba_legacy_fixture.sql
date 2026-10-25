-- Contratos previos reales relevantes: temporadas partidas, puntos NOT NULL,
-- COPA rechazada, IDs de fuente globales y catálogos compartidos por FK.
CREATE TABLE competiciones_baloncesto (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),codigo text UNIQUE NOT NULL,
 nombre text NOT NULL,nombre_corto text NOT NULL,tipo text NOT NULL,
 espn_league_id text,formato_competicion text,tiene_playoffs boolean,activo boolean);
CREATE TABLE equipos (
 id uuid PRIMARY KEY,nombre text UNIQUE NOT NULL,nombre_corto text NOT NULL,
 abreviatura varchar(3) UNIQUE NOT NULL,competicion_principal_id uuid REFERENCES competiciones_baloncesto(id));
CREATE TABLE equipos_baloncesto (
 id uuid PRIMARY KEY,nombre text NOT NULL,nombre_corto text,abreviatura text,
 espn_team_id text,competicion_principal_id uuid REFERENCES competiciones_baloncesto(id));
CREATE TABLE temporadas_baloncesto (
 id uuid PRIMARY KEY,competicion_id uuid NOT NULL REFERENCES competiciones_baloncesto(id),
 nombre text NOT NULL,anio_inicio int NOT NULL,anio_fin int NOT NULL,
 CONSTRAINT check_anios CHECK(anio_fin=anio_inicio+1), UNIQUE(competicion_id,nombre));
CREATE TABLE partidos_baloncesto (
 id uuid PRIMARY KEY,competicion_id uuid NOT NULL REFERENCES competiciones_baloncesto(id),
 temporada_id uuid REFERENCES temporadas_baloncesto(id),fecha_partido date NOT NULL,
 equipo_local_id uuid NOT NULL REFERENCES equipos(id),equipo_visitante_id uuid NOT NULL REFERENCES equipos(id),
 tipo_partido text NOT NULL CONSTRAINT partidos_tipo_partido_check CHECK(tipo_partido IN ('PRE','REG','POST')),
 local_q1 int NOT NULL CHECK(local_q1>=0),local_q2 int NOT NULL,local_q3 int NOT NULL,local_q4 int NOT NULL,
 visitante_q1 int NOT NULL,visitante_q2 int NOT NULL,visitante_q3 int NOT NULL,visitante_q4 int NOT NULL,
 local_ot int,visitante_ot int,local_total int NOT NULL,visitante_total int NOT NULL,
 ganador_id uuid REFERENCES equipos(id),diferencia_puntos int,hubo_overtime boolean,
 source text,source_game_id text,espn_game_id text,fuente_datos text,url_referencia text,valido boolean,
 CHECK(equipo_local_id<>equipo_visitante_id),
 CHECK(local_q1+local_q2+local_q3+local_q4+local_ot=local_total),
 CHECK(visitante_q1+visitante_q2+visitante_q3+visitante_q4+visitante_ot=visitante_total),
 UNIQUE(source,source_game_id),UNIQUE(temporada_id,fecha_partido,tipo_partido,equipo_local_id,equipo_visitante_id));
INSERT INTO competiciones_baloncesto(id,codigo,nombre,nombre_corto,tipo,espn_league_id)
 VALUES ('00000000-0000-0000-0000-000000000001','nba','NBA','NBA','LIGA_PROFESIONAL','nba');
INSERT INTO equipos VALUES('00000000-0000-0000-0000-000000000002','Equipo NBA','NBA','NBA','00000000-0000-0000-0000-000000000001');
INSERT INTO equipos_baloncesto VALUES('00000000-0000-0000-0000-000000000002','Equipo NBA','NBA','NBA','1','00000000-0000-0000-0000-000000000001');
INSERT INTO temporadas_baloncesto VALUES('00000000-0000-0000-0000-000000000003','00000000-0000-0000-0000-000000000001','2019-20',2019,2020);
