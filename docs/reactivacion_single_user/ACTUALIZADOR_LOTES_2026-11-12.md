# Actualizador manual por lotes — contrato y continuidad

## Alcance

El botón existente conserva fuentes, parsers y guardas de calidad. El worker
recorre varios lotes dentro de su misma exclusión mutua y presupuesto: 48
turnos/lote y 200 turnos máximos de agenda por ciclo, con 216 HTTP de margen.
Una URL y sus parámetros sólo consumen un turno por ciclo aunque acrediten
varias consultas de contexto. Sin elegibles no significa cobertura completa.
Los recibos SQL y el resumen de consultas pendientes/error son la evidencia.

## Contadores

`cobertura_operativa` es aditiva y compatible con consumidores anteriores.
Separa 22 competiciones de revisión diaria y dos torneos archivados explícitos
(ARG_MARADONA y USA_MLS_BACK). No se archiva un feed porque responda vacío.
Los campos faltantes son seis métricas FT de fútbol por partido válido,
guardado, final y con goles completos en la ventana. No miden todo el histórico
ni certifican estadísticas ausentes en la fuente. La cola acumulada se muestra
por separado; la fecha de reintento habilita un próximo ciclo manual, no un cron.
El estado global continúa PARCIAL mientras existan limitaciones, sin fecha
integral completa inventada. La antigüedad de un torneo terminado no prueba atraso.

## Evidencia alternativa

`estadisticas_html_personal.py` es puro: no descarga ni escribe. Sólo interpreta
capturas públicas de uso personal acotado, atribuidas a ScoreMondo y enlazadas
por una revisión explícita de identidad. Exige SHA/HTTP, localía, UTC ±2 minutos,
FT y cierre inequívoco del mismo evento. Excluye prórroga y valores aproximados
`~`; conserva ausencias como NULL. Cualquier conflicto no NULL retiene todo el
partido en el procedimiento personal. No presume independencia del upstream ni
habilita scraping masivo. Las observaciones WEB conservan su origen; no se
renombra una evidencia ESPN rechazada. La guarda vigente impide que una captura
posterior rechazada reabra un campo ya acreditado.

## Registro persistente y reanudación

El checklist solicitado por Erik vive fuera del producto en:
`C:/Users/ING-ERIK/AnalyticsPredict/Carpeta de Entregas de Borlty/MEJORA_ACTUALIZADOR_2026-11-12/CHECKLIST.md`.
Leer también ESTADO_ACTUAL.json y BITACORA.jsonl de esa entrega antes de retomar.
Los planes V1 de catálogo NO son aplicables: fueron rechazados por duplicados
potenciales durante revisión. Sólo el paquete V2 sellado, ensayado en un clon
fresco, es candidato. Confirmar recibos SQL y de commit antes de cualquier apply;
no repetir creación, restauración o carga ya acreditada. Los datos/recibos de la
base personal no se deducen de este commit: constan en el informe externo final.

## Límites

Sin entrenamiento, promoción de modelos, apuestas, cron o histórico masivo.
Las identidades no acreditadas, horas desconocidas, TBD, conflictos y campos
sin fuente admisible permanecen visibles. No se admite fuzzy como decisión de
identidad ni se inventa país/competición principal de los clubes nuevos.
