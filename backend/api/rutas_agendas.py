"""Estado local y activación acotada del servicio de fuentes; nunca por tarjeta."""
import subprocess
from fastapi import APIRouter, HTTPException
from servicios.operacion_agendas import estado_local

router=APIRouter(prefix='/api/agendas',tags=['Agendas'])


@router.get('/sincronizacion')
def estado_sincronizacion():
    return estado_local()


@router.post('/sincronizar',status_code=202)
def solicitar_sincronizacion():
    try:
        r=subprocess.run(['systemctl','--user','start','--no-block','analyticspredict-agendas.service'],
            capture_output=True,timeout=3,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise HTTPException(503,'Servicio local no disponible; consultar la BD sigue disponible.') from exc
    if r.returncode:
        raise HTTPException(503,'Sincronización local no instalada o no disponible. Revisar la operación documentada.')
    return {'estado':'SOLICITADA','detalle':'Verificación de fuentes solicitada al servicio local. No implica que haya terminado ni que se guardaran cambios; refresca el estado para comprobarlo.'}
