"""Estado local y activación acotada del servicio de fuentes; nunca por tarjeta."""
import subprocess
import os
from pathlib import Path
import sys
from fastapi import APIRouter, HTTPException
from servicios.operacion_agendas import estado_local

router=APIRouter(prefix='/api/agendas',tags=['Agendas'])


@router.get('/sincronizacion')
def estado_sincronizacion():
    return estado_local()


@router.post('/sincronizar',status_code=202)
def solicitar_sincronizacion():
    if os.environ.get('ANALYTICSPREDICT_SOLO_BASE_LOCAL') == '1':
        raise HTTPException(409, 'Modo base local: sincronización deshabilitada. No se consultan fuentes ni BD.')
    if os.name == 'nt':
        # Operación única y explícita, no instala un timer ni arranca por GET.
        # El runner conserva exclusión, respaldo previo, transacción y recibos.
        backend = Path(__file__).resolve().parents[1]
        try:
            subprocess.Popen([sys.executable, str(backend / 'scripts/sincronizar_agendas.py'), '--aplicar'],
                cwd=backend, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as exc:
            raise HTTPException(503, 'No se pudo iniciar la sincronización local; los datos previos se conservan.') from exc
        return {'estado': 'SOLICITADA', 'detalle': 'Sincronización puntual solicitada. No acredita finalización ni cambios guardados; consulta su estado. No se instaló una tarea periódica.'}
    try:
        r=subprocess.run(['systemctl','--user','start','--no-block','analyticspredict-agendas.service'],
            capture_output=True,timeout=3,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise HTTPException(503,'Servicio local no disponible; consultar la BD sigue disponible.') from exc
    if r.returncode:
        raise HTTPException(503,'Sincronización local no instalada o no disponible. Revisar la operación documentada.')
    return {'estado':'SOLICITADA','detalle':'Verificación de fuentes solicitada al servicio local. No implica que haya terminado ni que se guardaran cambios; refresca el estado para comprobarlo.'}
