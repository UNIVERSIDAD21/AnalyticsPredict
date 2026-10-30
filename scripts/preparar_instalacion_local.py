"""Prepara una copia nueva del producto vigente, sin credenciales.

Incluye el working tree, build ya compilado, artefactos y herramientas de migración.
Puede incluir Python Windows y dependencias para ejecutar el modo base sin instalaciones externas.
No conecta a BD, no restaura y no altera la instalación anterior.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

EXCLUIDOS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.pytest_cache', 'runtime', 'bd'}
PRIVADOS = {'SOUL.md', 'MEMORY.md', 'USER.md', 'TOOLS.md', 'IDENTITY.md'}


def ruta_io(path):
    """Soporta rutas largas sin cambiar la política global LongPathsEnabled de Windows."""
    path = Path(path).absolute()
    value = str(path)
    if os.name == 'nt' and not value.startswith('\\\\?\\'):
        value = '\\\\?\\UNC\\' + value[2:] if value.startswith('\\\\') else '\\\\?\\' + value
        return Path(value)
    return path


def digest(path):
    h = hashlib.sha256()
    with ruta_io(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def relativa_segura(valor):
    p = PurePosixPath(valor)
    if p.is_absolute() or not p.parts or '..' in p.parts or '\\' in valor or ':' in valor:
        raise ValueError('Ruta de paquete no permitida')
    return p


def publicable(relative):
    p = relativa_segura(relative)
    return not (set(p.parts) & EXCLUIDOS or p.name in PRIVADOS or
        (p.name.startswith('.env') and not p.name.endswith(('.example', '.sample', '.template'))) or
        p.suffix.lower() in {'.env', '.log', '.dump', '.backup', '.sqlite', '.db', '.pyc', '.pyo'} or
        p.name in {'pgpass.conf', '.pgpass'} or 'dist' in p.parts)


def verificar(paquete):
    paquete = ruta_io(paquete).resolve()
    manifest = json.loads((paquete / 'MANIFIESTO.json').read_text(encoding='utf-8'))
    for relative, esperado in manifest['files'].items():
        relativa_segura(relative)
        path = ruta_io(paquete / relative)
        if not path.resolve().is_relative_to(ruta_io(paquete).resolve()) or not path.is_file() or path.is_symlink() or digest(path) != esperado:
            raise ValueError('Archivo ausente o modificado: ' + relative)
    identity = hashlib.sha256(json.dumps({k: v for k, v in manifest['files'].items() if k.startswith('producto/')}, sort_keys=True).encode()).hexdigest()
    if identity != manifest['product_worktree_sha256']: raise ValueError('La identidad del producto no coincide con su inventario')
    return {'paquete_verificado': True, 'archivos': len(manifest['files']),
            'producto_worktree_sha256': manifest['product_worktree_sha256'],
            'estado_bd': manifest['database']['kind'], 'migracion_completa': False}


def batch_quote(value):
    value = str(value)
    if any(c in value for c in '\r\n"'): raise ValueError('Ruta no válida para el lanzador Windows')
    return '"' + value.replace('%', '%%') + '"'


def inspeccionar_python(executable):
    """Solo rutas, versión y distribución instaladas; no lee configuración de proyecto."""
    code = ('import json,sys,sysconfig,importlib.metadata; '
            'print(json.dumps({"base":sys.base_prefix,"paquetes":sysconfig.get_path("purelib"),'
            '"version":list(sys.version_info[:3]),"plataforma":sys.platform,'
            '"distribuciones":sorted((d.metadata["Name"],d.version) for d in importlib.metadata.distributions())}))')
    info = json.loads(subprocess.check_output([str(executable), '-I', '-B', '-c', code], timeout=30))
    if info['plataforma'] != 'win32' or info['version'][:2] != [3, 12]:
        raise ValueError('El runtime autónomo requiere Python 3.12 Windows con dependencias ya instaladas')
    return info


def copiar_runtime(executable, copiar):
    info = inspeccionar_python(executable)
    base, paquetes = (ruta_io(info[k]).resolve() for k in ('base', 'paquetes'))
    if not (base / 'Lib/encodings/__init__.py').is_file() or not paquetes.is_dir():
        raise ValueError('La distribución Python no contiene biblioteca estándar o dependencias')
    for nombre in ('python.exe', 'python312.dll', 'python3.dll', 'vcruntime140.dll', 'LICENSE.txt'):
        copiar(base / nombre, 'runtime/python/' + nombre, base)
    if (base / 'vcruntime140_1.dll').is_file():
        copiar(base / 'vcruntime140_1.dll', 'runtime/python/vcruntime140_1.dll', base)
    for root, prefijo in ((base / 'Lib', 'Lib'), (base / 'DLLs', 'DLLs'), (paquetes, 'Lib/site-packages')):
        for path in sorted(root.rglob('*')):
            rel = path.relative_to(root)
            if '__pycache__' in rel.parts or path.suffix.lower() in ('.pyc', '.pyo'): continue
            if prefijo == 'Lib' and set(rel.parts) & {'site-packages', 'test', 'idlelib', 'tkinter', 'turtledemo', 'ensurepip'}: continue
            if path.is_symlink() or path.is_junction():
                raise ValueError('El runtime no admite enlaces a dependencias externas')
            if not path.is_file(): continue
            if path.suffix == '.egg-link' or path.name == 'pyvenv.cfg':
                raise ValueError('El runtime no admite dependencias editables ni referencias a otra venv')
            if path.suffix == '.pth':
                for line in path.read_text(encoding='utf-8-sig').splitlines():
                    line = line.strip()
                    if line and not line.startswith(('#', 'import ')) and not (root / line).resolve().is_relative_to(paquetes):
                        raise ValueError('Una dependencia referencia una ruta fuera del runtime')
            copiar(path, 'runtime/python/' + prefijo + '/' + rel.as_posix(), root)
    return {'python_relativo': 'runtime/python/python.exe', 'version': info['version'],
            'plataforma': info['plataforma'], 'distribuciones': info['distribuciones'],
            'aislado': True, 'licencia_python': 'runtime/python/LICENSE.txt'}


def preparar(repo, estado, original, salida, runtime, *, autonomo=False):
    repo, estado, original, salida = (Path(p).resolve() for p in (repo, estado, original, salida))
    if ruta_io(salida).exists(): raise ValueError('El destino ya existe; prepara una carpeta nueva sin sobrescribirla')
    if salida.is_relative_to(repo) or salida.is_relative_to(estado) or salida.is_relative_to(original):
        raise ValueError('El destino debe estar fuera de las fuentes y del paquete original')
    if not (repo / 'frontend/dist/index.html').is_file(): raise ValueError('Falta la compilación frontend vigente')
    for relative in ('backend/app.py', 'scripts/iniciar_local.py', 'scripts/servir_frontend_local.py', 'scripts/preparar_instalacion_local.py', 'scripts/plantillas/continuar_migracion_actualizada.ps1'):
        if not (repo / relative).is_file(): raise ValueError('Falta código requerido: ' + relative)
    if not (estado / 'modelo_nba_activo.npz').is_file(): raise ValueError('Falta el artefacto NBA existente')
    base = json.loads((original / 'MANIFIESTO.json').read_text(encoding='utf-8'))
    if base['database']['kind'] != 'pending_current_export':
        raise ValueError('El paquete original ya contiene datos de BD; revisar su corte antes de preparar otra copia')
    for name in ('exportar_vigente.py', 'restaurar_local.py', 'verificar_bd.py', 'verificar_windows.py', 'arrancar_backend.py'):
        if 'herramientas/' + name not in base['files']: raise ValueError('Falta herramienta original: ' + name)
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    raw = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
    sources = sorted(set(p.decode('utf-8') for p in raw.split(b'\0') if p))
    inventory = [p for p in sources if publicable(p) and (repo / p).is_file()]
    files = {}
    originals = {}
    salida = ruta_io(salida)
    salida.mkdir(parents=True, exist_ok=False)

    def copiar(source, relative, root):
        relativa_segura(relative)
        source = ruta_io(source)
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(ruta_io(root).resolve()):
            raise ValueError('Fuente ausente o enlace no permitido: ' + relative)
        content = source.read_bytes()
        fingerprint = hashlib.sha256(content).hexdigest()
        target = ruta_io(salida / relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as out: out.write(content)
        files[relative] = fingerprint
        originals[source] = fingerprint

    count = 0
    for relative in inventory:
        copiar(repo / relative, 'producto/' + relative, repo); count += 1
    for path in sorted((repo / 'frontend/dist').rglob('*')):
        if path.is_file(): copiar(path, 'producto/' + path.relative_to(repo).as_posix(), repo)
    for relative, fingerprint in base['files'].items():
        if relative.startswith('estado/'):
            source = estado / PurePosixPath(relative).relative_to('estado')
            if not source.is_file() or digest(source) != fingerprint:
                raise ValueError('El estado difiere del manifiesto original: ' + relative)
            copiar(source, relative, estado)
        elif relative.startswith('herramientas/'):
            if digest(original / relative) != fingerprint: raise ValueError('Herramienta original modificada: ' + relative)
            copiar(original / relative, relative, original)
    identity = hashlib.sha256(json.dumps({k: v for k, v in files.items() if k.startswith('producto/')}, sort_keys=True).encode()).hexdigest()
    runtime = dict(runtime)
    runtime_info = None
    if autonomo:
        runtime_info = copiar_runtime(runtime['python'], copiar)
        pth = salida / 'runtime/python/python312._pth'
        # Rutas relativas; ignora PYTHONHOME, PYTHONPATH y el site-packages del usuario.
        pth.write_text('.\nLib\nDLLs\nLib/site-packages\nimport site\n', encoding='utf-8')
        files['runtime/python/python312._pth'] = digest(pth)
        runtime['python'] = runtime_info['python_relativo']
        runtime['autonomo_base_local'] = True
    runtime_path = salida / 'RUNTIME_LOCAL.json'
    runtime_path.write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding='utf-8')
    files['RUNTIME_LOCAL.json'] = digest(runtime_path)
    template = repo / 'scripts/plantillas/continuar_migracion_actualizada.ps1'
    copiar(template, 'CONTINUAR_MIGRACION.ps1', repo)
    py = '"%~dp0runtime\\python\\python.exe"' if autonomo else batch_quote(runtime['python'])
    script = '"%~dp0producto\\scripts\\iniciar_local.py"'
    state = '"%~dp0estado"'
    command = f'{py} -X utf8 -B {script} --estado {state} %*'
    launch = salida / 'ABRIR_BASE_LOCAL.cmd'
    launch.write_text('@echo off\nsetlocal\nchcp 65001 >nul\nset "PYTHONUTF8=1"\nset "PYTHONIOENCODING=utf-8"\n' + command + '\nset "AP_EXIT=%ERRORLEVEL%"\nif not "%AP_EXIT%"=="0" pause\nexit /b %AP_EXIT%\n', encoding='utf-8', newline='\r\n')
    files[launch.name] = digest(launch)
    check = salida / 'COMPROBAR_BASE_LOCAL.cmd'
    check.write_text('@echo off\ncall "%~dp0ABRIR_BASE_LOCAL.cmd" --comprobar --sin-abrir\nexit /b %ERRORLEVEL%\n', encoding='utf-8', newline='\r\n')
    files[check.name] = digest(check)
    if autonomo:
        leeme = salida / 'LEEME.md'
        leeme.write_text('# AnalyticsPredict local autónomo — Windows x64\n\n'
            'Abre ABRIR_BASE_LOCAL.cmd. Puedes mover esta carpeta completa a otra ubicación.\n'
            'Incluye Python 3.12, sus dependencias, la interfaz compilada y los modelos guardados. '
            'No necesita Python, Node o npm instalados para consultar el modo base.\n\n'
            'Mis análisis guarda copias y notas en el navegador/perfil de 127.0.0.1:5173. '
            'Crea un respaldo personal antes de cambiar de navegador o equipo.\n\n'
            'La base de datos NO está migrada. Agendas, contexto reciente, fútbol y Seguimiento en BD '
            'siguen pendientes. CONTINUAR_MIGRACION.ps1 requiere por separado PostgreSQL y el origen autorizado.\n\n'
            'No se actualizan modelos ni datos al abrir. Los puertos ocupados no se liberan automáticamente. '
            'Ctrl+C cierra solo los procesos de esta ejecución.\n\n'
            'COMPROBAR_BASE_LOCAL.cmd verifica el arranque y cierra. '
            'Conserva las licencias de Python y de los paquetes incluidas en runtime/python.\n', encoding='utf-8')
        files[leeme.name] = digest(leeme)
    manifest = {'schema_version': 1, 'product_head': head, 'product_worktree_sha256': identity,
        'product_source': 'working_tree_integrado', 'source_files': count, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'database': dict(base['database']), 'source_identity': dict(base['source_identity']), 'files': dict(sorted(files.items())),
        'runtime': runtime_info,
        'dependencies': ('Python y dependencias incluidos y aislados; sin Node para el modo base. BD no incluida.' if autonomo else
                         'Python Windows externo existente; no se copia .venv ni node_modules. Frontend compilado incluido.')}
    if any(digest(path) != fingerprint for path, fingerprint in originals.items()):
        raise ValueError('Una fuente cambió durante la copia; no se declara preparado el paquete')
    after = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
    inventory_after = sorted(set(p.decode('utf-8') for p in after.split(b'\0') if p and publicable(p.decode('utf-8')) and (repo / p.decode('utf-8')).is_file()))
    if inventory_after != inventory: raise ValueError('El inventario de fuentes cambió durante la copia')
    if subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() != head:
        raise ValueError('HEAD cambió durante la preparación')
    (salida / 'MANIFIESTO.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    receipt = verificar(salida)
    (salida / 'PREPARACION_VERIFICADA.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', type=Path)
    parser.add_argument('--repositorio', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--estado', type=Path)
    parser.add_argument('--paquete-original', type=Path)
    parser.add_argument('--salida', type=Path)
    parser.add_argument('--runtime', type=Path, help='JSON de rutas locales existentes; sin contraseñas')
    parser.add_argument('--autonomo', action='store_true', help='Incluye Python Windows y dependencias; ejecución base trasladable')
    args = parser.parse_args(argv)
    if args.verificar: result = verificar(args.verificar)
    else:
        if not all((args.estado, args.paquete_original, args.salida, args.runtime)):
            parser.error('Se requieren --estado, --paquete-original, --salida y --runtime')
        result = preparar(args.repositorio, args.estado, args.paquete_original, args.salida,
            json.loads(args.runtime.read_text(encoding='utf-8-sig')), autonomo=args.autonomo)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try: raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'tipo': type(exc).__name__, 'error': str(exc) if isinstance(exc, ValueError) else 'No se completó la preparación; revisar rutas y permisos'}, ensure_ascii=False))
        raise SystemExit(1)
