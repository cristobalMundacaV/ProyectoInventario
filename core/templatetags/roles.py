from __future__ import annotations

from django import template

from core.roles import is_admin, is_encargado

register = template.Library()


@register.filter
def user_is_admin(user) -> bool:
    return is_admin(user)


@register.filter
def user_is_encargado(user) -> bool:
    return is_encargado(user)
