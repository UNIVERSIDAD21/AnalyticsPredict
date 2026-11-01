# -*- coding: utf-8 -*-
"""Resolver predicciones de fútbol en tabla predicciones_futbol."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict, Any

from db import obtener_pool

logger = logging.getLogger(__name__)


@dataclass
class ResumenResolucionFutbol:
    resueltas: int = 0
    push: int = 0
    anuladas: int = 0
    pendientes: int = 0
    sin_datos_partido: int = 0
    errores: int = 0
    detalles_errores: List[str] = field(default_factory=list)
    motivos_pendientes: Dict[str, int] = field(default_factory=dict)
    simulacion: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resueltas": self.resueltas,
            "push": self.push,
            "anuladas": self.anuladas,
            "pendientes": self.pendientes,
            "sin_datos_partido": self.sin_datos_partido,
            "errores": self.errores,
            "detalles_errores": self.detalles_errores[:10],
            "motivos_pendientes": self.motivos_pendientes,
            "simulacion": self.simulacion,
        }


def _valor_real_futbol(mercado: str, fila_partido: Dict[str, Any]) -> Optional[float]:
    """Mismo contrato observado que la elegibilidad, nunca FT por una mitad."""
    from motor.resolucion_analitica import valor_futbol
    return valor_futbol(mercado, fila_partido)[0]


def resolver_predicciones_futbol(
    *, limite: int = 2000, mercado: Optional[str] = None,
    solo_hasta_fecha: Optional[date] = None, force: bool = False,
    pool=None, simular: bool = False,
) -> ResumenResolucionFutbol:
    """Solo no resueltas; POSPUESTO/SUSPENDIDO no son outcomes terminales.

    Los resultados antiguos requieren auditoría y reparación expresamente acotada;
    force no puede reescribir silenciosamente cohortes utilizadas para métricas.
    """
    from collections import Counter
    from psycopg.rows import dict_row
    from motor.resolucion_analitica import valor_futbol, comparar, instante

    if force:
        raise ValueError('No se reabren predicciones resueltas; auditar antes de reparar')
    if not 1 <= limite <= 20000:
        raise ValueError('Límite fuera de rango')
    resumen = ResumenResolucionFutbol()
    motivos = Counter()
    condiciones = ['pfu.resuelto IS NOT TRUE']
    params = []
    if mercado:
        condiciones.append('pfu.mercado::text=%s')
        params.append(mercado.upper())
    if solo_hasta_fecha:
        condiciones.append('pfu.fecha_partido<=%s')
        params.append(solo_hasta_fecha)
    params.append(limite)
    consulta = f"""SELECT pfu.id,pfu.mercado::text, pfu.linea,to_jsonb(pf) partido
        FROM predicciones_futbol pfu LEFT JOIN partidos_futbol pf ON pf.id=pfu.partido_id
        WHERE {' AND '.join(condiciones)} ORDER BY pfu.fecha_partido,pfu.id LIMIT %s"""
    if not simular:
        consulta += ' FOR UPDATE OF pfu SKIP LOCKED'
    with (pool or obtener_pool()).connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            if simular:
                cursor.execute('SET TRANSACTION READ ONLY')
            ahora = cursor.execute('SELECT clock_timestamp() ahora').fetchone()['ahora']
            for fila in cursor.execute(consulta, params).fetchall():
                p = fila['partido']
                motivo = None
                if not p or p.get('valido') is not True:
                    motivo = 'PARTIDO_AUSENTE_O_INVALIDO'
                elif p.get('estado') != 'FINALIZADO':
                    motivo = 'PARTIDO_NO_FINALIZADO'
                else:
                    fecha = instante(p.get('fecha_partido'))
                    if fecha is None or fecha > ahora:
                        motivo = 'FECHA_NO_ACREDITADA_O_FUTURA'
                if motivo is None:
                    valor, motivo = valor_futbol(fila['mercado'], p)
                if motivo is None:
                    relacion, motivo = comparar(valor, fila['linea'])
                if motivo:
                    motivos[motivo] += 1
                    resumen.pendientes += 1
                    if motivo != 'PARTIDO_NO_FINALIZADO':
                        resumen.sin_datos_partido += 1
                    continue
                try:
                    if not simular:
                        with conn.transaction():
                            cursor.execute("""UPDATE predicciones_futbol SET valor_real=%s,
                                outcome_binario=%s,resultado=%s,resuelto=true,
                                timestamp_resolucion=clock_timestamp(),actualizado_en=clock_timestamp()
                                WHERE id=%s AND resuelto IS NOT TRUE""",
                                (valor, None if relacion == 'PUSH' else relacion == 'OVER', relacion, fila['id']))
                            if cursor.rowcount != 1:
                                raise RuntimeError('Predicción cambió durante resolución')
                    resumen.resueltas += 1
                    resumen.push += int(relacion == 'PUSH')
                except Exception:
                    resumen.errores += 1
                    resumen.detalles_errores.append(f"prediccion_id={fila['id']}: no se modificó el registro")
    resumen.motivos_pendientes = dict(motivos)
    resumen.simulacion = simular
    return resumen
