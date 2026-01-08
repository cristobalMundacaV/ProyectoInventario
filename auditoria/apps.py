from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    name = 'auditoria'

    def ready(self):
        try:
            import auditoria.signals  # noqa: F401
        except Exception:
            pass
