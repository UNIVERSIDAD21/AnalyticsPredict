"""Contrato único del dataset Ridge NBA (no Euroliga ni placeholders)."""

DOMINIO = "nba"
POLITICA_DATOS = "nba_finales_validos_v1"

# Alias p obligatorio. Comparaciones NULL se excluyen deliberadamente.
FILTRO_NBA = """EXISTS (
    SELECT 1 FROM competiciones_baloncesto dominio
    WHERE dominio.id = p.competicion_id AND dominio.codigo = 'nba'
)"""
FILTRO_NBA_ENTRENABLE = FILTRO_NBA + """
    AND p.valido IS TRUE
    AND p.local_total > 0 AND p.visitante_total > 0
    AND p.local_q1 >= 0 AND p.local_q2 >= 0 AND p.local_q3 >= 0 AND p.local_q4 >= 0
    AND p.visitante_q1 >= 0 AND p.visitante_q2 >= 0 AND p.visitante_q3 >= 0 AND p.visitante_q4 >= 0
    AND p.local_q1 + p.local_q2 + p.local_q3 + p.local_q4 BETWEEN 1 AND p.local_total
    AND p.visitante_q1 + p.visitante_q2 + p.visitante_q3 + p.visitante_q4 BETWEEN 1 AND p.visitante_total
"""
