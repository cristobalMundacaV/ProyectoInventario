from django.urls import path
from . import views

urlpatterns = [
    path('', views.venta_list, name='venta_list'),
    path('reporte/por-dia/', views.ventas_reporte_por_dia, name='ventas_reporte_por_dia'),
    path('reporte/por-metodo/', views.ventas_reporte_por_metodo, name='ventas_reporte_por_metodo'),
    path('create/', views.venta_create, name='venta_create'),
    path('fiados/', views.fiado_list, name='fiado_list'),
    path('fiados/nuevo/', views.fiado_create, name='fiado_create'),
    path('fiados/<int:pk>/', views.fiado_detail, name='fiado_detail'),
    path('fiados/<int:pk>/abonar/', views.fiado_abonar, name='fiado_abonar'),
    path('agregar-producto/', views.agregar_producto_ajax, name='agregar_producto_ajax'),
    path('<int:pk>/', views.venta_detail, name='venta_detail'),
    path('<int:pk>/comprobante/', views.venta_comprobante, name='venta_comprobante'),
    path('<int:pk>/exists/', views.venta_exists, name='venta_exists'),
]
