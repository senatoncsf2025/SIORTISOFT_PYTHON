from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("activo", True)
        extra_fields.setdefault("rol", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self.create_user(email, nombre, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO = [
        ("INTERNO", "Interno"),
        ("EXTERNO", "Externo"),
    ]

    GENERO = [
        ("Masculino", "Masculino"),
        ("Femenino", "Femenino"),
        ("Otro", "Otro"),
    ]

    HORARIO = [
        ("AM", "AM"),
        ("PM", "PM"),
    ]

    ROLES = [
        ("admin", "Admin"),
        ("vigilante", "Vigilante"),
        ("administrativo", "Administrativo"),
        ("servicios", "Servicios"),
        ("personal", "Personal"),
    ]

    SUBROLES = [
        ("oficinas", "Oficinas"),
        ("enfermeria", "Enfermería"),
        ("vigilantes", "Vigilantes"),
        ("parqueadero", "Parqueadero"),
        ("visitantes", "Visitantes"),
        ("acudientes", "Acudientes"),
        ("docentes", "Docentes"),
        ("estudiantes", "Estudiantes"),
        ("personal_general", "Personal General"),
    ]

    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255, blank=True, null=True)

    cedula = models.CharField(max_length=20, unique=True)
    genero = models.CharField(max_length=10, choices=GENERO, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)

    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO)

    cargo = models.CharField(max_length=255, blank=True, null=True)
    codigo_vigilante = models.CharField(max_length=255, blank=True, null=True)

    fecha_visita = models.DateField(blank=True, null=True)
    horario = models.CharField(max_length=2, choices=HORARIO, blank=True, null=True)

    registrado_por = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios_registrados",
    )

    rol = models.CharField(max_length=20, choices=ROLES, default="personal")
    subrol = models.CharField(max_length=30, choices=SUBROLES, blank=True, null=True)

    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    email_verified_at = models.DateTimeField(blank=True, null=True)
    telefono_verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=255, blank=True, null=True)
    remember_token = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    def __str__(self):
        return f"{self.nombre} {self.apellido or ''} - {self.rol}"

    @property
    def is_active(self):
        return self.activo


class Registro(models.Model):
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="registros"
    )
    fecha_entrada = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario.nombre} - Entrada: {self.fecha_entrada}"
