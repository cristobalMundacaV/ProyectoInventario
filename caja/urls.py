from django.urls import path
from . import views

urlpatterns = [
    path('', views.caja_list, name='caja_list'),
    path('abrir/', views.abrir_caja, name='abrir_caja'),
    path('confirmar-cerrar/', views.confirmar_cerrar_caja, name='confirmar_cerrar_caja'),
    path('cerrar/', views.cerrar_caja, name='cerrar_caja'),
    path('detalle/<int:pk>/', views.caja_detail, name='caja_detail'),
]
