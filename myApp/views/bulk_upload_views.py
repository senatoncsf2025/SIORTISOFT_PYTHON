import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render

from .common import (
    ROLES_VALIDOS,
    crear_usuario_desde_form_data,
    normalizar_genero,
    normalizar_tipo_usuario,
    parse_fecha,
    poblar_usuario_desde_form,
    redirigir_por_rol,
    validar_cedula,
    validar_email,
    validar_genero,
    validar_nombre,
    validar_telefono,
    validar_tipo_usuario,
)
from ..models import Usuario


@login_required
def carga_masiva_view(request):
    if request.user.rol != "admin":
        messages.error(request, "Solo el administrador puede realizar cargas masivas")
        return redirigir_por_rol(request.user)

    if request.method != "POST":
        return render(request, "carga_masiva.html")

    archivo = request.FILES.get("archivo")

    if not archivo:
        messages.error(request, "Debes seleccionar un archivo CSV")
        return render(request, "carga_masiva.html")

    if not archivo.name.lower().endswith(".csv"):
        messages.error(request, "Solo se permiten archivos CSV")
        return render(request, "carga_masiva.html")

    try:
        contenido = archivo.read().decode("utf-8-sig")
        csv_file = io.StringIO(contenido)
        reader = csv.DictReader(csv_file)

        columnas_obligatorias = [
            "nombre",
            "apellido",
            "cedula",
            "email",
            "telefono",
            "direccion",
            "genero",
            "fecha_nacimiento",
            "cargo",
            "tipo_usuario",
            "tipo_persona",
            "codigo_vigilante",
        ]

        if not reader.fieldnames:
            messages.error(request, "El archivo está vacío o no tiene encabezados")
            return render(request, "carga_masiva.html")

        faltantes = [col for col in columnas_obligatorias if col not in reader.fieldnames]

        if faltantes:
            messages.error(request, f"Faltan columnas obligatorias: {', '.join(faltantes)}")
            return render(request, "carga_masiva.html")

        creados = 0
        actualizados = 0
        sin_cambios = 0
        errores = []

        for fila_num, fila in enumerate(reader, start=2):
            try:
                resultado = _procesar_fila_csv(fila, request.user)
                if resultado == "creado":
                    creados += 1
                elif resultado == "actualizado":
                    actualizados += 1
                elif resultado == "sin_cambios":
                    sin_cambios += 1
            except Exception as e:
                errores.append(f"Fila {fila_num}: {str(e)}")

        context = {
            "creados": creados,
            "actualizados": actualizados,
            "sin_cambios": sin_cambios,
            "errores": errores,
        }

        if creados > 0:
            messages.success(request, f"Se crearon {creados} registros correctamente")
        if actualizados > 0:
            messages.success(request, f"Se actualizaron {actualizados} registros correctamente")
        if sin_cambios > 0:
            messages.info(request, f"{sin_cambios} registros no tuvieron cambios")
        if creados == 0 and actualizados == 0 and sin_cambios == 0 and not errores:
            messages.info(request, "No hubo datos para procesar")

        return render(request, "carga_masiva.html", context)

    except UnicodeDecodeError:
        messages.error(request, "El archivo debe estar codificado en UTF-8")
        return render(request, "carga_masiva.html")
    except Exception as e:
        messages.error(request, f"Error procesando el archivo: {str(e)}")
        return render(request, "carga_masiva.html")


def _procesar_fila_csv(fila, usuario_admin):
    form_data = {
        "nombre": (fila.get("nombre") or "").strip(),
        "apellido": (fila.get("apellido") or "").strip(),
        "cedula": (fila.get("cedula") or "").strip(),
        "email": (fila.get("email") or "").strip().lower(),
        "telefono": (fila.get("telefono") or "").strip(),
        "direccion": (fila.get("direccion") or "").strip(),
        "genero": normalizar_genero((fila.get("genero") or "").strip()),
        "fecha_nacimiento": (fila.get("fecha_nacimiento") or "").strip(),
        "cargo": (fila.get("cargo") or "").strip(),
        "tipo_usuario": normalizar_tipo_usuario((fila.get("tipo_usuario") or "").strip()),
        "codigo_vigilante": (fila.get("codigo_vigilante") or "").strip(),
    }

    tipo_persona = (fila.get("tipo_persona") or "").strip().lower()

    validaciones = [
        validar_nombre(form_data["nombre"], "nombre", True),
        validar_nombre(form_data["apellido"], "apellido", False),
        validar_cedula(form_data["cedula"]),
        validar_email(form_data["email"], False) if form_data["email"] else None,
        validar_telefono(form_data["telefono"], False) if form_data["telefono"] else None,
        validar_genero(form_data["genero"], obligatorio=False),
        validar_tipo_usuario(form_data["tipo_usuario"], obligatorio=False),
    ]

    for error in validaciones:
        if error:
            raise ValueError(error)

    if not tipo_persona:
        raise ValueError("La columna tipo_persona es obligatoria")

    if tipo_persona not in ROLES_VALIDOS:
        raise ValueError(f"Tipo de persona no válido: {tipo_persona}")

    if form_data["fecha_nacimiento"]:
        _, error = parse_fecha(form_data["fecha_nacimiento"], obligatoria=False)

        if error:
            raise ValueError("La fecha_nacimiento debe tener formato YYYY-MM-DD")

    rol = "vigilante" if tipo_persona == "vigilantes" else "persona"

    if rol == "vigilante" and not form_data["codigo_vigilante"]:
        raise ValueError("El código del vigilante es obligatorio")

    with transaction.atomic():
        usuario_existente = Usuario.objects.filter(cedula=form_data["cedula"]).first()

        if form_data["email"]:
            email_qs = Usuario.objects.filter(email=form_data["email"])

            if usuario_existente:
                email_qs = email_qs.exclude(id=usuario_existente.id)

            if email_qs.exists():
                raise ValueError("El correo ya está registrado en otro usuario")

        if usuario_existente:
            return _actualizar_usuario_si_cambia(
                usuario_existente,
                form_data,
                tipo_persona,
                rol,
                usuario_admin,
            )

        crear_usuario_desde_form_data(
            form_data,
            rol_sistema=rol,
            subrol=tipo_persona,
            registrado_por=usuario_admin,
            activo=True,
        )

        return "creado"


def _actualizar_usuario_si_cambia(usuario, form_data, tipo_persona, rol, usuario_admin):
    fecha_nueva, _ = parse_fecha(form_data["fecha_nacimiento"], obligatoria=False)

    cambios = any(
        [
            (usuario.nombre or "") != (form_data["nombre"] or ""),
            (usuario.apellido or "") != (form_data["apellido"] or ""),
            (usuario.email or "") != (form_data["email"] or ""),
            (usuario.telefono or "") != (form_data["telefono"] or ""),
            (usuario.direccion or "") != (form_data["direccion"] or ""),
            (usuario.genero or "") != (form_data["genero"] or ""),
            usuario.fecha_nacimiento != fecha_nueva,
            (usuario.cargo or "") != (form_data["cargo"] or ""),
            (usuario.tipo_usuario or "") != (form_data["tipo_usuario"] or ""),
            (usuario.rol or "") != rol,
            (usuario.subrol or "") != tipo_persona,
            bool(usuario.activo) is not True,
            tipo_persona == "vigilantes"
            and (usuario.codigo_vigilante or "") != (form_data["codigo_vigilante"] or ""),
            tipo_persona != "vigilantes" and bool(usuario.codigo_vigilante),
        ]
    )

    if not cambios:
        return "sin_cambios"

    poblar_usuario_desde_form(usuario, form_data, tipo_persona)
    usuario.rol = rol
    usuario.subrol = tipo_persona
    usuario.registrado_por = usuario_admin
    usuario.activo = True

    if tipo_persona != "vigilantes":
        usuario.codigo_vigilante = None

    usuario.save()
    return "actualizado"