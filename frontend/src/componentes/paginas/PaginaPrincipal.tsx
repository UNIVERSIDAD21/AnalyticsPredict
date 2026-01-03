/**
 * PaginaPrincipal.tsx — Página principal de la aplicación
 */

import { useEffect } from 'react';
import { Encabezado, FormularioAnalisis, ResultadoAnalisis } from '../organismos';
import { MensajeError } from '../moleculas';
import { Spinner } from '../atomos';
import { useEquipos, useAnalisis } from '../../hooks';

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Página principal del Analizador NBA
 */
export function PaginaPrincipal() {
  const {
    equipos,
    estado: estadoEquipos,
    error: errorEquipos,
    recargar: recargarEquipos,
  } = useEquipos();

  const {
    resultado,
    estado: estadoAnalisis,
    error: errorAnalisis,
    analizar,
    limpiar: limpiarAnalisis,
  } = useAnalisis();

  // Scroll al resultado cuando se completa el análisis
  useEffect(() => {
    if (resultado) {
      const elementoResultado = document.getElementById('resultado-analisis');
      if (elementoResultado) {
        elementoResultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [resultado]);

  return (
    <div className="min-h-screen bg-nba-gris-50">
      {/* Encabezado */}
      <Encabezado />

      {/* Contenido principal */}
      <main className="contenedor py-8">
        <div className="space-y-8">
          {/* Error de conexión */}
          {estadoEquipos === 'error' && (
            <MensajeError
              titulo="Error de conexión"
              mensaje={errorEquipos || 'No se pudo conectar con el servidor'}
              onCerrar={recargarEquipos}
            />
          )}

          {/* Estado de carga inicial */}
          {estadoEquipos === 'cargando' && (
            <div className="flex justify-center py-12">
              <Spinner tamano="lg" texto="Conectando con el servidor..." centrado />
            </div>
          )}

          {/* Formulario */}
          {estadoEquipos === 'exito' && (
            <FormularioAnalisis
              equipos={equipos}
              onAnalizar={analizar}
              cargando={estadoAnalisis === 'cargando'}
              cargandoEquipos={estadoEquipos === 'cargando'}
            />
          )}

          {/* Error de análisis */}
          {errorAnalisis && (
            <MensajeError
              titulo="Error en el análisis"
              mensaje={errorAnalisis}
              onCerrar={limpiarAnalisis}
            />
          )}

          {/* Spinner de análisis */}
          {estadoAnalisis === 'cargando' && (
            <div className="flex justify-center py-8">
              <Spinner tamano="lg" texto="Analizando partido..." centrado />
            </div>
          )}

          {/* Resultados */}
          {resultado && (
            <div id="resultado-analisis">
              <ResultadoAnalisis resultado={resultado} />
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-nba-gris-800 text-nba-gris-400 py-6 mt-12">
        <div className="contenedor text-center text-sm">
          <p>
            Analizador NBA — Sistema de análisis de apuestas deportivas
          </p>
          <p className="mt-1 text-nba-gris-500">
            Los análisis son orientativos. Apuesta responsablemente.
          </p>
        </div>
      </footer>
    </div>
  );
}
