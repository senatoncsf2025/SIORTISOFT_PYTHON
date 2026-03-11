from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Usuario


def index(request):
    return render(request, "index.html")


@login_required
def index2(request):
    return render(request, "index2.html")


@login_required
def role_index(request, rol):
    usuarios = []

    context = {
        "rol": rol,
        "rol_singular": "acudiente" if rol == "acudientes" else rol,
        "usuarios": usuarios,
        "create_url_name": f"{rol}.create",
        "edit_url_name": f"{rol}.edit",
        "activar_url_name": f"{rol}.activar",
        "inactivar_url_name": f"{rol}.inactivar",
        "reporte_url_name": f"{rol}.reporte",
        "edit_base_url": f"/dashboard/{rol}/",
        "activar_base_url": f"/dashboard/{rol}/activar/",
        "inactivar_base_url": f"/dashboard/{rol}/inactivar/",
    }
    return render(request, f"crud/{rol}/index.html", context)


@login_required
def role_create(request, rol):
    context = {
        "rol": rol,
        "rol_singular": "acudiente" if rol == "acudientes" else rol,
        "action_url": f"/dashboard/{rol}/store/",
        "cancel_url": f"/dashboard/{rol}/",
        "form": {},
    }
    return render(request, f"crud/{rol}/create.html", context)


@login_required
def role_reporte(request, rol):
    return HttpResponse(f"Reporte de {rol}")


def redirigir_por_rol(user):
    return redirect("index2")


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

    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        cedula = request.POST.get("cedula", "").strip()
        email = request.POST.get("email", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        tipo_usuario = request.POST.get("tipo_usuario", "").strip()
        rol = request.POST.get("rol", "").strip()
        subrol = request.POST.get("subrol", "").strip()
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
            "subrol": subrol,
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

        if not telefono:
            messages.error(request, "El teléfono es obligatorio")
            return render(request, "auth/register.html", context)

        if not direccion:
            messages.error(request, "La dirección es obligatoria")
            return render(request, "auth/register.html", context)

        if not tipo_usuario:
            messages.error(request, "Debes seleccionar el tipo de usuario")
            return render(request, "auth/register.html", context)

        if not rol:
            messages.error(request, "Debes seleccionar el rol")
            return render(request, "auth/register.html", context)

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "auth/register.html", context)

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "El email ya está registrado")
            return render(request, "auth/register.html", context)

        if Usuario.objects.filter(cedula=cedula).exists():
            messages.error(request, "La cédula ya está registrada")
            return render(request, "auth/register.html", context)

        Usuario.objects.create_user(
            email=email,
            nombre=nombre,
            apellido=apellido,
            cedula=cedula,
            telefono=telefono,
            direccion=direccion,
            tipo_usuario=tipo_usuario,
            rol=rol,
            subrol=subrol if subrol else None,
            password=password,
        )

        messages.success(
            request, "Usuario creado correctamente. Ya puedes iniciar sesión"
        )
        return redirect("login")

    return render(request, "auth/register.html")
