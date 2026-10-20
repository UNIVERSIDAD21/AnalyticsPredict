from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
from pathlib import Path
from uuid import uuid4

import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg import sql

from db import PoolAplicacion
from servicios.resolucion_multifuente_futbol import (
    ConflictoConcurrente,
    EvidenciaCampo,
    EvidenciaNoValida,
    PartidoCanonico,
    PartidoProveedor,
    construir_plan_resolucion,
    aplicar_plan_resolucion,
    extraer_evidencia_espn,
    extraer_evidencia_pitchapi_estadistica,
    extraer_evidencia_estadistica,
    validar_vinculo_partido,
    vincular_partido_unico,
)


AHORA = datetime(2026, 10, 20, 20, 0, tzinfo=timezone.utc)


def fixture_identidad():
    canon = PartidoCanonico(
        partido_id="partido-1",
        competicion_id="competicion-1",
        equipo_local_id="equipo-1",
        equipo_visitante_id="equipo-2",
        inicio_utc=AHORA,
        estado="FINALIZADO",
        goles_local=2,
        goles_visitante=1,
    )
    prov = PartidoProveedor(
        fuente="PITCHAPI",
        evento_id="m_Ab12Z9",
        competicion_id="l_Cd34Xy",
        equipo_local_id="t_Ef56Qr",
        equipo_visitante_id="t_Gh78Ws",
        inicio_utc=AHORA + timedelta(seconds=60),
        estado="finished",
        goles_local=2,
        goles_visitante=1,
    )
    comps = {("PITCHAPI", prov.competicion_id): canon.competicion_id}
    equipos = {
        ("PITCHAPI", prov.equipo_local_id): canon.equipo_local_id,
        ("PITCHAPI", prov.equipo_visitante_id): canon.equipo_visitante_id,
    }
    return canon, prov, comps, equipos


def test_vinculo_exige_ids_mapeados_y_concilia_final():
    canon, prov, comps, equipos = fixture_identidad()
    validar_vinculo_partido(
        canon, prov, mapeo_competiciones=comps, mapeo_equipos=equipos
    )

    intercambiado = PartidoProveedor(**{**prov.__dict__, "equipo_local_id": prov.equipo_visitante_id})
    with pytest.raises(EvidenciaNoValida, match="Equipo local"):
        validar_vinculo_partido(
            canon, intercambiado, mapeo_competiciones=comps, mapeo_equipos=equipos
        )


def test_vinculo_candidato_debe_ser_unico():
    canon, prov, comps, equipos = fixture_identidad()
    otro = PartidoCanonico(**{**canon.__dict__, "partido_id": "partido-duplicado"})
    with pytest.raises(EvidenciaNoValida, match="ambiguo"):
        vincular_partido_unico(
            [canon, otro], prov, mapeo_competiciones=comps, mapeo_equipos=equipos
        )
    assert vincular_partido_unico(
        [canon], prov, mapeo_competiciones=comps, mapeo_equipos=equipos
    ) == canon


@pytest.mark.parametrize(
    "cambio,patron",
    [
        ({"competicion_id": "l_OtroId"}, "Competición"),
        ({"inicio_utc": AHORA + timedelta(minutes=5)}, "Inicio UTC"),
        ({"goles_local": 3}, "marcador FT"),
        ({"estado": "upcoming"}, "finalizados"),
    ],
)
def test_vinculo_rechaza_competencia_fecha_marcador_o_estado(cambio, patron):
    canon, prov, comps, equipos = fixture_identidad()
    modificado = PartidoProveedor(**{**prov.__dict__, **cambio})
    with pytest.raises(EvidenciaNoValida, match=patron):
        validar_vinculo_partido(
            canon, modificado, mapeo_competiciones=comps, mapeo_equipos=equipos
        )


def test_extraccion_solo_toma_claves_y_periodos_explicitos_y_preserva_cero():
    payload = {
        "match_id": "m_Ab12Z9",
        "home_team": {"id": "t_Ef56Qr"},
        "away_team": {"id": "t_Gh78Ws"},
        "periods": [
            {
                "period": "All",
                "groups": [
                    {
                        "items": [
                            {"key": "synthetic_corners", "home": "0", "away": "4", "format_type": "integer"},
                            {"key": "unmapped_shots", "home": "15", "away": "8", "format_type": "integer"},
                        ]
                    }
                ],
            },
            {
                "period": "FirstHalf",
                "groups": [{"items": [{"key": "synthetic_corners_1h", "home": "0", "away": "2", "format_type": ""}]}],
            },
        ],
    }
    mapeo = {
        ("synthetic_corners", "All"): ("local_corners_total", "visitante_corners_total"),
        ("synthetic_corners_1h", "FirstHalf"): ("local_corners_1t", "visitante_corners_1t"),
    }

    evidencia = extraer_evidencia_estadistica(
        fuente="PITCHAPI",
        evento_id="m_Ab12Z9",
        payload=payload,
        esperado_local_proveedor_id="t_Ef56Qr",
        esperado_visitante_proveedor_id="t_Gh78Ws",
        mapeo_metricas=mapeo,
        observado_en=AHORA,
    )

    assert [(x.campo, x.valor) for x in evidencia] == [
        ("local_corners_total", 0),
        ("visitante_corners_total", 4),
        ("local_corners_1t", 0),
        ("visitante_corners_1t", 2),
    ]
    assert all(len(x.sha256_payload) == 64 for x in evidencia)


def test_extraccion_multifuente_permite_un_lado_mientras_el_otro_es_null():
    payload = {
        "match_id": "m_Ab12Z9",
        "home_team": {"id": "t_Ef56Qr"},
        "away_team": {"id": "t_Gh78Ws"},
        "periods": [{"period": "All", "groups": [{"items": [
            {"key": "synthetic_corners", "home": "6", "away": None, "format_type": "integer"}
        ]}]}],
    }
    evidencia = extraer_evidencia_estadistica(
        fuente="PITCHAPI",
        evento_id="m_Ab12Z9",
        payload=payload,
        esperado_local_proveedor_id="t_Ef56Qr",
        esperado_visitante_proveedor_id="t_Gh78Ws",
        mapeo_metricas={("synthetic_corners", "All"): ("local_corners_total", "visitante_corners_total")},
        observado_en=AHORA,
    )
    assert [(e.campo, e.valor) for e in evidencia] == [("local_corners_total", 6)]
    payload["periods"][0]["groups"][0]["items"][0]["home"] = None
    assert extraer_evidencia_estadistica(
        fuente="PITCHAPI",
        evento_id="m_Ab12Z9",
        payload=payload,
        esperado_local_proveedor_id="t_Ef56Qr",
        esperado_visitante_proveedor_id="t_Gh78Ws",
        mapeo_metricas={("synthetic_corners", "All"): ("local_corners_total", "visitante_corners_total")},
        observado_en=AHORA,
    ) == ()


def test_pitchapi_mapea_solo_campos_compatibles_de_stats_por_campo_y_periodo():
    payload = {
        "match_id": "m_Ab12Z9",
        "home_team": {"id": "t_Ef56Qr"},
        "away_team": {"id": "t_Gh78Ws"},
        "periods": [
            {"period": "All", "groups": [{"items": [
                {"key": "shots", "home": "12", "away": "9", "format_type": "integer"},
                {"key": "shots_on_target", "home": "4", "away": "2", "format_type": "integer"},
                {"key": "BallPossesion", "home": "54", "away": "46", "format_type": "integer"},
                {"key": "expected_goals", "home": "1.35", "away": "0.62", "format_type": "double"},
                {"key": "guessed_metric", "home": "500", "away": "500", "format_type": "integer"},
            ]}]},
            {"period": "FirstHalf", "groups": [{"items": [
                {"key": "expected_goals", "home": "0.41", "away": "0.21", "format_type": "double"},
            ]}]},
        ],
    }
    evidencia = extraer_evidencia_pitchapi_estadistica(
        evento_id="m_Ab12Z9",
        payload=payload,
        esperado_local_proveedor_id="t_Ef56Qr",
        esperado_visitante_proveedor_id="t_Gh78Ws",
        observado_en=AHORA,
    )
    assert {item.campo: item.valor for item in evidencia} == {
        "local_disparos_total": 12,
        "visitante_disparos_total": 9,
        "local_posesion": Decimal("54"),
        "visitante_posesion": Decimal("46"),
    }
    assert all(item.contrato == "PITCHAPI_TEAM_STATS_DOCS_2026_10_20_V1" for item in evidencia)


def test_extraccion_y_plan_conservan_decimales_de_posesion_y_xg():
    payload = {
        "match_id": "m_Ab12Z9",
        "home_team": {"id": "t_Ef56Qr"},
        "away_team": {"id": "t_Gh78Ws"},
        "periods": [{"period": "All", "groups": [{"items": [
            {"key": "synthetic_xg", "home": "1.25", "away": "0.70", "format_type": "double"}
        ]}]}],
    }
    evidencias = extraer_evidencia_estadistica(
        fuente="PITCHAPI",
        evento_id="m_Ab12Z9",
        payload=payload,
        esperado_local_proveedor_id="t_Ef56Qr",
        esperado_visitante_proveedor_id="t_Gh78Ws",
        mapeo_metricas={("synthetic_xg", "All"): ("local_xg", "visitante_xg")},
        observado_en=AHORA,
    )
    plan = construir_plan_resolucion({}, evidencias)
    assert plan.actualizaciones == {"local_xg": Decimal("1.25"), "visitante_xg": Decimal("0.70")}


@pytest.mark.parametrize(
    "valor,formato",
    [("2 (50%)", "integerWithPercentage"), (2.5, "double"), (-1, "integer")],
)
def test_extraccion_rechaza_nulos_porcentajes_decimales_y_negativos(valor, formato):
    payload = {
        "match_id": "m_Ab12Z9",
        "home_team": {"id": "t_Ef56Qr"},
        "away_team": {"id": "t_Gh78Ws"},
        "periods": [{"period": "All", "groups": [{"items": [
            {"key": "synthetic_metric", "home": valor, "away": "1", "format_type": formato}
        ]}]}],
    }
    with pytest.raises(EvidenciaNoValida):
        extraer_evidencia_estadistica(
            fuente="PITCHAPI",
            evento_id="m_Ab12Z9",
            payload=payload,
            esperado_local_proveedor_id="t_Ef56Qr",
            esperado_visitante_proveedor_id="t_Gh78Ws",
            mapeo_metricas={("synthetic_metric", "All"): ("local_corners_total", "visitante_corners_total")},
            observado_en=AHORA,
        )


def fixture_espn():
    esperado = {
        "id_fuente": "401234567",
        "liga": "eng.fa",
        "inicio_utc": "2026-03-01T15:00:00+00:00",
        "local_id_fuente": "100",
        "visitante_id_fuente": "200",
        "local_goles": 2,
        "visitante_goles": 1,
    }
    payload = {
        "header": {
            "id": esperado["id_fuente"],
            "competitions": [
                {
                    "id": esperado["id_fuente"],
                    "date": esperado["inicio_utc"],
                    "status": {"type": {"completed": True, "name": "STATUS_FULL_TIME"}},
                    "competitors": [
                        {"homeAway": "home", "team": {"id": "100"}, "score": "2"},
                        {"homeAway": "away", "team": {"id": "200"}, "score": "1"},
                    ],
                }
            ],
        },
        "boxscore": {
            "teams": [
                {"team": {"id": "100"}, "statistics": [
                    {"name": "wonCorners", "displayValue": "0"},
                    {"name": "totalShots", "displayValue": "13"},
                ]},
                {"team": {"id": "200"}, "statistics": [
                    {"name": "totalShots", "displayValue": "7"},
                    {"name": "shotsOnTarget", "displayValue": "3"},
                ]},
            ]
        },
    }
    return payload, esperado


def test_espn_extrae_campos_disponibles_independientemente_y_conserva_cero():
    payload, esperado = fixture_espn()
    evidencia = extraer_evidencia_espn(payload, esperado, observado_en=AHORA)
    assert [(e.campo, e.valor) for e in evidencia] == [
        ("local_corners_total", 0),
        ("local_disparos_total", 13),
        ("visitante_disparos_total", 7),
        ("visitante_disparos_arco", 3),
    ]
    assert all(e.fuente == "ESPN_SOCCER" and e.periodo_proveedor == "All" for e in evidencia)
    assert all(e.contrato == "ESPN_BOX_SCORE_FIELD_STATS_V1" for e in evidencia)


def test_espn_acepta_campos_adicionales_solo_con_mapeo_explicito():
    payload, esperado = fixture_espn()
    for equipo, valor in zip(payload["boxscore"]["teams"], ("1.28", "0.74")):
        equipo["statistics"].append({"name": "syntheticXg", "displayValue": valor})
    evidencia = extraer_evidencia_espn(
        payload,
        esperado,
        observado_en=AHORA,
        mapeo_metricas={"syntheticXg": ("local_xg", "visitante_xg")},
    )
    assert [(e.campo, e.valor) for e in evidencia] == [
        ("local_xg", Decimal("1.28")), ("visitante_xg", Decimal("0.74"))
    ]


@pytest.mark.parametrize("cambio", ["id", "date", "team", "score", "status"])
def test_espn_rechaza_resumen_que_no_concilia_con_el_evento_vinculado(cambio):
    payload, esperado = fixture_espn()
    competition = payload["header"]["competitions"][0]
    if cambio == "id":
        payload["header"]["id"] = "999"
    elif cambio == "date":
        competition["date"] = "2026-03-01T16:00:00Z"
    elif cambio == "team":
        competition["competitors"][0]["team"]["id"] = "999"
    elif cambio == "score":
        competition["competitors"][0]["score"] = "3"
    elif cambio == "status":
        competition["status"]["type"]["completed"] = False
    with pytest.raises(EvidenciaNoValida):
        extraer_evidencia_espn(payload, esperado, observado_en=AHORA)


def test_espn_resumen_sin_stats_es_ausencia_no_cero():
    payload, esperado = fixture_espn()
    payload["boxscore"]["teams"] = [
        {"team": {"id": "100"}, "statistics": []},
        {"team": {"id": "200"}, "statistics": []},
    ]
    assert extraer_evidencia_espn(payload, esperado, observado_en=AHORA) == ()

    payload, esperado = fixture_espn()
    assert extraer_evidencia_espn(
        payload, esperado, observado_en=AHORA, mapeo_metricas={}
    ) == ()


def test_espn_admite_diferencia_de_inicio_dentro_de_dos_minutos():
    payload, esperado = fixture_espn()
    inicio = datetime.fromisoformat(esperado["inicio_utc"])
    payload["header"]["competitions"][0]["date"] = (inicio + timedelta(seconds=90)).isoformat()
    assert extraer_evidencia_espn(payload, esperado, observado_en=AHORA)

    payload["header"]["competitions"][0]["date"] = (inicio + timedelta(seconds=121)).isoformat()
    with pytest.raises(EvidenciaNoValida, match="Fecha ESPN"):
        extraer_evidencia_espn(payload, esperado, observado_en=AHORA)


def evidencia(campo, valor, fuente="PITCHAPI", evento="m_Ab12Z9"):
    return EvidenciaCampo(
        campo=campo,
        valor=valor,
        fuente=fuente,
        evento_id=evento,
        clave_proveedor=f"synthetic_{campo}",
        periodo_proveedor="All",
        sha256_payload="a" * 64,
        observado_en=AHORA,
    )


def test_plan_rellena_solo_nulls_y_preserva_cero_y_dato_existente():
    plan = construir_plan_resolucion(
        {"local_corners_total": 0, "visitante_corners_total": None},
        [evidencia("local_corners_total", 0), evidencia("visitante_corners_total", 5)],
    )

    assert plan.actualizaciones == {"visitante_corners_total": 5}
    assert plan.preservados == ("local_corners_total",)
    assert plan.conflictos == {}


def test_plan_aparta_conflicto_entre_fuentes_y_no_sobrescribe_canonico():
    plan = construir_plan_resolucion(
        {"local_disparos_total": 10},
        [
            evidencia("local_disparos_total", 11, "PITCHAPI"),
            evidencia("local_disparos_total", 12, "THESTATSAPI"),
            evidencia("visitante_disparos_total", 7, "PITCHAPI"),
        ],
    )

    assert plan.actualizaciones == {"visitante_disparos_total": 7}
    assert plan.conflictos["local_disparos_total"].startswith("Fuentes discrepan")
    assert "local_disparos_total" not in plan.actualizaciones


def test_plan_no_acepta_total_de_corners_que_no_concilia_con_periodos():
    plan = construir_plan_resolucion(
        {},
        [
            evidencia("local_corners_total", 5),
            evidencia("local_corners_1t", 2),
            evidencia("local_corners_2t", 2),
        ],
    )

    assert plan.actualizaciones == {}
    assert set(plan.conflictos) == {
        "local_corners_total", "local_corners_1t", "local_corners_2t"
    }


def test_plan_exige_ambos_lados_para_prorroga_y_penales():
    prorroga_incompleta = construir_plan_resolucion(
        {}, [evidencia("local_goles_et", 1)]
    )
    assert prorroga_incompleta.actualizaciones == {}
    assert set(prorroga_incompleta.conflictos) == {"local_goles_et", "visitante_goles_et"}

    tanda_incompleta = construir_plan_resolucion(
        {}, [evidencia("local_penales", 5)]
    )
    assert tanda_incompleta.actualizaciones == {}
    assert set(tanda_incompleta.conflictos) == {"local_penales", "visitante_penales"}

    prorroga = construir_plan_resolucion(
        {}, [evidencia("local_goles_et", 1), evidencia("visitante_goles_et", 0)]
    )
    preview = aplicar_plan_resolucion(
        object(), partido_id="p", goles_local_ft=2, goles_visitante_ft=1,
        plan=prorroga,
        identidades={},
    )
    assert set(preview["flags_derivados"]) == {"hubo_tiempo_extra=true"}


def test_plan_no_acepta_disparos_a_puerta_mayores_que_totales():
    plan = construir_plan_resolucion(
        {}, [evidencia("visitante_disparos_total", 2), evidencia("visitante_disparos_arco", 3)]
    )

    assert plan.actualizaciones == {}
    assert set(plan.conflictos) == {"visitante_disparos_total", "visitante_disparos_arco"}


def test_aplicacion_dry_run_no_toca_la_conexion():
    plan = construir_plan_resolucion({}, [evidencia("local_corners_total", 4)])

    salida = aplicar_plan_resolucion(
        object(),
        partido_id="no-se-conecta",
        goles_local_ft=2,
        goles_visitante_ft=1,
        plan=plan,
        identidades={},
    )

    assert salida["modo"] == "DRY_RUN"
    assert salida["actualizaciones"] == {"local_corners_total": 4}


def test_aplicacion_postgresql_sintetico_es_null_only_idempotente_y_contratos():
    url = os.environ.get("DATABASE_URL") or ""
    if not conninfo_to_dict(url).get("dbname", "").startswith("ap_suite_test_"):
        pytest.skip("Solo PostgreSQL sintético desechable ap_suite_test_*")

    schema = "ap_multi_fuente_" + uuid4().hex
    admin = PoolAplicacion(url, min_size=1, max_size=1, open=True)
    pid = uuid4()
    ev = evidencia("local_corners_total", 4)
    plan = construir_plan_resolucion({}, [ev])
    identity = {
        "metodo": "MAPPED_PROVIDER_IDS_AND_EVENT_CONCILIATION_V1",
        "canonical_competition_id": "competicion-1",
        "provider_competition_id": "l_Cd34Xy",
        "canonical_home_team_id": "equipo-1",
        "provider_home_team_id": "t_Ef56Qr",
        "canonical_away_team_id": "equipo-2",
        "provider_away_team_id": "t_Gh78Ws",
        "canonical_start_utc": AHORA.isoformat(),
        "provider_start_utc": AHORA.isoformat(),
        "canonical_ft": [2, 1],
        "provider_ft": [2, 1],
    }
    identidades = {("PITCHAPI", ev.evento_id): identity}
    try:
        with admin.connection() as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            conn.execute(sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema)))
            conn.execute(
                """CREATE TABLE partidos_futbol (
                    id uuid PRIMARY KEY, estado text NOT NULL,
                    competicion_id text NOT NULL, equipo_local_id text NOT NULL,
                    equipo_visitante_id text NOT NULL, fecha_partido timestamptz NOT NULL,
                    hubo_tiempo_extra boolean NOT NULL DEFAULT false,
                    hubo_penales boolean NOT NULL DEFAULT false,
                    local_goles_1t integer, local_goles_2t integer, local_goles_et integer,
                    visitante_goles_1t integer, visitante_goles_2t integer, visitante_goles_et integer,
                    local_penales integer, visitante_penales integer,
                    local_goles_total integer, visitante_goles_total integer,
                    local_corners_total integer, visitante_corners_total integer,
                    local_corners_1t integer, visitante_corners_1t integer,
                    local_corners_2t integer, visitante_corners_2t integer,
                    local_disparos_total integer, visitante_disparos_total integer,
                    local_disparos_arco integer, visitante_disparos_arco integer,
                    local_disparos_fuera integer, visitante_disparos_fuera integer,
                    local_disparos_bloqueados integer, visitante_disparos_bloqueados integer,
                    local_posesion numeric, visitante_posesion numeric,
                    local_faltas integer, visitante_faltas integer,
                    local_tarjetas_amarillas integer, visitante_tarjetas_amarillas integer,
                    local_tarjetas_rojas integer, visitante_tarjetas_rojas integer,
                    local_fueras_juego integer, visitante_fueras_juego integer,
                    local_xg numeric, visitante_xg numeric, local_xg_1t numeric, visitante_xg_1t numeric
                )"""
            )
            conn.execute(
                "INSERT INTO partidos_futbol(id,estado,competicion_id,equipo_local_id,equipo_visitante_id,fecha_partido,local_goles_total,visitante_goles_total) "
                "VALUES (%s,'FINALIZADO','competicion-1','equipo-1','equipo-2',%s,2,1)",
                (pid, AHORA),
            )
            migration = (Path(__file__).parents[1] / "migrations/2026-10-20_observaciones_multifuente_futbol.sql").read_text()
            migration = migration[migration.index("CREATE TABLE"):migration.rindex("COMMIT;")]
            conn.execute(migration)

        pool = PoolAplicacion(
            make_conninfo(url, options=f"-c search_path={schema}"),
            min_size=1,
            max_size=1,
            open=True,
        )
        try:
            with pool.connection() as conn:
                with conn.transaction():
                    first = aplicar_plan_resolucion(
                        conn,
                        partido_id=str(pid),
                        goles_local_ft=2,
                        goles_visitante_ft=1,
                        plan=plan,
                        identidades=identidades,
                        dry_run=False,
                    )
                assert first["campos_aplicados"] == ["local_corners_total"]
                assert first["filas_evidencia_insertadas"] == 1

                with conn.transaction():
                    repeated = aplicar_plan_resolucion(
                        conn,
                        partido_id=str(pid),
                        goles_local_ft=2,
                        goles_visitante_ft=1,
                        plan=plan,
                        identidades=identidades,
                        dry_run=False,
                    )
                assert repeated["campos_aplicados"] == []
                assert repeated["filas_evidencia_insertadas"] == 0

                assert conn.execute("SELECT local_corners_total FROM partidos_futbol WHERE id=%s", (pid,)).fetchone() == (4,)
                assert conn.execute(
                    "SELECT count(*) FROM observaciones_multifuente_estadisticas_futbol WHERE partido_id=%s", (pid,)
                ).fetchone() == (1,)

                conflicto = construir_plan_resolucion({}, [evidencia("local_corners_total", 5)])
                with pytest.raises(ConflictoConcurrente, match="no se sobrescribe"):
                    with conn.transaction():
                        aplicar_plan_resolucion(
                            conn,
                            partido_id=str(pid),
                            goles_local_ft=2,
                            goles_visitante_ft=1,
                            plan=conflicto,
                            identidades=identidades,
                            dry_run=False,
                        )
                assert conn.execute("SELECT local_corners_total FROM partidos_futbol WHERE id=%s", (pid,)).fetchone() == (4,)
        finally:
            pool.close()
    finally:
        with admin.connection() as conn:
            conn.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
        admin.close()
