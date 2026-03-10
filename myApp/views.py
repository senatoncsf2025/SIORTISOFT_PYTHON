from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Rol


# =========================
# PAGINAS PRINCIPALES
# =========================

def index(request):
    return render(request, 'index.html')


def index2(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'index2.html')


# =========================
# CRUD GENERICO POR ROL
# =========================

def role_index(request, rol):

    usuarios = []  # aquí luego puedes traer usuarios según el rol

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


# =========================
# ROLES
# =========================

# Ver roles
def lista_roles(request):

    roles = Rol.objects.all()

    return render(
        request,
        'roles/lista_roles.html',
        {'roles': roles}
    )


# Crear rol
def crear_rol(request):

    if request.method == "POST":

        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')

        Rol.objects.create(
            nombre=nombre,
            descripcion=descripcion
        )

        messages.success(request, "Rol creado correctamente")

        return redirect('lista_roles')

    return render(request, 'roles/crear_rol.html')


# Eliminar rol
def eliminar_rol(request, id):

    rol = get_object_or_404(Rol, id=id)

    rol.delete()

    messages.success(request, "Rol eliminado correctamente")

    return redirect('lista_roles')


# =========================
# LOGIN
# =========================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("index2")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                f"¡Bienvenido {user.username}!"
            )

            return redirect("index2")

        else:

            messages.error(
                request,
                "Usuario o contraseña incorrectos"
            )

            return render(
                request,
                "login.html",
                {"username": username}
            )

    return render(request, "login.html")


# =========================
# LOGOUT
# =========================

def logout_view(request):

    logout(request)

    messages.info(
        request,
        "Has cerrado sesión correctamente"
    )

    return redirect("login")


# =========================
# REGISTRO
# =========================

def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()

        if password != password2:

            messages.error(
                request,
                "Las contraseñas no coinciden"
            )

            return render(request, "register.html", {
                "username": username,
                "email": email
            })

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                "El usuario ya existe"
            )

            return render(request, "register.html", {
                "email": email
            })

        if User.objects.filter(email=email).exists():

            messages.error(
                request,
                "El email ya está registrado"
            )

            return render(request, "register.html", {
                "username": username
            })

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(
            request,
            "Usuario creado correctamente. Ya puedes iniciar sesión"
        )

        return redirect("login")

    return render(request, "register.html")