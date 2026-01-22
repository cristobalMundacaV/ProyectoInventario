param(
  [string]$ExePath = "$(Split-Path -Parent $PSScriptRoot)\dist\Inventario.exe"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Onefile EXE extrae al %TEMP%. Si C: está sin espacio, puede fallar con errores de extracción.
$tmpRoot = "$root\.tmp_run"
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$env:TEMP = $tmpRoot
$env:TMP = $tmpRoot

if (!(Test-Path $ExePath)) {
  throw "No se encontró el EXE en: $ExePath"
}

Write-Host "Usando TEMP=$env:TEMP"
Write-Host "Ejecutando: $ExePath"
& $ExePath
