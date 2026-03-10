from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def index2(request):
    return render(request, 'index2.html')


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'auth/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return render(request, 'auth/register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        user.save()
        messages.success(request, 'Usuario creado exitosamente')
        return redirect('login')

    return render(request, 'auth/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
            return render(request, 'auth/login.html', {'username': username})

    return render(request, 'auth/login.html')


def role_index(request, rol):
    usuarios = []
    context = {
        "rol": rol,
        "rol_singular": "acudiente" if rol == "acudientes" else rol,
        "usuarios": usuarios,
    }
    return render(request, f'crud/{rol}/index.html', context)


def role_create(request, rol):
    context = {
        "rol": rol,
        "rol_singular": "acudiente" if rol == "acudientes" else rol,
        "action_url": f"/{rol}/store/",
        "cancel_url": f"/{rol}/",
        "form": {}
    }
    return render(request, f'crud/{rol}/create.html', context)


def role_reporte(request, rol):
    return HttpResponse(f"Reporte de {rol}")
