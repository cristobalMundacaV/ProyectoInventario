import os
import sys
import traceback
import threading
import time
import webbrowser
from typing import TextIO
from pathlib import Path


_STD_STREAM: TextIO | None = None


def _log_path() -> Path:
    return _runtime_dir() / "inventario.log"


def _log(msg: str) -> None:
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        _log_path().open("a", encoding="utf-8").write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def _ensure_std_streams() -> None:
    """Ensure sys.stdout/sys.stderr are valid file-like objects.

    In windowed PyInstaller builds, these can be None, but Django management
    commands write to stdout/stderr.
    """

    global _STD_STREAM

    def _is_broken(stream: object) -> bool:
        return stream is None or not hasattr(stream, "write")

    if not _is_broken(sys.stdout) and not _is_broken(sys.stderr):
        return

    try:
        # Keep this handle open for the whole process lifetime.
        _STD_STREAM = _log_path().open("a", encoding="utf-8")
        if _is_broken(sys.stdout):
            sys.stdout = _STD_STREAM  # type: ignore[assignment]
        if _is_broken(sys.stderr):
            sys.stderr = _STD_STREAM  # type: ignore[assignment]
    except Exception:
        # Last resort: drop output (still avoids crashes).
        try:
            devnull = open(os.devnull, "w", encoding="utf-8")
            if _is_broken(sys.stdout):
                sys.stdout = devnull  # type: ignore[assignment]
            if _is_broken(sys.stderr):
                sys.stderr = devnull  # type: ignore[assignment]
        except Exception:
            pass


def _show_error(title: str, message: str) -> None:
    # Best-effort UI error for windowed EXE.
    try:
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        pass


def _runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _bundle_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", _runtime_dir()))


def _ensure_db_present() -> None:
    runtime_db = _runtime_dir() / "db.sqlite3"
    if runtime_db.exists():
        return

    bundled_db = _bundle_dir() / "db.sqlite3"
    if bundled_db.exists():
        try:
            runtime_db.write_bytes(bundled_db.read_bytes())
        except Exception:
            # If we can't copy, Django will create an empty DB on migrate.
            pass


def _open_browser_later(url: str) -> None:
    def _worker():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def main() -> int:
    try:
        _ensure_std_streams()

        # Make sure our project root is importable both when frozen and when running from source.
        # This helps Django resolve DJANGO_SETTINGS_MODULE='core.settings'.
        try:
            bundle_dir = _bundle_dir()
            runtime_dir = _runtime_dir()
            project_root = runtime_dir  # when frozen, code is in the archive but runtime dir is stable
            for p in (str(project_root), str(bundle_dir)):
                if p and p not in sys.path:
                    sys.path.insert(0, p)
        except Exception:
            pass

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
        # Hint for settings/urls when running as EXE
        os.environ.setdefault("INVENTARIO_EXE", "1")

        _ensure_db_present()

        # Eager import so PyInstaller/runtime don't miss the dynamically-imported settings module.
        import core.settings  # noqa: F401

        import django
        from django.core.management import call_command, execute_from_command_line

        django.setup()

        # Ensure schema exists
        try:
            # In frozen builds, migration modules for local apps can occasionally be missed by the bundler.
            # `run_syncdb=True` ensures tables for apps without detected migrations are created.
            call_command("migrate", interactive=False, run_syncdb=True)
        except Exception as e:
            _log(f"migrate failed: {e}")

        # Desktop/EXE behavior: force login on every app launch.
        # Even if the browser keeps the session cookie, deleting server-side sessions
        # makes Django treat the user as anonymous on next launch.
        if os.environ.get("INVENTARIO_EXE") == "1":
            try:
                from django.contrib.sessions.models import Session

                Session.objects.all().delete()
            except Exception as e:
                _log(f"Session cleanup failed: {e}")

        host = os.environ.get("INVENTARIO_HOST", "127.0.0.1")
        port = os.environ.get("INVENTARIO_PORT", "8000")
        url = f"http://{host}:{port}/"

        _open_browser_later(url)
        _log(f"Starting server at {url}")

        # Run server without autoreload (important for PyInstaller onefile)
        execute_from_command_line(["manage.py", "runserver", f"{host}:{port}", "--noreload"])
        return 0
    except Exception as e:
        tb = traceback.format_exc()
        _log(f"FATAL: {e}\n{tb}")
        _show_error(
            "Inventario - Error",
            f"No se pudo iniciar la aplicación.\n\nDetalle: {e}\n\nRevisá el log: {_log_path()}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
