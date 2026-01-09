from __future__ import annotations

from functools import wraps

from django.core.exceptions import PermissionDenied

from .roles import Role, is_admin, is_encargado


def role_required(*allowed_roles: str):
    """Restrict a view to users with one of the allowed roles.

    Admin always has access.
    """

    allowed = set(allowed_roles)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if is_admin(user):
                return view_func(request, *args, **kwargs)

            if Role.ENCARGADO in allowed and is_encargado(user):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return _wrapped

    return decorator


def admin_required(view_func):
    return role_required(Role.ADMIN)(view_func)
