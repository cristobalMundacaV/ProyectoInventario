from django.urls import path
from . import views

urlpatterns = [
    path('', views.auditoria_list, name='auditoria_list'),
    path('ventas-mes/', views.ventas_por_fecha, name='auditoria_ventas_por_fecha'),
]
