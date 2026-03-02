#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ejecuta ciclo de calidad local y muestra resumen compacto."""

from __future__ import annotations

import asyncio

from api.rutas_internas import ejecutar_ciclo_calidad


async def main() -> None:
    respuesta = await ejecutar_ciclo_calidad(limite_baloncesto=2000, limite_futbol=3000)
    print('exito:', respuesta.exito)
    print('mensaje:', respuesta.mensaje)


if __name__ == '__main__':
    asyncio.run(main())
