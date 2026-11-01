import '@testing-library/jest-dom/vitest';
import { useEffect } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PaginaFutbol } from './PaginaFutbol';
import { analizarPartido, crearApuesta, obtenerH2HPartidos, obtenerPartido, obtenerPartidosEquipoDetalle } from '../../servicios/futbol';
import { listarPartidosGuardados, guardarPartidoParaRevisar } from '../../servicios/bitacora';
import { listarTemporadas } from '../../servicios/futbol/catalogo';
import { clienteAPI } from '../../servicios/api';
import type { AnalisisFutbolResponse, PartidoFutbolResumen } from '../../tipos/futbol';

const toast = vi.hoisted(() => vi.fn());
const scrollOriginal = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'scrollIntoView');
const partidos: PartidoFutbolResumen[] = [
  { id: 'mls-prueba', competicion: 'mls', competicionNombre: 'MLS', fechaPartido: '2099-11-01T20:00:00Z',
    equipoLocal: 'club-mls-a', equipoLocalNombre: 'Atlanta', equipoVisitante: 'club-mls-b', equipoVisitanteNombre: 'Chicago', estado: 'PROGRAMADO' },
  { id: 'arg-prueba', competicion: 'arg', competicionNombre: 'Argentina', fechaPartido: '2099-11-01T21:00:00Z',
    equipoLocal: 'club-arg-a', equipoLocalNombre: 'River', equipoVisitante: 'club-arg-b', equipoVisitanteNombre: 'Boca', estado: 'PROGRAMADO' },
];
vi.mock('../../contextos/Toasts', () => ({ useToasts: () => ({ agregarToast: toast }) }));
vi.mock('../../servicios/futbol', () => ({ analizarPartido: vi.fn(), crearApuesta: vi.fn(), obtenerH2HPartidos: vi.fn(), obtenerPartido: vi.fn(), obtenerPartidosEquipoDetalle: vi.fn() }));
vi.mock('../../servicios/bitacora', () => ({ listarPartidosGuardados: vi.fn(), guardarPartidoParaRevisar: vi.fn(), archivarPartidoGuardado: vi.fn() }));
vi.mock('../../servicios/futbol/catalogo', () => ({ listarTemporadas: vi.fn() }));
vi.mock('../moleculas/CatalogoFutbol', () => ({ CatalogoFutbol: (p: {
  onCargando: (v: boolean) => void; onDatos: (v: PartidoFutbolResumen[]) => void;
  onSeleccionar: (v: PartidoFutbolResumen) => void; onInicio: () => void;
}) => {
  useEffect(() => { p.onDatos(partidos); p.onCargando(false); }, [p.onDatos, p.onCargando]);
  return <div><button onClick={p.onInicio}>Buscar otro partido</button>{partidos.map(partido =>
    <button key={partido.id} onClick={() => p.onSeleccionar(partido)}>Elegir {partido.competicionNombre}</button>)}</div>;
} }));
vi.mock('../organismos', async importOriginal => ({ ...await importOriginal<object>(), Encabezado: () => null,
  CreadorCombinada: () => null, SeccionHistorialDetallado: () => null,
}));
vi.mock('../moleculas', async importOriginal => ({ ...await importOriginal<object>(), TarjetaCalidadDatosFutbol: () => null }));

function respuesta(partido: PartidoFutbolResumen, mercado = 'GOLES_FT', lado = 'UNDER', linea = 2.5): AnalisisFutbolResponse {
  return { exito: true, partido, modo: 'PREPARTIDO', timestampAnalisis: '2099-10-31T10:00:00Z',
    objetivo: { estado: 'no_disponible', mercado, lado, linea, unidad: 'goles',
      mediaObjetivo: null, desviacionObjetivo: null, probabilidadesObjetivo: { over: null, under: null },
      calidadDatos: { muestraInsuficiente: true, datosIncompletos: true } },
    mercadosGoles: {}, mercadosCorners: {}, mercadosDisparos: {}, recomendaciones: [],
    advertencias: [], modeloVersion: 'heuristico-americas::1.0.0',
  } as unknown as AnalisisFutbolResponse;
}

beforeEach(() => {
  vi.resetAllMocks(); window.sessionStorage.clear(); window.localStorage.clear();
  Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { configurable: true, value: vi.fn() });
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => { callback(0); return 1; });
  window.history.replaceState({}, '', '/futbol');
  vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { estado: 'SIN_CONSULTAR', consultas: [], favoritos: [], revision: 0 } });
  vi.mocked(listarPartidosGuardados).mockResolvedValue({ partidos: [] } as never);
  vi.mocked(guardarPartidoParaRevisar).mockResolvedValue({} as never);
  vi.mocked(obtenerPartido).mockImplementation(async id => partidos.find(p => p.id === id)!);
  vi.mocked(obtenerH2HPartidos).mockResolvedValue([]);
  vi.mocked(obtenerPartidosEquipoDetalle).mockResolvedValue([]);
  vi.mocked(listarTemporadas).mockImplementation(async id => [{ id: `temporada-${id}`, nombre: `${id} 2025`, anio_inicio: 2025, finales: 30 }] as never);
  vi.mocked(analizarPartido).mockImplementation(async p => respuesta(partidos.find(f => f.id === p.partidoId)!, p.mercadoObjetivo, p.ladoObjetivo, p.lineaObjetivo));
  vi.mocked(crearApuesta).mockResolvedValue({} as never);
});
afterEach(() => {
  cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals();
  if (scrollOriginal) Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', scrollOriginal);
  else Reflect.deleteProperty(HTMLElement.prototype, 'scrollIntoView');
});

function configurar() {
  fireEvent.change(screen.getByLabelText('Mercado fútbol'), { target: { value: 'GOLES' } });
  fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'COMPLETO' } });
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Línea del análisis' }), { target: { value: '2.5' } });
  fireEvent.click(screen.getByRole('button', { name: /Menos de|Under/i }));
}

describe('flujo fútbol por encuentro', () => {
  it.each([['MLS', 'mls-prueba'], ['Argentina', 'arg-prueba']])('registra la selección manual exacta de %s con cuota real y analítica N/D', async (liga, id) => {
    render(<PaginaFutbol />);
    fireEvent.click(await screen.findByRole('button', { name: `Elegir ${liga}` }));
    configurar();
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Guardar en Seguimiento' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('Selección manual');
    fireEvent.change(screen.getByLabelText('Monto a Apostar'), { target: { value: '20' } });
    fireEvent.change(screen.getByLabelText('Cuota decimal real'), { target: { value: '1.92' } });
    fireEvent.click(screen.getByRole('button', { name: 'Guardar Apuesta' }));
    await waitFor(() => expect(crearApuesta).toHaveBeenCalledTimes(1));
    expect(crearApuesta).toHaveBeenCalledWith(expect.objectContaining({ partidoId: id, mercado: 'GOLES_FT',
      lado: 'UNDER', linea: 2.5, cuota: 1.92, stake: 20, probabilidadSistema: null, confianzaSistema: null, valorEsperado: null }));
    expect(guardarPartidoParaRevisar).not.toHaveBeenCalled();
  });

  it('conserva configuración por partido al buscar, cambiar de liga y volver, sin cruzar resultados o cuotas', async () => {
    const vista = render(<PaginaFutbol />);
    fireEvent.click(await screen.findByRole('button', { name: 'Elegir MLS' }));
    configurar();
    fireEvent.change(screen.getByLabelText('Alcance'), { target: { value: 'LOCAL' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'Q2' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: /Cuota Under/i }), { target: { value: '1.85' } });
    fireEvent.click(await screen.findByLabelText(/mls 2025/));
    fireEvent.click(screen.getByRole('button', { name: /Elegir otro partido en la agenda/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Buscar otro partido' }));
    fireEvent.click(screen.getByRole('button', { name: 'Elegir Argentina' }));
    expect(screen.getByRole('spinbutton', { name: 'Línea del análisis' })).toHaveDisplayValue('');
    expect(screen.getByRole('spinbutton', { name: /Cuota Under/i })).toHaveDisplayValue('');
    fireEvent.click(screen.getByRole('button', { name: /Elegir otro partido en la agenda/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Buscar otro partido' }));
    fireEvent.click(screen.getByRole('button', { name: 'Elegir MLS' }));
    expect(screen.getByLabelText('Mercado fútbol')).toHaveValue('GOLES');
    expect(screen.getByLabelText('Alcance')).toHaveValue('LOCAL');
    expect(screen.getByRole('combobox', { name: 'Mercado' })).toHaveValue('Q2');
    expect(screen.getByRole('spinbutton', { name: 'Línea del análisis' })).toHaveValue(2.5);
    expect(screen.getByRole('spinbutton', { name: /Cuota Under/i })).toHaveValue(1.85);
    expect(await screen.findByLabelText(/mls 2025/)).toBeChecked();
    expect(analizarPartido).not.toHaveBeenCalled();
    vista.unmount(); render(<PaginaFutbol />);
    fireEvent.click(await screen.findByRole('button', { name: 'Elegir MLS' }));
    expect(screen.getByRole('combobox', { name: 'Mercado' })).toHaveValue('Q2');
    expect(screen.getByRole('spinbutton', { name: 'Línea del análisis' })).toHaveValue(2.5);
    expect(crearApuesta).not.toHaveBeenCalled();
  });

  it('mantiene visible el marcador de seguimiento sin exigir ejecutar el análisis', async () => {
    render(<PaginaFutbol />);
    fireEvent.click(await screen.findByRole('button', { name: 'Elegir Argentina' }));
    const boton = screen.getByRole('button', { name: 'Guardar partido en Seguimiento' });
    expect(boton).toBeVisible(); fireEvent.click(boton);
    await waitFor(() => expect(guardarPartidoParaRevisar).toHaveBeenCalledWith('arg-prueba'));
    expect(crearApuesta).not.toHaveBeenCalled();
    expect(analizarPartido).not.toHaveBeenCalled();
  });
});
