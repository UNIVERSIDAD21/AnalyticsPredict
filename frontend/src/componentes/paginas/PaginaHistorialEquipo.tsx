// hace parte del diseño de analisis
/**
 * PaginaHistorialEquipo.tsx — Página de historial de partidos por equipo
 */

import { Encabezado, HistorialEquipo } from '../organismos';

interface PropsPaginaHistorialEquipo {
  equipoId: string;
}

export function PaginaHistorialEquipo({ equipoId }: PropsPaginaHistorialEquipo) {
  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <HistorialEquipo
          equipoId={equipoId}
          onCerrar={() => window.location.assign('/')}
          textoCerrar="Volver al análisis"
        />
      </main>
    </div>
  );
}
