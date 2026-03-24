# C2 — Estrategia de persistencia productiva (mínimo viable de go-live)

## Decisión C2
Para salida comercial controlada:
- **AuthStore** y **PagosStore** se aceptan temporalmente en SQLite **solo** con:
  1) backups frecuentes,
  2) restore test validado,
  3) runbook operativo,
  4) observabilidad mínima.

## Qué queda fuera de ambigüedad
- Persistencia launch-critical identificada y documentada.
- No se considera "producción segura" sin evidencia de restore test.

## Criterio de transición posterior
- Migración a motor gestionado (post C2) cuando:
  - volumen y concurrencia superen umbral operativo,
  - SLO de disponibilidad exija multi-nodo,
  - operaciones de soporte indiquen carga no sostenible en SQLite.

## Política de aceptación temporal
- Aceptar temporal no significa cerrar deuda.
- Significa go-live controlado con mitigaciones verificables.
