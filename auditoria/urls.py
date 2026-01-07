from django.urls import path
from . import views

urlpatterns = [
    path('', views.auditoria_list, name='auditoria_list'),
]
