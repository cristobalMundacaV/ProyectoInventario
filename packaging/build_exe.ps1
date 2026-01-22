param(
  [string]$Python = "py",
  [bool]$OneFile = $true,
  [switch]$RecreateVenv,
  [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# PyInstaller onefile y ensurepip usan %TEMP%/%TMP% intensivamente.
# Si el disco del usuario está justo (p.ej. C:), pueden aparecer errores como WinError 112
# o fallas de extracción/descompresión. Forzamos un TEMP dentro del proyecto.
$tmpRoot = "$root\.tmp"
New-Item -ItemType Directory -Force $tmpRoot | Out-Null
$env:TEMP = $tmpRoot
$env:TMP = $tmpRoot

if ($Clean) {
  Write-Host "[0/4] Limpiando build/ dist/ staticfiles/"
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$root\build", "$root\dist", "$root\staticfiles"
}

function Test-VenvHealthy {
  param([string]$Root)
  $py = "$Root\.venv\Scripts\python.exe"
  if (!(Test-Path $py)) { return $false }
  try {
    & $py -c "import sys; print(sys.executable)" | Out-Null
    return $true
  } catch {
    return $false
  }
}

Write-Host "[1/4] Creando venv .venv (si no existe)"
if ($RecreateVenv -or !(Test-VenvHealthy -Root $root)) {
  if (Test-Path "$root\.venv") {
    Write-Host "- Eliminando venv existente (posible ruta movida / launcher roto)"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$root\.venv"
  }
  & $Python -m venv .venv
}

Write-Host "[2/4] Instalando dependencias"
& "$root\.venv\Scripts\python.exe" -m pip install -U pip
& "$root\.venv\Scripts\python.exe" -m pip install -r "$root\requirements.txt"
& "$root\.venv\Scripts\python.exe" -m pip install pyinstaller

Write-Host "[3/4] Generando staticfiles (collectstatic)"
$env:DJANGO_SETTINGS_MODULE = "core.settings"
& "$root\.venv\Scripts\python.exe" "$root\manage.py" collectstatic --noinput

Write-Host "[4/4] Construyendo EXE con PyInstaller"
$spec = "$root\packaging\inventario_app.spec"
if (-not $OneFile) {
  Write-Host "Nota: con un archivo .spec PyInstaller no acepta --onedir/--onefile; el modo lo define el .spec. Se compilará según inventario_app.spec."
}

# En Windows, si el EXE anterior está abierto o siendo escaneado por antivirus, PyInstaller puede
# fallar con WinError 5 al intentar reemplazarlo. Intentamos liberarlo y borrarlo antes de compilar.
try {
  Get-Process -Name "Inventario" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
} catch {
  # ignore
}

$exeCandidates = @(
  "$root\dist\Inventario\Inventario.exe",
  "$root\dist\Inventario.exe"
)

foreach ($exePath in $exeCandidates) {
  if (Test-Path $exePath) {
    for ($i = 1; $i -le 6; $i++) {
      try {
        Remove-Item -Force -ErrorAction Stop $exePath
        break
      } catch {
        Start-Sleep -Milliseconds 600
        if ($i -eq 6) {
          throw "No se pudo borrar $exePath (posible archivo en uso). Cerrá la app Inventario y reintentá."
        }
      }
    }
  }
}

# Si existe el directorio onedir, intentamos limpiarlo (ayuda si quedaron templates viejos).
$onedir = "$root\dist\Inventario"
if (Test-Path $onedir) {
  try {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $onedir
  } catch {
    # ignore
  }
}

& "$root\.venv\Scripts\pyinstaller.exe" --noconfirm --clean $spec


if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller falló con código $LASTEXITCODE"
}

Write-Host "Listo. Revisá dist\Inventario\Inventario.exe"
