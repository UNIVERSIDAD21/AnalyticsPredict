# Módulo de Scraping de Sofascore

Módulo completo para la extracción de datos de fútbol desde Sofascore, incluyendo partidos históricos, estadísticas detalladas (corners, disparos, posesión, xG) y sincronización con base de datos PostgreSQL.

## Descripción General

Este módulo forma parte del sistema AnalyticsPredict y proporciona:

- **Cliente HTTP robusto** con rate limiting y reintentos automáticos
- **Extractores especializados** para temporadas, equipos, partidos y estadísticas
- **Sincronización a PostgreSQL** con upsert idempotente
- **Calculador de estadísticas agregadas** por equipo
- **Sistema de monitoreo y logging** completo
- **Scripts de línea de comandos** para carga histórica y sincronización

## Requisitos

- Python 3.9+
- PostgreSQL con tablas de fútbol creadas (Fase 1)
- Acceso a internet para consultar Sofascore

### Dependencias

```
requests>=2.31.0
psycopg>=3.2.1
psycopg-pool>=3.2.2
python-dotenv>=1.0.0
```

## Instalación

1. Asegúrate de tener las dependencias instaladas:

```bash
pip install requests psycopg psycopg-pool python-dotenv
```

2. Configura las variables de entorno en `.env`:

```bash
DATABASE_URL=postgresql://usuario:password@host:5432/database

# Opcionales - configuración de Sofascore
SOFASCORE_MIN_REQUEST_INTERVAL=0.5  # segundos entre peticiones
SOFASCORE_MAX_RETRIES=5             # reintentos máximos
SOFASCORE_BACKOFF_BASE=1.0          # base para backoff exponencial
```

3. Inicializa las competiciones en la BD:

```bash
python backend/scripts/actualizar_ids_sofascore.py --crear-faltantes
```

## Estructura del Módulo

```
backend/scrapers/sofascore/
├── __init__.py              # Exports principales
├── cliente.py               # Cliente HTTP con rate limiting
├── excepciones.py           # Excepciones personalizadas
├── temporadas.py            # Extractor de temporadas
├── equipos.py               # Extractor de equipos
├── partidos.py              # Extractor de partidos básicos
├── estadisticas.py          # Extractor de estadísticas detalladas
├── sincronizador.py         # Persistencia a PostgreSQL
├── calculador_estadisticas.py # Estadísticas agregadas por equipo
├── monitoreo.py             # Logging y métricas
└── README.md                # Esta documentación

backend/scripts/
├── cargar_historico_futbol.py    # Carga histórica
├── sincronizar_futbol.py         # Sincronización continua
├── actualizar_ids_sofascore.py   # Mapeo de IDs
└── auditar_datos_futbol.py       # Auditoría de datos
```

## Uso Básico

### Cliente HTTP

```python
from scrapers.sofascore import SofascoreClient

# Crear cliente
cliente = SofascoreClient()

# Obtener temporadas de La Liga
datos = cliente.get('/unique-tournament/8/seasons')

# El cliente maneja automáticamente:
# - Rate limiting (espera entre peticiones)
# - Reintentos con backoff exponencial
# - Headers de navegador
```

### Obtener Partidos

```python
from scrapers.sofascore.cliente import SofascoreClient
from scrapers.sofascore.partidos import obtener_partidos_pasados

cliente = SofascoreClient()

# Obtener partidos de La Liga temporada 2024-25
partidos = obtener_partidos_pasados(
    cliente,
    liga_id=8,
    temporada_id=52376
)

for p in partidos:
    print(f"{p.equipo_local_nombre} {p.goles_local_total} - "
          f"{p.goles_visitante_total} {p.equipo_visitante_nombre}")
```

### Obtener Estadísticas Detalladas

```python
from scrapers.sofascore.estadisticas import obtener_estadisticas_partido

# Obtener estadísticas de un partido específico
stats = obtener_estadisticas_partido(cliente, evento_id=12345678)

if stats:
    print(f"Corners: {stats.corners_local_total} - {stats.corners_visitante_total}")
    print(f"Disparos: {stats.disparos_local_total} - {stats.disparos_visitante_total}")
    if stats.tiene_xg():
        print(f"xG: {stats.xg_local:.2f} - {stats.xg_visitante:.2f}")
```

### Sincronizar con Base de Datos

```python
from db import obtener_pool
from scrapers.sofascore.sincronizador import sincronizar_partido_completo

with obtener_pool().connection() as conn:
    resultado = sincronizar_partido_completo(
        conn, cliente, partido, liga_id=8
    )

    if resultado['insertado']:
        print(f"Nuevo partido: {resultado['partido_id']}")
    else:
        print(f"Actualizado: {resultado['cambios']}")
```

## Scripts de Línea de Comandos

### Carga Histórica

```bash
# Cargar La Liga temporada 2024-25
python backend/scripts/cargar_historico_futbol.py \
    --liga laliga \
    --temporadas 2024-25 \
    --verbose

# Cargar múltiples temporadas de múltiples ligas
python backend/scripts/cargar_historico_futbol.py \
    --liga todas \
    --temporadas 2024-25,2023-24 \
    --con-estadisticas

# Solo partidos finalizados, sin estadísticas
python backend/scripts/cargar_historico_futbol.py \
    --liga premier \
    --solo-finalizados \
    --sin-estadisticas

# Simulación sin guardar
python backend/scripts/cargar_historico_futbol.py \
    --liga laliga \
    --dry-run \
    --verbose
```

### Sincronización Continua

```bash
# Sincronizar últimos 7 días
python backend/scripts/sincronizar_futbol.py \
    --liga laliga \
    --dias 7

# Incluir partidos futuros
python backend/scripts/sincronizar_futbol.py \
    --liga todas \
    --dias 3 \
    --incluir-futuros \
    --dias-futuros 14

# Completar estadísticas faltantes
python backend/scripts/sincronizar_futbol.py \
    --liga premier \
    --completar-estadisticas

# Recalcular estadísticas de equipos
python backend/scripts/sincronizar_futbol.py \
    --liga laliga \
    --calcular-agregados
```

### Actualizar IDs de Sofascore

```bash
# Actualizar IDs existentes
python backend/scripts/actualizar_ids_sofascore.py

# Verificar IDs con Sofascore
python backend/scripts/actualizar_ids_sofascore.py --verificar

# Crear competiciones faltantes
python backend/scripts/actualizar_ids_sofascore.py --crear-faltantes

# Simulación
python backend/scripts/actualizar_ids_sofascore.py --dry-run
```

### Auditoría de Datos

```bash
# Auditar todas las competiciones
python backend/scripts/auditar_datos_futbol.py

# Auditar una competición específica
python backend/scripts/auditar_datos_futbol.py --competicion ESP_LALIGA

# Exportar reporte
python backend/scripts/auditar_datos_futbol.py --exportar reporte.json

# Solo mostrar errores
python backend/scripts/auditar_datos_futbol.py --solo-errores --listar-partidos
```

## API de Sofascore

### Endpoints Utilizados

| Endpoint | Descripción |
|----------|-------------|
| `/unique-tournament/{id}/seasons` | Temporadas de una liga |
| `/unique-tournament/{id}/season/{id}/standings/total` | Clasificación |
| `/unique-tournament/{id}/season/{id}/events/last/{page}` | Partidos pasados |
| `/unique-tournament/{id}/season/{id}/events/next/{page}` | Partidos futuros |
| `/event/{id}/statistics` | Estadísticas de un partido |

### IDs de Ligas Principales

| Liga | Sofascore ID |
|------|--------------|
| La Liga | 8 |
| Premier League | 17 |
| Bundesliga | 35 |
| Serie A | 23 |
| Ligue 1 | 34 |
| Champions League | 7 |
| Europa League | 679 |
| Conference League | 17015 |

### Limitaciones

- **Rate limiting**: Sofascore bloquea IPs que hacen muchas peticiones. El cliente implementa esperas automáticas.
- **Sin documentación oficial**: Los endpoints se descubren por ingeniería inversa y pueden cambiar.
- **Datos incompletos**: Algunos partidos (especialmente antiguos) pueden no tener estadísticas detalladas.

## Estructura de Datos

### PartidoBasico

```python
@dataclass
class PartidoBasico:
    sofascore_id: int
    fecha_partido: datetime
    equipo_local_id: int
    equipo_local_nombre: str
    equipo_visitante_id: int
    equipo_visitante_nombre: str
    goles_local_1t: Optional[int]
    goles_local_2t: Optional[int]
    goles_local_total: Optional[int]
    goles_visitante_1t: Optional[int]
    goles_visitante_2t: Optional[int]
    goles_visitante_total: Optional[int]
    estado: str  # finished, notstarted, inprogress, postponed, cancelled
    jornada: Optional[int]
```

### EstadisticasPartido

```python
@dataclass
class EstadisticasPartido:
    # Corners
    corners_local_1t, corners_local_2t, corners_local_total
    corners_visitante_1t, corners_visitante_2t, corners_visitante_total

    # Disparos
    disparos_local_total, disparos_local_arco
    disparos_visitante_total, disparos_visitante_arco

    # Posesión
    posesion_local, posesion_visitante

    # xG
    xg_local, xg_visitante

    # Flags
    datos_completos: bool
    datos_corners_completos: bool
    datos_xg_disponible: bool
```

## Troubleshooting

### Error 429 (Rate Limiting)

El cliente maneja automáticamente los errores 429 con backoff exponencial. Si persiste:

```python
# Aumentar intervalo entre peticiones
cliente = SofascoreClient(min_intervalo=2.0)

# O vía variable de entorno
SOFASCORE_MIN_REQUEST_INTERVAL=2.0
```

### Partidos sin Estadísticas

Algunos partidos no tienen estadísticas disponibles. El código lo maneja:

```python
stats = obtener_estadisticas_partido(cliente, evento_id)
if stats is None:
    print("No hay estadísticas disponibles")
elif not stats.tiene_xg():
    print("Partido sin xG")
```

### Competición No Encontrada

Si recibes errores de "competición no encontrada":

```bash
# Ejecutar mapeo de IDs
python backend/scripts/actualizar_ids_sofascore.py --crear-faltantes --verificar
```

### Errores de Conexión a BD

Verifica que `DATABASE_URL` esté configurado correctamente:

```python
from db import obtener_pool

try:
    pool = obtener_pool()
    with pool.connection() as conn:
        print("Conexión exitosa")
except Exception as e:
    print(f"Error: {e}")
```

## Agregar Nueva Competición

1. Identificar el ID de Sofascore de la competición (usar herramientas de desarrollo del navegador en sofascore.com)

2. Agregar al mapeo en `actualizar_ids_sofascore.py`:

```python
MAPEO_COMPETICIONES = {
    # ...
    'NUEVA_LIGA': 12345,
}
```

3. Ejecutar actualización:

```bash
python backend/scripts/actualizar_ids_sofascore.py --crear-faltantes
```

4. Cargar datos:

```bash
python backend/scripts/cargar_historico_futbol.py \
    --liga nueva_liga \
    --temporadas 2024-25
```

## Monitoreo

### Logs

```python
from scrapers.sofascore.monitoreo import configurar_logging

# Configurar logging a archivo
configurar_logging(
    nivel=logging.INFO,
    archivo_log='logs/sofascore.log'
)
```

### Métricas del Cliente

```python
metricas = cliente.obtener_metricas()
print(f"Peticiones: {metricas['peticiones_totales']}")
print(f"Errores: {metricas['errores_totales']}")
print(f"Tasa éxito: {metricas['tasa_exito']:.1f}%")
```

### Reporte de Estado

```python
from scrapers.sofascore.monitoreo import imprimir_reporte_estado

with obtener_pool().connection() as conn:
    imprimir_reporte_estado(conn)
```

## Desarrollo

### Ejecutar Tests

```bash
# Tests unitarios (cuando estén implementados)
pytest backend/tests/scrapers/sofascore/
```

### Modo Debug

```python
import logging
from scrapers.sofascore.monitoreo import configurar_logging

configurar_logging(nivel=logging.DEBUG)
```

## Licencia

Uso interno - Sistema AnalyticsPredict
