import re

from django.contrib import messages
from django.shortcuts import redirect, render

from .common import (
    SERIAL_PC_REGEX,
    parse_fecha,
    validar_cedula,
    validar_nombre,
    validar_telefono,
)
from ..models import Computador, Usuario, Vehiculo


def registro_visita_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        cedula = request.POST.get("cedula", "").strip()
        trae_vehiculo = request.POST.get("trae_vehiculo", "0")
        placa = request.POST.get("placa", "").strip().upper()
        marca = request.POST.get("marca", "").strip()
        modelo = request.POST.get("modelo", "").strip()
        color = request.POST.get("color", "").strip()
        trae_pc = request.POST.get("trae_pc", "0")
        serial_pc = request.POST.get("serial_pc", "").strip().upper()
        fecha_visita = request.POST.get("fecha_visita", "").strip()
        horario = request.POST.get("horario", "").strip()

        context = {
            "nombre": nombre,
            "telefono": telefono,
            "cedula": cedula,
            "trae_vehiculo": trae_vehiculo,
            "placa": placa,
            "marca": marca,
            "modelo": modelo,
            "color": color,
            "trae_pc": trae_pc,
            "serial_pc": serial_pc,
            "fecha_visita": fecha_visita,
            "horario": horario,
        }

        error = validar_nombre(nombre, "nombre", True)
        if error:
            messages.error(request, error)
            return render(request, "public/registro_visita.html", context)

        error = validar_telefono(telefono, False)
        if error:
            messages.error(request, error)
            return render(request, "public/registro_visita.html", context)

        error = validar_cedula(cedula)
        if error:
            messages.error(request, error)
            return render(request, "public/registro_visita.html", context)

        fecha_visita_date, error = parse_fecha(fecha_visita, obligatoria=True)
        if error:
            messages.error(request, "La fecha de visita no es válida")
            return render(request, "public/registro_visita.html", context)

        if horario not in ["AM", "PM"]:
            messages.error(request, "Debes seleccionar un horario válido")
            return render(request, "public/registro_visita.html", context)

        if trae_vehiculo == "1" and not placa:
            messages.error(request, "Debes ingresar la placa del vehículo")
            return render(request, "public/registro_visita.html", context)

        if trae_pc == "1":
            if not serial_pc:
                messages.error(
                    request,
                    "Debes ingresar los últimos 4 caracteres del serial del PC",
                )
                return render(request, "public/registro_visita.html", context)

            if not re.fullmatch(SERIAL_PC_REGEX, serial_pc):
                messages.error(
                    request,
                    "El serial del PC debe tener exactamente 4 caracteres alfanuméricos",
                )
                return render(request, "public/registro_visita.html", context)

        usuario = Usuario(
            nombre=nombre,
            cedula=cedula,
            email=None,
            telefono=telefono or None,
            fecha_visita=fecha_visita_date,
            horario=horario,
            rol="persona",
            subrol="visitantes",
            activo=True,
        )
        usuario.set_unusable_password()
        usuario.save()

        if trae_vehiculo == "1":
            Vehiculo.objects.create(
                usuario=usuario,
                placa=placa,
                marca=marca or None,
                modelo=modelo or None,
                color=color or None,
            )

        if trae_pc == "1":
            Computador.objects.create(
                usuario=usuario,
                serial=serial_pc,
            )

        messages.success(request, "La visita fue registrada correctamente")
        return redirect("registro_visita")

    return render(request, "public/registro_visita.html")