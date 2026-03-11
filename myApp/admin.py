from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Registro


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


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ("usuario", "fecha_entrada", "fecha_salida")
    search_fields = ("usuario__nombre", "usuario__email", "usuario__cedula")
    list_filter = ("fecha_entrada", "fecha_salida")
