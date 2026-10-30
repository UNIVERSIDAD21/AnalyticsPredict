"""Verifica el Python incluido sin conexión a BD, red, entrenamiento o escrituras."""
import importlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo


def verificar():
    paquete = Path(__file__).resolve().parents[2]
    runtime = paquete / 'runtime/python'
    if not Path(sys.executable).resolve().is_relative_to(runtime):
        raise ValueError('Ejecuta este comprobador con runtime/python/python.exe del paquete')
    if not sys.flags.isolated or sys.flags.ignore_environment != 1:
        raise ValueError('El Python incluido no está aislado del entorno externo')
    nombres = ('ssl', 'sqlite3', 'numpy', 'scipy', 'sklearn', 'pandas', 'fastapi', 'uvicorn',
               'psycopg', 'psycopg_pool', 'dotenv', 'pydantic', 'tzdata')
    for nombre in nombres:
        importlib.import_module(nombre)
    from scipy.stats import norm
    import numpy as np
    if float(np.dot([1., 2.], [3., 4.])) != 11. or norm.cdf(0) != .5:
        raise ValueError('Las dependencias numéricas no completaron la comprobación')
    ZoneInfo('America/Bogota')
    externos = []
    for nombre, modulo in tuple(sys.modules.items()):
        archivo = getattr(modulo, '__file__', None)
        if archivo and Path(archivo).is_absolute() and not Path(archivo).resolve().is_relative_to(paquete):
            externos.append(nombre)
    if externos:
        raise ValueError('Se cargaron módulos externos al paquete: ' + ', '.join(externos))
    return {'runtime_autonomo': True, 'python': list(sys.version_info[:3]),
            'interprete_relativo': Path(sys.executable).resolve().relative_to(paquete).as_posix(),
            'aislado': True, 'dependencias_comprobadas': list(nombres), 'modulos_externos': 0,
            'zona_Colombia': True, 'red_BD_fit': False}


if __name__ == '__main__':
    try:
        print(json.dumps(verificar(), ensure_ascii=False))
    except (ValueError, ImportError, OSError) as exc:
        print(json.dumps({'runtime_autonomo': False, 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
