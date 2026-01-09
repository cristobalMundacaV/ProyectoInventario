from __future__ import annotations

from dataclasses import dataclass


ADMIN_GROUP_NAME = 'Administrador'
ENCARGADO_GROUP_NAME = 'Encargado'


@dataclass(frozen=True)
class Role:
    ADMIN: str = 'ADMIN'
    ENCARGADO: str = 'ENCARGADO'


def is_admin(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    try:
        return user.groups.filter(name=ADMIN_GROUP_NAME).exists()
    except Exception:
        return False


def is_encargado(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if is_admin(user):
        return True
    try:
        return user.groups.filter(name=ENCARGADO_GROUP_NAME).exists()
    except Exception:
        return False
