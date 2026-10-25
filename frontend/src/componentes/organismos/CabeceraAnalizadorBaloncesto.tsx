/** Cabecera y pestañas originales NBA, compartidas sin variantes de layout. */
export function CabeceraAnalizadorBaloncesto({ tabActivo, onTab, liga = 'NBA' }: { tabActivo: 'analisis' | 'estadisticas'; onTab: (tab: 'analisis' | 'estadisticas') => void; liga?: 'NBA' | 'WNBA' }) {
  return <>
        <div className="mb-6 tarjeta p-4 border border-neon-cyan/20">
          <p className="text-xs uppercase tracking-wider text-neon-cyan">Marco de uso responsable</p>
          <p className="text-sm text-texto-secundario mt-2">
            AnalyticsPredict prioriza disciplina operativa y trazabilidad de decisiones. No promete ganancias fáciles.
            Es una herramienta personal de consulta y análisis exploratorio. La eficacia predictiva no está certificada.
            La pretemporada {liga} se interpreta por separado de la temporada regular; fútbol no dispone de un modelo ML apto activo.
          </p>
        </div>


        {/* Tabs */}
        <div className="mb-6 flex items-center gap-3">
          <button
            type="button"
            className={`px-4 py-2 rounded-md text-sm font-semibold border ${
              tabActivo === 'analisis'
                ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                : 'border-neon-cyan/20 text-texto-secundario'
            }`}
            onClick={() => onTab('analisis')}
          >
            Análisis
          </button>
          <button
            type="button"
            className={`px-4 py-2 rounded-md text-sm font-semibold border ${
              tabActivo === 'estadisticas'
                ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                : 'border-neon-cyan/20 text-texto-secundario'
            }`}
            onClick={() => onTab('estadisticas')}
          >
            Estadísticas de equipos
          </button>
        </div>

  </>;
}
