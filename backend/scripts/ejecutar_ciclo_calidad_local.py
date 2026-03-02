#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ejecuta ciclo de calidad local y muestra resumen compacto."""

from __future__ import annotations

import argparse
import asyncio

from api.rutas_internas import ejecutar_ciclo_calidad


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecutar ciclo de calidad local")
    parser.add_argument("--limite-baloncesto", type=int, default=2000)
    parser.add_argument("--limite-futbol", type=int, default=3000)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    respuesta = await ejecutar_ciclo_calidad(limite_baloncesto=args.limite_baloncesto, limite_futbol=args.limite_futbol)
    print('exito:', respuesta.exito)
    print('mensaje:', respuesta.mensaje)


if __name__ == '__main__':
    asyncio.run(main())
