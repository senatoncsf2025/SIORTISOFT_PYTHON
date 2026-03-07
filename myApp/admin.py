from django.contrib import admin
from .models import Usuario, Registro


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'apellido',
        'email',
        'telefono',
        'cedula',
        'tipo_usuario',
        'activo',
        'created_at'
    )
    list_filter = (
        'tipo_usuario',
        'genero',
        'activo',
        'horario'
    )
    search_fields = (
        'nombre',
        'apellido',
        'email',
        'cedula'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'usuario',
        'fecha_entrada',
        'fecha_salida'
    )
    list_filter = ('fecha_entrada',)
    search_fields = (
        'usuario__nombre',
        'usuario__apellido',
        'usuario__email'
    )
    ordering = ('-fecha_entrada',)