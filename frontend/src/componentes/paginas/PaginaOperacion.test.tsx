import { afterEach, describe, expect, it, vi } from 'vitest';
import { StrictMode } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { clienteAPI } from '../../servicios/api';
import { PaginaOperacion } from './PaginaOperacion';

vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <nav>Estado</nav> }));
vi.mock('../../servicios/estadoLocal', () => ({ leerEstadoLocal: vi.fn().mockResolvedValue({
  formato: 'diagnostico-local-v1', observado_en: '2026-10-30T20:00:00Z', modo: 'CON_BD_CONFIGURADA',
  bd: { deshabilitada: false, conexion_comprobada: false, estado: 'NO_COMPROBADA' }, modelos: {}, limites: [],
}) }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe('Estado operativo', () => {
  it('no desplaza fechas sin hora y conserva N/D del seguimiento ausente', async () => {
    vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: {
      observado_en: '2026-10-16T01:00:00Z',
      nba: { n: 30, ultimo_final: '2026-10-15', por_fase: [{ fase: 'PRE', n: 8, finales_validos: 7, ultimo_final: '2026-10-15' }, { fase: 'REG', n: 22, finales_validos: 22, ultimo_final: '2026-06-14' }] }, futbol: { n: 200, ultimo_final: null },
      modelo_nba: { estado: 'DISPONIBLE', version: 2123, equipos: 30 },
      frescura_modelo_nba: { estado: 'HAY_FINALES_ELEGIBLES_NUEVOS', finales_elegibles_nuevos: 13, pretemporada_excluida: 66, criterio: 'Solo datos del alcance; no entrena.' },
      capturas_futbol: { lotes: 10, observado_en: null },
      predictor_ml_futbol: { estado: 'SIN_VERSION_ACTIVA', familias: {}, carga_en_proceso: { estado: 'NO_INICIALIZADO', familias: {} } },
      prospectiva: { congeladas: null, resueltas: null, resueltas_independientes: 0, estado: 'ALMACEN_NO_INSTALADO' }, notas: [],
    } });
    render(<StrictMode><PaginaOperacion /></StrictMode>);
    expect(await screen.findByText(/último final: 2026-10-15/)).toBeTruthy();
    expect(screen.getByText(/N\/D predicciones congeladas/)).toBeTruthy();
    expect(screen.getByText('Seguimiento aún no instalado')).toBeTruthy();
    expect(screen.getByText(/fuente independiente acreditada: 0/)).toBeTruthy();
    expect(screen.queryByText(/resultados acreditados/)).toBeNull();
    expect(screen.getByText(/Pretemporada: 8 registros · 7 finales válidos/)).toBeTruthy();
    expect(screen.getByText(/Temporada regular: 22 registros/)).toBeTruthy();
    expect(screen.getByText(/Pretemporada posterior excluida por diseño: 66/)).toBeTruthy();
    expect(screen.getByText(/Finales posteriores al corte del artefacto/).textContent).toContain('13');
    expect(clienteAPI.get).toHaveBeenCalledTimes(1);
  });
  it('no inventa ceros al fallar la carga y permite reintentar', async () => {
    const get = vi.spyOn(clienteAPI, 'get').mockRejectedValue(new Error('sin conexión'));
    render(<PaginaOperacion />);
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryByText(/0 partidos/)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar estado' }));
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
  });
  it('muestra las cuatro áreas y conserva la última respuesta al fallar una actualización', async () => {
    const inventario = { codigo: 'wnba', nombre: 'WNBA', registros: 2088, finales_con_marcador: 2088,
      ultimo_final: '2026-10-24', invalidados: 0, faltantes_por_campo: { local_q1: 0 },
      calendario: { estado: 'REGISTROS_LOCALES', proximos: 3, completo_acreditado: false, condicionales: 1 },
      modelo: { estado: 'DISPONIBLE', version: 'wnba-local', ultimo_dato: '2026-09-24', partidos: 1840, calibracion: 'SIN_CALIBRAR' } };
    vi.spyOn(clienteAPI, 'get').mockResolvedValueOnce({ data: {
      observado_en: '2026-10-25T20:00:00Z', nba: { n: 100, ultimo_final: null }, futbol: { n: 200, ultimo_final: null },
      modelo_nba: { estado: 'DISPONIBLE' }, capturas_futbol: { lotes: 0, observado_en: null },
      prospectiva: { congeladas: null, resueltas: null, estado: 'ALMACEN_NO_INSTALADO' }, notas: [],
      predictor_ml_futbol: { estado: 'SIN_VERSION_ACTIVA', familias: {}, carga_en_proceso: { familias: {} } },
      competiciones: { baloncesto: { wnba: inventario, euroleague: { ...inventario, codigo: 'euroleague', registros: 0, finales_con_marcador: 0, calendario: { ...inventario.calendario, proximos: null }, modelo: undefined } },
        futbol: [{ ...inventario, codigo: 'COPA', nombre: 'Copa local', registros: 100, finales_con_marcador: 80, calendario: { ...inventario.calendario, proximos: 1 }, faltantes_por_campo: { local_disparos_arco: 60 }, modelo: undefined }],
        ventana_calendario: { desde: '2026-10-25T15:00:00-05:00', hasta: '2027-01-25T15:00:00-05:00', zona: 'America/Bogota' }, criterio: 'Solo finales válidos.' },
    } }).mockRejectedValueOnce(new Error('fallo'));
    render(<PaginaOperacion />);
    expect(await screen.findByRole('heading', { name: 'WNBA' })).toBeTruthy();
    for (const name of ['NBA', 'Euroliga', 'Fútbol']) expect(screen.getByRole('heading', { name })).toBeTruthy();
    expect(screen.getByText(/2088 registros · 2088 finales/)).toBeTruthy();
    expect(screen.getByText(/1840 partidos/)).toBeTruthy();
    expect(screen.getByText('Calibración: RAW / sin calibrar')).toBeTruthy();
    expect(screen.getByText(/Sin muestra de finales/)).toBeTruthy();
    expect(screen.getByText('Local · tiros al arco: 60')).toBeTruthy();
    expect(screen.getByText(/próximos tres meses: 3 · cobertura completa no acreditada/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar estado' }));
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(/Se conserva la última respuesta/)).toBeTruthy();
    expect(screen.getByText(/2088 registros · 2088 finales/)).toBeTruthy();
  });
});
