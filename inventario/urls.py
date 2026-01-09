from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.producto_list, name='producto_list'),
    path('productos/nuevo/', views.producto_create, name='producto_create'),
    path('productos/<int:pk>/editar/', views.producto_update, name='producto_update'),
    path('productos/<int:pk>/eliminar/', views.producto_delete, name='producto_delete'),
    path('productos/<int:pk>/desactivar/', views.producto_deactivate, name='producto_deactivate'),
    path('productos/<int:pk>/desvincular/', views.producto_unlink, name='producto_unlink'),
    path('ingresos/', views.ingreso_stock_list, name='ingreso_stock_list'),
    path('ingresos/nuevo/', views.ingreso_stock_create, name='ingreso_stock_create'),
    path('ingresos/<int:pk>/', views.ingreso_stock_detail, name='ingreso_stock_detail'),
    path('productos/bajo-stock/', views.productos_bajo_stock, name='productos_bajo_stock'),
    path('categorias/nueva/', views.categoria_create, name='categoria_create'),
    path('categorias/', views.categoria_list, name='categoria_list'),
    path('categorias/<int:pk>/editar/', views.categoria_update, name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.categoria_delete, name='categoria_delete'),
    path('productos/anadir-stock/', views.anadir_stock, name='anadir_stock'),
    path('productos/vendidos/', views.productos_vendidos, name='productos_vendidos'),
]