param([switch]$SoloPreflight)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = $PSScriptRoot
$Config = Get-Content -LiteralPath (Join-Path $Root 'RUNTIME_LOCAL.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Py = $Config.python
if (-not [System.IO.Path]::IsPathRooted($Py)) { $Py = Join-Path $Root $Py }
$PgBin = $Config.pg_bin
$Run = $Config.postgres_runtime
$Data = Join-Path $Run 'datos'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
& $Py (Join-Path $Root 'producto\scripts\preparar_instalacion_local.py') --verificar $Root
if ($LASTEXITCODE -ne 0) { throw 'La copia actualizada no supera su verificacion de integridad.' }
foreach ($required in @($Py,(Join-Path $PgBin 'pg_dump.exe'),(Join-Path $PgBin 'pg_restore.exe'),(Join-Path $Data 'PG_VERSION'),(Join-Path $Run 'pgpass.conf'),$Config.source_env)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw 'Falta una dependencia local del continuador. No se cambia el destino.' }
}
if ((Get-Content -LiteralPath (Join-Path $Data 'PG_VERSION') -Raw).Trim() -ne '18') { throw 'Se requiere el cluster PostgreSQL 18 preparado.' }
if ($SoloPreflight) { Write-Output 'PREPARADO_CODIGO_ACTUAL_BD_PENDIENTE: integridad y rutas comprobadas, sin conectar ni restaurar BD.'; return }
if (Test-Path -LiteralPath (Join-Path $Root 'producto\backend\.env')) { throw 'La copia ya tiene configuracion de aplicacion. No se sobrescribe ni se restaura otra BD automaticamente.' }
foreach ($port in @(8000,5173,55433)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) { throw "Puerto $port ocupado; no se detiene otro proceso." }
}
$Manifest = Get-Content -LiteralPath (Join-Path $Root 'MANIFIESTO.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Manifest.database.kind -eq 'pending_current_export') {
    & $Py (Join-Path $Root 'herramientas\exportar_vigente.py') --pg-bin $PgBin --env-origen $Config.source_env
    if ($LASTEXITCODE -ne 0) { throw 'No se obtuvo exportacion vigente. No se inicia PostgreSQL ni se restaura la aplicacion.' }
} elseif ($Manifest.database.kind -ne 'current_consistent_export') { throw 'Estado de exportacion no admitido.' }
$env:PGPASSFILE = Join-Path $Run 'pgpass.conf'
foreach ($name in @('PGPASSWORD','PGHOSTADDR','PGSERVICE','PGSERVICEFILE','PGOPTIONS')) { Remove-Item -LiteralPath "Env:\$name" -ErrorAction SilentlyContinue }
$pgProcess = Start-Process -FilePath (Join-Path $PgBin 'pg_ctl.exe') -WindowStyle Hidden -PassThru -ArgumentList @('-D',('"'+$Data+'"'),'-l',('"'+(Join-Path $Run 'postgresql.log')+'"'),'-w','-t','30','start') -RedirectStandardOutput (Join-Path $Run 'pgctl_actualizado.stdout.log') -RedirectStandardError (Join-Path $Run 'pgctl_actualizado.stderr.log')
if (-not $pgProcess.WaitForExit(40000)) { throw 'No se confirmo inicio del cluster propio.' }
$pgProcess.Refresh()
if ($pgProcess.ExitCode -ne 0) { throw 'Fallo inicio del cluster propio; revisar sus registros privados.' }
$Base = 'ap_actual_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + ([guid]::NewGuid().ToString('N').Substring(0,6))
& $Py (Join-Path $Root 'herramientas\restaurar_local.py') --pg-bin $PgBin --puerto 55433 --administrador ap_migracion_admin --base $Base
if ($LASTEXITCODE -ne 0) { throw 'Restauracion no verificada. Se conserva el destino para diagnostico, sin activar la aplicacion.' }
$AppRun = Join-Path $Root ('runtime\'+$Base)
$backend = Start-Process -FilePath $Py -WindowStyle Hidden -PassThru -ArgumentList @(('"'+(Join-Path $Root 'herramientas\arrancar_backend.py')+'"'),'--puerto','8000') -RedirectStandardOutput (Join-Path $AppRun 'backend.stdout.log') -RedirectStandardError (Join-Path $AppRun 'backend.stderr.log')
$frontend = Start-Process -FilePath $Py -WindowStyle Hidden -PassThru -ArgumentList @(('"'+(Join-Path $Root 'producto\scripts\servir_frontend_local.py')+'"'),'--directorio',('"'+(Join-Path $Root 'producto\frontend\dist')+'"'),'--puerto','5173') -RedirectStandardOutput (Join-Path $AppRun 'frontend.stdout.log') -RedirectStandardError (Join-Path $AppRun 'frontend.stderr.log')
@{database=$Base;postgres_port=55433;backend_pid=$backend.Id;frontend_pid=$frontend.Id;api_port=8000;web_port=5173;migration_closed=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $AppRun 'PROCESOS_PROPIOS.json') -Encoding UTF8
$ready=$false
for($attempt=0;$attempt -lt 30;$attempt++) {
    try { $api=Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/salud' -TimeoutSec 1; $web=Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173/' -TimeoutSec 1; if($api.StatusCode -eq 200 -and $web.StatusCode -eq 200){$ready=$true;break} } catch { Start-Sleep -Seconds 1 }
}
if(-not $ready){throw 'La aplicacion propia no confirmo disponibilidad. Revisar sus PIDs y registros; no se matan procesos ajenos.'}
& $Py (Join-Path $Root 'herramientas\verificar_windows.py') --puerto-api 8000 --puerto-web 5173
if($LASTEXITCODE -ne 0){throw 'Las lecturas BD/API no quedaron verificadas. La migracion permanece abierta.'}
$Backup=Join-Path $AppRun ('BACKUP_LOCAL_'+$Base+'.dump')
$env:PGHOST='127.0.0.1';$env:PGPORT='55433';$env:PGUSER='ap_migracion_admin';$env:PGSSLMODE='disable'
& (Join-Path $PgBin 'pg_dump.exe') -Fc --no-owner --no-acl --file $Backup --dbname $Base
if($LASTEXITCODE -ne 0){throw 'Fallo el respaldo local posterior; no se declara cierre.'}
& (Join-Path $PgBin 'pg_restore.exe') --list $Backup | Out-Null
if($LASTEXITCODE -ne 0){throw 'El respaldo no es legible.'}
(Get-FileHash -LiteralPath $Backup -Algorithm SHA256).Hash | Set-Content -LiteralPath ($Backup+'.sha256') -Encoding ASCII
Write-Output 'Datos/API verificados. Quedan inspeccion visual, reinicio y ensayo de restauracion del respaldo antes de cerrar la migracion.'
