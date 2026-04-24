from datetime import date

from django.core.management.base import BaseCommand
from myApp.models import Usuario


class Command(BaseCommand):
    help = "Seeder solo para usuarios del sistema (admin y vigilante)"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🌱 Ejecutando seeder..."))

        self.crear_admin()
        self.crear_vigilante()

        self.stdout.write(self.style.SUCCESS("✅ Seeder ejecutado correctamente"))

    def crear_admin(self):
        email = "elkingustavo15@gmail.com"

        if Usuario.objects.filter(email=email).exists():
            self.stdout.write("ℹ️ Admin ya existe")
            return

        admin = Usuario.objects.create_user(
            email=email,
            nombre="Admin",
            apellido="Principal",
            cedula="1000000000",
            telefono="3000000000",
            direccion="Sistema",
            genero="Masculino",
            fecha_nacimiento=date(1990, 1, 1),
            cargo="Administrador",
            tipo_usuario="INTERNO",
            rol="admin",
            password="Admin123*",
            activo=True,
        )

        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        self.stdout.write(self.style.SUCCESS("✅ Admin creado"))
        self.stdout.write("   Email: elkingustavo15@gmail.com")
        self.stdout.write("   Password: Admin123*")

    def crear_vigilante(self):
        email = "sebasarez123@gmail.com"

        if Usuario.objects.filter(email=email).exists():
            self.stdout.write("ℹ️ Vigilante ya existe")
            return

        Usuario.objects.create_user(
            email=email,
            nombre="Carlos",
            apellido="Seguridad",
            cedula="2000000000",
            telefono="3000000001",
            direccion="Portería",
            genero="Masculino",
            fecha_nacimiento=date(1995, 1, 1),
            cargo="Vigilante",
            tipo_usuario="INTERNO",
            rol="vigilante",
            subrol="vigilantes",
            codigo_vigilante="VIG001",
            password="Vigilante123*",
            activo=True,
        )

        self.stdout.write(self.style.SUCCESS("✅ Vigilante creado"))
        self.stdout.write("   Email: sebasarez123@gmail.com")
        self.stdout.write("   Password: Vigilante123*")