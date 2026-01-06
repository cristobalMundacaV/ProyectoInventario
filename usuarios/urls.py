from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_redirect),
    path('login/', views.login_view, name='login'),
    path('inicio/', views.inicio, name='inicio'),
    path('logout/', views.logout_view, name='logout'),
]
