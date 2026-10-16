"""Registro Ridge fútbol sobre el esquema canónico, con artefacto JSON íntegro.

Guardar no activa. Activar valida antes de desactivar y no promociona mercados.
No requiere DDL ni archivos externos; usa metadata JSONB ya existente.
"""
from datetime import datetime

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ..modelos.artefacto import exportar, sha256, cargar_registro
from ..modelos.base import ModeloPrediccionBase
from ..tipos import TipoModelo


MERCADOS = {TipoModelo.CORNERS: 'CORNERS_FT', TipoModelo.GOLES: 'GOLES_FT', TipoModelo.DISPAROS: 'DISPAROS_FT'}


class GestorVersiones:
    def __init__(self, pool):
        self._pool = pool

    @staticmethod
    def _bloquear(cursor, tipo):
        cursor.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ['ridge_futbol_' + tipo.value])

    def guardar_lote(self, modelos, activar=False):
        """Publicación atómica de familias: todos los artefactos o ninguno."""
        preparados = []
        for modelo in modelos:
            if not isinstance(modelo, ModeloPrediccionBase):
                raise ValueError('Se requiere el modelo entrenado, no solo sus métricas')
            payload = exportar(modelo)
            dataset = payload['dataset']
            if dataset.get('politica') != 'final_valido_targets_completos_coherentes_v1' or len(dataset.get('hash_sha256', '')) != 64 or not dataset.get('n_partidos'):
                raise ValueError('Dataset efectivo sin procedencia verificable')
            if dataset['n_filas_diseno'] != 2*dataset['n_partidos'] or dataset['equipos'] != modelo.obtener_equipos():
                raise ValueError('Dataset y diseño Ridge no corresponden')
            if not dataset.get('fecha_min') or not dataset.get('fecha_max'):
                raise ValueError('Faltan fechas del dataset efectivo')
            preparados.append((modelo, payload))
        if not preparados or len({m.tipo for m, _ in preparados}) != len(preparados):
            raise ValueError('Lote vacío o familias duplicadas')
        ids = {}
        with self._pool.connection() as conn:
            with conn.transaction(), conn.cursor(row_factory=dict_row) as cursor:
                for modelo, payload in sorted(preparados, key=lambda par: par[0].tipo.value):
                    self._bloquear(cursor, modelo.tipo)
                    mercado = MERCADOS[modelo.tipo]
                    version = cursor.execute('SELECT COALESCE(MAX(version),0)+1 AS siguiente FROM modelo_versiones_futbol WHERE mercado_principal=%s', [mercado]).fetchone()['siguiente']
                    dataset = payload['dataset']
                    metadata = {'tipo_modelo': modelo.tipo.value, 'artefacto': payload, 'artefacto_sha256': sha256(payload)}
                    registro = cursor.execute('''INSERT INTO modelo_versiones_futbol
                        (version,nombre,mercado_principal,fecha_entrenamiento,cutoff_entrenamiento,
                         fecha_min_entrenamiento,fecha_max_entrenamiento,partidos_entrenamiento,equipos,
                         hash_datos,config_entrenamiento,metadata,activo)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE) RETURNING *''',
                        [version, 'Ridge ' + modelo.tipo.value, mercado, modelo.fecha_entrenamiento,
                         dataset.get('config', {}).get('fecha_corte'), dataset['fecha_min'][:10], dataset['fecha_max'][:10],
                         dataset['n_partidos'], modelo.cantidad_equipos, dataset['hash_sha256'][:32],
                         Jsonb(dataset.get('config', {})), Jsonb(metadata)]).fetchone()
                    cargar_registro(registro)  # Verifica lo realmente almacenado antes del commit.
                    if activar:
                        cursor.execute('UPDATE modelo_versiones_futbol SET activo=FALSE WHERE mercado_principal=%s AND activo IS TRUE', [mercado])
                        cursor.execute('UPDATE modelo_versiones_futbol SET activo=TRUE WHERE id=%s', [registro['id']])
                    ids[modelo.tipo.value] = registro['id']
        for modelo, _ in preparados:
            modelo.version_id = ids[modelo.tipo.value]
        return ids

    def guardar_modelo(self, modelo, tipo=None):
        if tipo is not None and modelo.tipo != TipoModelo(tipo):
            raise ValueError('Familia distinta de la del modelo')
        return self.guardar_lote([modelo])[modelo.tipo.value]

    def activar_version(self, tipo_modelo, version_id):
        tipo = TipoModelo(tipo_modelo)
        with self._pool.connection() as conn:
            with conn.transaction(), conn.cursor(row_factory=dict_row) as cursor:
                self._bloquear(cursor, tipo)
                registro = cursor.execute('SELECT * FROM modelo_versiones_futbol WHERE id=%s FOR UPDATE', [version_id]).fetchone()
                if not registro or registro['mercado_principal'] != MERCADOS[tipo]:
                    raise ValueError('La versión solicitada no existe para esta familia')
                cargar_registro(registro)
                cursor.execute('UPDATE modelo_versiones_futbol SET activo=FALSE WHERE mercado_principal=%s AND activo IS TRUE', [MERCADOS[tipo]])
                cursor.execute('UPDATE modelo_versiones_futbol SET activo=TRUE WHERE id=%s', [version_id])

    def obtener_activa(self, tipo_modelo):
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                filas = cursor.execute('SELECT * FROM modelo_versiones_futbol WHERE mercado_principal=%s AND activo IS TRUE ORDER BY id DESC', [MERCADOS[TipoModelo(tipo_modelo)]]).fetchall()
        if len(filas) > 1:
            raise ValueError('Más de una versión activa para la misma familia')
        return filas[0] if filas else None

    def obtener_activas(self):
        """Las tres familias se observan en un único snapshot SQL de solo lectura."""
        with self._pool.connection() as conn:
            with conn.transaction(), conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute('SET TRANSACTION READ ONLY')
                return cursor.execute('SELECT * FROM modelo_versiones_futbol WHERE activo IS TRUE ORDER BY id DESC').fetchall()

    def cargar_modelo(self, tipo_modelo, version_id=None):
        registro = self.obtener_version_por_id(version_id) if version_id is not None else self.obtener_activa(tipo_modelo)
        if registro is None:
            return None
        if registro['mercado_principal'] != MERCADOS[TipoModelo(tipo_modelo)]:
            raise ValueError('Versión de otra familia')
        return cargar_registro(registro)

    def obtener_version_por_id(self, version_id):
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                return cursor.execute('SELECT * FROM modelo_versiones_futbol WHERE id=%s', [version_id]).fetchone()

    def obtener_historial(self, tipo_modelo, limite=10):
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                return cursor.execute('''SELECT id,version,fecha_entrenamiento,partidos_entrenamiento,equipos,mae_general,activo
                    FROM modelo_versiones_futbol WHERE mercado_principal=%s ORDER BY id DESC LIMIT %s''', [MERCADOS[TipoModelo(tipo_modelo)], limite]).fetchall()

    def generar_version(self):
        """Etiqueta informativa legacy; la versión persistida es un entero por familia."""
        return f"v1.0.0_{datetime.now().strftime('%Y%m%d')}"
