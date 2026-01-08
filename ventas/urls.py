from django.urls import path
from . import views

urlpatterns = [
    path('', views.venta_list, name='venta_list'),
    path('create/', views.venta_create, name='venta_create'),
    path('<int:pk>/', views.venta_detail, name='venta_detail'),
    path('<int:pk>/comprobante/', views.venta_comprobante, name='venta_comprobante'),
]
