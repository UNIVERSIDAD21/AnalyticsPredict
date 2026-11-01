"""Contratos de las cinco fuentes, consolidación por país y coordinación de red."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scrapers.futbol_latam.archivo import Archivo, ArchivoError, bytes_json, guardar_json
from scrapers.futbol_latam.cliente import ClienteESPN, ConsultaError, FuenteError, url_consulta
from scrapers.futbol_latam.contrato import ContratoError, enriquecer, eventos_scoreboard, normalizar
from scrapers.futbol_latam.ligas import ARGENTINA, BRASIL, COLOMBIA, COPA_LIGA, COPA_SUPERLIGA, POR_PAIS, clasificar_fase
from scrapers.futbol_latam.pipeline import ejecutar
from scrapers.futbol_latam.red import ControlRed, PausaRed
from scrapers.futbol_latam import cli
from scripts.scraper_argentina import main as argentina
from scripts.scraper_brasil import main as brasil
from scripts.scraper_colombia import main as colombia
from test_latam_base import Clock, NOW, Response, Session, event, scoreboard, summary

TORNEOS = [ARGENTINA, BRASIL, COLOMBIA, COPA_LIGA, COPA_SUPERLIGA]


def fuente(torneo, eid="123", phase="regular-season", start="2019-10-06T20:00Z"):
    e = event(eid, phase=phase, start=start)
    e["uid"] = f"{torneo.uid}~e:{eid}"
    e["competitions"][0]["uid"] = f"{torneo.uid}~e:{eid}~c:{eid}"
    league = {"id":torneo.id,"slug":torneo.slug,"uid":torneo.uid}
    board = {"leagues":[league],"events":[e]}
    detail = summary(e)
    detail["header"]["league"] = deepcopy(league)
    return e, board, detail


def cliente(tmp_path, torneo, responses, *, gate=None, **kwargs):
    clock = Clock()
    session = Session(responses, clock)
    c = ClienteESPN(Archivo(tmp_path),torneo=torneo,control_red=gate,session=session,dormir=clock.sleep,reloj=clock.mono,ahora=lambda:NOW,jitter=lambda:0,**kwargs)
    return c, session, clock


@pytest.mark.parametrize("torneo",TORNEOS)
def test_cada_fuente_valida_identidad_y_no_acepta_otras(torneo):
    e,b,s = fuente(torneo)
    assert eventos_scoreboard(b,torneo)==[e]
    r = enriquecer(normalizar(e,torneo),s,e)
    assert r["codigo_liga"]==torneo.slug and r["competicion"]==torneo.codigo
    assert r["local_corners"]==0 and r["estadisticas_completas"]
    assert f"/{torneo.slug}/summary?event=123" in url_consulta("summary","123",torneo)
    other = BRASIL if torneo!=BRASIL else COLOMBIA
    with pytest.raises(ContratoError,match="OTRA_LIGA"):
        eventos_scoreboard(b,other)
    with pytest.raises(ContratoError,match="OTRA_LIGA"):
        normalizar(e,other)
    s["header"]["league"]["id"] = other.id
    with pytest.raises(ContratoError,match="OTRA_LIGA"):
        enriquecer(r,s)


@pytest.mark.parametrize("torneo,slug,expected",[
    (ARGENTINA,"superliga-argentina-2018-19","REG"),
    (ARGENTINA,"2020-21-copa-diego-armando-maradona---group-stage","COPA"),
    (ARGENTINA,"torneo-apertura","REG"),(ARGENTINA,"torneo-clausura","REG"),
    (COPA_LIGA,"group-stage","COPA"),(COPA_SUPERLIGA,"round-of-16","POST"),
    (BRASIL,"2019-brasileirao","REG"),(BRASIL,"2026-brasileiro-serie-a","REG"),
    (COLOMBIA,"apertura---quadrangular","POST"),(COLOMBIA,"playoffs---finals","POST"),
    (COLOMBIA,"clausura","REG"),(COLOMBIA,"fase-desconocida","OTRA"),
])
def test_fases_publicadas_y_desconocidas_sin_suposiciones(torneo,slug,expected):
    assert clasificar_fase(slug,torneo)==expected


@pytest.mark.parametrize("main,expected",[(argentina,282),(brasil,94),(colombia,94)])
def test_planes_independientes_sin_red_ni_archivos(main,expected,tmp_path,capsys):
    assert main(["--desde","2019-01-01","--hasta","2026-10-25","--salida",str(tmp_path/"nueva")])==0
    assert json.loads(capsys.readouterr().out)["ventanas_previstas"]==expected
    assert not (tmp_path/"nueva").exists()


def seed(root,pais):
    guardar_json(root/"identidad.json",{"contrato":"espn_latam_v1","pais":pais})
    for i,t in enumerate(POR_PAIS[pais],1):
        _,b,s=fuente(t,str(100+i))
        a=Archivo(root/"torneos"/t.slug)
        for endpoint,param,payload in [("scoreboard","201910",b),("summary",str(100+i),s)]:
            a.guardar(url_consulta(endpoint,param,t),bytes_json(payload),NOW.isoformat())


@pytest.mark.parametrize("pais,main,n",[("argentina",argentina,3),("brasil",brasil,1),("colombia",colombia,1)])
def test_cli_offline_consolida_fuentes_e_informes_trazables(tmp_path,capsys,pais,main,n):
    seed(tmp_path,pais)
    assert main(["--desde","2019-10-06","--hasta","2019-10-06","--offline","--salida",str(tmp_path)])==0
    r=json.loads(capsys.readouterr().out)
    assert r["finales_con_estadisticas_completas"]==n
    report=json.loads(Path(r["reporte"]).read_bytes())
    assert report["contadores_http"]["requests"]==0 and len(report["torneos"])==n
    assert len(Path(r["csv_completos"]).read_text().splitlines())==n+1
    assert report["cobertura_por_temporada"]["2019"]["finales"]==n


def test_salida_de_otro_pais_no_se_reutiliza(tmp_path,capsys):
    seed(tmp_path,"brasil")
    assert colombia(["--desde","2019-10-06","--hasta","2019-10-06","--offline","--salida",str(tmp_path)])==3
    assert "otro país" in capsys.readouterr().err


def test_rechazo_presupuesto_global_entre_torneos_conserva_resultado(tmp_path,monkeypatch,capsys):
    clients=[]
    def factory(archivo,**kw):
        t=kw["torneo"]
        _,b,s=fuente(t,"123" if t==ARGENTINA else "124")
        c,session,_=cliente(archivo.root,t,[Response(payload=b),Response(payload=s)],max_requests=kw["max_requests"])
        clients.append((c,session))
        return c
    monkeypatch.setattr(cli,"ClienteESPN",factory)
    code=argentina(["--desde","2019-10-06","--hasta","2019-10-06","--fetch","--salida",str(tmp_path),"--max-requests","3"])
    r=json.loads(capsys.readouterr().out)
    assert code==3 and r["finales_completos"]==2 and r["finales_con_estadisticas_completas"]==1
    assert r["torneos_pendientes"]==[COPA_SUPERLIGA.slug]
    assert sum(len(s.calls) for _,s in clients)==3


@pytest.mark.parametrize("status,header,seconds",[(429,"120",900),(429,"7200",7200),(429,None,900),(403,None,3600)])
def test_pausa_compartida_impide_nuevos_get_y_conserva_marcador(tmp_path,status,header,seconds):
    wall=Clock();wall.value=1000
    gate=ControlRed(tmp_path/"control",dormir=wall.sleep,reloj=wall.mono)
    _,b,_=fuente(BRASIL)
    c,s,_=cliente(tmp_path/"data",BRASIL,[Response(payload=b),Response(status,headers={"Retry-After":header} if header else {})],gate=gate)
    run,r,code=ejecutar(c,desde=date(2019,10,6),hasta=date(2019,10,6),rondas=1)
    assert code==3 and r["partidos_exportados"]==1 and r["detalles_pendientes"]==1
    assert json.loads((run/"partidos.jsonl").read_text())["local_goles"]==3
    state=json.loads((gate.root/"estado.json").read_bytes())
    assert state["pausa_hasta"]>=1000+seconds
    other,session,_=cliente(tmp_path/"other",COLOMBIA,[Response()],gate=ControlRed(gate.root,dormir=wall.sleep,reloj=wall.mono))
    with pytest.raises(PausaRed):other.obtener("scoreboard","201910")
    assert not session.calls and other.contadores["requests"]==0
    assert len(s.calls)==2


def test_circuito_de_tres_consultas_transitorias_evitan_mas_peticion(tmp_path):
    c,s,_=cliente(tmp_path,BRASIL,[Response(503)]*3,intentos=1)
    for month in ["201901","201902"]:
        with pytest.raises(ConsultaError):c.obtener("scoreboard",month)
    with pytest.raises(FuenteError,match="Tres consultas"):
        c.obtener("scoreboard","201903")
    assert len(s.calls)==3


def test_cobertura_incluye_temporada_2018_con_partido_de_2019(tmp_path):
    e,b,s=fuente(ARGENTINA,phase="superliga-argentina-2018-19")
    e["season"]["year"]=2018
    b["events"]=[e]
    s["header"]["season"]["year"]=2018
    c,_,_=cliente(tmp_path,ARGENTINA,[Response(payload=b),Response(payload=s)])
    _,r,code=ejecutar(c,desde=date(2019,10,6),hasta=date(2019,10,6),rondas=1)
    assert code==0 and r["cobertura_por_temporada"]["2018"]["finales"]==1
    assert r["cobertura_por_temporada"]["2019"]["finales"]==0


@pytest.mark.parametrize("state",[{"proximo_inicio":float("nan")},{"pausa_hasta":-1},[],{"proximo_inicio":"500"}])
def test_estado_de_red_alterado_no_se_ignora(tmp_path,state):
    (tmp_path/"estado.json").write_text(json.dumps(state))
    with pytest.raises(ArchivoError):
        with ControlRed(tmp_path).turno(5):pass


def test_turnos_de_red_se_serializan_entre_procesos(tmp_path):
    program='''
import sys,time,json
sys.path.insert(0,sys.argv[2])
from scrapers.futbol_latam.red import ControlRed
with ControlRed(sys.argv[1]).turno(0.2):
    print(json.dumps({"inicio":time.time()}),flush=True)
    time.sleep(0.1)
    print(json.dumps({"fin":time.time()}),flush=True)
'''
    backend=Path(__file__).resolve().parents[2]
    ps=[subprocess.Popen([sys.executable,"-c",program,str(tmp_path),str(backend)],cwd=backend,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
    intervals=[]
    for p in ps:
        out,err=p.communicate(timeout=10)
        assert p.returncode==0,err
        rows=[json.loads(x) for x in out.splitlines()]
        intervals.append((rows[0]["inicio"],rows[1]["fin"]))
    intervals.sort()
    assert intervals[1][0]>=intervals[0][1] and intervals[1][0]-intervals[0][0]>=0.19


def serie(e, *, aggregate=(4,4), winner="2"):
    c=e["competitions"][0]
    c["leg"]={"value":2}
    c["series"]={"totalCompetitions":2,"completed":True,"competitors":[{"id":t["id"],"winner":t["id"]==winner,"aggregateScore":a} for t,a in zip(c["competitors"],aggregate)]}
    for t,a in zip(c["competitors"],aggregate):
        t.update(aggregateScore=a,winner=t["id"]==winner)


def test_ganador_de_serie_no_se_confunde_con_el_del_partido():
    e=event(score=(4,1))
    serie(e)
    e["uid"]=f"{ARGENTINA.uid}~e:123"
    r=normalizar(e,ARGENTINA)
    assert r["ganador_partido_id"]=="1" and r["ganador_serie_id"]=="2"
    assert r["local_goles"]==4 and r["local_goles_global"]==4


def test_tanda_por_global_empatado_con_vuelta_no_empatada():
    e=event(name="STATUS_FINAL_PEN",score=(3,1))
    e["uid"]=f"{ARGENTINA.uid}~e:123"
    serie(e,winner="1")
    s=summary(e);s["header"]["league"]={"id":ARGENTINA.id,"slug":ARGENTINA.slug,"uid":ARGENTINA.uid}
    for t,points,pen in zip(s["header"]["competitions"][0]["competitors"],[[1,2,5],[0,1,4]],[5,4]):
        t["linescores"]=[{"displayValue":str(v)} for v in points]
        t["shootoutScore"]=pen
    s["keyEvents"]=[{"type":{"type":"start-shootout"},"clock":{"value":5400}}]
    r=enriquecer(normalizar(e,ARGENTINA),s)
    assert r["estadisticas_completas"] and not r["incidencias"]
    assert r["local_goles"]==3 and r["local_goles_90"]==3 and r["local_penales"]==5
    assert r["ganador_tanda_id"]=="1" and r["visitante_goles_global"]==4


def test_summary_puede_aportar_serie_ausente_en_scoreboard():
    e,b,s=fuente(ARGENTINA)
    serie(s["header"],aggregate=(4,4),winner="1")
    r=enriquecer(normalizar(e,ARGENTINA),s)
    assert r["es_ida_vuelta"] is True and r["local_goles_global"]==4


def test_global_inconsistente_no_se_confunde_con_goles_del_encuentro():
    e=event(score=(4,1));e["uid"]=f"{ARGENTINA.uid}~e:123"
    serie(e,aggregate=(2,4))
    with pytest.raises(ContratoError,match="GLOBAL_MENOR_QUE_PARTIDO"):
        normalizar(e,ARGENTINA)


def test_nombre_de_temporada_proviene_de_summary_y_competicion_ajena_se_rechaza():
    e,_,s=fuente(COLOMBIA)
    s["header"]["season"]["name"]="2019 Liga Águila, Apertura"
    r=enriquecer(normalizar(e,COLOMBIA),s)
    assert r["temporada_nombre_fuente"]=="2019 Liga Águila, Apertura"
    s["header"]["competitions"][0]["uid"]=f"{BRASIL.uid}~e:123~c:123"
    with pytest.raises(ContratoError,match="SUMMARY_OTRA_COMPETICION"):
        enriquecer(normalizar(e,COLOMBIA),s)


def test_pausa_se_levanta_al_vencer_sin_borrar_el_estado(tmp_path):
    clock=Clock();clock.value=1000
    gate=ControlRed(tmp_path,dormir=clock.sleep,reloj=clock.mono)
    with gate.turno(5):gate.pausar(900,"HTTP 429")
    clock.value=1901
    with gate.turno(5):pass
    assert json.loads((tmp_path/"estado.json").read_bytes())["proximo_inicio"]==1906


def test_cli_con_fecha_invalida_no_crea_archivos(tmp_path):
    assert brasil(["--desde","2026-12-01","--hasta","2026-01-01","--fetch","--salida",str(tmp_path/"nueva")])==3
    assert not (tmp_path/"nueva").exists()
