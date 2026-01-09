from django.urls import path
from . import views

urlpatterns = [
    path('', views.venta_list, name='venta_list'),
    path('create/', views.venta_create, name='venta_create'),
    path('agregar-producto/', views.agregar_producto_ajax, name='agregar_producto_ajax'),
    path('<int:pk>/', views.venta_detail, name='venta_detail'),
    path('<int:pk>/comprobante/', views.venta_comprobante, name='venta_comprobante'),
    path('<int:pk>/exists/', views.venta_exists, name='venta_exists'),
]
