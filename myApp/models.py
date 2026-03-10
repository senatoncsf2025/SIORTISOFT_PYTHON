from django.db import models

# ==== MANEJO DE ROLES ====
class Rol(models.Model):

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    # Permisos básicos del sistema
    puede_crear = models.BooleanField(default=False)
    puede_editar = models.BooleanField(default=False)
    puede_eliminar = models.BooleanField(default=False)
    puede_ver = models.BooleanField(default=True)

    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Usuario(models.Model):

    # ===== OPCIONES =====

    TIPO_USUARIO = [
        ('INTERNO', 'Interno'),
        ('EXTERNO', 'Externo'),
    ]

    GENERO = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Otro', 'Otro'),
    ]

    HORARIO = [
        ('AM', 'AM'),
        ('PM', 'PM'),
    ]

    # ===== DATOS PERSONALES =====

    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255, blank=True, null=True)

    cedula = models.CharField(max_length=20)
    genero = models.CharField(max_length=10, choices=GENERO, blank=True, null=True)

    fecha_nacimiento = models.DateField(blank=True, null=True)

    # ===== CONTACTO =====

    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)

    # ===== TIPO DE USUARIO =====

    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO)

    # ===== INFORMACIÓN LABORAL =====

    cargo = models.CharField(max_length=255, blank=True, null=True)
    codigo_vigilante = models.CharField(max_length=255, blank=True, null=True)

    # ===== VISITANTES =====

    fecha_visita = models.DateField(blank=True, null=True)
    horario = models.CharField(max_length=2, choices=HORARIO, blank=True, null=True)
    rol_externo = models.CharField(max_length=255, blank=True, null=True)

    registrado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_registrados'
    )

    # ===== AUTENTICACIÓN =====

    password = models.CharField(max_length=255, blank=True, null=True)
    
    rol = models.ForeignKey(
    Rol,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="usuarios"
)

    email_verified_at = models.DateTimeField(blank=True, null=True)
    telefono_verificado = models.BooleanField(default=False)

    codigo_verificacion = models.CharField(max_length=255, blank=True, null=True)
    remember_token = models.CharField(max_length=100, blank=True, null=True)

    # ===== ESTADO =====

    activo = models.BooleanField(default=True)

    # ===== FECHAS =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.tipo_usuario})"



class Registro(models.Model):

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="registros"
    )

    fecha_entrada = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario.nombre} - Entrada: {self.fecha_entrada}"
    