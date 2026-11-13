import { Encabezado } from '../organismos/Encabezado';
import { EstadoSincronizacionAgenda } from '../moleculas/EstadoSincronizacionAgenda';

export function PaginaActualizaciones() {
  return <div className="min-h-screen">
    <Encabezado />
    <main id="contenido-principal" tabIndex={-1} className="contenedor py-6 sm:py-8">
      <EstadoSincronizacionAgenda vista="tablero" />
    </main>
  </div>;
}
