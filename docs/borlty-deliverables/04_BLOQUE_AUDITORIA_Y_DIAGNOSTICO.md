# Bloque de Actividad — Auditoría y Diagnóstico

## Propósito del bloque

Este bloque existe para producir una lectura real del sistema antes de refactorizar o expandir.

## Objetivos del bloque

1. Entender arquitectura real
2. Validar estado real por dominio
3. Detectar deuda técnica
4. Contrastar código vs documentación
5. Contrastar BD vs documentación
6. Detectar inconsistencias de contratos
7. Verificar baselines operativos
8. Identificar prioridades reales

## Actividades

### A. Auditoría de arquitectura backend
- listar módulos
- listar routers
- listar servicios
- listar motores de predicción
- listar scrapers
- listar jobs automáticos
- revisar acoplamientos

### B. Auditoría de frontend
- listar páginas
- listar services
- listar hooks
- listar types
- identificar qué consume realmente del backend
- detectar pantallas mock o incompletas

### C. Auditoría de base de datos
- listar tablas
- listar vistas
- revisar foreign keys
- revisar constraints
- revisar natural keys
- revisar tablas legacy
- revisar columnas legacy
- revisar drift de esquema

### D. Auditoría de contratos
- comparar payloads reales vs tipos TypeScript
- revisar estructura de errores
- revisar naming inconsistencies
- revisar formatos de fechas, números y decimales

### E. Auditoría de métricas y baselines
- validar 81.48% win rate
- validar 11.53% ROI
- validar confidence paradox
- validar odds > 2.0
- validar superioridad de quarter markets
- validar stake rules observadas

### F. Auditoría de estado por dominio
- qué está estable en NBA
- qué está roto en NBA
- qué está construido en Football
- qué falta realmente en Football

## Entregable del bloque

`AUDITORIA_TECNICA_Y_ANALITICA.md`

## Regla del bloque

No refactorizar antes de terminar este diagnóstico.
