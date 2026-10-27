"""Estado de presentación y elegibilidad temporal, sin inventar estados de fuente."""
from datetime import datetime


def permite_consulta(estado: str, inicio: datetime, ahora: datetime) -> bool:
    """Todo encuentro iniciado se puede reconstruir; el futuro exige PROGRAMADO."""
    if inicio.tzinfo is None or ahora.tzinfo is None:
        raise ValueError("La consulta requiere instantes con zona horaria")
    return inicio <= ahora or estado.upper() == "PROGRAMADO"


def estado_agenda(estado: str, inicio: datetime, ahora: datetime) -> str:
    if inicio.tzinfo is None or ahora.tzinfo is None:
        raise ValueError("La agenda requiere instantes con zona horaria")
    estado = estado.upper()
    if estado == "PROGRAMADO":
        return "PROXIMO" if inicio > ahora else "POR_VERIFICAR"
    if estado in {"EN_VIVO", "EN_JUEGO", "ENTRETIEMPO", "PRIMER_TIEMPO", "SEGUNDO_TIEMPO", "TIEMPO_EXTRA", "PENALES"}:
        return "EN_JUEGO"
    if estado == "FINALIZADO":
        return "FINALIZADO"
    return "NO_DISPONIBLE"
