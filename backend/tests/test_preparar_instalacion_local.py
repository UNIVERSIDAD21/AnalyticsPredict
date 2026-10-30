"""Paquetes sintéticos en directorios temporales: sin BD, red o credenciales reales."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location('preparar_local', Path(__file__).resolve().parents[2] / 'scripts/preparar_instalacion_local.py')
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def escribir(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


@pytest.fixture
def fuentes(tmp_path):
    repo, original, state = (tmp_path / name for name in ('repo', 'original', 'estado'))
    repo.mkdir(); original.mkdir(); state.mkdir()
    escribir(repo, '.gitignore', 'frontend/dist/\nnode_modules/\n.venv/\n')
    app = escribir(repo, 'backend/app.py', '# versión anterior\n')
    for name in ('iniciar_local.py', 'servir_frontend_local.py', 'preparar_instalacion_local.py'):
        escribir(repo, 'scripts/' + name, '# código sintético\n')
    escribir(repo, 'scripts/plantillas/continuar_migracion_actualizada.ps1', '$Root = $PSScriptRoot\n')
    escribir(repo, 'frontend/dist/index.html', '<html>build sintético</html>')
    escribir(repo, 'node_modules/privado.txt', 'dependencia')
    escribir(repo, '.venv/privado.txt', 'dependencia')
    escribir(repo, 'backend/.env', 'DATABASE_URL=NO_COPIAR\n')
    escribir(repo, 'SOUL.md', 'NO_COPIAR_MEMORIA')
    subprocess.run(['git', '-C', str(repo), 'init', '-q'], check=True)
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Fixture local', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    app.write_text('# cambio local no publicado: Bogotá\n', encoding='utf-8')
    escribir(repo, 'backend/nuevo.py', '# archivo no seguido\n')
    escribir(state, 'modelo_nba_activo.npz', 'artefacto sintético, no entrenado')
    files = {'estado/modelo_nba_activo.npz': MOD.digest(state / 'modelo_nba_activo.npz')}
    for name in ('exportar_vigente.py', 'restaurar_local.py', 'verificar_bd.py', 'verificar_windows.py', 'arrancar_backend.py'):
        path = escribir(original, 'herramientas/' + name, '# herramienta sintética\n')
        files['herramientas/' + name] = MOD.digest(path)
    escribir(original, 'MANIFIESTO.json', json.dumps({'database': {'kind': 'pending_current_export'}, 'source_identity': {'origin_kind': 'fixture'}, 'files': files}))
    return repo, state, original, tmp_path / 'salida', {'python': 'C:/Python/python.exe'}


def test_copia_working_tree_y_build_sin_entorno_dependencias_o_memoria(fuentes):
    repo, state, original, target, runtime = fuentes
    before = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'])
    result = MOD.preparar(*fuentes)
    assert result['paquete_verificado'] and not result['migracion_completa']
    assert 'cambio local' in (target / 'producto/backend/app.py').read_text(encoding='utf-8')
    assert (target / 'producto/backend/nuevo.py').is_file()
    assert (target / 'producto/frontend/dist/index.html').is_file()
    for path in ('producto/backend/.env', 'producto/node_modules', 'producto/.venv', 'producto/SOUL.md'):
        assert not (target / path).exists()
    assert subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain']) == before
    assert MOD.digest(state / 'modelo_nba_activo.npz') == MOD.digest(target / 'estado/modelo_nba_activo.npz')


def test_no_sobrescribe_destino_existente(fuentes):
    fuentes[3].mkdir()
    sentinel = escribir(fuentes[3], 'previo.txt', 'conservar')
    with pytest.raises(ValueError, match='ya existe'): MOD.preparar(*fuentes)
    assert sentinel.read_text() == 'conservar'


def test_no_acepta_estado_diferente_del_original(fuentes):
    (fuentes[1] / 'modelo_nba_activo.npz').write_text('alterado')
    with pytest.raises(ValueError, match='estado difiere'): MOD.preparar(*fuentes)


def test_verificacion_detecta_manipulacion_de_producto(fuentes):
    MOD.preparar(*fuentes)
    (fuentes[3] / 'producto/backend/app.py').write_text('otro contenido')
    with pytest.raises(ValueError, match='modificado'): MOD.verificar(fuentes[3])


@pytest.mark.parametrize('relative', ['../fuera', 'C:/afuera', '/absoluta', 'a\\b'])
def test_rechaza_rutas_fuera_del_paquete(relative):
    with pytest.raises(ValueError): MOD.relativa_segura(relative)


def test_rechaza_manifest_que_apunta_fuera(fuentes):
    MOD.preparar(*fuentes)
    path = fuentes[3] / 'MANIFIESTO.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest['files']['../fuera'] = '0' * 64
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError): MOD.verificar(fuentes[3])


def test_no_declara_preparado_sin_build(fuentes):
    (fuentes[0] / 'frontend/dist/index.html').unlink()
    with pytest.raises(ValueError, match='compilación'): MOD.preparar(*fuentes)
    assert not fuentes[3].exists()


def test_comando_windows_escapa_porcentajes_y_no_admite_nuevas_lineas():
    assert MOD.batch_quote('C:/100%/python.exe') == '"C:/100%%/python.exe"'
    with pytest.raises(ValueError): MOD.batch_quote('C:/ruta\ncomando')


def test_huella_productiva_conserva_identidad_y_no_simula_exportacion(fuentes):
    MOD.preparar(*fuentes)
    manifest = json.loads((fuentes[3] / 'MANIFIESTO.json').read_text(encoding='utf-8'))
    assert manifest['database']['kind'] == 'pending_current_export'
    expected = hashlib.sha256(json.dumps({k: v for k, v in manifest['files'].items() if k.startswith('producto/')}, sort_keys=True).encode()).hexdigest()
    assert manifest['product_worktree_sha256'] == expected


def test_verificacion_contrasta_huella_global_del_producto(fuentes):
    MOD.preparar(*fuentes)
    path = fuentes[3] / 'MANIFIESTO.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest['product_worktree_sha256'] = '0' * 64
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError, match='identidad del producto'): MOD.verificar(fuentes[3])


def test_no_cierra_inventario_si_se_agregan_fuentes_durante_la_copia(fuentes, monkeypatch):
    real = MOD.subprocess.check_output
    calls = 0
    def consultar(args, **kwargs):
        nonlocal calls
        if 'ls-files' in args:
            calls += 1
            if calls == 2: escribir(fuentes[0], 'backend/agregado_durante_copia.py', '# nuevo\n')
        return real(args, **kwargs)
    monkeypatch.setattr(MOD.subprocess, 'check_output', consultar)
    with pytest.raises(ValueError, match='inventario de fuentes cambió'): MOD.preparar(*fuentes)
    assert not (fuentes[3] / 'MANIFIESTO.json').exists()


@pytest.fixture
def python_portatil(tmp_path, monkeypatch):
    base, paquetes = tmp_path / 'python_fuente', tmp_path / 'venv/Lib/site-packages'
    for name in ('python.exe', 'python312.dll', 'python3.dll', 'vcruntime140.dll', 'LICENSE.txt', 'DLLs/_ssl.pyd', 'Lib/encodings/__init__.py'):
        escribir(base, name, 'binario/licencia sintéticos')
    escribir(base, 'Lib/site-packages/no_incluir.txt', 'paquete global ajeno')
    escribir(paquetes, 'dependencia/__init__.py', '# paquete sintético')
    escribir(paquetes, 'dependencia-1.dist-info/licenses/LICENSE', 'licencia dependencia')
    monkeypatch.setattr(MOD, 'inspeccionar_python', lambda _: {'base': str(base), 'paquetes': str(paquetes),
        'version': [3, 12, 10], 'plataforma': 'win32', 'distribuciones': [['dependencia', '1']]})
    return base, paquetes


def test_paquete_autonomo_conserva_licencias_y_solo_referencias_relativas(fuentes, python_portatil):
    target = fuentes[3]
    MOD.preparar(*fuentes, autonomo=True)
    config = json.loads((target / 'RUNTIME_LOCAL.json').read_text(encoding='utf-8'))
    assert config['python'] == 'runtime/python/python.exe' and config['autonomo_base_local']
    assert (target / 'runtime/python/LICENSE.txt').is_file()
    assert (target / 'runtime/python/Lib/site-packages/dependencia-1.dist-info/licenses/LICENSE').is_file()
    assert not (target / 'runtime/python/Lib/site-packages/no_incluir.txt').exists()
    assert (target / 'runtime/python/python312._pth').read_text().splitlines() == ['.', 'Lib', 'DLLs', 'Lib/site-packages', 'import site']
    launch = (target / 'ABRIR_BASE_LOCAL.cmd').read_text(encoding='utf-8')
    assert '%~dp0runtime\\python\\python.exe' in launch and str(target) not in launch and 'C:/Python' not in launch
    moved = target.with_name('ubicación nueva con espacios')
    shutil.copytree(MOD.ruta_io(target), MOD.ruta_io(moved))
    assert MOD.verificar(moved)['paquete_verificado']


def test_integridad_cubre_los_binarios_del_runtime(fuentes, python_portatil):
    MOD.preparar(*fuentes, autonomo=True)
    (fuentes[3] / 'runtime/python/python.exe').write_text('alterado')
    with pytest.raises(ValueError, match='modificado'): MOD.verificar(fuentes[3])


def test_paquete_admite_rutas_largas_sin_cambiar_politicas_windows(fuentes, python_portatil):
    largas = fuentes[:3] + (fuentes[3].parent / ('carpeta_' * 20) / ('destino_' * 12),) + fuentes[4:]
    MOD.preparar(*largas, autonomo=True)
    assert MOD.verificar(largas[3])['paquete_verificado']


def test_runtime_rechaza_referencias_a_paquetes_externos(fuentes, python_portatil):
    escribir(python_portatil[1], 'editable.pth', '../../fuera_del_runtime')
    with pytest.raises(ValueError, match='fuera del runtime'): MOD.preparar(*fuentes, autonomo=True)


def test_runtime_rechaza_otra_plataforma(monkeypatch):
    monkeypatch.setattr(MOD.subprocess, 'check_output', lambda *a, **k: json.dumps({
        'version': [3, 12, 10], 'plataforma': 'linux'}).encode())
    with pytest.raises(ValueError, match='Python 3.12 Windows'): MOD.inspeccionar_python('python')
