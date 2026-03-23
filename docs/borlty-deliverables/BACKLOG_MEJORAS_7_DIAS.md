# Backlog Profesional de Mejoras (7 días)

## Objetivo
Cerrar brechas de calidad real y dejar una operación profesional, medible y estable.

---

## Día 1 (P1)
### 1. Resolución automática diaria (ambos deportes)
- Implementar job diario que ejecute:
  - `/api/interno/resolver-predicciones`
  - `/api/interno/resolver-predicciones-futbol`
- Resultado esperado: crecimiento continuo de `n_resueltas`.

### 2. Salud diaria automática
- Ejecutar `/api/metricas/tablero-salud` y guardar snapshot.
- Resultado esperado: trazabilidad histórica del score de salud.

---

## Día 2 (P1)
### 3. Ranking de calidad por mercado
- Activar y usar `/api/metricas/calidad-mercados`.
- Definir top 5 mercados críticos por Brier.

### 4. Recalibración de mercados críticos
- Ejecutar recalibración solo en mercados con muestra suficiente.
- Registrar mejora real (raw vs calibrado).

---

## Día 3 (P1)
### 5. Controles de riesgo en recomendaciones
- No emitir recomendaciones cuando:
  - muestra insuficiente,
  - varianza alta,
  - calibrador no confiable.
- Incluir bandera de calidad por pick.

---

## Día 4 (P2)
### 6. Drift por mercado
- Alertar cuando Brier 7d empeora > 12% vs 30d previos.
- Alertas con severidad (media/alta/crítica).

---

## Día 5 (P2)
### 7. Reporte ejecutivo automático
- Reporte diario (texto):
  - score global,
  - top mercados fuertes/débiles,
  - acciones recomendadas.

---

## Día 6 (P2)
### 8. Estabilidad de entrenamiento
- Congelar config de entrenamiento por versión.
- Guardar metadata completa de modelo (dataset/hash/periodo).

---

## Día 7 (P3)
### 9. QA final + endurecimiento
- Tests smoke + tests de endpoints críticos.
- Checklist operacional final para el equipo.

---

## KPIs de éxito (al final de 7 días)
1. `n_resueltas` sube cada día en ambos deportes.
2. `score_global` >= 85 sostenido.
3. Mercados críticos reducidos al menos 30%.
4. Menos alertas críticas de deriva.
5. Operación reproducible sin intervención manual constante.
