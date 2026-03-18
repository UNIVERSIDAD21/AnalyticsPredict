# ADR-003 — Estrategia de contexto para chatbot

- Estado: ACEPTADO
- Fecha: 2026-03-18

## Contexto
Enviar historial completo del usuario al LLM en cada request escala costos y latencia sin mejorar proporcionalmente la calidad.

## Decisión
Implementar `chat_contexto.py` con ventana deslizante de últimos **N** registros relevantes por usuario (N configurable), priorizando:
1. Predicciones recientes del usuario
2. Estado actual de suscripción
3. Señales de calidad relevantes actuales

## Restricciones
- Prohibido enviar historial completo por defecto.
- Registrar tamaño de contexto y costo estimado por request.

## Consecuencias
- Control de costos desde día 1.
- Necesidad de tuning de N y ranking de relevancia.
