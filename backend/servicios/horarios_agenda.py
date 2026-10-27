"""Una hora sólo existe si la fuente acreditó instante y precisión.

La fecha deportiva canónica se conserva para backtests. La agenda usa COT;
el modelo histórico sigue excluyendo el día canónico completo, conservador.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from psycopg.rows import dict_row
from servicios.predictor_euroliga import conexion_lectura

BOGOTA = ZoneInfo('America/Bogota')


def horario_partido(partido_id, *, conexion=None, tabla='horarios_baloncesto'):
    if tabla not in ('horarios_baloncesto','horarios_futbol'):
        raise ValueError('Tabla de horarios no admitida')
    if conexion is None:
        with conexion_lectura() as conn:
            return horario_partido(partido_id, conexion=conn,tabla=tabla)
    with conexion.cursor(row_factory=dict_row) as c:
        if c.execute("SELECT to_regclass(%s) AS tabla",(tabla,)).fetchone()['tabla'] is None:
            return None
        return c.execute('SELECT * FROM '+tabla+' WHERE partido_id=%s', [str(partido_id)]).fetchone()


def requiere_reconstruccion(fecha_canonica, horario, instante=None):
    instante = instante or datetime.now(BOGOTA)
    if instante.tzinfo is None:
        raise ValueError('El reloj requiere zona horaria')
    if horario and horario.get('precision_fecha') == 'HORA' and horario.get('inicio_utc'):
        return horario['estado'] != 'PROGRAMADO' or horario['inicio_utc'] <= instante
    # Sin instante acreditado no se emite un pronóstico prospectivo, incluso
    # si el día nominal es futuro (puede haberse aplazado o cambiado de zona).
    return True
