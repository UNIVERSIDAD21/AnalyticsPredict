# 02 — B3 cierre formal (2 ciclos semanales)

## Objetivo
Cerrar B3 con evidencia estadística semanal por liga sin estados críticos.

## Criterio de done
- 2 ciclos semanales consecutivos sin ligas críticas.
- Reporte comparativo consolidado entre ciclos.
- Estado B3 => CERRADO.

## Entregables
- Dos reportes semanales firmados.
- Reporte comparativo final.
- Actualización documental (estado/changelog).

---

## Runbook operativo

### Ejecutar ciclo semanal
```bash
BASE_URL="http://localhost:8000" ./scripts/b3_ciclo_semanal.sh
```

Salida:
- `docs/reportes/B3_CICLO_SEMANAL_<timestamp>.md`

### Regla de cierre
- Se requieren **2 reportes consecutivos** con `Ligas en estado crítico = 0`.
- Luego generar informe comparativo y cerrar B3 en estado documental.

## Evidencia mínima
1. Reporte ciclo semana 1.
2. Reporte ciclo semana 2.
3. Comparativo final con decisión de cierre.
