"""Pruebas sintéticas del acceso diario: no encienden ni detienen servicios."""
from contextlib import nullcontext
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / 'abrir_analytics_predict.py'
spec = importlib.util.spec_from_file_location('acceso_bajo_prueba', SOURCE)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class RecuperacionPostgres(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'runtime').mkdir()
        self.params = {'host': '127.0.0.1', 'port': '55433', 'dbname': 'base_sintetica'}
        self.diario = Mock()
        self.diario.ocupado.return_value = False
        self.identity = {'pid': 123, 'puerto': 55433}
        self.diario.acreditar_pg.return_value = self.identity

    def asegurar(self):
        return app.asegurar_postgres(self.root, self.diario, self.params, 'datos_sinteticos', 'bin_sintetico')

    def test_base_apagada_arranca_una_vez_antes_de_acreditar_sql(self):
        order = []
        self.diario.ctl.side_effect = lambda *a: order.append('start')
        self.diario.acreditar_pg.side_effect = lambda *a: order.append('sql') or self.identity
        self.assertEqual(self.asegurar(), self.identity)
        self.assertEqual(order, ['start', 'sql'])
        self.assertEqual(self.diario.ctl.call_count, 1)
        self.assertEqual(self.diario.ctl.call_args.args[2], 'start')
        self.assertEqual(self.diario.operador.atomico.call_args.args[1]['estado'], 'POSTGRES_VERIFICADO')

    def test_base_encendida_se_acredita_sin_control_ni_nuevo_recibo(self):
        self.diario.ocupado.return_value = True
        self.assertEqual(self.asegurar(), self.identity)
        self.diario.ctl.assert_not_called()
        self.diario.operador.atomico.assert_not_called()
        self.assertEqual(list((self.root / 'runtime').iterdir()), [])

    def test_puerto_ajeno_no_se_reinicia(self):
        self.diario.ocupado.return_value = True
        self.diario.acreditar_pg.side_effect = ValueError('Identidad distinta')
        with self.assertRaisesRegex(ValueError, 'Identidad distinta'):
            self.asegurar()
        self.diario.ctl.assert_not_called()

    def test_fallo_start_se_registra_sin_reintentar_ni_iniciar_api(self):
        self.diario.ctl.side_effect = RuntimeError('No inicia')
        with self.assertRaisesRegex(RuntimeError, 'No inicia'):
            self.asegurar()
        self.assertEqual(self.diario.ctl.call_count, 1)
        self.diario.acreditar_pg.assert_not_called()
        self.assertEqual(self.diario.operador.atomico.call_args.args[1]['estado'], 'FALLO_RECUPERACION_POSTGRES')

    def test_fallo_sql_no_autoriza_detener_procesos(self):
        self.diario.acreditar_pg.side_effect = ValueError('Identidad SQL no acreditada')
        with self.assertRaises(ValueError):
            self.asegurar()
        self.assertEqual(self.diario.ctl.call_count, 1)
        self.assertEqual(self.diario.ctl.call_args.args[2], 'start')

    def test_destino_remoto_o_redirigido_se_rechaza_antes_de_actuar(self):
        for change in [{'host': 'servidor.example'}, {'port': '5432'}, {'hostaddr': '10.0.0.2'}]:
            with self.subTest(change=change):
                params = {**self.params, **change}
                with self.assertRaises(ValueError):
                    app.asegurar_postgres(self.root, self.diario, params, 'datos', 'bin')
        self.diario.ocupado.assert_not_called()
        self.diario.ctl.assert_not_called()
        self.assertEqual(list((self.root / 'runtime').iterdir()), [])

    def preparar_apertura(self, existentes):
        self.diario.parametros.return_value = (self.params, 'datos', 'bin')
        self.diario.exclusividad.return_value = nullcontext()
        self.diario.operador.identidad_pid.return_value = 'identidad_sintetica'
        values = iter(existentes)
        return patch.object(app, 'verificar_existente', side_effect=lambda *a: next(values))

    def test_interfaz_existente_base_apagada_recupera_api_sin_tocar_interfaz(self):
        order = []
        frontend = {'nombre': 'frontend', 'pid': 55, 'identidad': 'identidad_frontend'}
        self.diario.ctl.side_effect = lambda *a: order.append('postgres')
        self.diario.acreditar_pg.side_effect = lambda *a: order.append('sql') or self.identity
        child = SimpleNamespace(pid=77)
        with self.preparar_apertura([None, frontend]), \
             patch.object(app.importlib.util, 'module_from_spec', return_value=self.diario), \
             patch.object(app.importlib.util, 'spec_from_file_location', return_value=Mock()), \
             patch.object(app, 'comprobar_http'), \
             patch.object(app.subprocess, 'Popen', side_effect=lambda *a, **k: order.append('backend') or child) as spawn, \
             patch.object(app.webbrowser, 'open') as browser:
            app.abrir(self.root, sin_abrir=True)
        self.assertEqual(order, ['postgres', 'sql', 'backend'])
        self.assertEqual(spawn.call_count, 1)
        self.assertIn('arrancar_backend.py', spawn.call_args.args[0])
        browser.assert_not_called()
        self.diario.ejecutar.assert_not_called()

    def test_todos_apagados_conserva_el_arranque_completo_soportado(self):
        with self.preparar_apertura([None, None]), \
             patch.object(app.importlib.util, 'module_from_spec', return_value=self.diario), \
             patch.object(app.importlib.util, 'spec_from_file_location', return_value=Mock()), \
             patch.object(app, 'asegurar_postgres') as asegurar:
            app.abrir(self.root, sin_abrir=True)
        self.diario.ejecutar.assert_called_once_with(self.root, sin_abrir=True, espera=90)
        asegurar.assert_not_called()

    def test_interfaz_ajena_impide_recuperar_postgres(self):
        with self.preparar_apertura([None, None]), \
             patch.object(app.importlib.util, 'module_from_spec', return_value=self.diario), \
             patch.object(app.importlib.util, 'spec_from_file_location', return_value=Mock()), \
             patch.object(app, 'verificar_existente', side_effect=ValueError('Proceso ajeno')), \
             patch.object(app, 'asegurar_postgres') as asegurar:
            with self.assertRaisesRegex(ValueError, 'Proceso ajeno'):
                app.abrir(self.root, sin_abrir=True)
        asegurar.assert_not_called()
        self.diario.ctl.assert_not_called()


if __name__ == '__main__':
    unittest.main()
