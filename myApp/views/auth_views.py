from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .common import (
    GENEROS,
    TIPOS_USUARIO,
    construir_contexto_registro_interno,
    extraer_form_data,
    parse_fecha,
    redirigir_por_rol,
    validar_form_registro_interno,
)
from ..models import Usuario


def index(request):
    return render(request, "index.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Correo o contraseña incorrectos")
            return render(request, "auth/login.html", {"email": email})

        if not user.activo:
            messages.error(request, "Tu usuario está inactivo")
            return render(request, "auth/login.html", {"email": email})

        if user.rol not in ["admin", "vigilante"]:
            messages.error(request, "No tienes permiso para ingresar al sistema")
            return render(request, "auth/login.html", {"email": email})

        login(request, user)
        messages.success(request, f"Bienvenido, {user.nombre}")
        return redirigir_por_rol(user)

    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente")
    return redirect("login")


@login_required
def register_view(request):
    if request.user.rol != "admin":
        messages.error(request, "Solo el administrador puede registrar usuarios del sistema")
        return redirigir_por_rol(request.user)

    if request.method == "POST":
        form_data = extraer_form_data(request)
        rol = request.POST.get("rol", "").strip()
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()

        context = construir_contexto_registro_interno(request)

        error = validar_form_registro_interno(form_data, rol, password, password2)

        if error:
            messages.error(request, error)
            return render(request, "auth/register.html", context)

        fecha_nac, _ = parse_fecha(
            form_data["fecha_nacimiento"],
            obligatoria=True,
            validar_mayoria_edad=True,
        )

        Usuario.objects.create_user(
            email=form_data["email"],
            nombre=form_data["nombre"],
            apellido=form_data["apellido"] or None,
            cedula=form_data["cedula"],
            telefono=form_data["telefono"],
            direccion=form_data["direccion"],
            genero=form_data["genero"],
            fecha_nacimiento=fecha_nac,
            cargo=form_data["cargo"] or None,
            tipo_usuario=form_data["tipo_usuario"],
            rol=rol,
            codigo_vigilante=form_data["codigo_vigilante"] if rol == "vigilante" else None,
            password=password,
            activo=True,
            registrado_por=request.user,
        )

        messages.success(request, "Usuario creado correctamente")
        return redirect("index2")

    return render(
        request,
        "auth/register.html",
        {
            "generos": GENEROS,
            "tipos_usuario": TIPOS_USUARIO,
        },
    )