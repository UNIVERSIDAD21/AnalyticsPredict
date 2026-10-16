#!/usr/bin/env python3
"""Evalúa Ridge por ventanas congeladas; solo SELECT en BD, salidas externas."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db import obtener_pool, cerrar_pool
from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.evaluacion.temporal_ridge import PoliticaTemporal, evaluar
from motor_futbol.modelos.artefacto import sha256
from motor_futbol.tipos import ConfiguracionEntrenamiento


class PoolSoloLectura:
    def __init__(self, pool): self.pool = pool
    @contextmanager
    def connection(self):
        with self.pool.connection() as conn:
            with conn.transaction():
                conn.execute('SET TRANSACTION READ ONLY')
                conn.execute("SET LOCAL statement_timeout='30s'")
                yield conn


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True, help='Datos deportivos observados hoy, fuera del repo')
    parser.add_argument('--politica', type=Path, help='Política JSON predeclarada, antes de medir')
    args = parser.parse_args(argv)
    politica = PoliticaTemporal()
    politica.validar()
    if args.politica:
        predeclarada = json.loads(args.politica.read_text())
        if predeclarada != politica.to_dict():
            raise ValueError('La política publicada no coincide con la predeclarada')
    config = ConfiguracionEntrenamiento(competiciones=list(politica.ligas), fecha_minima=politica.desde,
                                        fecha_corte=politica.ventanas[-1].fin_eval)
    try:
        e = EntrenadorFutbol(PoolSoloLectura(obtener_pool()), config=config)
        partidos = e._normalizar_partidos(e._obtener_partidos_entrenamiento())
        observado = datetime.now(timezone.utc).isoformat()
        contenido = json.loads(json.dumps(partidos, default=str))
        snapshot = {'observado_en': observado, 'politica_sha256': sha256(politica.to_dict()),
                    'partidos': contenido, 'sha256_datos': sha256(contenido)}
        args.snapshot.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2)+'\n')
        informe = evaluar(partidos, politica)
        informe.update(observado_en=observado, snapshot_sha256=snapshot['sha256_datos'])
        args.salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        print(json.dumps({t:{'n': f['resumen']['n_partidos'], 'mae': f['resumen']['mae'],
                            'mae_baseline': f['resumen']['mae_baseline'], 'gate': f['gate_activacion_exploratoria']}
                          for t,f in informe['familias'].items()}, ensure_ascii=False))
        return 0
    finally:
        cerrar_pool()


if __name__ == '__main__':
    raise SystemExit(main())
