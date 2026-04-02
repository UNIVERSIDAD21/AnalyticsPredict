/**
 * SelectorMercado.tsx — Selector de mercado (Q1-Q4, COMPLETO)
 */

import { Select, OpcionSelect } from '../atomos';
import { Mercado } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const OPCIONES_MERCADO: OpcionSelect[] = [
  { valor: 'Q1', etiqueta: 'Primer Cuarto (Q1)' },
  { valor: 'Q2', etiqueta: 'Segundo Cuarto (Q2)' },
  { valor: 'Q3', etiqueta: 'Tercer Cuarto (Q3)' },
  { valor: 'Q4', etiqueta: 'Cuarto Cuarto (Q4)' },
  { valor: 'COMPLETO', etiqueta: 'Juego Completo' },
];

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSelectorMercado {
  /** Valor seleccionado */
  valor: Mercado | '';
  /** Callback cuando cambia la selección */
  onChange: (valor: Mercado) => void;
  /** Mensaje de error */
  error?: string;
  /** Deshabilitado */
  deshabilitado?: boolean;
  /** Opciones custom por módulo (ej: fútbol) */
  opciones?: OpcionSelect[];
  /** Texto de ayuda custom */
  textoAyuda?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Selector para elegir el mercado a analizar
 */
export function SelectorMercado({
  valor,
  onChange,
  error,
  deshabilitado = false,
  opciones,
  textoAyuda,
}: PropsSelectorMercado) {
  return (
    <Select
      etiqueta="Mercado"
      opciones={opciones ?? OPCIONES_MERCADO}
      value={valor}
      onChange={(e) => onChange(e.target.value as Mercado)}
      placeholder="Selecciona el mercado"
      error={error}
      disabled={deshabilitado}
      textoAyuda={textoAyuda ?? "Q1-Q4 para cuartos individuales, COMPLETO para el juego entero"}
    />
  );
}
