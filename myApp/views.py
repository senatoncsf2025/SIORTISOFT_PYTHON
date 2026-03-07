from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

def index2(request):
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