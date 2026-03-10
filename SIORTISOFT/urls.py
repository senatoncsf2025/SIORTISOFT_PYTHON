from django.contrib import admin
from django.urls import path
from myApp import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.index2, name='home'),

    path('acudientes/', views.role_index, {'rol': 'acudientes'}, name='acudientes.index'),
    path('acudientes/create/', views.role_create, {'rol': 'acudientes'}, name='acudientes.create'),
    path('acudientes/reporte/', views.role_reporte, {'rol': 'acudientes'}, name='acudientes.reporte'),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),  
]   