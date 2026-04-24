from django.contrib import admin
from django.urls import path
from myApp import views
from myApp.views import enviar_correo

ROLES = [
    "acudientes",
    "docentes",
    "estudiantes",
    "enfermeria",
    "oficinas",
    "parqueadero",
    "personal",
    "visitantes",
    "vigilantes",
]

urlpatterns = [
    # =========================
    # ADMIN DJANGO
    # =========================
    path("admin/", admin.site.urls),
    # =========================
    # PÁGINAS PÚBLICAS
    # =========================
    path("", views.index, name="home"),
    path("index/", views.index, name="index"),
    path("registro-visita/", views.registro_visita_view, name="registro_visita"),
    # =========================
    # PANELES
    # =========================
    path("index2/", views.index2, name="index2"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # API DATOS DASHBOARD
    path("dashboard-data/", views.dashboard_data, name="dashboard_data"),
    # =========================
    # AUTENTICACIÓN
    # =========================
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Registro interno
    path("register/", views.register_view, name="register"),
    # =========================
    # CARGA MASIVA
    # =========================
    path("carga-masiva/", views.carga_masiva_view, name="carga_masiva"),
]

for rol in ROLES:
    urlpatterns += [
        # =========================
        # SECCIONES
        # =========================
        path(
            f"secciones/{rol}/",
            views.seccion_view,
            {"rol": rol},
            name=f"secciones.{rol}",
        ),
        # =========================
        # CRUD ADMIN
        # =========================
        path(
            f"crud/{rol}/",
            views.role_index,
            {"rol": rol},
            name=f"{rol}.index",
        ),
        path(
            f"crud/{rol}/create/",
            views.role_create,
            {"rol": rol},
            name=f"{rol}.create",
        ),
        path(
            f"crud/{rol}/<int:user_id>/edit/",
            views.role_edit,
            {"rol": rol},
            name=f"{rol}.edit",
        ),
        path(
            f"crud/{rol}/<int:user_id>/activar/",
            views.role_toggle_estado,
            {"rol": rol, "activar": True},
            name=f"{rol}.activar",
        ),
        path(
            f"crud/{rol}/<int:user_id>/inactivar/",
            views.role_toggle_estado,
            {"rol": rol, "activar": False},
            name=f"{rol}.inactivar",
        ),
        path(
            f"crud/{rol}/correo/",
            views.enviar_correo,
            {"tipo": rol},
            name=f"{rol}.enviar_correo",
        ),
        # =========================
        # REPORTE PDF NORMAL
        # =========================
        path(
            f"crud/{rol}/reporte/pdf/",
            views.role_report_pdf,
            {"rol": rol},
            name=f"{rol}.reporte_pdf",
        ),
        # =========================
        # REPORTE PDF ESTADÍSTICO
        # =========================
        path(
            f"crud/{rol}/estadistico/pdf/",
            views.role_stats_pdf,
            {"rol": rol},
            name=f"{rol}.estadistico_pdf",
        ),
    ]
