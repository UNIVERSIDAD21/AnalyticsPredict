param([Parameter(Mandatory=$true)][string]$RaizPaquete,[switch]$SoloPreflight,[switch]$SoloExportar,[switch]$SoloRestaurar,[switch]$Reanudar,[int]$EsperaApi=90)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=(Resolve-Path -LiteralPath $RaizPaquete).Path
$Config=Get-Content -LiteralPath (Join-Path $Root 'RUNTIME_LOCAL.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Py=$Config.python
if (-not [System.IO.Path]::IsPathRooted($Py)) { $Py=Join-Path $Root $Py }
$PgBin=$Config.pg_bin; $Run=$Config.postgres_runtime; $Data=Join-Path $Run 'datos'
$Bootstrap=Join-Path $Root 'producto\scripts\ejecutar_herramienta_local.py'
$Operador=Join-Path $Root 'producto\scripts\operar_instalacion_local.py'
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
if ($EsperaApi -lt 1 -or $EsperaApi -gt 180) { throw 'EsperaApi debe estar entre 1 y 180 segundos.' }
& $Py -X utf8 -B (Join-Path $Root 'producto\scripts\preparar_instalacion_local.py') --verificar $Root
if ($LASTEXITCODE -ne 0) { throw 'La copia no supera su integridad; no se continua.' }
foreach ($required in @($Py,$Bootstrap,$Operador,(Join-Path $PgBin 'pg_dump.exe'),(Join-Path $PgBin 'pg_restore.exe'),(Join-Path $Data 'PG_VERSION'),(Join-Path $Run 'pgpass.conf'),$Config.source_env)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw 'Falta una dependencia; no se cambia el destino.' }
}
if ((Get-Content -LiteralPath (Join-Path $Data 'PG_VERSION') -Raw).Trim() -ne '18') { throw 'Cluster PostgreSQL no reconocido.' }
if ($SoloPreflight) { Write-Output 'PREFLIGHT_OK: no se ha conectado, exportado ni restaurado.'; return }
$Manifest=Get-Content -LiteralPath (Join-Path $Root 'MANIFIESTO.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Manifest.database.kind -eq 'pending_current_export') {
    & $Py -X utf8 -B $Bootstrap --paquete $Root exportar_vigente.py --pg-bin $PgBin --env-origen $Config.source_env
    if ($LASTEXITCODE -ne 0) { throw 'No se obtuvo exportacion vigente; destino sin activar.' }
} elseif ($Manifest.database.kind -ne 'current_consistent_export') { throw 'Estado de exportacion no admitido.' }
elseif (-not $Reanudar) { throw 'Existe exportacion previa: conciliar corte/recibo y usar Reanudar explicitamente.' }
if ($SoloExportar) { Write-Output 'EXPORTACION_VERIFICADA: falta corte final/restauracion/operacion.'; return }
foreach ($port in @(8000,5173,55433)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) { throw "Puerto $port ocupado; no se detienen procesos existentes." }
}
if ((Test-Path -LiteralPath (Join-Path $Root 'producto\backend\.env')) -and -not $Reanudar) { throw 'Existe configuracion; no se sobrescribe. Conciliar y reanudar explicitamente.' }
$Journal=Join-Path $Root ('runtime\MIGRACION_'+([guid]::NewGuid().ToString('N'))+'.json')
$Own=[ordered]@{paquete=$Root;data_directory=$Data;pgctl_pid=$null;pg_server_pid=$null;app_registry=$null;estado='PREPARANDO';migration_closed=$false}
function Save-Own {
    $temp=$Journal+'.tmp'
    $Own | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $temp -Encoding UTF8
    Move-Item -LiteralPath $temp -Destination $Journal -Force
}
Save-Own
$PgAttempted=$false; $Completed=$false
try {
    $env:PGPASSFILE=Join-Path $Run 'pgpass.conf'
    foreach ($name in @('PGPASSWORD','PGHOSTADDR','PGSERVICE','PGSERVICEFILE','PGOPTIONS')) { Remove-Item -LiteralPath "Env:\$name" -ErrorAction SilentlyContinue }
    $PgAttempted=$true
    $pg=Start-Process -FilePath (Join-Path $PgBin 'pg_ctl.exe') -WindowStyle Hidden -PassThru -ArgumentList @('-D',('"'+$Data+'"'),'-l',('"'+(Join-Path $Run 'postgresql.log')+'"'),'-w','-t','30','start') -RedirectStandardOutput ($Journal+'.pg.stdout.log') -RedirectStandardError ($Journal+'.pg.stderr.log')
    $Own.pgctl_pid=$pg.Id; $Own.estado='INICIANDO_PG'; Save-Own
    if (-not $pg.WaitForExit(40000)) { throw 'No se confirmo arranque del cluster propio; conservar el registro.' }
    $pg.Refresh(); if ($pg.ExitCode -ne 0) { throw 'Fallo pg_ctl propio.' }
    $Own.pg_server_pid=[int](Get-Content -LiteralPath (Join-Path $Data 'postmaster.pid') -First 1); Save-Own
    if (-not (Test-Path -LiteralPath (Join-Path $Root 'producto\backend\.env'))) {
        $Base='ap_actual_'+(Get-Date -Format 'yyyyMMdd_HHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
        & $Py -X utf8 -B $Bootstrap --paquete $Root restaurar_local.py --pg-bin $PgBin --puerto 55433 --administrador ap_migracion_admin --base $Base
        if ($LASTEXITCODE -ne 0) { throw 'Restauracion no conciliada; no se activa.' }
    }
    $Own.estado='RESTAURADO'; Save-Own
    if ($SoloRestaurar) { $Completed=$true; return }
    & $Py -X utf8 -B $Operador --paquete $Root --espera-api $EsperaApi
    if ($LASTEXITCODE -ne 0) { throw 'No se confirmaron API/web; el operador cierra sus hijos propios ante fallo.' }
    $Own.app_registry=Join-Path $Root 'runtime\PROCESOS_ACTUALES.json'; $Own.estado='API_WEB_DISPONIBLES'; Save-Own
    & $Py -X utf8 -B $Bootstrap --paquete $Root verificar_windows.py
    if ($LASTEXITCODE -ne 0) { throw 'Las lecturas locales no quedaron verificadas.' }
    $Own.estado='API_VERIFICADA_UI_Y_RECUPERACION_PENDIENTES'; Save-Own
    $Completed=$true
    Write-Output 'API local comprobada. Faltan corte final, UI autentica, reinicio y restauracion del backup antes de cerrar.'
} finally {
    if (-not $Completed) {
        if ($null -ne $Own.app_registry) { & $Py -X utf8 -B $Operador --paquete $Root --detener }
        $Own.estado='FALLO_CONSERVADO_SIN_ACTIVAR'; Save-Own
    }
    if ($PgAttempted -and ((-not $Completed) -or $SoloRestaurar)) {
        $stop=Start-Process -FilePath (Join-Path $PgBin 'pg_ctl.exe') -WindowStyle Hidden -PassThru -ArgumentList @('-D',('"'+$Data+'"'),'-w','-t','30','-m','fast','stop') -RedirectStandardOutput ($Journal+'.stop.stdout.log') -RedirectStandardError ($Journal+'.stop.stderr.log')
        $Own.pgctl_pid=$stop.Id; Save-Own
        if (-not $stop.WaitForExit(40000)) { Write-Output 'Parada propia no confirmada: revisar registro antes de reanudar.' }
    }
}
