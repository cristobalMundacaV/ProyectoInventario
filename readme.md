git clone https://github.com/cristobalMundacaV/ProyectoInventario.git
cd ProyectoInventario
python -m venv venv
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

## Generar EXE (Windows)

Esto empaqueta el sistema completo (Django + templates + staticfiles/admin + db inicial) en un ejecutable local para Windows.

### Requisitos

- Windows 10/11
- Python instalado (recomendado: 3.11+). También funciona usando el launcher `py`.
- PowerShell

### Paso a paso (build)

1) Abrí **PowerShell** en la carpeta raíz del proyecto (donde está `manage.py`).

2) Ejecutá el script de build:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_exe.ps1
```

Qué hace el script automáticamente:
- Crea/usa un virtualenv `.venv` en la raíz.
- Instala `requirements.txt` y `pyinstaller`.
- Ejecuta `collectstatic`.
- Construye el ejecutable con `packaging/inventario_app.spec`.

3) Resultado: el ejecutable queda en:

- `dist\Inventario.exe`

### Cómo ejecutar el EXE

1) Doble click en `dist\Inventario.exe`.
2) Abre el navegador en `http://127.0.0.1:8000/`.

Archivos que genera al correr:
- `dist\inventario.log`: log de arranque/errores (muy útil si algo falla).
- `dist\db.sqlite3`: base de datos local (si no existía, se copia desde el bundle y se ejecuta `migrate`).

### Configuración (opcional)

Podés cambiar host/puerto con variables de entorno antes de abrir el EXE:

```powershell
$env:INVENTARIO_HOST = "127.0.0.1"
$env:INVENTARIO_PORT = "8000"
Start-Process .\dist\Inventario.exe
```

### Para llevarlo a otra PC

Copiá como mínimo:
- `dist\Inventario.exe`

Recomendado (para mantener datos y logs):
- `dist\db.sqlite3`
- `dist\inventario.log` (opcional)

### Problemas comunes

**1) “Acceso denegado” al compilar (`PermissionError` sobre `dist\Inventario.exe`)**
- Cerrá `Inventario.exe` si está abierto y volvé a ejecutar el build.

**2) No abre o no carga en el navegador**
- Revisá `dist\inventario.log`.
- Verificá que el puerto 8000 no esté ocupado (podés cambiar `INVENTARIO_PORT`).

**3) Firewall de Windows**
- Si Windows pregunta, permití el acceso en red privada (usa localhost).

**4) Login**
- La URL raíz suele redirigir a `/login/` si no estás autenticado.
- Si necesitás crear un usuario administrador, hacelo en modo desarrollo (desde el proyecto):

```powershell
py manage.py createsuperuser
```