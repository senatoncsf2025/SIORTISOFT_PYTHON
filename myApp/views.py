from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Usuario


def index(request):
    return render(request, "index.html")


@login_required
def index2(request):
    if request.user.rol != "admin":
        messages.error(request, "No tienes acceso al panel de administrador")
        return redirigir_por_rol(request.user)

    return render(request, "index2.html")


def redirigir_por_rol(user):
    if user.rol == "admin":
        return redirect("index2")
    elif user.rol == "vigilante":
        return redirect("dashboard")
    return redirect("home")


def login_view(request):
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.activo:
                login(request, user)
                messages.success(request, f"Bienvenido, {user.nombre}")
                return redirigir_por_rol(user)
            else:
                messages.error(request, "Tu usuario está inactivo")
        else:
            messages.error(request, "Correo o contraseña incorrectos")

        return render(request, "auth/login.html", {"email": email})

    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente")
    return redirect("login")


def register_view(request):
    # Registro SOLO de usuarios del sistema:
    # admin y vigilante

    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        cedula = request.POST.get("cedula", "").strip()
        email = request.POST.get("email", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        tipo_usuario = request.POST.get("tipo_usuario", "").strip()
        rol = request.POST.get("rol", "").strip()
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()

        context = {
            "nombre": nombre,
            "apellido": apellido,
            "cedula": cedula,
            "email": email,
            "telefono": telefono,
            "direccion": direccion,
            "tipo_usuario": tipo_usuario,
            "rol": rol,
        }

        if not nombre:
            messages.error(request, "El nombre es obligatorio")
            return render(request, "auth/register.html", context)

        if not cedula:
            messages.error(request, "La cédula es obligatoria")
            return render(request, "auth/register.html", context)

        if not email:
            messages.error(request, "El correo es obligatorio")
            return render(request, "auth/register.html", context)

        if not tipo_usuario:
            messages.error(request, "Debes seleccionar el tipo de usuario")
            return render(request, "auth/register.html", context)

        if rol not in ["admin", "vigilante"]:
            messages.error(request, "Solo puedes registrar administradores o vigilantes")
            return render(request, "auth/register.html", context)

        if not password or not password2:
            messages.error(request, "Debes ingresar y confirmar la contraseña")
            return render(request, "auth/register.html", context)

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "auth/register.html", context)

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "El correo ya está registrado")
            return render(request, "auth/register.html", context)

        if Usuario.objects.filter(cedula=cedula).exists():
            messages.error(request, "La cédula ya está registrada")
            return render(request, "auth/register.html", context)

        Usuario.objects.create_user(
            email=email,
            nombre=nombre,
            apellido=apellido or None,
            cedula=cedula,
            telefono=telefono or None,
            direccion=direccion or None,
            tipo_usuario=tipo_usuario,
            rol=rol,
            password=password,
            activo=True,
            is_staff=True,
        )

        messages.success(request, "Usuario creado correctamente. Ya puedes iniciar sesión")
        return redirect("login")

    return render(request, "auth/register.html")


# =========================
# VISTAS DEL PANEL VIGILANTE
# =========================

@login_required
def dashboard_view(request):
    if request.user.rol not in ["admin", "vigilante"]:
        messages.error(request, "No tienes acceso al dashboard")
        return redirigir_por_rol(request.user)

    return render(request, "dashboard.html")


@login_required
def seccion_view(request, rol):
    if request.user.rol not in ["admin", "vigilante"]:
        messages.error(request, "No tienes acceso a esta sección")
        return redirigir_por_rol(request.user)

    roles_validos = [
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

    if rol not in roles_validos:
        messages.error(request, "La sección solicitada no existe")
        return redirect("dashboard")

    singular_map = {
        "acudientes": "acudiente",
        "docentes": "docente",
        "estudiantes": "estudiante",
        "enfermeria": "enfermería",
        "oficinas": "oficina",
        "parqueadero": "parqueadero",
        "personal": "personal",
        "visitantes": "visitante",
        "vigilantes": "vigilante",
    }

    context = {
        "rol": rol,
        "rol_singular": singular_map.get(rol, rol),
    }

    return render(request, f"secciones/{rol}.html", context)


# =========================
# VISTAS DEL ADMIN
# =========================

@login_required
def role_index(request, rol):
    if request.user.rol != "admin":
        messages.error(request, "No tienes acceso al CRUD administrativo")
        return redirigir_por_rol(request.user)

    usuarios = Usuario.objects.filter(subrol=rol).order_by("-created_at")

    singular_map = {
        "acudientes": "acudiente",
        "docentes": "docente",
        "estudiantes": "estudiante",
        "enfermeria": "enfermería",
        "oficinas": "oficina",
        "parqueadero": "parqueadero",
        "personal": "personal",
        "visitantes": "visitante",
        "vigilantes": "vigilante",
    }

    context = {
        "rol": rol,
        "rol_singular": singular_map.get(rol, rol),
        "usuarios": usuarios,
        "create_url_name": f"{rol}.create",
        "edit_url_name": f"{rol}.edit",
        "activar_url_name": f"{rol}.activar",
        "inactivar_url_name": f"{rol}.inactivar",
        "reporte_url_name": f"{rol}.reporte",
        "edit_base_url": f"/crud/{rol}/",
        "activar_base_url": f"/crud/{rol}/activar/",
        "inactivar_base_url": f"/crud/{rol}/inactivar/",
    }
    return render(request, f"crud/{rol}/index.html", context)


@login_required
def role_create(request, rol):
    if request.user.rol != "admin":
        messages.error(request, "No tienes acceso al CRUD administrativo")
        return redirigir_por_rol(request.user)

    singular_map = {
        "acudientes": "acudiente",
        "docentes": "docente",
        "estudiantes": "estudiante",
        "enfermeria": "enfermería",
        "oficinas": "oficina",
        "parqueadero": "parqueadero",
        "personal": "personal",
        "visitantes": "visitante",
        "vigilantes": "vigilante",
    }

    context = {
        "rol": rol,
        "rol_singular": singular_map.get(rol, rol),
        "action_url": f"/crud/{rol}/store/",
        "cancel_url": f"/crud/{rol}/",
        "form": {},
    }
    return render(request, f"crud/{rol}/create.html", context)


@login_required
def role_edit(request, rol, user_id):
    if request.user.rol != "admin":
        messages.error(request, "No tienes acceso al CRUD administrativo")
        return redirigir_por_rol(request.user)

    usuario = get_object_or_404(Usuario, id=user_id, subrol=rol)

    singular_map = {
        "acudientes": "acudiente",
        "docentes": "docente",
        "estudiantes": "estudiante",
        "enfermeria": "enfermería",
        "oficinas": "oficina",
        "parqueadero": "parqueadero",
        "personal": "personal",
        "visitantes": "visitante",
        "vigilantes": "vigilante",
    }

    context = {
        "rol": rol,
        "rol_singular": singular_map.get(rol, rol),
        "usuario": usuario,
        "action_url": f"/crud/{rol}/{user_id}/update/",
        "cancel_url": f"/crud/{rol}/",
    }
    return render(request, f"crud/{rol}/edit.html", context)


@login_required
def role_reporte(request, rol):
    if request.user.rol != "admin":
        messages.error(request, "No tienes acceso a reportes")
        return redirigir_por_rol(request.user)

    return render(request, f"crud/{rol}/reporte.html", {"rol": rol})