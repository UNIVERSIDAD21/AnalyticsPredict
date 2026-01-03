# -*- coding: utf-8 -*-
"""
utilidades.py — Funciones auxiliares del motor de predicción.

Este módulo contiene funciones de utilidad que se usan en múltiples
partes del motor: normalización, formateo, validación, etc.
"""

from __future__ import annotations

import re
import math
from typing import Optional, Dict, Tuple


# ══════════════════════════════════════════════════════════════
# NORMALIZACIÓN Y FORMATEO
# ══════════════════════════════════════════════════════════════

def normalizar_nombre(texto: str) -> str:
    """
    Normaliza el nombre de un equipo para comparaciones consistentes.

    Convierte a minúsculas, elimina espacios extras y reemplaza
    guiones bajos por espacios.

    Argumentos:
        texto: Nombre del equipo a normalizar

    Retorna:
        Nombre normalizado en minúsculas
    """
    texto = (texto or "").strip().lower()
    texto = texto.replace("_", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def formatear_porcentaje(probabilidad: float, decimales: int = 1) -> str:
    """
    Formatea una probabilidad (0-1) como porcentaje.

    Argumentos:
        probabilidad: Valor entre 0 y 1
        decimales: Cantidad de decimales a mostrar

    Retorna:
        String formateado como porcentaje
    """
    return f"{probabilidad * 100:.{decimales}f}%"


def formatear_puntos(puntos: float, decimales: int = 1) -> str:
    """
    Formatea puntos con el número especificado de decimales.

    Argumentos:
        puntos: Cantidad de puntos
        decimales: Cantidad de decimales

    Retorna:
        String formateado
    """
    return f"{puntos:.{decimales}f}"


# ══════════════════════════════════════════════════════════════
# VALIDACIÓN Y LÍMITES
# ══════════════════════════════════════════════════════════════

def limitar_entre_0_y_1(valor: float) -> float:
    """
    Limita un valor al rango [0, 1].

    Útil para asegurar que las probabilidades estén en rango válido.

    Argumentos:
        valor: Número a limitar

    Retorna:
        Valor limitado entre 0 y 1
    """
    return max(0.0, min(1.0, float(valor)))


def es_probabilidad_valida(valor: float) -> bool:
    """
    Verifica si un valor es una probabilidad válida (entre 0 y 1).

    Argumentos:
        valor: Número a verificar

    Retorna:
        True si está entre 0 y 1, False en caso contrario
    """
    return 0.0 <= valor <= 1.0


# ══════════════════════════════════════════════════════════════
# PARSEO DE DATOS
# ══════════════════════════════════════════════════════════════

def parsear_lineas(texto: Optional[str]) -> Dict[str, float]:
    """
    Parsea una cadena de líneas en formato "Q1:57.5,Q2:55.5".

    Argumentos:
        texto: Cadena con líneas separadas por coma

    Retorna:
        Diccionario con cuarto como clave y línea como valor

    Raises:
        ValueError: Si el formato es inválido
    """
    if not texto:
        return {}

    resultado: Dict[str, float] = {}
    partes = [p.strip() for p in texto.split(",") if p.strip()]

    for parte in partes:
        if ":" not in parte:
            raise ValueError(
                f'Línea inválida "{parte}". '
                f'Formato esperado: Q1:57.5'
            )

        clave, valor = parte.split(":", 1)
        clave = clave.strip().upper()
        valor = valor.strip()

        cuartos_validos = ("Q1", "Q2", "Q3", "Q4")
        if clave not in cuartos_validos:
            raise ValueError(
                f'Cuarto inválido "{clave}". '
                f'Usa Q1, Q2, Q3 o Q4.'
            )

        try:
            resultado[clave] = float(valor)
        except ValueError as exc:
            raise ValueError(
                f'Valor de línea inválido "{valor}" para {clave}. '
                f'Debe ser un número.'
            ) from exc

    return resultado


def parsear_marcador(texto: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    Parsea un marcador en formato "28-32" o "team=28,opp=32".

    El primer número es siempre los puntos del equipo analizado,
    el segundo es los puntos del rival.

    Argumentos:
        texto: Cadena con el marcador

    Retorna:
        Tupla (puntos_equipo, puntos_rival) o None si texto es vacío

    Raises:
        ValueError: Si el formato es inválido
    """
    if not texto:
        return None

    texto = texto.strip()

    # Formato "28-32" o "28:32"
    patron_simple = r"^\s*(\d+(?:\.\d+)?)\s*[-:]\s*(\d+(?:\.\d+)?)\s*$"
    match = re.fullmatch(patron_simple, texto)
    if match:
        return float(match.group(1)), float(match.group(2))

    # Formato "team=28,opp=32" o "equipo=28,rival=32"
    patron_explicito = (
        r"^\s*(?:team|equipo)\s*[:=]\s*(\d+(?:\.\d+)?)\s*,\s*"
        r"(?:opp|rival)\s*[:=]\s*(\d+(?:\.\d+)?)\s*$"
    )
    match = re.fullmatch(patron_explicito, texto, flags=re.IGNORECASE)
    if match:
        return float(match.group(1)), float(match.group(2))

    raise ValueError(
        f'Formato de marcador inválido: "{texto}". '
        f'Usa formato "28-32" o "equipo=28,rival=32".'
    )


# ══════════════════════════════════════════════════════════════
# MATEMÁTICAS
# ══════════════════════════════════════════════════════════════

def cdf_normal(z: float) -> float:
    """
    Función de distribución acumulativa (CDF) de la normal estándar.

    Calcula P(Z <= z) donde Z ~ Normal(0, 1).

    Argumentos:
        z: Valor z (número de desviaciones estándar desde la media)

    Retorna:
        Probabilidad acumulada entre 0 y 1
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calcular_intervalo_confianza(
    media: float,
    desviacion: float,
    z: float = 1.0
) -> Tuple[float, float]:
    """
    Calcula un intervalo de confianza simétrico.

    Argumentos:
        media: Centro del intervalo
        desviacion: Desviación estándar
        z: Número de desviaciones estándar (1.0 = 68%, 1.96 = 95%)

    Retorna:
        Tupla (límite_inferior, límite_superior)
    """
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
    "la clippers": "LAC",
    "los angeles clippers": "LAC",
    "los angeles lakers": "LAL",
    "la lakers": "LAL",
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
    "la clippers": "Clippers",
    "los angeles clippers": "Clippers",
    "los angeles lakers": "Lakers",
    "la lakers": "Lakers",
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
    """
    Obtiene la abreviatura de un equipo NBA.

    Argumentos:
        nombre: Nombre del equipo (se normaliza automáticamente)

    Retorna:
        Abreviatura de 3 letras o las primeras 3 letras si no se encuentra
    """
    nombre_norm = normalizar_nombre(nombre)

    # Buscar por nombre completo
    if nombre_norm in ABREVIATURAS_NBA:
        return ABREVIATURAS_NBA[nombre_norm]

    # Buscar si el nombre está contenido
    for nombre_completo, abrev in ABREVIATURAS_NBA.items():
        if nombre_norm in nombre_completo or nombre_completo in nombre_norm:
            return abrev

    # Buscar por nombre corto
    for nombre_completo, nombre_corto in NOMBRES_CORTOS_NBA.items():
        if nombre_norm == normalizar_nombre(nombre_corto):
            return ABREVIATURAS_NBA[nombre_completo]

    # Fallback: primeras 3 letras en mayúscula
    return nombre_norm[:3].upper()


def obtener_nombre_corto(nombre: str) -> str:
    """
    Obtiene el nombre corto (mascota) de un equipo NBA.

    Argumentos:
        nombre: Nombre del equipo

    Retorna:
        Nombre corto del equipo
    """
    nombre_norm = normalizar_nombre(nombre)

    if nombre_norm in NOMBRES_CORTOS_NBA:
        return NOMBRES_CORTOS_NBA[nombre_norm]

    # Buscar parcial
    for nombre_completo, nombre_corto in NOMBRES_CORTOS_NBA.items():
        if nombre_norm in nombre_completo:
            return nombre_corto

    # Fallback: última palabra capitalizada
    partes = nombre.strip().split()
    return partes[-1].title() if partes else nombre.title()


def obtener_nombre_completo(identificador: str) -> Optional[str]:
    """
    Intenta obtener el nombre completo de un equipo a partir de cualquier identificador.

    Argumentos:
        identificador: Puede ser nombre completo, corto o abreviatura

    Retorna:
        Nombre completo del equipo o None si no se encuentra
    """
    id_norm = normalizar_nombre(identificador)

    # ¿Es un nombre completo?
    if id_norm in ABREVIATURAS_NBA:
        return id_norm.title()

    # ¿Es una abreviatura?
    id_upper = identificador.strip().upper()
    for nombre, abrev in ABREVIATURAS_NBA.items():
        if abrev == id_upper:
            return nombre.title()

    # ¿Es un nombre corto?
    for nombre_completo, nombre_corto in NOMBRES_CORTOS_NBA.items():
        if id_norm == normalizar_nombre(nombre_corto):
            return nombre_completo.title()

    # Buscar parcial
    for nombre_completo in ABREVIATURAS_NBA.keys():
        if id_norm in nombre_completo:
            return nombre_completo.title()

    return None
