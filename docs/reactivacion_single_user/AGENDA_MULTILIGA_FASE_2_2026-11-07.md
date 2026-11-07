# Agenda multiliga — fase 2, candidato aislado

Autor: Borlty-Predict. Revisión independiente: Codex, pendiente.

## Estado y dependencia

Extensión de agenda sobre el candidato de fase 1 cuyo ZIP tiene SHA-256
`6d50d266314647062290124198a9b391259bd13c676ca5e52cfe3634bc7b4621`.
La observación **F1-R01** de durabilidad de estadísticas nuevas sigue pendiente
del autor de fase 1. Continuar esta fase fue autorizado expresamente por Erik;
no supone aprobar ese candidato ni retirar la observación.

No hay instalación, reinicios, cambios en los modelos 2123/2191 ni escrituras
en la BD habitual. El cierre operativo del botón, escritorio y cobertura UI
corresponde a fase 3 y a la activación posterior del plan maestro.

## Entregables de software

- `backend/servicios/agenda_multiliga.py`: pedidos por competición, rotación,
  verificación de bytes/URL/liga/truncamiento, inventario y cobertura observada.
  Usa el mismo cliente recibido por el coordinador y los normalizadores
  existentes de agenda, periodos fútbol y baloncesto.
- `backend/servicios/etapa_agenda_multiliga.py`: reserva durable de consultas,
  lectura, plan, confirmación con preimágenes y obligaciones de identidad/fecha.
  No crea procesos, servidores, locks de trabajador, backups ni clientes propios.
- Migración y reversión `2026-11-07_agenda_multiliga.sql`: admite lotes AGENDA y
  añade `ap_m2_agenda_consultas`. La reversión se detiene si hay evidencia.
- `backend/tests/test_agenda_multiliga.py`: controles sin proveedores reales.

La extensión no modifica los archivos del candidato de fase 1. La publicación
Git contiene seis archivos nuevos y materializa dos dependencias de la base
ya instalada: `fuentes_agenda.py` y `sincronizacion_agendas.py`, con sus bytes
sellados, que aún diferían del HEAD publicado. No se atribuyen esos cambios
previos a esta fase ni se publica el resto del trabajo de Codex. El ZIP externo contiene los 581
archivos sellados de fase 1 para reproducir las pruebas contra una base exacta;
no confundirlo con el contenido publicado de esta rama.

## Contrato de integración para fase 3

1. El operador prepara explícitamente fase 1 y después llama
   `migrar_agenda(conn_operador, rol_aplicacion=rol_personal)`. No ejecutar DDL
   desde un GET ni desde una navegación. El helper se detiene si el esquema ya
   existe; conciliar su recibo antes de repetir. `conceder_acceso_agenda` permite
   conceder SELECT/INSERT/UPDATE sobre la nueva tabla, sin DELETE ni cambios
   globales de permisos.
2. El coordinador conserva el preflight, respaldo y lock de trabajador; reserva
   y reclama una única ejecución SQL de fase 1, manteniendo la conexión abierta.
3. Pasar esa conexión, ejecución, catálogo y **el mismo cliente** a
   `ejecutar_etapa_agenda(conn, ejecucion, ligas, client, hoy_cot, ahora_utc)`.
   No envolver el HTTP en una transacción deportiva ni lanzar el CLI antiguo
   con otro proceso/lock. El parámetro `cupo` limita consultas seleccionadas,
   no borra las no seleccionadas. El cliente sigue aplicando el presupuesto
   global, pausas por origen y caché; esta etapa no lo amplía ni lo reinicia.
4. Guardar/publicar el recibo retornado después del commit. Si la publicación
   falla, recuperarlo de `ap_m1_lotes` con etapa AGENDA. El resumen SQL de fase 1
   aún no incluye automáticamente esta nueva sección: fase 3 debe integrarla.
5. Continuar resultados y estadísticas únicamente con la fase 1 corregida.
   Los finales observados por agenda dejan una obligación
   `IDENTIDAD_RESULTADO` localizable; **agenda no escribe FT ni cierra ese trabajo**.

## Avance, recuperación e identidad

Las consultas se registran antes del HTTP, incluidas las que exceden el cupo.
Se alternan consultas recientes con consultas antiguas fallidas/no atendidas
o asociadas a eventos todavía pendientes. La selección no depende únicamente
de que la fecha del evento siga dentro de la ventana reciente.

El registro de lectura futura está separado de `ap_m1_tramos`: **no adelanta
el cursor de resultados**. Una ventana leída no implica que cada evento se
haya conciliado ni que la fuente tenga todo el calendario oficial.

El plan y la confirmación reutilizan IDs existentes, crosswalks revisados,
protección de finales y preimágenes. Una fecha sin hora no se convierte en un
alta canónica a medianoche. Si la cola necesita un instante para localizarla,
su evidencia indica que esa fecha es solo un ancla, no un kickoff acreditado.
Los duplicados contradictorios quedan pendientes, sin elegir arbitrariamente
la última copia. Se preservan cancelación, aplazamiento, suspensión, condición
WNBA, cuartos/OT y desglose FT/ET/tanda.

## Horizonte y clasificación

Objetivo: desde ayer COT hasta hoy +60 días, filtrado por fecha COT; se consulta
un día UTC adicional para cubrir partidos nocturnos. Fútbol se recolecta por mes,
NBA/WNBA por día y Euroliga por temporada oficial. La rotación evita concentrar
todo el turno inicial en una liga. El informe conserva por separado consultas
solicitadas, observadas, eventos enumerados, normalizados, horas confirmadas,
último evento publicado y cobertura oficial **DESCONOCIDA**.

La clasificación de las 23 competiciones se conserva con los motivos del
inventario de fase 0; una ventana vacía no reclasifica un torneo ni prueba
que haya terminado. Los códigos sin adaptador quedan explícitos y no aparentan
una fuente caída. El detalle y los horizontes medidos están en la entrega externa.

## Pruebas y revisión

Pruebas locales de autor: 75 dirigidas aprobadas; dos antiguas de integración
se excluyeron de ese comando y no se cuentan como aprobadas. Los controles SQL
específicos se ejecutaron por separado en el clon registrado. Se comprobaron
preimagen, rollback, permisos mínimos, mismo ID al reprogramar fútbol/NBA,
consulta futura sin avance FT, cortes reales antes/después del commit y +45 días.
El replay de 127 capturas mantiene 120 rechazos, 642 campos que pasan los
controles y el cero auténtico. Estas pruebas no certifican el histórico entero.

La restauración acreditada del clon pertenece a la entrega de fase 1; no se
repitió una restauración completa por esta fase. Solo quedó en el clon el
esquema aditivo y evidencia SQL de ensayo. Los casos deportivos se revirtieron.

Entrega de autor y evidencias:
`C:/Users/ING-ERIK/AnalyticsPredict/Carpeta de Entregas de Borlty/FASE_2_AGENDA_MULTILIGA_2026-11-07`.
Codex debe verificar el ZIP/SHA, repetir los controles críticos contra ese mismo
artefacto y emitir APTO o REQUIERE CORRECCIÓN. Revisar F1-R01 aparte sobre un
candidato nuevo de su autor. No instalar el conjunto por el solo hecho de que
esta fase tenga pruebas de autor aprobadas.
