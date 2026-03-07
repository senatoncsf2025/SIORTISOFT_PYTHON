from django.contrib import admin
from django.urls import path
from myApp import views

ROLES = [
    'personal',
    'estudiantes',
    'docentes',
    'oficinas',
    'vigilantes',
    'enfermeria',
    'parqueadero',
    'visitantes',
    'acudientes',
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index2, name='home'),
]

for rol in ROLES:
    urlpatterns += [
        path(f'{rol}/', views.role_index, {'rol': rol}, name=f'{rol}.index'),
        path(f'{rol}/create/', views.role_create, {'rol': rol}, name=f'{rol}.create'),
        path(f'{rol}/reporte/', views.role_reporte, {'rol': rol}, name=f'{rol}.reporte'),
    ]