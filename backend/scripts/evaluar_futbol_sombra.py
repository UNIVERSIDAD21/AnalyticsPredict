"""Evalúa una cohorte externa con outcomes posteriores; solo SELECT, sin activación."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import obtener_pool, cerrar_pool
from motor_futbol.evaluacion.cohorte_sombra import evaluar_cohorte
from motor_futbol.evaluacion.temporal_ridge import LIGAS
from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.tipos import ConfiguracionEntrenamiento
from scripts.evaluar_futbol_temporal import PoolSoloLectura
from scripts.preparar_futbol_sombra import escribir_nuevo


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohorte', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args(argv)
    cohorte = json.loads(args.cohorte.read_text())
    try:
        pool = PoolSoloLectura(obtener_pool())
        with pool.connection() as c:
            observado = c.execute('SELECT clock_timestamp()').fetchone()[0]
        config = ConfiguracionEntrenamiento(competiciones=list(LIGAS),
            fecha_minima=datetime.fromisoformat(cohorte['declaracion']['inicio_eval']), fecha_corte=observado)
        entrenador = EntrenadorFutbol(pool, config=config)
        partidos = entrenador._normalizar_partidos(entrenador._obtener_partidos_entrenamiento())
        for p in partidos: p['estado'] = 'FINALIZADO'
        informe = evaluar_cohorte(cohorte, partidos, observado)
        escribir_nuevo(args.salida, informe)
        print(json.dumps({k: {'n': v['metricas']['n_partidos'], 'pendientes': v['pendientes'],
                              'motivos': v['motivos']} for k, v in informe['familias'].items()}, ensure_ascii=False))
    finally:
        cerrar_pool()


if __name__ == '__main__':
    main()
