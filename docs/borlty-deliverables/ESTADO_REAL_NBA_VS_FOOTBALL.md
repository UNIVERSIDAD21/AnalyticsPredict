# ESTADO_REAL_NBA_VS_FOOTBALL.md

## Objetivo
Comparar el estado real de madurez entre NBA y Football en código, contratos y operación observables.

---

## 1) NBA — estado real observado

## Qué está terminado/funcional
- Endpoints de análisis pre-partido y en vivo (`/api/analizar`, `/api/analizar-en-vivo`).
- Flujo de bitácora operativo (`/api/bitacora*`).
- Historial de predicciones (`/api/predicciones/historial`).
- Capa de métricas robusta (`/api/metricas/*`) con salud/calibración/drift/política.
- Integración de gates operativos:
  - bloqueo por mala calidad histórica (Brier),
  - modo estricto cuando hay volumen sin resolución.

## Qué está estable
- Superficie API amplia y consistente para operación diaria.
- Señales claras de trazabilidad (registro de predicciones, rutas internas de resolución/recalibración).

## Qué produce valor hoy (evidencia estructural)
- Existe flujo completo análisis → registro → métricas → operación.
- Hay comandos de operación/reporting en `README.md` (`make calidad-ciclo`, `make reporte-ejecutivo`, etc.).

## Riesgos pendientes en NBA
- Baselines numéricos críticos no revalidados en esta fase por falta de consulta productiva a BD.
- Posible desalineación confidence/calibración aún no cerrada cuantitativamente.

---

## 2) Football — estado real observado

## Qué está construido
- Endpoint principal de análisis (`POST /api/futbol/analizar`) con predicción multi-mercado.
- Rutas de catálogo y exploración:
  - competiciones,
  - equipos,
  - partidos (hoy/proximos/recientes/h2h/detalle).
- Flujo de apuestas fútbol (`/api/futbol/apuestas*`) con resolver/cancelar/actualizar.
- Métricas de fútbol (`/api/futbol/metricas/*`).

## Qué parece estable
- Motor de análisis fútbol con lógica extensa y mecanismos de calibración/policy gate.
- Persistencia de `predicciones_futbol` y calibradores específicos.

## Qué falta / brechas reales
1. **Contrato faltante**
   - Front consume `/api/futbol/apuestas/estadisticas` pero backend no lo expone.
2. **UI parcialmente no productiva**
   - `DashboardFutbol.tsx` usa datos temporales mock para gráfica 30 días.
3. **Funcionalidad pendiente visible**
   - `BitacoraFutbol.tsx` mantiene TODO de edición.
4. **Semántica de contratos más heterogénea**
   - Transformaciones manuales snake↔camel en frontend para sostener compatibilidad.

## Partes mock / parciales / no confiables
- Mock explícito de serie temporal en dashboard fútbol.
- Endpoint de estadísticas de apuestas fútbol no alineado frontend/backend.
- Señales de compatibilidad forzada en acceso a columnas (`apuestas_futbol`) por drift.

---

## 3) Comparación de madurez NBA vs Football

| Dimensión | NBA | Football |
|---|---|---|
| Cobertura API | Alta | Alta |
| Consistencia contratos FE/BE | Media-Alta | Media-Baja |
| Operación continua (métricas/gates) | Alta | Media-Alta |
| Señales de mock en UI | Baja | Media |
| Deuda por drift de esquema | Media | Alta (visible en apuestas_futbol) |
| Riesgo contractual inmediato | Medio | Alto |

### Lectura ejecutiva
- **NBA está más maduro y más defendible operativamente.**
- **Football tiene gran avance funcional, pero todavía con fricción de producto/contrato** que reduce confiabilidad percibida.

---

## 4) Estado operativo real (síntesis)

## NBA
- Operativo y utilizable.
- Más cerca de “producción controlada”.

## Football
- Funcional en núcleo analítico y API principal.
- Aún requiere cierre de brechas de contrato + limpieza de componentes mock/parciales para nivel de madurez equivalente a NBA.

---

## 5) Conclusión

El sistema ya funciona en dos dominios, pero la madurez es asimétrica:
- NBA = dominio actualmente más sólido para decisiones operativas.
- Football = dominio con buen progreso técnico, pero todavía con deuda de integración/consistencia para considerarlo al mismo nivel de confiabilidad.
