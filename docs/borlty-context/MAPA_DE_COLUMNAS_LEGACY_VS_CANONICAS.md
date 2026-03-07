# MAPA_DE_COLUMNAS_LEGACY_VS_CANONICAS.md

## Objetivo
Mapear código ↔ tabla ↔ columnas para identificar drift activo y compatibilidad forzada.

---

## A) `backend/api/rutas_apuestas_futbol.py`

### Código defensivo detectado
- `_obtener_columnas_apuestas()`
- `_resolver_columna(columnas, *candidatos)`
- uso repetido de selección dinámica de columnas en list/detail/update/resolver/cancelar.

### Mapa legacy vs canónica

| Función/campo lógico | Tabla | Canónica | Legacy en fallback |
|---|---|---|---|
| estado | apuestas_futbol | `estado` | `status` |
| probabilidad | apuestas_futbol | `probabilidad_sistema` | `probabilidad` |
| confianza | apuestas_futbol | `confianza_sistema` | `confianza` |
| cuota | apuestas_futbol | `cuota` | `odds`, `cuota_decimal` |
| ganancia real | apuestas_futbol | `ganancia` | `ganancia_real`, `ganancia_neta` |
| resultado | apuestas_futbol | `resultado` | `resultado_real` |
| casa apuestas | apuestas_futbol | `casa_apuestas` | `casa_apuesta` |

---

## B) `backend/api/rutas_metricas_futbol.py`

### Código defensivo detectado
- `_resolver_columna_estado_apuestas()`
- `_resolver_columna_ganancia_apuestas()`
- `_resolver_columna_modelo()` para `modelo_versiones_futbol`

### Mapa

| Resolver | Tabla | Canónica | Legacy en fallback |
|---|---|---|---|
| estado apuestas | apuestas_futbol | `estado` | `resultado`, `status` |
| ganancia apuestas | apuestas_futbol | `ganancia` | `ganancia_real`, `ganancia_neta`, `beneficio_real`, `beneficio` |
| columnas modelo | modelo_versiones_futbol | columnas específicas por contrato | variantes (`tipo`, `modelo`, `mae_total`, etc.) |

---

## C) Estado real en BD (evidencia)

En BD actual, para `apuestas_futbol` existen columnas canónicas como:
- `cuota`, `probabilidad_sistema`, `confianza_sistema`, `ganancia`, `resultado`, `casa_apuestas`.

No se verificó presencia activa de las columnas legacy citadas arriba como canónicas de producción en este entorno.

---

## D) Riesgo operativo por drift

1. Métricas pueden variar si se resuelve columna distinta por entorno.
2. Contrato API puede cambiar silenciosamente si aparece columna legacy en una instancia.
3. Debugging difícil por comportamiento dinámico sin señal explícita.

---

## E) Mitigación aplicada en esta fase

Se añadieron alertas `logger.warning` cuando:
- se usa una columna legacy en lugar de canónica,
- no se encuentra ninguna candidata esperada.

Archivos con mitigación:
- `backend/api/rutas_apuestas_futbol.py`
- `backend/api/rutas_metricas_futbol.py`
