import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ModalGuardarApuestaFutbol } from './ModalGuardarApuestaFutbol';

afterEach(cleanup);
const base = { mostrar: true, onCerrar: vi.fn(), partidoInfo: { equipoLocal: 'River', equipoVisitante: 'Boca', fecha: '2099-01-01' },
  recomendacion: { mercado: 'GOLES_FT' as const, lado: 'UNDER' as const, linea: 2.5, cuota: 0,
    probabilidad: null, confianza: null, esRecomendacion: false } };

describe('registro fútbol sin cuota del proveedor', () => {
  it('rechaza la cuota ausente, inválida o infinita sin enviar un registro', () => {
    const guardar = vi.fn(); render(<ModalGuardarApuestaFutbol {...base} onGuardar={guardar} />);
    fireEvent.change(screen.getByLabelText('Monto a Apostar'), { target: { value: '10' } });
    const form = screen.getByRole('button', { name: 'Guardar Apuesta' }).closest('form')!;
    for (const cuota of ['', '0', '1', '-2', 'Infinity']) {
      fireEvent.change(screen.getByLabelText('Cuota decimal real'), { target: { value: cuota } });
      fireEvent.submit(form);
    }
    expect(guardar).not.toHaveBeenCalled();
    expect(screen.getByText('Ingresa la cuota decimal real, mayor que 1.')).toBeInTheDocument();
    expect(screen.getAllByText('N/D')).toHaveLength(3);
  });
  it('mantiene la cuota original de la recomendación y no solicita una sustitución', () => {
    const guardar = vi.fn(); render(<ModalGuardarApuestaFutbol {...base} onGuardar={guardar}
      recomendacion={{ ...base.recomendacion, cuota: 1.95, probabilidad: .6, confianza: 'MEDIA', esRecomendacion: true }} />);
    expect(screen.queryByLabelText('Cuota decimal real')).toBeNull();
    fireEvent.change(screen.getByLabelText('Monto a Apostar'), { target: { value: '25' } });
    fireEvent.click(screen.getByRole('button', { name: 'Guardar Apuesta' }));
    expect(guardar).toHaveBeenCalledExactlyOnceWith(25, 1.95);
  });
});
