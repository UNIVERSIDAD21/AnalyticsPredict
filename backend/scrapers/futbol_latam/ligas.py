"""Identidades ESPN verificadas; nunca deducir IDs del archivo del logotipo."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Torneo:
    codigo: str
    slug: str
    id: str
    pais: str
    nombre: str
    copa: bool = False

    @property
    def uid(self):
        return f"s:600~l:{self.id}"


ARGENTINA = Torneo("argentina_primera", "arg.1", "745", "Argentina", "Liga Profesional / Primera División")
COPA_LIGA = Torneo("argentina_copa_liga", "arg.copa_lpf", "20243", "Argentina", "Copa de la Liga Profesional", True)
COPA_SUPERLIGA = Torneo("argentina_copa_superliga", "arg.copa_de_la_superliga", "19264", "Argentina", "Copa de la Superliga", True)
BRASIL = Torneo("brasil_serie_a", "bra.1", "630", "Brasil", "Brasileirão Série A")
COLOMBIA = Torneo("colombia_primera_a", "col.1", "650", "Colombia", "Primera A")
POR_PAIS = {"argentina": (ARGENTINA, COPA_LIGA, COPA_SUPERLIGA), "brasil": (BRASIL,), "colombia": (COLOMBIA,)}
POR_SLUG = {t.slug: t for ts in POR_PAIS.values() for t in ts}


def clasificar_fase(slug, torneo):
    """Etiqueta conservadora: siempre conservar fase_fuente y season_type_fuente."""
    text = slug.lower()
    if "preseason" in text or "pre-season" in text or "friendly" in text:
        return "PRE"
    if any(k in text for k in ("playoff", "quarterfinal", "semifinal", "quadrangular", "cuadrangular", "round-of-")) or text in {"final", "finals"}:
        return "POST"
    if torneo.copa:
        return "COPA"
    if "copa-diego-armando-maradona" in text:
        return "COPA"
    if text in {"regular-season", "apertura", "clausura", "torneo-apertura", "torneo-clausura"} or any(k in text for k in ("brasileir", "argentine-liga-profesional", "argentine-superliga", "argentine-primera", "superliga-argentina")):
        return "REG"
    return "OTRA"
