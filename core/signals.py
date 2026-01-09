from __future__ import annotations

from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_roles(sender, **kwargs):
    """Create role groups after migrations.

    Uses a signal instead of a migration so it works in tests and fresh DBs.
    """

    # Avoid running multiple times for each app import; keep it simple and idempotent.
    try:
        from django.contrib.auth.models import Group
    except Exception:
        return

    from .roles import ADMIN_GROUP_NAME, ENCARGADO_GROUP_NAME

    Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
    Group.objects.get_or_create(name=ENCARGADO_GROUP_NAME)

    # Optional: attach permissions (best-effort; views are still protected by role checks)
    try:
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        admin_group = Group.objects.get(name=ADMIN_GROUP_NAME)
        encargado_group = Group.objects.get(name=ENCARGADO_GROUP_NAME)

        # Admin gets all permissions for local apps
        local_apps = {'inventario', 'ventas', 'caja', 'auditoria'}
        perms = Permission.objects.filter(content_type__app_label__in=local_apps)
        admin_group.permissions.set(perms)

        # Encargado: day-to-day operations (no deletes on sensitive/history-affecting models)
        encargado_app_models = {
            ('inventario', 'producto'),
            ('inventario', 'categoria'),
            ('ventas', 'venta'),
            ('ventas', 'ventadetalle'),
            ('caja', 'caja'),
        }
        encargado_perm_codenames = set()
        for app_label, model in encargado_app_models:
            encargado_perm_codenames.update({
                f'view_{model}',
                f'add_{model}',
                f'change_{model}',
            })

        encargado_perms = Permission.objects.filter(
            content_type__app_label__in={a for a, _ in encargado_app_models},
            codename__in=encargado_perm_codenames,
        )
        encargado_group.permissions.set(encargado_perms)

    except Exception:
        # Non-fatal: permissions can be managed manually in admin
        return
