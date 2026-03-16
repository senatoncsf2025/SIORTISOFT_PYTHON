from django.contrib import admin
from django.urls import path
from myApp import views

urlpatterns = [
    # Admin Django
    path("admin/", admin.site.urls),

    # Públicas
    path("", views.index, name="home"),
    path("index/", views.index, name="index"),

    # Paneles
    path("index2/", views.index2, name="index2"),          # panel admin
    path("dashboard/", views.dashboard_view, name="dashboard"),  # panel vigilante

    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    # =========================
    # SECCIONES (vigilante y admin)
    # =========================
    path(
        "secciones/acudientes/",
        views.seccion_view,
        {"rol": "acudientes"},
        name="secciones.acudientes",
    ),
    path(
        "secciones/docentes/",
        views.seccion_view,
        {"rol": "docentes"},
        name="secciones.docentes",
    ),
    path(
        "secciones/estudiantes/",
        views.seccion_view,
        {"rol": "estudiantes"},
        name="secciones.estudiantes",
    ),
    path(
        "secciones/enfermeria/",
        views.seccion_view,
        {"rol": "enfermeria"},
        name="secciones.enfermeria",
    ),
    path(
        "secciones/oficinas/",
        views.seccion_view,
        {"rol": "oficinas"},
        name="secciones.oficinas",
    ),
    path(
        "secciones/parqueadero/",
        views.seccion_view,
        {"rol": "parqueadero"},
        name="secciones.parqueadero",
    ),
    path(
        "secciones/personal/",
        views.seccion_view,
        {"rol": "personal"},
        name="secciones.personal",
    ),
    path(
        "secciones/visitantes/",
        views.seccion_view,
        {"rol": "visitantes"},
        name="secciones.visitantes",
    ),
    path(
        "secciones/vigilantes/",
        views.seccion_view,
        {"rol": "vigilantes"},
        name="secciones.vigilantes",
    ),

    # =========================
    # CRUD ADMIN
    # =========================
    path(
        "crud/acudientes/",
        views.role_index,
        {"rol": "acudientes"},
        name="acudientes.index",
    ),
    path(
        "crud/acudientes/create/",
        views.role_create,
        {"rol": "acudientes"},
        name="acudientes.create",
    ),
    path(
        "crud/acudientes/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "acudientes"},
        name="acudientes.edit",
    ),
    path(
        "crud/acudientes/reporte/",
        views.role_reporte,
        {"rol": "acudientes"},
        name="acudientes.reporte",
    ),

    path(
        "crud/docentes/",
        views.role_index,
        {"rol": "docentes"},
        name="docentes.index",
    ),
    path(
        "crud/docentes/create/",
        views.role_create,
        {"rol": "docentes"},
        name="docentes.create",
    ),
    path(
        "crud/docentes/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "docentes"},
        name="docentes.edit",
    ),
    path(
        "crud/docentes/reporte/",
        views.role_reporte,
        {"rol": "docentes"},
        name="docentes.reporte",
    ),

    path(
        "crud/estudiantes/",
        views.role_index,
        {"rol": "estudiantes"},
        name="estudiantes.index",
    ),
    path(
        "crud/estudiantes/create/",
        views.role_create,
        {"rol": "estudiantes"},
        name="estudiantes.create",
    ),
    path(
        "crud/estudiantes/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "estudiantes"},
        name="estudiantes.edit",
    ),
    path(
        "crud/estudiantes/reporte/",
        views.role_reporte,
        {"rol": "estudiantes"},
        name="estudiantes.reporte",
    ),

    path(
        "crud/enfermeria/",
        views.role_index,
        {"rol": "enfermeria"},
        name="enfermeria.index",
    ),
    path(
        "crud/enfermeria/create/",
        views.role_create,
        {"rol": "enfermeria"},
        name="enfermeria.create",
    ),
    path(
        "crud/enfermeria/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "enfermeria"},
        name="enfermeria.edit",
    ),
    path(
        "crud/enfermeria/reporte/",
        views.role_reporte,
        {"rol": "enfermeria"},
        name="enfermeria.reporte",
    ),

    path(
        "crud/oficinas/",
        views.role_index,
        {"rol": "oficinas"},
        name="oficinas.index",
    ),
    path(
        "crud/oficinas/create/",
        views.role_create,
        {"rol": "oficinas"},
        name="oficinas.create",
    ),
    path(
        "crud/oficinas/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "oficinas"},
        name="oficinas.edit",
    ),
    path(
        "crud/oficinas/reporte/",
        views.role_reporte,
        {"rol": "oficinas"},
        name="oficinas.reporte",
    ),

    path(
        "crud/parqueadero/",
        views.role_index,
        {"rol": "parqueadero"},
        name="parqueadero.index",
    ),
    path(
        "crud/parqueadero/create/",
        views.role_create,
        {"rol": "parqueadero"},
        name="parqueadero.create",
    ),
    path(
        "crud/parqueadero/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "parqueadero"},
        name="parqueadero.edit",
    ),
    path(
        "crud/parqueadero/reporte/",
        views.role_reporte,
        {"rol": "parqueadero"},
        name="parqueadero.reporte",
    ),

    path(
        "crud/personal/",
        views.role_index,
        {"rol": "personal"},
        name="personal.index",
    ),
    path(
        "crud/personal/create/",
        views.role_create,
        {"rol": "personal"},
        name="personal.create",
    ),
    path(
        "crud/personal/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "personal"},
        name="personal.edit",
    ),
    path(
        "crud/personal/reporte/",
        views.role_reporte,
        {"rol": "personal"},
        name="personal.reporte",
    ),

    path(
        "crud/visitantes/",
        views.role_index,
        {"rol": "visitantes"},
        name="visitantes.index",
    ),
    path(
        "crud/visitantes/create/",
        views.role_create,
        {"rol": "visitantes"},
        name="visitantes.create",
    ),
    path(
        "crud/visitantes/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "visitantes"},
        name="visitantes.edit",
    ),
    path(
        "crud/visitantes/reporte/",
        views.role_reporte,
        {"rol": "visitantes"},
        name="visitantes.reporte",
    ),

    path(
        "crud/vigilantes/",
        views.role_index,
        {"rol": "vigilantes"},
        name="vigilantes.index",
    ),
    path(
        "crud/vigilantes/create/",
        views.role_create,
        {"rol": "vigilantes"},
        name="vigilantes.create",
    ),
    path(
        "crud/vigilantes/<int:user_id>/edit/",
        views.role_edit,
        {"rol": "vigilantes"},
        name="vigilantes.edit",
    ),
    path(
        "crud/vigilantes/reporte/",
        views.role_reporte,
        {"rol": "vigilantes"},
        name="vigilantes.reporte",
    ),
]