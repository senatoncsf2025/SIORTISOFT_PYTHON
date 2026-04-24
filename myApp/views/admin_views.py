import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .common import (
    ROL_SINGULAR,
    SERIAL_PC_REGEX,
    TITULOS_ROL,
    validar_acceso_sistema,
    validar_cedula,
    validar_rol_valido,
    redirigir_por_rol,
)
from ..models import Computador, Movimiento, Usuario, Vehiculo


@login_required
def dashboard_view(request):
    if not validar_acceso_sistema(request):
        return redirigir_por_rol(request.user)

    return render(request, "dashboard.html")


@login_required
def seccion_view(request, rol):
    if not validar_acceso_sistema(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "La sección solicitada no existe")
        return redirect("dashboard")

    context = {
        "rol": rol,
        "rol_titulo": TITULOS_ROL.get(rol, rol.title()),
        "rol_singular": ROL_SINGULAR.get(rol, rol),
        "errors": {},
        "cedula": "",
        "tipo": "",
        "observaciones": "",
        "trae_vehiculo": "0",
        "placa": "",
        "marca": "",
        "modelo": "",
        "color": "",
        "trae_pc": "0",
        "serial": "",
        "mostrar_form_consulta": False,
        "mostrar_form_registro": False,
    }

    if request.method != "POST":
        return render(request, f"secciones/{rol}.html", context)

    formulario = request.POST.get("formulario", "consulta").strip()

    if formulario == "registro":
        context["mostrar_form_registro"] = True
        context["mostrar_form_consulta"] = False
        return render(request, f"secciones/{rol}.html", context)

    cedula = request.POST.get("cedula", "").strip()
    tipo = request.POST.get("tipo", "").strip()
    observaciones = request.POST.get("observaciones", "").strip()
    trae_vehiculo = request.POST.get("trae_vehiculo", "0").strip()
    placa = request.POST.get("placa", "").strip().upper()
    marca = request.POST.get("marca", "").strip()
    modelo = request.POST.get("modelo", "").strip()
    color = request.POST.get("color", "").strip()
    trae_pc = request.POST.get("trae_pc", "0").strip()
    serial = request.POST.get("serial", "").strip().upper()

    context.update(
        {
            "cedula": cedula,
            "tipo": tipo,
            "observaciones": observaciones,
            "trae_vehiculo": trae_vehiculo,
            "placa": placa,
            "marca": marca,
            "modelo": modelo,
            "color": color,
            "trae_pc": trae_pc,
            "serial": serial,
        }
    )

    errors = {}

    error = validar_cedula(cedula)
    if error:
        errors["cedula"] = error

    if tipo not in ["ingreso", "salida"]:
        errors["tipo"] = "Debes seleccionar un tipo de movimiento válido"

    if trae_vehiculo not in ["0", "1"]:
        errors["placa"] = "Debes seleccionar una opción válida para vehículo"

    if trae_pc not in ["0", "1"]:
        errors["serial"] = "Debes seleccionar una opción válida para PC"

    if trae_vehiculo == "1" and not placa:
        errors["placa"] = "Debes ingresar la placa del vehículo"

    if trae_pc == "1":
        if not serial:
            errors["serial"] = "Debes ingresar el serial del PC"
        elif not re.fullmatch(SERIAL_PC_REGEX, serial):
            errors["serial"] = "El serial del PC debe tener exactamente 4 caracteres alfanuméricos"

    usuario = None

    if not errors:
        usuario = Usuario.objects.filter(
            cedula=cedula,
            subrol=rol,
            activo=True,
        ).first()

        if not usuario:
            errors["cedula"] = f"No existe un {ROL_SINGULAR.get(rol, rol)} activo con esa cédula"

    if not errors:
        ultimo_movimiento = Movimiento.objects.filter(usuario=usuario).order_by("-fecha").first()

        if ultimo_movimiento and ultimo_movimiento.tipo == tipo:
            errors["tipo"] = f"No puedes registrar dos {tipo}s consecutivos para este usuario"

    if errors:
        context["errors"] = errors
        context["mostrar_form_consulta"] = True
        context["mostrar_form_registro"] = False
        return render(request, f"secciones/{rol}.html", context)

    with transaction.atomic():
        Movimiento.objects.create(
            usuario=usuario,
            tipo=tipo,
            observaciones=observaciones or None,
            trae_vehiculo=(trae_vehiculo == "1"),
            placa=placa or None,
            marca=marca or None,
            modelo=modelo or None,
            color=color or None,
            trae_pc=(trae_pc == "1"),
            serial_pc=serial or None,
            registrado_por=request.user,
        )

        if trae_vehiculo == "1":
            vehiculo_obj, _ = Vehiculo.objects.get_or_create(
                usuario=usuario,
                defaults={
                    "placa": placa,
                    "marca": marca or None,
                    "modelo": modelo or None,
                    "color": color or None,
                },
            )
            vehiculo_obj.placa = placa
            vehiculo_obj.marca = marca or None
            vehiculo_obj.modelo = modelo or None
            vehiculo_obj.color = color or None
            vehiculo_obj.save()
        else:
            Vehiculo.objects.filter(usuario=usuario).delete()

        if trae_pc == "1":
            computador_obj, _ = Computador.objects.get_or_create(
                usuario=usuario,
                defaults={"serial": serial},
            )
            computador_obj.serial = serial
            computador_obj.save()
        else:
            Computador.objects.filter(usuario=usuario).delete()

    messages.success(
        request,
        f"Movimiento de {tipo} registrado correctamente para {usuario.nombre_completo}",
    )

    context.update(
        {
            "cedula": "",
            "tipo": "",
            "observaciones": "",
            "trae_vehiculo": "0",
            "placa": "",
            "marca": "",
            "modelo": "",
            "color": "",
            "trae_pc": "0",
            "serial": "",
            "errors": {},
            "mostrar_form_consulta": True,
            "mostrar_form_registro": False,
        }
    )

    return render(request, f"secciones/{rol}.html", context)


@login_required
def dashboard_data(request):
    hoy = timezone.localdate()

    data = {
        "usuarios": Usuario.objects.count(),
        "estudiantes": Usuario.objects.filter(subrol="estudiantes").count(),
        "docentes": Usuario.objects.filter(subrol="docentes").count(),
        "visitantes": Usuario.objects.filter(
            subrol="visitantes",
            fecha_visita=hoy,
        ).count(),
    }

    return JsonResponse(data)