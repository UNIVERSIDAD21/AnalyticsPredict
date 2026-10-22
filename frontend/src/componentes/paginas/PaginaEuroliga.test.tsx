import '@testing-library/jest-dom/vitest';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProveedorDeporte } from '../../contextos/DeporteContext';
import { ToastsProvider } from '../../contextos/Toasts';
import { obtenerTemporadasEquipos, obtenerPartidosProximos } from '../../servicios';
import * as bitacora from '../../servicios/bitacora';
import { ModuloEuroliga } from './PaginaEuroliga';
import { analizarEuroliga, cargarEuroliga, type ResultadoEuro } from '../../servicios/euroliga';

vi.mock('../../servicios', async (original) => ({ ...await original<typeof import('../../servicios')>(), obtenerTemporadasEquipos: vi.fn(), obtenerPartidosProximos: vi.fn() }));
vi.mock('../../servicios/euroliga', () => ({ cargarEuroliga: vi.fn(), analizarEuroliga: vi.fn() }));
afterEach(() => { cleanup(); vi.clearAllMocks(); vi.restoreAllMocks(); });

const pred = { media_local: 80, media_visitante: 81, media_total: 161, desviacion_total: 17, intervalo_predictivo_80_raw: [140, 182] as [number, number], observado: false };
const resultado = {
  analisis_id: 'captura-euro', partido_id: '00000000-0000-0000-0000-000000000301', fecha_partido: '2026-10-22',
  modelo_version: 'euro-version', dataset_sha256: 'abc', fecha_analisis: '2026-10-21T21:00:00Z', corte_datos: '2026-10-16',
  equipo_local: 'Real Madrid', equipo_visitante: 'Maccabi', mercado: 'COMPLETO', linea: 170.5, modo: 'PREPARTIDO',
  muestras: { local: 200, visitante: 6 }, predicciones: { Q1: pred, Q2: pred, Q3: pred, Q4: pred, COMPLETO: pred },
  muestras_temporada: { local: 6, visitante: 6 }, temporada_reciente: '2026-2027',
  probabilidades: { over: 0.3, under: 0.7, push: 0 }, ventaja_regulacion: { local: 0.45, visitante: 0.55, definicion: 'Sin OT' },
  advertencias: ['Probabilidades RAW no calibradas.', 'Muestra pequeña.'], prospectiva_acreditada_por_fecha: true,
  contexto: { uso: 'Descriptivo, no ajusta el modelo', equipos: {}, h2h: [] },
} satisfies ResultadoEuro;

function preparar() {
  vi.mocked(cargarEuroliga).mockResolvedValue({
    estado: { version: 'euro-version', corte_datos: '2026-10-16', fit_completed_at: '2026-10-21', partidos: 2590, equipos: 30, dataset_sha256: 'abc', min_partidos_equipo: 6,
      validacion: { train_n: 1798, cal_util_n: 292, evaluacion: { partidos: 462, evaluados: 327, abstenciones: 135, cobertura: 0.7, mercados: {} }, limitacion: 'No mide el refit final' } },
    equipos: [{ id: 'real', nombre: 'Real Madrid', muestras: 200, elegible: true }, { id: 'maccabi', nombre: 'Maccabi', muestras: 6, elegible: true }],
    partidos: [{ id: '00000000-0000-0000-0000-000000000301', fecha_partido: '2026-10-22', equipo_local_id: 'real', equipo_visitante_id: 'maccabi', equipo_local_nombre: 'Real Madrid', equipo_visitante_nombre: 'Maccabi', temporada_id: 'euro-26', temporada_nombre: 'Euroliga', tipo_partido: 'REG', local_total: null, visitante_total: null, finalizado: false }],
    ultimoFinal: '2026-10-16', historial: [],
  });
  vi.mocked(analizarEuroliga).mockResolvedValue(resultado);
  render(<ToastsProvider><MemoryRouter initialEntries={['/euroliga']}><ProveedorDeporte><ModuloEuroliga /></ProveedorDeporte></MemoryRouter></ToastsProvider>);
}

async function completar() {
  fireEvent.click(await screen.findByRole('button', { name: /Seleccionar partido/ }));
  fireEvent.click(screen.getByRole('button', { name: /Real Madrid vs Maccabi/ }));
  fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'COMPLETO' } });
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Línea del análisis' }), { target: { value: '170.5' } });
}

describe('predictor Euroliga integrado', () => {
  it('manda exactamente fixture, modo y línea a Euro; muestra porcentajes y conserva historial sin repetir POST', async () => {
    preparar(); await completar();
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    await screen.findByRole('region', { name: 'Resultado Euroliga' });
    expect(analizarEuroliga).toHaveBeenCalledTimes(1);
    expect(analizarEuroliga).toHaveBeenCalledWith({ equipo_local: 'Real Madrid', equipo_visitante: 'Maccabi', mercado: 'COMPLETO', linea: 170.5, partido_id: '00000000-0000-0000-0000-000000000301', parciales: [] });
    expect(screen.getByText('70.00%')).toBeInTheDocument();
    expect(obtenerTemporadasEquipos).not.toHaveBeenCalled();
    expect(obtenerPartidosProximos).not.toHaveBeenCalled();
    expect(screen.queryByText('Temporadas para el análisis')).toBeNull();
    expect(screen.queryByLabelText(/Cuota decimal/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Guardar en Bitácora' })).toBeInTheDocument();
    expect(screen.getByText('Probabilidades RAW no calibradas.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Historial Euroliga (1)' }));
    expect(screen.getByText(/21.*Real Madrid — Maccabi/)).toBeInTheDocument();
    expect(analizarEuroliga).toHaveBeenCalledTimes(1);
  });

  it('permite ingresar cuota decimal y guarda la apuesta en bitácora con liga y campos honestos', async () => {
    preparar(); await completar();
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    await screen.findByRole('region', { name: 'Resultado Euroliga' });
    const guardar = vi.spyOn(bitacora, 'crearApuesta').mockResolvedValue({ exito: true, apuesta: {} as never });

    fireEvent.click(screen.getByRole('button', { name: 'Guardar en Bitácora' }));
    fireEvent.change(screen.getByLabelText('Cuota decimal (obligatoria)'), { target: { value: '1.91' } });
    fireEvent.change(screen.getByLabelText(/Cuanto vas a apostar/), { target: { value: '25' } });
    expect(document.body.textContent).toContain('30.0%');
    expect(document.body.textContent).toContain('no calibrada');
    expect(document.body.textContent).toContain('N/D · no certificada');
    fireEvent.click(screen.getByRole('button', { name: 'Guardar apuesta' }));

    await waitFor(() => expect(guardar).toHaveBeenCalledTimes(1));
    expect(guardar).toHaveBeenCalledWith(expect.objectContaining({
      partido_id: '00000000-0000-0000-0000-000000000301',
      competicion_codigo: 'euroleague',
      equipo_local: 'Real Madrid', equipo_visitante: 'Maccabi',
      mercado: 'COMPLETO', lado: 'OVER', linea: 170.5,
      cuota: 1.91, stake: 25, probabilidad_sistema: 0.3,
      confianza_sistema: null, valor_esperado: undefined,
      razones: [expect.objectContaining({
        tipo: 'trazabilidad_euroliga', analisis_id: 'captura-euro',
        modelo_version: 'euro-version', dataset_sha256: 'abc',
      })],
    }));
    await waitFor(() => expect(screen.getByText('La selección Euroliga quedó registrada.')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: 'Guardar apuesta' })).toBeNull();
  });

  it('limpia salida al cambiar línea y condiciona al cierre de Q1 con parciales por cuarto', async () => {
    preparar(); await completar();
    fireEvent.change(screen.getByRole('combobox', { name: 'Modo de análisis' }), { target: { value: '1' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Q1 local' }), { target: { value: '20' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Q1 visitante' }), { target: { value: '19' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    await screen.findByRole('region', { name: 'Resultado Euroliga' });
    expect(analizarEuroliga).toHaveBeenCalledWith(expect.objectContaining({ parciales: [[20, 19]] }));
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Línea del análisis' }), { target: { value: '175.5' } });
    expect(screen.queryByRole('region', { name: 'Resultado Euroliga' })).not.toBeInTheDocument();
  });

  it('muestra error del servicio y permite reintentar sin fabricar un resultado', async () => {
    preparar(); await completar();
    vi.mocked(analizarEuroliga).mockRejectedValue(new Error('Abstención por muestra insuficiente'));
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Abstención por muestra insuficiente'));
    expect(screen.queryByRole('region', { name: 'Resultado Euroliga' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analizar Partido' })).not.toBeDisabled();
  });
  it('no convierte una selección vacía en el primer equipo con abreviatura vacía', async () => {
    preparar();
    await screen.findByRole('combobox', { name: 'Equipo Local' });
    fireEvent.change(screen.getByRole('combobox', { name: 'Equipo Visitante' }), { target: { value: 'maccabi' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'COMPLETO' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Línea del análisis' }), { target: { value: '170.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    expect(analizarEuroliga).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('Selecciona los dos equipos Euroliga.');
  });

  it('rechaza parciales vacíos y un mercado ya observado antes de enviar al motor', async () => {
    preparar(); await completar();
    fireEvent.change(screen.getByRole('combobox', { name: 'Modo de análisis' }), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    expect(analizarEuroliga).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('Completa cada cuarto terminado');
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Q1 local' }), { target: { value: '20' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Q1 visitante' }), { target: { value: '19' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'Q1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    expect(analizarEuroliga).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('posterior al corte observado');
  });

  it('las pestañas conservan línea y equipos; limpiar elimina salida y modo live', async () => {
    preparar(); await completar();
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    await screen.findByRole('region', { name: 'Resultado Euroliga' });
    fireEvent.click(screen.getByRole('button', { name: 'Estadísticas de equipos' }));
    expect(screen.getByRole('region', { name: 'Muestra de equipos Euroliga' })).toHaveTextContent('Muestra pequeña');
    fireEvent.click(screen.getByRole('button', { name: 'Análisis' }));
    expect(screen.getByRole('spinbutton', { name: 'Línea del análisis' })).toHaveValue(170.5);
    expect(screen.getByRole('combobox', { name: 'Equipo Local' })).toHaveValue('real madrid');
    expect(analizarEuroliga).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByRole('combobox', { name: 'Modo de análisis' }), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar' }));
    expect(screen.queryByRole('region', { name: 'Resultado Euroliga' })).toBeNull();
    expect(screen.getByRole('spinbutton', { name: 'Línea del análisis' })).toHaveValue(null);
    expect(screen.getByRole('combobox', { name: 'Equipo Local' })).toHaveValue('');
    expect(screen.getByRole('combobox', { name: 'Modo de análisis' })).toHaveValue('0');
    expect(screen.queryByRole('spinbutton', { name: 'Q1 local' })).toBeNull();
  });

});
