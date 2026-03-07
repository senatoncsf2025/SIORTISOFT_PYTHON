from django.shortcuts import render
from django.http import HttpResponse


def index2(request):
    return render(request, 'index2.html')


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