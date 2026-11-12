"""Estado local y activación acotada del servicio de fuentes; nunca por tarjeta."""
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from fastapi import APIRouter, HTTPException
from servicios.operacion_agendas import estado_local
from servicios.actualizacion_ligas import obtener_actualizacion_ligas
from servicios import cola_actualizador as cola
from db import obtener_pool

router=APIRouter(prefix='/api/agendas',tags=['Agendas'])


@router.get('/sincronizacion')
def estado_sincronizacion():
    estado = estado_local()
    if os.environ.get('ANALYTICSPREDICT_SOLO_BASE_LOCAL') == '1':
        return {**estado, 'actualizacion_ligas': None}
    try:
        with obtener_pool().connection() as conn, conn.transaction():
            conn.execute('SET TRANSACTION READ ONLY')
            estado = cola.estado_compatible(conn, estado, datetime.now(timezone.utc))
        return {**estado, 'actualizacion_ligas': obtener_actualizacion_ligas()}
    except Exception:
        # El fallo de frescura no bloquea el calendario ni expone detalles SQL.
        return {**estado, 'actualizacion_ligas': None,
                'error_actualizacion': 'No se pudo consultar la última actualización de las ligas.'}


@router.post('/sincronizar',status_code=202)
def solicitar_sincronizacion():
    if os.environ.get('ANALYTICSPREDICT_SOLO_BASE_LOCAL') == '1':
        raise HTTPException(409, 'Modo base local: sincronización deshabilitada. No se consultan fuentes ni BD.')
    if os.name == 'nt':
        # Operación única y explícita, no instala un timer ni arranca por GET.
        # El runner conserva exclusión, respaldo previo, transacción y recibos.
        backend = Path(__file__).resolve().parents[1]
        execution = None
        try:
            with obtener_pool().connection() as conn, conn.transaction():
                if cola.disponible(conn):
                    execution, new = cola.reservar(conn, datetime.now(timezone.utc))
                    if not new:
                        return {'estado': 'SOLICITADA', 'ejecucion_id': str(execution),
                                'detalle': 'Se reutiliza la actualización ya solicitada.'}
            command = [sys.executable, str(backend / 'scripts/sincronizar_agendas.py'), '--aplicar']
            if execution:
                command = [sys.executable, str(backend / 'scripts/actualizar_partidos_local.py'),
                           '--aplicar', '--ejecucion-id', str(execution)]
            subprocess.Popen(command,
                cwd=backend, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as exc:
            if execution:
                with obtener_pool().connection() as conn, conn.transaction():
                    cola.finalizar(conn, execution, 'ERROR', datetime.now(timezone.utc), {'causa': 'ARRANQUE_WORKER'})
            raise HTTPException(503, 'No se pudo iniciar la sincronización local; los datos previos se conservan.') from exc
        state = {'estado': 'SOLICITADA', 'detalle': 'Sincronización puntual solicitada. No acredita finalización ni cambios guardados; consulta su estado. No se instaló una tarea periódica.'}
        if execution:
            state['ejecucion_id'] = str(execution)
        return state
    try:
        r=subprocess.run(['systemctl','--user','start','--no-block','analyticspredict-agendas.service'],
            capture_output=True,timeout=3,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise HTTPException(503,'Servicio local no disponible; consultar la BD sigue disponible.') from exc
    if r.returncode:
        raise HTTPException(503,'Sincronización local no instalada o no disponible. Revisar la operación documentada.')
    return {'estado':'SOLICITADA','detalle':'Verificación de fuentes solicitada al servicio local. No implica que haya terminado ni que se guardaran cambios; refresca el estado para comprobarlo.'}
