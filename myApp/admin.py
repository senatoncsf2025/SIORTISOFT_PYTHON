from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Vehiculo, Computador, Movimiento


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario

    list_display = (
        "email",
        "nombre",
        "apellido",
        "cedula",
        "rol",
        "subrol",
        "tipo_usuario",
        "activo",
        "is_staff",
    )
    list_filter = (
        "rol",
        "subrol",
        "tipo_usuario",
        "activo",
        "is_staff",
        "is_superuser",
    )
    search_fields = ("email", "nombre", "apellido", "cedula")
    ordering = ("email",)

    fieldsets = (
        ("Acceso", {"fields": ("email", "password")}),
        (
            "Información personal",
            {
                "fields": (
                    "nombre",
                    "apellido",
                    "cedula",
                    "genero",
                    "fecha_nacimiento",
                    "telefono",
                    "direccion",
                )
            },
        ),
        ("Clasificación", {"fields": ("tipo_usuario", "rol", "subrol")}),
        (
            "Información laboral / visita",
            {
                "fields": (
                    "cargo",
                    "codigo_vigilante",
                    "fecha_visita",
                    "horario",
                    "registrado_por",
                )
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "activo",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Verificación",
            {
                "fields": (
                    "email_verified_at",
                    "telefono_verificado",
                    "codigo_verificacion",
                    "remember_token",
                )
            },
        ),
        ("Fechas", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    readonly_fields = ("last_login", "created_at", "updated_at")

    add_fieldsets = (
        (
            "Crear usuario",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nombre",
                    "apellido",
                    "cedula",
                    "telefono",
                    "direccion",
                    "tipo_usuario",
                    "rol",
                    "subrol",
                    "password1",
                    "password2",
                    "activo",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "placa", "marca", "modelo", "color", "created_at")
    search_fields = (
        "usuario__nombre",
        "usuario__apellido",
        "usuario__cedula",
        "placa",
        "marca",
        "modelo",
        "color",
    )
    list_filter = ("marca", "modelo", "color", "created_at")


@admin.register(Computador)
class ComputadorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "serial", "created_at")
    search_fields = (
        "usuario__nombre",
        "usuario__apellido",
        "usuario__cedula",
        "serial",
    )
    list_filter = ("created_at",)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tipo", "registrado_por", "fecha")
    search_fields = (
        "usuario__nombre",
        "usuario__apellido",
        "usuario__cedula",
        "usuario__email",
        "registrado_por__nombre",
        "registrado_por__email",
        "observaciones",
    )
    list_filter = ("tipo", "fecha", "registrado_por")
