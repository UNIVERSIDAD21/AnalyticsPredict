"""Compara finales guardados con el alcance del artefacto; nunca entrena."""
from psycopg.rows import dict_row
from motor_autoentrenamiento.artefacto_nba import cargar_artefacto
from motor_autoentrenamiento.dominio_nba import FILTRO_NBA_ENTRENABLE


def leer_frescura_nba(conn, modelo=None):
    try:
        modelo = modelo or cargar_artefacto()
        if not modelo:
            return {'estado':'NO_VERIFICABLE','motivo':'No hay artefacto NBA disponible.'}
        metadatos = modelo['metricas']
        ultimo = metadatos.get('training_data_latest_game_date')
        if not ultimo:
            return {'estado':'NO_VERIFICABLE','motivo':'El artefacto no declara el último dato.'}
        with conn.cursor(row_factory=dict_row) as c:
            if not c.execute("SELECT to_regclass('public.modelo_versiones') tabla").fetchone()['tabla']:
                return {'estado':'NO_VERIFICABLE','motivo':'Registro de versiones no instalado.'}
            registro = c.execute('SELECT hash_datos,temporadas_incluidas FROM modelo_versiones WHERE id=%s', (modelo['modelo_version_id'],)).fetchone()
            if not registro or registro['hash_datos'] != metadatos.get('hash_datos'):
                return {'estado':'NO_VERIFICABLE','motivo':'No se pudo conciliar artefacto y versión registrada.'}
            temporadas = registro['temporadas_incluidas']
            filtro, params = '', [ultimo]
            if temporadas:
                filtro = ' AND p.temporada_id::text=ANY(%s)'
                params.append([str(t) for t in temporadas])
            filas = c.execute(f'''SELECT COALESCE(p.tipo_partido,'SIN_CLASIFICAR') fase,count(*) n,
                min(p.fecha_partido) primero,max(p.fecha_partido) ultimo
                FROM partidos_baloncesto p WHERE {FILTRO_NBA_ENTRENABLE}
                AND p.fecha_partido>%s {filtro} GROUP BY p.tipo_partido ORDER BY 1''',params).fetchall()
        nuevos = sum(r['n'] for r in filas if r['fase'] != 'PRE')
        return {'estado':'HAY_FINALES_ELEGIBLES_NUEVOS' if nuevos else 'SIN_NUEVOS_ELEGIBLES_GUARDADOS',
                'modelo_version_id':modelo['modelo_version_id'], 'ultimo_dato_artefacto':ultimo,
                'finales_elegibles_nuevos':nuevos,'pretemporada_excluida':sum(r['n'] for r in filas if r['fase']=='PRE'),
                'por_fase':filas,'temporadas_restringidas':[str(t) for t in temporadas] if temporadas else None,
                'criterio':'Solo finales NBA con cuartos válidos y temporadas del artefacto; PRE excluida por el contrato del entrenador. No acredita cobertura oficial ni precisión. No actualiza el modelo.'}
    except (ValueError, KeyError, TypeError, OSError):
        return {'estado':'NO_VERIFICABLE','motivo':'El alcance del artefacto no está disponible.'}
