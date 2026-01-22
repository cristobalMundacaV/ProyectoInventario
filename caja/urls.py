from django.urls import path
from . import views

urlpatterns = [
    path('', views.caja_list, name='caja_list'),
    path('ganancia-diaria/', views.ganancia_diaria_hoy, name='ganancia_diaria_hoy'),
    path('reporte/ganancia-diaria/', views.reporte_ganancia_diaria, name='reporte_ganancia_diaria'),
    path('abrir/', views.abrir_caja, name='abrir_caja'),
    path('confirmar-cerrar/', views.confirmar_cerrar_caja, name='confirmar_cerrar_caja'),
    path('cerrar/', views.cerrar_caja, name='cerrar_caja'),
    path('boleta/<int:pk>/', views.caja_boleta, name='caja_boleta'),
    path('boletas/', views.caja_boletas, name='caja_boletas'),
    path('detalle/<int:pk>/', views.caja_detail, name='caja_detail'),
]
