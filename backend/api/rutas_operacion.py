"""Estado operativo local: solo lecturas; jamás ingiere, entrena o resuelve."""
from datetime import datetime, timezone

from fastapi import APIRouter,HTTPException
from psycopg.rows import dict_row

from db import obtener_pool
from motor_autoentrenamiento.artefacto_nba import cargar_artefacto
from motor_autoentrenamiento.dominio_nba import FILTRO_NBA_ENTRENABLE

router=APIRouter(prefix='/api/operacion',tags=['Operación local'])


def leer_estado(conn):
    with conn.cursor(row_factory=dict_row) as c:
        nba=c.execute(f'''SELECT count(*) n,max(p.fecha_partido) ultima_fecha,
            max(p.fecha_partido) FILTER(WHERE {FILTRO_NBA_ENTRENABLE}) ultimo_final,
            count(*) FILTER(WHERE p.valido IS FALSE) invalidados
            FROM partidos_baloncesto p JOIN competiciones_baloncesto cb ON cb.id=p.competicion_id WHERE cb.codigo='nba' ''').fetchone()
        futbol=c.execute('''SELECT count(*) n,max(fecha_partido) ultima_fecha,
            max(fecha_partido) FILTER(WHERE estado='FINALIZADO' AND valido AND local_goles_total IS NOT NULL AND visitante_goles_total IS NOT NULL) ultimo_final,
            count(*) FILTER(WHERE estado='FINALIZADO' AND valido AND local_goles_total IS NOT NULL AND visitante_goles_total IS NOT NULL) finales_evaluables
            FROM partidos_futbol''').fetchone()
        capturas={'estado':'ALMACEN_NO_INSTALADO','observado_en':None,'lotes':None}
        if c.execute("SELECT to_regclass('public.capturas_espn_soccer_lotes') AS tabla").fetchone()['tabla']:
            capturas=c.execute('SELECT count(*) lotes,max(observado_en) observado_en FROM capturas_espn_soccer_lotes').fetchone()
            capturas['estado']='CAPTURADO' if capturas['lotes'] else 'SIN_CAPTURA'
        nba_job=None
        if c.execute("SELECT to_regclass('public.ingestion_state_baloncesto') AS tabla").fetchone()['tabla']:
            nba_job=c.execute("SELECT ultima_exito,ultima_error,ultimo_error,ultimo_insertados,ultimo_actualizados,cursor_fecha FROM ingestion_state_baloncesto WHERE clave='nba_partidos'").fetchone()
        prospectiva={'congeladas':None,'resueltas':None,'estado':'ALMACEN_NO_INSTALADO'}
        if c.execute("SELECT to_regclass('public.predicciones_prospectivas') AS tabla").fetchone()['tabla']:
            prospectiva['congeladas']=c.execute('SELECT count(*) n FROM predicciones_prospectivas').fetchone()['n']
            prospectiva['resueltas']=c.execute('SELECT count(*) n FROM outcomes_prospectivos').fetchone()['n']
            prospectiva['estado']='ESPERANDO_OUTCOMES' if prospectiva['congeladas']>prospectiva['resueltas'] else 'SIN_CAPTURAS' if not prospectiva['congeladas'] else 'EVALUACION_PENDIENTE'
        modelos_futbol=[]
        if c.execute("SELECT to_regclass('public.modelo_versiones_futbol') AS tabla").fetchone()['tabla']:
            modelos_futbol=c.execute('SELECT id,mercado_principal,version,fecha_entrenamiento,cutoff_entrenamiento,partidos_entrenamiento FROM modelo_versiones_futbol WHERE activo=true ORDER BY fecha_entrenamiento DESC LIMIT 20').fetchall()
        return {'nba':dict(nba),'futbol':dict(futbol),'capturas_futbol':capturas,
                'ultimo_job_nba':nba_job,'prospectiva':prospectiva,'versiones_futbol_registradas':modelos_futbol,
                'predictor_ml_futbol': {'estado':'SIN_CARGA_PERSISTIDA_IMPLEMENTADA',
                    'motivo':'La ruta sin archivos inicializa modelos vacíos; no recarga versiones de BD.'}}


@router.get('/estado')
def estado_operacion():
    try:
        with obtener_pool().connection() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            conn.execute("SET LOCAL statement_timeout='10s'")
            datos=leer_estado(conn)
    except Exception as exc:
        raise HTTPException(503,detail={'estado':'ALMACEN_NO_DISPONIBLE','mensaje':'No se pudo consultar el estado operativo'}) from exc
    try:
        modelo=cargar_artefacto()
        datos['modelo_nba']={'estado':'DISPONIBLE','version':modelo['modelo_version_id'],
                            'equipos':len(modelo['entidad_a_indice']),
                            'ultimo_dato':modelo['metricas'].get('training_data_latest_game_date'),
                            'dominio':modelo['metricas'].get('dominio')} if modelo else {'estado':'NO_DISPONIBLE'}
    except (ValueError,OSError,KeyError):
        datos['modelo_nba']={'estado':'ARTEFACTO_NO_APTO'}
    datos.update(observado_en=datetime.now(timezone.utc).isoformat(),certificacion='NO_CERTIFICADO',
                 modo='EXPLORATORIO',notas=[
                     'Disponibilidad técnica no certifica probabilidades ni rentabilidad.',
                     'Capturas FT de ESPN no completan automáticamente primer/segundo tiempo.',
                     'Una versión de fútbol registrada no demuestra que el predictor la haya cargado.',
                 ])
    return datos
