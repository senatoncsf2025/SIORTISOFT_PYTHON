from django.contrib import admin
from django.urls import path
from myApp import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.index, name='home'),
    path('index2/', views.index2, name='index2'),

    # ===== CRUD DINÁMICO POR ROL =====

    path('acudientes/', views.role_index, {'rol': 'acudientes'}, name='acudientes.index'),

    path('acudientes/create/', views.crear_rol, {'rol': 'acudientes'}, name='acudientes.create'),

    path('acudientes/reporte/', views.lista_roles, {'rol': 'acudientes'}, name='acudientes.reporte'),

    # ===== AUTENTICACIÓN =====

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # ===== ROLES =====

    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('roles/eliminar/<int:id>/', views.eliminar_rol, name='eliminar_rol'),
]
