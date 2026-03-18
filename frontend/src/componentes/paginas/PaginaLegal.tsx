import { Link } from 'react-router-dom';

type TipoLegal = 'terminos' | 'privacidad' | 'disclaimer';

const CONTENIDO: Record<TipoLegal, { titulo: string; texto: string[] }> = {
  terminos: {
    titulo: 'Términos y Condiciones',
    texto: [
      'AnalyticsPredict ofrece analítica deportiva informativa y no garantiza resultados.',
      'El uso comercial del servicio requiere cuenta activa y cumplimiento normativo local.',
      'El usuario es responsable de sus decisiones de apuesta y gestión de riesgo.',
    ],
  },
  privacidad: {
    titulo: 'Política de Privacidad',
    texto: [
      'Recolectamos correo, trazas operativas y eventos de uso para seguridad y mejora del servicio.',
      'No compartimos datos personales con terceros salvo obligación legal o proveedores operativos.',
      'Puedes solicitar actualización o eliminación de datos según normativa aplicable.',
    ],
  },
  disclaimer: {
    titulo: 'Disclaimer de Riesgo',
    texto: [
      'Las probabilidades son estimaciones estadísticas sujetas a incertidumbre y sesgos de mercado.',
      'No existe promesa de ganancias; puedes perder total o parcialmente el capital apostado.',
      'Usa límites de bankroll y evita apostar dinero que afecte tu estabilidad financiera.',
    ],
  },
};

export function PaginaLegal({ tipo }: { tipo: TipoLegal }) {
  const data = CONTENIDO[tipo];

  return (
    <div className="min-h-screen bg-futurista-negro p-6 text-texto-principal">
      <div className="mx-auto max-w-3xl rounded-xl border border-neon-cyan/20 bg-futurista-oscuro/60 p-6 space-y-4">
        <h1 className="text-2xl font-bold text-neon-cyan">{data.titulo}</h1>
        <p className="text-xs text-texto-secundario">Versión legal vigente: 2026-03-18</p>
        <ul className="space-y-2 text-sm text-texto-secundario list-disc pl-5">
          {data.texto.map((linea) => (
            <li key={linea}>{linea}</li>
          ))}
        </ul>
        <div className="pt-4">
          <Link to="/login" className="text-neon-cyan hover:underline text-sm">
            ← Volver a login
          </Link>
        </div>
      </div>
    </div>
  );
}
