#!/usr/bin/env python3
"""Diagnostica sin escritura por defecto; entrenamiento/publicación explícitos.

python3 scripts/entrenar_futbol.py --salida cobertura.json
python3 scripts/entrenar_futbol.py --entrenar --guardar [--activar]

Las métricas de ajuste no son validación temporal ni permiten promoción beta.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import obtener_pool, cerrar_pool
from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.entrenamiento.gestor_versiones import GestorVersiones
from motor_futbol.tipos import ConfiguracionEntrenamiento, TipoModelo


def ejecutar(pool, args):
    config = ConfiguracionEntrenamiento(
        competiciones=args.competicion, temporadas=args.temporada_id,
        fecha_corte=args.fecha_corte, alpha_ridge=args.alpha,
        min_partidos_equipo=args.min_partidos_equipo, incluir_copas=False,
    )
    entrenador = EntrenadorFutbol(pool, config=config, min_partidos=args.min_partidos)
    informe = {'certificacion': 'NO_CERTIFICADO', 'dataset': entrenador.diagnosticar_dataset(), 'versiones_guardadas': {}, 'activadas': False}
    if args.entrenar:
        familias = getattr(args, 'familia', None)
        resultados = {t: entrenador.entrenar_modelo(TipoModelo(t)) for t in familias} if familias else entrenador.entrenar_completo()
        modelos = [getattr(entrenador, 'obtener_modelo_' + tipo.value)() for tipo in TipoModelo if tipo.value in resultados]
        informe['ajuste'] = {m.tipo.value: {'dataset': m.dataset, 'metricas': m.metricas} for m in modelos}
        if args.guardar:
            informe['versiones_guardadas'] = GestorVersiones(pool).guardar_lote(modelos, activar=args.activar)
            informe['activadas'] = args.activar
            # Un segundo loader, sin volver a entrenar, acredita la publicación.
            for m in modelos:
                cargado = GestorVersiones(pool).cargar_modelo(m.tipo, informe['versiones_guardadas'][m.tipo.value])
                if cargado.to_dict() != m.to_dict():
                    raise ValueError('La recarga no reproduce el artefacto publicado')
    return informe


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entrenar', action='store_true', help='Ejecuta Ridge explícitamente; por defecto solo diagnostica')
    parser.add_argument('--guardar', action='store_true', help='Publica coeficientes y dataset; no activa por defecto')
    parser.add_argument('--activar', action='store_true', help='Activa las familias publicadas, sin promocionar mercados beta')
    parser.add_argument('--alpha', type=float, default=5.0)
    parser.add_argument('--min-partidos', type=int, default=100)
    parser.add_argument('--min-partidos-equipo', type=int, default=5)
    parser.add_argument('--competicion', action='append', help='Código canónico; repetible')
    parser.add_argument('--familia', action='append', choices=[t.value for t in TipoModelo], help='Entrena solo estas familias; repetible')
    parser.add_argument('--temporada-id', action='append', help='UUID canónico; repetible')
    parser.add_argument('--fecha-corte', type=date.fromisoformat, help='Límite exclusivo YYYY-MM-DD en UTC')
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args(argv)
    if args.guardar and not args.entrenar or args.activar and not args.guardar:
        parser.error('--guardar requiere --entrenar; --activar requiere --guardar')
    if not 0 < args.alpha < float('inf') or args.min_partidos < 1 or args.min_partidos_equipo < 1:
        parser.error('Alpha y mínimos deben ser positivos y finitos')
    try:
        informe = ejecutar(obtener_pool(), args)
        contenido = json.dumps(informe, default=str, indent=2, allow_nan=False)
        if args.salida:
            args.salida.write_text(contenido + '\n')
        print(contenido)
        return 0
    finally:
        cerrar_pool()


if __name__ == '__main__':
    raise SystemExit(main())
