# ARQUITECTURA_POR_DOMINIOS

Versión: 1.0  
Fecha: 2026-03-09

## 1. Mapa de módulos backend por dominio

| Módulo | Tipo | Acoplamiento |
|---|---|---|
| `backend/api/rutas_predicciones.py` | NBA | Bajo |
| `backend/api/rutas_metricas.py` | NBA | Medio |
| `backend/api/rutas_apuestas.py` | NBA | Medio |
| `backend/api/rutas_apuestas_futbol.py` | FUTBOL | Bajo |
| `backend/api/rutas_metricas_futbol.py` | FUTBOL | Bajo |
| `backend/motor_futbol/*` | FUTBOL | Medio (interno) |
| `backend/calidad/scorecard.py` | COMPARTIDO | Alto |
| `backend/calidad/alertas.py` | COMPARTIDO | Alto |
| `backend/explicabilidad/contrato.py` | COMPARTIDO | Alto |
| `backend/feature_flags.py` | COMPARTIDO | Bajo |

## 2. Mapa frontend por dominio

| Módulo | Tipo |
|---|---|
| `componentes/paginas/DashboardFutbol.tsx` | FUTBOL |
| `componentes/explicabilidad/*` | COMPARTIDO |
| `componentes/dashboard/DashboardCalidad.tsx` | COMPARTIDO |

## 3. Mapa de rutas API por dominio

- NBA: `/api/predicciones/*`, `/api/metricas/*` (no futbol), rutas de análisis NBA.
- Fútbol: `/api/apuestas-futbol/*`, `/api/metricas-futbol/*`, `/api/partidos-futbol/*`.
- Compartidas: `/api/calidad/*`, `/api/prediccion/{id}/explicacion`.

## 4. Dependencias cruzadas detectadas

1. `rutas_explicabilidad.py` consume scorecard/alertas compartidas para ambos deportes.
2. Deuda contractual legacy impacta ambos flujos en endpoint de explicación.
3. `estado-sistema` mezcla estado de NBA y fútbol en una sola salida.

## 5. Riesgos de acoplamiento

- Fallo en tabla/estructura común de calidad puede impactar ambos dominios.
- Cambios en contrato de explicación pueden afectar frontend completo.
- Deuda de drift fútbol contamina percepción de estado global si no se segmenta visualmente.

## 6. Módulos que deben seguir compartidos

- `feature_flags.py`: control global de rollout.
- `calidad/*`: gobierno unificado de calidad y alertas.
- `explicabilidad/contrato.py`: contrato canónico consistente para clientes.

## 7. Estado

Documento de diagnóstico y planificación. No ejecuta separación física por sí mismo.
