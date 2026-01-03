# -*- coding: utf-8 -*-
"""
utilidades.py — Funciones auxiliares del motor de predicción.

IMPORTANTE: Este archivo DEBE estar en backend/motor/utilidades.py
El mapeo MAPEO_NOMBRES_ALTERNATIVOS debe coincidir con el de setup_completo.py
"""

from __future__ import annotations

import re
import math
from typing import Optional, Dict, Tuple


# ══════════════════════════════════════════════════════════════
# MAPEO DE NOMBRES ALTERNATIVOS
# CRÍTICO: Este mapeo DEBE coincidir con el de setup_completo.py
# ══════════════════════════════════════════════════════════════

MAPEO_NOMBRES_ALTERNATIVOS = {
    "la clippers": "los angeles clippers",
    "la lakers": "los angeles lakers",
}


def normalizar_nombre(texto: str) -> str:
    """
    Normaliza el nombre de un equipo para comparaciones consistentes.
    
    CRÍTICO: Esta función DEBE producir el mismo resultado que
    normalize_name() en setup_completo.py
    """
    texto = (texto or "").strip().lower()
    texto = texto.replace("_", " ")
    texto = re.sub(r"\s+", " ", texto)
    return MAPEO_NOMBRES_ALTERNATIVOS.get(texto, texto)


def formatear_porcentaje(probabilidad: float, decimales: int = 1) -> str:
    """Formatea una probabilidad (0-1) como porcentaje."""
    return f"{probabilidad * 100:.{decimales}f}%"


def formatear_puntos(puntos: float, decimales: int = 1) -> str:
    """Formatea puntos con decimales."""
    return f"{puntos:.{decimales}f}"


def limitar_entre_0_y_1(valor: float) -> float:
    """Limita un valor al rango [0, 1]."""
    return max(0.0, min(1.0, float(valor)))


def es_probabilidad_valida(valor: float) -> bool:
    """Verifica si un valor es una probabilidad válida."""
    return 0.0 <= valor <= 1.0


def parsear_lineas(texto: Optional[str]) -> Dict[str, float]:
    """Parsea líneas en formato 'Q1:57.5,Q2:55.5'."""
    if not texto:
        return {}

    resultado: Dict[str, float] = {}
    partes = [p.strip() for p in texto.split(",") if p.strip()]

    for parte in partes:
        if ":" not in parte:
            raise ValueError(f'Línea inválida "{parte}".')

        clave, valor = parte.split(":", 1)
        clave = clave.strip().upper()
        valor = valor.strip()

        if clave not in ("Q1", "Q2", "Q3", "Q4"):
            raise ValueError(f'Cuarto inválido "{clave}".')

        try:
            resultado[clave] = float(valor)
        except ValueError as exc:
            raise ValueError(f'Valor inválido "{valor}" para {clave}.') from exc

    return resultado


def parsear_marcador(texto: Optional[str]) -> Optional[Tuple[float, float]]:
    """Parsea marcador en formato '28-32'."""
    if not texto:
        return None

    texto = texto.strip()
    patron = r"^\s*(\d+(?:\.\d+)?)\s*[-:]\s*(\d+(?:\.\d+)?)\s*$"
    match = re.fullmatch(patron, texto)
    if match:
        return float(match.group(1)), float(match.group(2))

    patron2 = r"^\s*(?:team|equipo)\s*[:=]\s*(\d+(?:\.\d+)?)\s*,\s*(?:opp|rival)\s*[:=]\s*(\d+(?:\.\d+)?)\s*$"
    match = re.fullmatch(patron2, texto, flags=re.IGNORECASE)
    if match:
        return float(match.group(1)), float(match.group(2))

    raise ValueError(f'Formato de marcador inválido: "{texto}".')


def cdf_normal(z: float) -> float:
    """CDF de la normal estándar."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calcular_intervalo_confianza(media: float, desviacion: float, z: float = 1.0) -> Tuple[float, float]:
    """Calcula intervalo de confianza simétrico."""
    margen = z * desviacion
    return media - margen, media + margen


# ══════════════════════════════════════════════════════════════
# INFORMACIÓN DE EQUIPOS NBA
# ══════════════════════════════════════════════════════════════

ABREVIATURAS_NBA = {
    "atlanta hawks": "ATL",
    "boston celtics": "BOS",
    "brooklyn nets": "BKN",
    "charlotte hornets": "CHA",
    "chicago bulls": "CHI",
    "cleveland cavaliers": "CLE",
    "dallas mavericks": "DAL",
    "denver nuggets": "DEN",
    "detroit pistons": "DET",
    "golden state warriors": "GSW",
    "houston rockets": "HOU",
    "indiana pacers": "IND",
    "los angeles clippers": "LAC",
    "los angeles lakers": "LAL",
    "memphis grizzlies": "MEM",
    "miami heat": "MIA",
    "milwaukee bucks": "MIL",
    "minnesota timberwolves": "MIN",
    "new orleans pelicans": "NOP",
    "new york knicks": "NYK",
    "oklahoma city thunder": "OKC",
    "orlando magic": "ORL",
    "philadelphia 76ers": "PHI",
    "phoenix suns": "PHX",
    "portland trail blazers": "POR",
    "sacramento kings": "SAC",
    "san antonio spurs": "SAS",
    "toronto raptors": "TOR",
    "utah jazz": "UTA",
    "washington wizards": "WAS",
}

NOMBRES_CORTOS_NBA = {
    "atlanta hawks": "Hawks",
    "boston celtics": "Celtics",
    "brooklyn nets": "Nets",
    "charlotte hornets": "Hornets",
    "chicago bulls": "Bulls",
    "cleveland cavaliers": "Cavaliers",
    "dallas mavericks": "Mavericks",
    "denver nuggets": "Nuggets",
    "detroit pistons": "Pistons",
    "golden state warriors": "Warriors",
    "houston rockets": "Rockets",
    "indiana pacers": "Pacers",
    "los angeles clippers": "Clippers",
    "los angeles lakers": "Lakers",
    "memphis grizzlies": "Grizzlies",
    "miami heat": "Heat",
    "milwaukee bucks": "Bucks",
    "minnesota timberwolves": "Timberwolves",
    "new orleans pelicans": "Pelicans",
    "new york knicks": "Knicks",
    "oklahoma city thunder": "Thunder",
    "orlando magic": "Magic",
    "philadelphia 76ers": "76ers",
    "phoenix suns": "Suns",
    "portland trail blazers": "Trail Blazers",
    "sacramento kings": "Kings",
    "san antonio spurs": "Spurs",
    "toronto raptors": "Raptors",
    "utah jazz": "Jazz",
    "washington wizards": "Wizards",
}


def obtener_abreviatura(nombre: str) -> str:
    """Obtiene abreviatura de un equipo NBA."""
    nombre_norm = normalizar_nombre(nombre)
    if nombre_norm in ABREVIATURAS_NBA:
        return ABREVIATURAS_NBA[nombre_norm]
    for nc, ab in ABREVIATURAS_NBA.items():
        if nombre_norm in nc or nc in nombre_norm:
            return ab
    return nombre_norm[:3].upper()


def obtener_nombre_corto(nombre: str) -> str:
    """Obtiene nombre corto de un equipo NBA."""
    nombre_norm = normalizar_nombre(nombre)
    if nombre_norm in NOMBRES_CORTOS_NBA:
        return NOMBRES_CORTOS_NBA[nombre_norm]
    for nc, short in NOMBRES_CORTOS_NBA.items():
        if nombre_norm in nc:
            return short
    partes = nombre.strip().split()
    return partes[-1].title() if partes else nombre.title()


def obtener_nombre_completo(identificador: str) -> Optional[str]:
    """Obtiene nombre completo desde cualquier identificador."""
    id_norm = normalizar_nombre(identificador)
    
    if id_norm in ABREVIATURAS_NBA:
        return id_norm.title()
    
    id_upper = identificador.strip().upper()
    for nombre, abrev in ABREVIATURAS_NBA.items():
        if abrev == id_upper:
            return nombre.title()
    
    for nombre_completo, nombre_corto in NOMBRES_CORTOS_NBA.items():
        if id_norm == normalizar_nombre(nombre_corto):
            return nombre_completo.title()
    
    for nombre_completo in ABREVIATURAS_NBA.keys():
        if id_norm in nombre_completo:
            return nombre_completo.title()
    
    return None