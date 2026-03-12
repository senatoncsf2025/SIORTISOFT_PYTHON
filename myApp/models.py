from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio para usuarios del sistema")

        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra_fields)
        user.set_password(password)

        # Si no se define rol, por defecto será admin/vigilante según quien lo cree manualmente.
        # Para usuarios del sistema el email sí es obligatorio.
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

        if extra_fields.get("rol") != "admin":
            raise ValueError("El superusuario debe tener rol='admin'")

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

    # Solo estos roles inician sesión en el sistema
    ROLES = [
        ("admin", "Administrador"),
        ("vigilante", "Vigilante"),
        ("persona", "Persona Registrada"),
    ]

    # Clasificación funcional de las personas registradas
    SUBROLES = [
        ("oficinas", "Oficinas"),
        ("enfermeria", "Enfermería"),
        ("parqueadero", "Parqueadero"),
        ("visitantes", "Visitantes"),
        ("acudientes", "Acudientes"),
        ("docentes", "Docentes"),
        ("estudiantes", "Estudiantes"),
        ("personal", "Personal"),
    ]

    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255, blank=True, null=True)
    cedula = models.CharField(max_length=20, unique=True)

    genero = models.CharField(max_length=10, choices=GENERO, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    # Solo admin y vigilante necesitan email para login.
    # Para personas registradas puede ir vacío.
    email = models.EmailField(unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO,
        blank=True,
        null=True,
    )

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

    rol = models.CharField(max_length=20, choices=ROLES, default="persona")
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

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-created_at"]

    def __str__(self):
        etiqueta = self.subrol if self.rol == "persona" else self.rol
        return f"{self.nombre_completo} - {etiqueta}"

    @property
    def is_active(self):
        return self.activo

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido or ''}".strip()

    @property
    def puede_iniciar_sesion(self):
        return self.rol in ["admin", "vigilante"]

    def save(self, *args, **kwargs):
        # Normaliza reglas de acceso:
        # solo admin y vigilante pueden entrar al sistema
        if self.rol in ["admin", "vigilante"]:
            self.is_staff = True
        else:
            self.is_staff = False
            self.is_superuser = False

        # Si es una persona registrada normal, debe tener subrol
        if self.rol == "persona" and not self.subrol:
            # No lanzamos error aquí para no romper cargas parciales;
            # esto idealmente se valida en forms/serializers/admin.
            pass

        super().save(*args, **kwargs)


class Vehiculo(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="vehiculo",
    )
    placa = models.CharField(max_length=20, blank=True, null=True)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"

    def __str__(self):
        return self.placa or f"Vehículo de {self.usuario.nombre_completo}"


class Computador(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="computador",
    )
    serial = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Computador"
        verbose_name_plural = "Computadores"

    def __str__(self):
        return self.serial or f"PC de {self.usuario.nombre_completo}"


class Movimiento(models.Model):
    TIPO_MOVIMIENTO = [
        ("ingreso", "Ingreso"),
        ("salida", "Salida"),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="movimientos",
    )
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    observaciones = models.TextField(blank=True, null=True)

    # normalmente lo registra un vigilante o admin
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_registrados",
    )

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.tipo} - {self.fecha:%Y-%m-%d %H:%M}"
