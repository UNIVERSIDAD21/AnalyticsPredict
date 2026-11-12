"""Controles semánticos de cobertura ESPN. Un número presente no basta.

No estima métricas. Solo retira afirmaciones incompatibles o sin cobertura
acreditada y explica cada campo. Los ceros aislados coherentes se conservan.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation

CONTRATO_CALIDAD = 'ESPN_FIELD_COVERAGE_V2'
METRICAS = ('wonCorners', 'totalShots', 'shotsOnTarget')


def numero(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value).strip().removesuffix('%'))
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def goles_regulares_explicitos(payload):
    """Solo goles no autogol con periodo1/2 y fuera de tanda acreditados.

Los details de ESPN pueden carecer de periodo: se exige entonces una unión
única con keyEvents por equipo/reloj, sin inferir periodos del marcador.
"""
    competitions = (payload.get('header') or {}).get('competitions') or []
    competition = competitions[0] if competitions else {}
    events = payload.get('keyEvents') or []
    goals, seen = Counter(), set()
    for detail in competition.get('details') or []:
        if not isinstance(detail, dict):
            continue
        if detail.get('scoringPlay') is not True or detail.get('ownGoal') is not False or detail.get('shootout') is True:
            continue
        team = str((detail.get('team') or {}).get('id', ''))
        clock = (detail.get('clock') or {}).get('value')
        period = (detail.get('period') or {}).get('number')
        if period is not None and (type(period) is not int or period not in (1, 2)):
            continue
        regular = period in (1, 2) and detail.get('shootout') is False
        if not regular:
            matches = [e for e in events if isinstance(e, dict) and e.get('scoringPlay') is True
                and e.get('ownGoal') is not True and str((e.get('team') or {}).get('id', '')) == team
                and clock is not None and (e.get('clock') or {}).get('value') == clock]
            if len(matches) == 1:
                other = (matches[0].get('period') or {}).get('number')
                regular = (type(other) is int and other in (1, 2) and period in (None, other)
                           and matches[0].get('shootout') is False)
                period = other if regular else period
        if regular and team and (team, period, clock) not in seen:
            seen.add((team, period, clock)); goals[team] += 1
    return goals


def evaluar(payload, expected_ids, mapping):
    teams = payload.get('boxscore', {}).get('teams') or []
    stats = {str(t.get('team', {}).get('id', '')):
             {s.get('name'): numero(s.get('displayValue')) for s in t.get('statistics') or [] if isinstance(s, dict)}
             for t in teams}
    ids = [expected_ids['home'], expected_ids['away']]
    goals = goles_regulares_explicitos(payload)
    rejected = {}
    values = [stats.get(t, {}).get(k) for t in ids for k in METRICAS]
    all_zero = all(v is not None and v == 0 for v in values)
    possession = [stats.get(t, {}).get('possessionPct') for t in ids]
    possession_ok = all(v is not None and 0 <= v <= 100 for v in possession) and 99 <= sum(possession) <= 101
    passing_ok = any((stats.get(t, {}).get('totalPasses') or 0) > 0 for t in ids)
    empty_block = all_zero and (not (possession_ok or passing_ok) or any(goals.get(t, 0) for t in ids))
    for metric, fields in mapping.items():
        for side, field in zip(('home', 'away'), fields):
            team = expected_ids[side]
            value = stats.get(team, {}).get(metric)
            if value is None:
                continue
            if empty_block and (metric in METRICAS or metric == 'possessionPct' and not possession_ok):
                rejected[field] = 'BLOQUE_CEROS_SIN_COBERTURA: el bloque no acredita estadísticas observadas coherentes'
            elif metric in ('totalShots', 'shotsOnTarget') and value < goals.get(team, 0):
                rejected[field] = 'GOLES_REGULARES_CONTRADICEN_TIROS: goles no autogol explícitos del periodo1/2 exceden esta métrica'
    return rejected
