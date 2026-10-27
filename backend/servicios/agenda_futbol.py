"""Estado de presentación y elegibilidad temporal, sin inventar estados de fuente."""
from datetime import datetime


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
