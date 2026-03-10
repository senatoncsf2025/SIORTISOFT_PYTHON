from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User


def index(request):
    return render(request, 'index.html')


def index2(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'index2.html')


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


def role_create(request, rol):
    context = {
        "rol": rol,
        "rol_singular": "acudiente" if rol == "acudientes" else rol,
        "action_url": f"/dashboard/{rol}/store/",
        "cancel_url": f"/dashboard/{rol}/",
        "form": {}
    }
    return render(request, f"crud/{rol}/create.html", context)


def role_reporte(request, rol):
    return HttpResponse(f"Reporte de {rol}")


from .models import Usuario

def login_view(request):
    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            usuario = Usuario.objects.get(email=email, password=password)

            request.session["usuario_id"] = usuario.id
            request.session["usuario_nombre"] = usuario.nombre

            return redirect("index2")

        except Usuario.DoesNotExist:
            messages.error(request, "Correo o contraseña incorrectos")

    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "auth/register.html", {
                "username": username,
                "email": email
            })

        if User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe")
            return render(request, "auth/register.html", {
                "email": email
            })

        if User.objects.filter(email=email).exists():
            messages.error(request, "El email ya está registrado")
            return render(request, "auth/register.html", {
                "username": username
            })

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(request, "Usuario creado correctamente. Ya puedes iniciar sesión")
        return redirect("login")

    return render(request, "auth/register.html")