param([switch]$SoloPreflight,[switch]$SoloExportar,[switch]$SoloRestaurar,[switch]$Reanudar,[int]$EsperaApi=90)
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'producto\scripts\continuar_migracion_windows.ps1') -RaizPaquete $PSScriptRoot @PSBoundParameters
