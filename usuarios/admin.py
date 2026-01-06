from django.contrib import admin
from .models import Rol, Usuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'nombre', 'activo', 'rol', 'created_at')
    list_filter = ('activo', 'rol')
    search_fields = ('username', 'nombre')
    readonly_fields = ('created_at',)
