"""Almacén personal exclusivo de loopback. Ninguna ruta procede del cliente."""
import ipaddress
import json
import sqlite3
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from servicios import almacen_personal as store

router=APIRouter(prefix='/api/personal', tags=['Mis análisis duradero'])


def local(request: Request):
    try:
        assert ipaddress.ip_address(request.client.host).is_loopback
        assert request.url.hostname in ('127.0.0.1','localhost','::1') and (request.url.port or 80) in (8000,5173)
        origin=request.headers.get('origin')
        if origin:
            parsed=urlsplit(origin)
            assert parsed.scheme in ('http','https') and parsed.hostname in ('127.0.0.1','localhost','::1') and (parsed.port or 80) in (5173,8000)
        if request.method not in ('GET','HEAD'):
            assert request.headers.get('x-ap-personal')=='1'
            assert request.headers.get('content-type','').split(';')[0]=='application/json'
    except (AssertionError,ValueError,AttributeError):
        raise HTTPException(403,'El almacén personal solo admite el acceso local autorizado') from None


def ejecutar(fn):
    try:return fn()
    except store.Conflicto as exc:raise HTTPException(409,str(exc)) from None
    except (ValidationError,ValueError,UnicodeError):raise HTTPException(422,'Datos personales no compatibles; no se sobrescribió el almacén') from None
    except sqlite3.Error as exc:
        if getattr(exc,'sqlite_errorcode',None)==sqlite3.SQLITE_FULL:
            raise HTTPException(507,'No hubo espacio para guardar; los datos anteriores se conservan') from None
        raise HTTPException(503,'Almacén no disponible. Conserva tu copia; puedes reintentar o recuperar el almacén tras un cierre abrupto') from None
    except OSError:raise HTTPException(503,'No se pudo acceder al almacén privado; no se anunció un guardado') from None


@router.get('',dependencies=[Depends(local)])
def leer():return ejecutar(store.leer)


@router.post('',dependencies=[Depends(local)])
async def guardar(request: Request):
    content=bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content)>12_000_000:raise HTTPException(413,'El documento supera12MB; no se sobrescribió')
    def operation():
        def invalid(_):raise ValueError('JSON no finito')
        body=json.loads(content,parse_constant=invalid)
        return store.guardar(store.Cambio.model_validate(body))
    try:return await run_in_threadpool(lambda:ejecutar(operation))
    except RecursionError:raise HTTPException(422,'Documento demasiado profundo') from None


@router.post('/respaldo',dependencies=[Depends(local)])
def respaldar():return ejecutar(store.respaldar)


@router.post('/recuperar',dependencies=[Depends(local)])
def recuperar():return ejecutar(store.recuperar)
