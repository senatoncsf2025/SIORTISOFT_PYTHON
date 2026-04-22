import csv
import io
import re
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, IntegerField, Value
from django.db.models.functions import TruncDate, ExtractHour, Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Computador, Movimiento, Usuario, Vehiculo


# =========================================================
# CONSTANTES
# =========================================================
ROLES_VALIDOS = [
    "acudientes",
    "docentes",
    "estudiantes",
    "enfermeria",
    "oficinas",
    "parqueadero",
    "personal",
    "visitantes",
    "vigilantes",
]

TITULOS_ROL = {
    "acudientes": "Acudientes",
    "docentes": "Docentes",
    "estudiantes": "Estudiantes",
    "enfermeria": "Enfermería",
    "oficinas": "Oficinas",
    "parqueadero": "Parqueadero",
    "personal": "Personal",
    "visitantes": "Visitantes",
    "vigilantes": "Vigilantes",
}

ROL_SINGULAR = {
    "acudientes": "acudiente",
    "docentes": "docente",
    "estudiantes": "estudiante",
    "enfermeria": "enfermería",
    "oficinas": "oficina",
    "parqueadero": "parqueadero",
    "personal": "personal",
    "visitantes": "visitante",
    "vigilantes": "vigilante",
}

GENEROS = Usuario.GENERO
TIPOS_USUARIO = Usuario.TIPO_USUARIO

CORREO_REGEX = r"^[a-zA-Z0-9._%+-]+@(gmail\.com|hotmail\.com|outlook\.com|yahoo\.com|icloud\.com|live\.com)$"
NOMBRE_REGEX = r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+"
TELEFONO_REGEX = r"3\d{9}"
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.#_\-+=/\\])[A-Za-z\d@$!%*?&.#_\-+=/\\]{8,}$"
SERIAL_PC_REGEX = r"[A-Za-z0-9]{4}"


# =========================================================
# HELPERS
# =========================================================
def redirigir_por_rol(user):
    if user.rol == "admin":
        return redirect("index2")
    if user.rol == "vigilante":
        return redirect("dashboard")
    return redirect("index")


def validar_admin(request):
    if request.user.rol != "admin":
        messages.error(request, "No tienes acceso al CRUD administrativo")
        return False
    return True


def validar_acceso_sistema(request):
    if request.user.rol not in ["admin", "vigilante"]:
        messages.error(request, "No tienes acceso a esta sección")
        return False
    return True


def validar_rol_valido(rol):
    return rol in ROLES_VALIDOS


def validar_rol_login(rol):
    if rol not in ["admin", "vigilante"]:
        return "Solo puedes registrar administradores o vigilantes"
    return None


def get_role_urls(rol):
    return {
        "index_url_name": f"{rol}.index",
        "create_url_name": f"{rol}.create",
        "edit_url_name": f"{rol}.edit",
        "activar_url_name": f"{rol}.activar",
        "inactivar_url_name": f"{rol}.inactivar",
        "reporte_pdf_url_name": f"{rol}.reporte_pdf",
        "estadistico_pdf_url_name": f"{rol}.estadistico_pdf",
    }


def get_role_context(rol, extra=None):
    context = {
        "rol": rol,
        "rol_titulo": TITULOS_ROL.get(rol, rol.title()),
        "rol_singular": ROL_SINGULAR.get(rol, rol),
        "generos": GENEROS,
        "tipos_usuario": TIPOS_USUARIO,
        **get_role_urls(rol),
    }
    if extra:
        context.update(extra)
    return context


def get_role_queryset(rol):
    return Usuario.objects.filter(subrol=rol).order_by("-created_at")


def normalizar_genero(valor):
    if not valor:
        return ""

    valor = valor.strip()
    mapa = {
        "masculino": "Masculino",
        "femenino": "Femenino",
        "otro": "Otro",
        "Masculino": "Masculino",
        "Femenino": "Femenino",
        "Otro": "Otro",
    }
    return mapa.get(valor, valor)


def normalizar_tipo_usuario(valor):
    if not valor:
        return ""

    valor = valor.strip()
    mapa = {
        "interno": "INTERNO",
        "externo": "EXTERNO",
        "INTERNO": "INTERNO",
        "EXTERNO": "EXTERNO",
        "Interno": "INTERNO",
        "Externo": "EXTERNO",
    }
    return mapa.get(valor, valor)


def validar_nombre(valor, campo="nombre", obligatorio=True):
    if obligatorio and not valor:
        return f"El {campo} es obligatorio"

    if valor:
        if len(valor) > 60:
            return f"El {campo} no puede tener más de 60 caracteres"
        if not re.fullmatch(NOMBRE_REGEX, valor):
            return f"El {campo} solo puede contener letras y espacios"

    return None


def validar_cedula(cedula):
    if not cedula:
        return "La cédula es obligatoria"
    if not cedula.isdigit():
        return "La cédula solo puede contener números"
    if len(cedula) < 6 or len(cedula) > 14:
        return "La cédula debe tener entre 6 y 14 dígitos"
    return None


def validar_email(email, obligatorio=False):
    if obligatorio and not email:
        return "El correo es obligatorio"
    if email and not re.fullmatch(CORREO_REGEX, email):
        return "Debes ingresar un correo válido de Gmail, Hotmail, Outlook, Yahoo, iCloud o Live"
    return None


def validar_telefono(telefono, obligatorio=False):
    if obligatorio and not telefono:
        return "El teléfono es obligatorio"
    if telefono and not re.fullmatch(TELEFONO_REGEX, telefono):
        return "El teléfono debe tener 10 números y comenzar por 3"
    return None


def validar_genero(valor, obligatorio=False):
    if obligatorio and not valor:
        return "Debes seleccionar el género"

    valores_genero = [v for v, _ in GENEROS]
    if valor and valor not in valores_genero:
        return "Debes seleccionar un género válido"

    return None


def validar_tipo_usuario(valor, obligatorio=False):
    if obligatorio and not valor:
        return "Debes seleccionar el tipo de usuario"

    valores_tipo_usuario = [v for v, _ in TIPOS_USUARIO]
    if valor and valor not in valores_tipo_usuario:
        return "Debes seleccionar un tipo de usuario válido"

    return None


def validar_password_registro(password, password2):
    if not password or not password2:
        return "Debes ingresar y confirmar la contraseña"

    if password != password2:
        return "Las contraseñas no coinciden"

    if not re.fullmatch(PASSWORD_REGEX, password):
        return (
            "La contraseña debe tener mínimo 8 caracteres, incluir mayúscula, "
            "minúscula, número y caracter especial"
        )

    return None


def parse_fecha(fecha_texto, obligatoria=False, validar_mayoria_edad=False):
    if not fecha_texto:
        if obligatoria:
            return None, "La fecha es obligatoria"
        return None, None

    try:
        fecha = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    except ValueError:
        return None, "La fecha no es válida"

    if validar_mayoria_edad:
        hoy = date.today()
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 18:
            return None, "Solo se permite el registro a personas mayores de 18 años"

    return fecha, None


def extraer_form_data(request):
    return {
        "nombre": request.POST.get("nombre", "").strip(),
        "apellido": request.POST.get("apellido", "").strip(),
        "cedula": request.POST.get("cedula", "").strip(),
        "email": request.POST.get("email", "").strip().lower(),
        "telefono": request.POST.get("telefono", "").strip(),
        "direccion": request.POST.get("direccion", "").strip(),
        "genero": normalizar_genero(request.POST.get("genero", "").strip()),
        "fecha_nacimiento": request.POST.get("fecha_nacimiento", "").strip(),
        "cargo": request.POST.get("cargo", "").strip(),
        "tipo_usuario": normalizar_tipo_usuario(
            request.POST.get("tipo_usuario", "").strip()
        ),
        "codigo_vigilante": request.POST.get("codigo_vigilante", "").strip(),
    }


def construir_contexto_registro_interno(request, extra=None):
    context = extraer_form_data(request)
    context["rol"] = request.POST.get("rol", "").strip()
    if extra:
        context.update(extra)
    return context


def validar_form_usuario(form_data, rol, usuario_id=None):
    error = validar_nombre(form_data["nombre"], "nombre", True)
    if error:
        return error

    error = validar_nombre(form_data["apellido"], "apellido", False)
    if error:
        return error

    error = validar_cedula(form_data["cedula"])
    if error:
        return error

    error = validar_email(form_data["email"], False)
    if error:
        return error

    error = validar_telefono(form_data["telefono"], False)
    if error:
        return error

    _, error = parse_fecha(form_data["fecha_nacimiento"], obligatoria=False)
    if error:
        return error

    error = validar_genero(form_data["genero"], obligatorio=False)
    if error:
        return error

    error = validar_tipo_usuario(form_data["tipo_usuario"], obligatorio=False)
    if error:
        return error

    cedula_qs = Usuario.objects.filter(cedula=form_data["cedula"])
    if usuario_id:
        cedula_qs = cedula_qs.exclude(id=usuario_id)
    if cedula_qs.exists():
        return "La cédula ya está registrada"

    if form_data["email"]:
        email_qs = Usuario.objects.filter(email=form_data["email"])
        if usuario_id:
            email_qs = email_qs.exclude(id=usuario_id)
        if email_qs.exists():
            return "El correo ya está registrado"

    if rol == "vigilantes" and not form_data["codigo_vigilante"]:
        return "El código del vigilante es obligatorio"

    return None


def poblar_usuario_desde_form(usuario, form_data, rol):
    fecha_nac, _ = parse_fecha(form_data["fecha_nacimiento"], obligatoria=False)

    usuario.nombre = form_data["nombre"]
    usuario.apellido = form_data["apellido"] or None
    usuario.cedula = form_data["cedula"]
    usuario.email = form_data["email"] or None
    usuario.telefono = form_data["telefono"] or None
    usuario.direccion = form_data["direccion"] or None
    usuario.genero = form_data["genero"] or None
    usuario.fecha_nacimiento = fecha_nac
    usuario.cargo = form_data["cargo"] or None
    usuario.tipo_usuario = form_data["tipo_usuario"] or None

    if rol == "vigilantes":
        usuario.codigo_vigilante = form_data["codigo_vigilante"] or None

    return usuario


def validar_form_registro_interno(form_data, rol_login, password, password2):
    error = validar_nombre(form_data["nombre"], "nombre", True)
    if error:
        return error

    error = validar_nombre(form_data["apellido"], "apellido", False)
    if error:
        return error

    error = validar_cedula(form_data["cedula"])
    if error:
        return error

    error = validar_email(form_data["email"], True)
    if error:
        return error

    error = validar_telefono(form_data["telefono"], True)
    if error:
        return error

    if not form_data["direccion"]:
        return "La dirección es obligatoria"

    error = validar_genero(form_data["genero"], obligatorio=True)
    if error:
        return error

    _, error = parse_fecha(
        form_data["fecha_nacimiento"],
        obligatoria=True,
        validar_mayoria_edad=True,
    )
    if error:
        return error

    error = validar_tipo_usuario(form_data["tipo_usuario"], obligatorio=True)
    if error:
        return error

    error = validar_rol_login(rol_login)
    if error:
        return error

    if rol_login == "vigilante" and not form_data["codigo_vigilante"]:
        return "El código del vigilante es obligatorio"

    error = validar_password_registro(password, password2)
    if error:
        return error

    if Usuario.objects.filter(email=form_data["email"]).exists():
        return "El correo ya está registrado"

    if Usuario.objects.filter(cedula=form_data["cedula"]).exists():
        return "La cédula ya está registrada"

    return None


def crear_usuario_desde_form_data(
    form_data,
    *,
    rol_sistema,
    subrol,
    registrado_por,
    password=None,
    activo=True,
):
    fecha_nac, _ = parse_fecha(form_data["fecha_nacimiento"], obligatoria=False)

    usuario = Usuario(
        nombre=form_data["nombre"],
        apellido=form_data["apellido"] or None,
        cedula=form_data["cedula"],
        email=form_data["email"] or None,
        telefono=form_data["telefono"] or None,
        direccion=form_data["direccion"] or None,
        genero=form_data["genero"] or None,
        fecha_nacimiento=fecha_nac,
        cargo=form_data["cargo"] or None,
        tipo_usuario=form_data["tipo_usuario"] or None,
        rol=rol_sistema,
        subrol=subrol,
        codigo_vigilante=(
            form_data["codigo_vigilante"] if subrol == "vigilantes" else None
        ),
        activo=activo,
        registrado_por=registrado_por,
    )

    if password:
        usuario.set_password(password)
    elif rol_sistema == "vigilante":
        usuario.set_password("Temporal123*")
    else:
        usuario.set_unusable_password()

    usuario.save()
    return usuario


def construir_styles_pdf():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TituloCustom",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            spaceAfter=12,
            textColor=colors.HexColor("#0f172a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtituloCustom",
            parent=styles["Normal"],
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#475569"),
        )
    )
    return styles


def construir_tabla_resumen_filtros(filtros_reporte):
    resumen_filtros = [
        [
            "Nombre",
            filtros_reporte["reporte_nombre"] or "Todos",
            "Apellido",
            filtros_reporte["reporte_apellido"] or "Todos",
        ],
        [
            "Cédula",
            filtros_reporte["reporte_cedula"] or "Todas",
            "Email",
            filtros_reporte["reporte_email"] or "Todos",
        ],
        [
            "Teléfono",
            filtros_reporte["reporte_telefono"] or "Todos",
            "Estado",
            filtros_reporte["reporte_estado"] or "Todos",
        ],
        [
            "Género",
            filtros_reporte["reporte_genero"] or "Todos",
            "Tipo usuario",
            filtros_reporte["reporte_tipo_usuario"] or "Todos",
        ],
        [
            "Fecha desde",
            filtros_reporte["reporte_fecha_desde"] or "Sin filtro",
            "Movimientos",
            (
                "Ingresos y salidas"
                if filtros_reporte["incluir_ingresos"] == "1"
                and filtros_reporte["incluir_salidas"] == "1"
                else "Solo ingresos"
                if filtros_reporte["incluir_ingresos"] == "1"
                else "Solo salidas"
                if filtros_reporte["incluir_salidas"] == "1"
                else "Todos"
            ),
        ],
    ]

    resumen_table = Table(
        resumen_filtros,
        colWidths=[3 * cm, 7 * cm, 3 * cm, 7 * cm],
    )
    resumen_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return resumen_table


def construir_headers_reporte(columnas_reporte):
    headers = []

    if columnas_reporte["mostrar_nombre"]:
        headers.append("Nombre")
    if columnas_reporte["mostrar_apellido"]:
        headers.append("Apellido")
    if columnas_reporte["mostrar_cedula"]:
        headers.append("Cédula")
    if columnas_reporte["mostrar_telefono"]:
        headers.append("Teléfono")
    if columnas_reporte["mostrar_email"]:
        headers.append("Email")
    if columnas_reporte["mostrar_direccion"]:
        headers.append("Dirección")
    if columnas_reporte["mostrar_vehiculo"]:
        headers.append("Vehículo")
    if columnas_reporte["mostrar_pc"]:
        headers.append("PC")
    if columnas_reporte["mostrar_estado"]:
        headers.append("Estado")

    return headers


def construir_data_usuarios_reporte(usuarios_reporte, columnas_reporte):
    headers = construir_headers_reporte(columnas_reporte)
    data = [headers]

    for usuario in usuarios_reporte:
        row = []
        if columnas_reporte["mostrar_nombre"]:
            row.append(usuario.nombre or "-")
        if columnas_reporte["mostrar_apellido"]:
            row.append(usuario.apellido or "-")
        if columnas_reporte["mostrar_cedula"]:
            row.append(usuario.cedula or "-")
        if columnas_reporte["mostrar_telefono"]:
            row.append(usuario.telefono or "-")
        if columnas_reporte["mostrar_email"]:
            row.append(usuario.email or "-")
        if columnas_reporte["mostrar_direccion"]:
            row.append(usuario.direccion or "-")
        if columnas_reporte["mostrar_vehiculo"]:
            row.append(usuario.vehiculo.placa if getattr(usuario, "vehiculo", None) else "-")
        if columnas_reporte["mostrar_pc"]:
            row.append(usuario.computador.serial if getattr(usuario, "computador", None) else "-")
        if columnas_reporte["mostrar_estado"]:
            row.append("Activo" if usuario.activo else "Inactivo")
        data.append(row)

    if len(data) == 1:
        data.append(["No hay datos para el reporte"] + [""] * (len(headers) - 1))

    return headers, data


def construir_tabla_usuarios_reporte(usuarios_reporte, columnas_reporte):
    headers, data = construir_data_usuarios_reporte(usuarios_reporte, columnas_reporte)

    col_count = max(len(headers), 1)
    total_width = 26 * cm
    col_widths = [total_width / col_count] * col_count

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def construir_tabla_movimientos(movimientos_reporte):
    mov_data = [[
        "Fecha",
        "Usuario",
        "Cédula",
        "Tipo",
        "Vehículo",
        "Placa",
        "PC",
        "Serial PC",
        "Observaciones",
        "Registrado por",
    ]]

    for movimiento in movimientos_reporte:
        mov_data.append(
            [
                movimiento.fecha.strftime("%Y-%m-%d %H:%M"),
                movimiento.usuario.nombre_completo if movimiento.usuario else "-",
                movimiento.usuario.cedula if movimiento.usuario else "-",
                movimiento.tipo.capitalize(),
                "Sí" if movimiento.trae_vehiculo else "No",
                movimiento.placa or "-",
                "Sí" if movimiento.trae_pc else "No",
                movimiento.serial_pc or "-",
                movimiento.observaciones or "-",
                movimiento.registrado_por.nombre_completo if movimiento.registrado_por else "-",
            ]
        )

    if len(mov_data) == 1:
        mov_data.append(["No hay movimientos registrados", "", "", "", "", "", "", "", "", ""])

    mov_table = Table(
        mov_data,
        colWidths=[2.8 * cm, 3.6 * cm, 2.4 * cm, 2.1 * cm, 1.8 * cm, 2.4 * cm, 1.5 * cm, 2.5 * cm, 5.8 * cm, 3.1 * cm],
        repeatRows=1,
    )
    mov_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return mov_table


# =========================================================
# HELPERS REPORTE
# =========================================================
def obtener_filtros_reporte(request):
    return {
        "reporte_nombre": request.GET.get("reporte_nombre", "").strip(),
        "reporte_apellido": request.GET.get("reporte_apellido", "").strip(),
        "reporte_cedula": request.GET.get("reporte_cedula", "").strip(),
        "reporte_email": request.GET.get("reporte_email", "").strip(),
        "reporte_telefono": request.GET.get("reporte_telefono", "").strip(),
        "reporte_estado": request.GET.get("reporte_estado", "").strip(),
        "reporte_genero": normalizar_genero(request.GET.get("reporte_genero", "").strip()),
        "reporte_tipo_usuario": normalizar_tipo_usuario(
            request.GET.get("reporte_tipo_usuario", "").strip()
        ),
        "reporte_fecha_desde": request.GET.get("reporte_fecha_desde", "").strip(),
        "incluir_ingresos": request.GET.get("incluir_ingresos", ""),
        "incluir_salidas": request.GET.get("incluir_salidas", ""),
        "generar_reporte": request.GET.get("generar_reporte", ""),
    }


def _checkbox_get(request, key, default=True):
    valor = request.GET.get(key)
    if valor is None:
        return default
    return valor == "1"


def obtener_config_columnas(request):
    return {
        "mostrar_nombre": _checkbox_get(request, "mostrar_nombre", True),
        "mostrar_apellido": _checkbox_get(request, "mostrar_apellido", True),
        "mostrar_cedula": _checkbox_get(request, "mostrar_cedula", True),
        "mostrar_telefono": _checkbox_get(request, "mostrar_telefono", True),
        "mostrar_email": _checkbox_get(request, "mostrar_email", True),
        "mostrar_direccion": _checkbox_get(request, "mostrar_direccion", False),
        "mostrar_vehiculo": _checkbox_get(request, "mostrar_vehiculo", False),
        "mostrar_pc": _checkbox_get(request, "mostrar_pc", False),
        "mostrar_estado": _checkbox_get(request, "mostrar_estado", True),
    }


def construir_datos_reporte(request, rol, base_qs=None):
    if base_qs is None:
        base_qs = get_role_queryset(rol)

    filtros_reporte = obtener_filtros_reporte(request)
    columnas_reporte = obtener_config_columnas(request)

    usuarios_reporte = base_qs

    if filtros_reporte["reporte_nombre"]:
        usuarios_reporte = usuarios_reporte.filter(
            nombre__icontains=filtros_reporte["reporte_nombre"]
        )
    if filtros_reporte["reporte_apellido"]:
        usuarios_reporte = usuarios_reporte.filter(
            apellido__icontains=filtros_reporte["reporte_apellido"]
        )
    if filtros_reporte["reporte_cedula"]:
        usuarios_reporte = usuarios_reporte.filter(
            cedula__icontains=filtros_reporte["reporte_cedula"]
        )
    if filtros_reporte["reporte_email"]:
        usuarios_reporte = usuarios_reporte.filter(
            email__icontains=filtros_reporte["reporte_email"]
        )
    if filtros_reporte["reporte_telefono"]:
        usuarios_reporte = usuarios_reporte.filter(
            telefono__icontains=filtros_reporte["reporte_telefono"]
        )
    if filtros_reporte["reporte_estado"] == "activos":
        usuarios_reporte = usuarios_reporte.filter(activo=True)
    elif filtros_reporte["reporte_estado"] == "inactivos":
        usuarios_reporte = usuarios_reporte.filter(activo=False)
    if filtros_reporte["reporte_genero"]:
        usuarios_reporte = usuarios_reporte.filter(
            genero=filtros_reporte["reporte_genero"]
        )
    if filtros_reporte["reporte_tipo_usuario"]:
        usuarios_reporte = usuarios_reporte.filter(
            tipo_usuario=filtros_reporte["reporte_tipo_usuario"]
        )

    usuario_reporte = None
    texto_periodo_reporte = "Reporte de movimientos"
    error_fecha_reporte = ""

    if filtros_reporte["reporte_cedula"]:
        usuario_reporte = Usuario.objects.filter(
            cedula=filtros_reporte["reporte_cedula"],
            subrol=rol,
        ).first()

    movimientos_reporte = Movimiento.objects.filter(usuario__subrol=rol)

    tipos = []
    if filtros_reporte["incluir_ingresos"] == "1":
        tipos.append("ingreso")
    if filtros_reporte["incluir_salidas"] == "1":
        tipos.append("salida")

    if tipos:
        movimientos_reporte = movimientos_reporte.filter(tipo__in=tipos)

    fecha_desde_obj = None
    if filtros_reporte["reporte_fecha_desde"]:
        fecha_desde_obj, error_fecha = parse_fecha(
            filtros_reporte["reporte_fecha_desde"],
            obligatoria=False,
        )
        if error_fecha:
            error_fecha_reporte = error_fecha
        elif fecha_desde_obj:
            movimientos_reporte = movimientos_reporte.filter(
                fecha__date__gte=fecha_desde_obj
            )
            texto_periodo_reporte = (
                f"Reportes desde la fecha: {fecha_desde_obj.strftime('%Y-%m-%d')}"
            )

    movimientos_reporte = movimientos_reporte.filter(usuario__in=usuarios_reporte)

    incluir_movimientos = (
        filtros_reporte["incluir_ingresos"] == "1"
        or filtros_reporte["incluir_salidas"] == "1"
        or bool(filtros_reporte["reporte_fecha_desde"])
    )

    if incluir_movimientos:
        usuarios_con_movimientos = movimientos_reporte.values_list("usuario_id", flat=True)
        usuarios_reporte = usuarios_reporte.filter(id__in=usuarios_con_movimientos).distinct()
        movimientos_reporte = movimientos_reporte.filter(usuario__in=usuarios_reporte)

    movimientos_reporte = movimientos_reporte.select_related(
        "usuario",
        "registrado_por",
    ).order_by("-fecha")

    return {
        "usuarios_reporte": usuarios_reporte,
        "filtros_reporte": filtros_reporte,
        "columnas_reporte": columnas_reporte,
        "movimientos_reporte": movimientos_reporte,
        "usuario_reporte": usuario_reporte,
        "texto_periodo_reporte": texto_periodo_reporte,
        "error_fecha_reporte": error_fecha_reporte,
        "reporte_generado": bool(filtros_reporte["generar_reporte"]),
        "incluir_movimientos": incluir_movimientos,
    }


def construir_datos_estadisticos(request, rol):
    usuarios = Usuario.objects.filter(subrol=rol)

    fecha_inicio_txt = request.GET.get("fecha_inicio", "").strip()
    fecha_fin_txt = request.GET.get("fecha_fin", "").strip()

    fecha_inicio = None
    fecha_fin = None
    error_fecha_estadistica = ""

    if fecha_inicio_txt:
        fecha_inicio, error_inicio = parse_fecha(fecha_inicio_txt)
        if error_inicio:
            error_fecha_estadistica = f"Fecha inicio inválida: {error_inicio}"
            fecha_inicio = None

    if fecha_fin_txt:
        fecha_fin, error_fin = parse_fecha(fecha_fin_txt)
        if error_fin:
            error_fecha_estadistica = f"Fecha fin inválida: {error_fin}"
            fecha_fin = None

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        error_fecha_estadistica = "La fecha inicial no puede ser mayor que la fecha final"
        fecha_inicio = None
        fecha_fin = None
        fecha_inicio_txt = ""
        fecha_fin_txt = ""

    movimientos_filtrados = Movimiento.objects.filter(usuario__in=usuarios)

    if fecha_inicio:
        movimientos_filtrados = movimientos_filtrados.filter(fecha__date__gte=fecha_inicio)
    if fecha_fin:
        movimientos_filtrados = movimientos_filtrados.filter(fecha__date__lte=fecha_fin)

    movimientos_filtrados = movimientos_filtrados.select_related("usuario")

    subquery_total_movimientos = (
        Movimiento.objects.filter(usuario=OuterRef("pk"))
        .values("usuario")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )

    usuarios_con_total = usuarios.annotate(
        total_movimientos=Coalesce(
            Subquery(subquery_total_movimientos, output_field=IntegerField()),
            Value(0),
        )
    )

    total_usuarios = usuarios.count()
    total_movimientos = movimientos_filtrados.count()
    total_ingresos = movimientos_filtrados.filter(tipo="ingreso").count()
    total_salidas = movimientos_filtrados.filter(tipo="salida").count()

    ingresos_por_dia = list(
        movimientos_filtrados.filter(tipo="ingreso")
        .annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(total=Count("id"))
        .order_by("dia")
    )

    salidas_por_dia = list(
        movimientos_filtrados.filter(tipo="salida")
        .annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(total=Count("id"))
        .order_by("dia")
    )

    horas_pico = list(
        movimientos_filtrados.annotate(hora=ExtractHour("fecha"))
        .values("hora")
        .annotate(total=Count("id"))
        .order_by("-total", "hora")[:5]
    )

    usuarios_frecuentes = usuarios_con_total.order_by(
        "-total_movimientos", "nombre", "apellido"
    )[:5]

    usuarios_menos = usuarios_con_total.order_by(
        "total_movimientos", "nombre", "apellido"
    )[:5]

    usuarios_sin_movimientos = usuarios_con_total.filter(total_movimientos=0).count()

    ultimo_movimiento_usuario = (
        Movimiento.objects.filter(usuario=OuterRef("pk"))
        .order_by("-fecha")
    )

    dentro = usuarios.annotate(
        ultimo_tipo=Subquery(ultimo_movimiento_usuario.values("tipo")[:1]),
        ultima_fecha=Subquery(ultimo_movimiento_usuario.values("fecha")[:1]),
    ).filter(
        ultimo_tipo="ingreso"
    ).order_by("nombre", "apellido")

    total_dentro = dentro.count()

    hoy = date.today()
    iso = hoy.isocalendar()

    movimientos_base = Movimiento.objects.filter(usuario__in=usuarios)

    conteo_hoy = movimientos_base.filter(fecha__date=hoy).count()
    conteo_semana = movimientos_base.filter(
        fecha__week=iso.week,
        fecha__year=iso.year,
    ).count()
    conteo_mes = movimientos_base.filter(
        fecha__month=hoy.month,
        fecha__year=hoy.year,
    ).count()

    promedio_ingresos_dia = 0
    if ingresos_por_dia:
        promedio_ingresos_dia = round(
            sum(item["total"] for item in ingresos_por_dia) / len(ingresos_por_dia),
            2,
        )

    movimientos_por_dia = list(
        movimientos_filtrados.annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(total=Count("id"))
        .order_by("dia")
    )

    promedio_movimientos_dia = 0
    if movimientos_por_dia:
        promedio_movimientos_dia = round(
            sum(item["total"] for item in movimientos_por_dia) / len(movimientos_por_dia),
            2,
        )

    distribucion_genero = list(
        usuarios.values("genero")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    distribucion_tipo_usuario = list(
        usuarios.values("tipo_usuario")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    ultimos_movimientos = (
        movimientos_base.select_related("usuario", "registrado_por")
        .order_by("-fecha")[:10]
    )

    estadistico_generado = bool(
        fecha_inicio_txt or fecha_fin_txt or request.GET.get("generar_estadistico")
    )

    return {
        "fecha_inicio": fecha_inicio_txt,
        "fecha_fin": fecha_fin_txt,
        "error_fecha_estadistica": error_fecha_estadistica,
        "estadistico_generado": estadistico_generado,

        "total_usuarios": total_usuarios,
        "total_movimientos": total_movimientos,
        "total_ingresos": total_ingresos,
        "total_salidas": total_salidas,
        "total_dentro": total_dentro,
        "usuarios_sin_movimientos": usuarios_sin_movimientos,

        "conteo_hoy": conteo_hoy,
        "conteo_semana": conteo_semana,
        "conteo_mes": conteo_mes,

        "promedio_ingresos_dia": promedio_ingresos_dia,
        "promedio_movimientos_dia": promedio_movimientos_dia,

        "ingresos_por_dia": ingresos_por_dia,
        "salidas_por_dia": salidas_por_dia,
        "horas_pico": horas_pico,

        "usuarios_frecuentes": usuarios_frecuentes,
        "usuarios_menos": usuarios_menos,
        "dentro": dentro,

        "distribucion_genero": distribucion_genero,
        "distribucion_tipo_usuario": distribucion_tipo_usuario,
        "ultimos_movimientos": ultimos_movimientos,
    }


# =========================================================
# VISTAS PÚBLICAS
# =========================================================
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


# =========================================================
# PANEL ADMIN
# =========================================================
@login_required
def index2(request):
    if request.user.rol != "admin":
        messages.error(request, "No tienes acceso al panel de administrador")
        return redirigir_por_rol(request.user)

    cedula = request.GET.get("cedula", "").strip()
    nombre = request.GET.get("nombre", "").strip()
    apellido = request.GET.get("apellido", "").strip()
    subrol_filtro = request.GET.get("subrol", "").strip()
    tipo_usuario = normalizar_tipo_usuario(request.GET.get("tipo_usuario", "").strip())
    genero = normalizar_genero(request.GET.get("genero", "").strip())

    usuarios = Usuario.objects.all().order_by("nombre", "apellido")

    if cedula:
        usuarios = usuarios.filter(cedula__icontains=cedula)
    if nombre:
        usuarios = usuarios.filter(nombre__icontains=nombre)
    if apellido:
        usuarios = usuarios.filter(apellido__icontains=apellido)
    if subrol_filtro:
        usuarios = usuarios.filter(subrol=subrol_filtro)
    if tipo_usuario:
        usuarios = usuarios.filter(tipo_usuario=tipo_usuario)
    if genero:
        usuarios = usuarios.filter(genero=genero)

    secciones = []
    for subrol in ROLES_VALIDOS:
        usuarios_subrol = usuarios.filter(subrol=subrol)
        if usuarios_subrol.exists():
            secciones.append(
                {
                    "titulo": TITULOS_ROL.get(subrol, subrol.title()),
                    "usuarios": usuarios_subrol,
                    "rol": subrol,
                }
            )

    paginator = Paginator(secciones, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "cedula": cedula,
        "nombre": nombre,
        "apellido": apellido,
        "subrol_filtro": subrol_filtro,
        "tipo_usuario": tipo_usuario,
        "genero": genero,
        "roles_validos": ROLES_VALIDOS,
    }

    return render(request, "index2.html", context)


# =========================================================
# REGISTRO INTERNO
# =========================================================
@login_required
def register_view(request):
    if request.user.rol != "admin":
        messages.error(
            request, "Solo el administrador puede registrar usuarios del sistema"
        )
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

    return render(request, "auth/register.html")


# =========================================================
# FORMULARIO PÚBLICO DE VISITAS
# =========================================================
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
                    request, "Debes ingresar los últimos 4 caracteres del serial del PC"
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


# =========================
# PANEL VIGILANTE
# =========================
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

    if request.method == "POST":
        formulario = request.POST.get("formulario", "consulta").strip()

        if formulario == "consulta":
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

            errors = {}

            context.update({
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
            })

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
                    errors["cedula"] = (
                        f"No existe un {ROL_SINGULAR.get(rol, rol)} activo con esa cédula"
                    )

            if not errors:
                ultimo_movimiento = (
                    Movimiento.objects.filter(usuario=usuario)
                    .order_by("-fecha")
                    .first()
                )

                if ultimo_movimiento and ultimo_movimiento.tipo == tipo:
                    errors["tipo"] = (
                        f"No puedes registrar dos {tipo}s consecutivos para este usuario"
                    )

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

            context.update({
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
            })
            return render(request, f"secciones/{rol}.html", context)

        elif formulario == "registro":
            context["mostrar_form_registro"] = True
            context["mostrar_form_consulta"] = False
            return render(request, f"secciones/{rol}.html", context)

    return render(request, f"secciones/{rol}.html", context)


# =========================
# CRUD ADMIN
# =========================
@login_required
def role_index(request, rol):
    if not validar_admin(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "El rol solicitado no es válido")
        return redirect("index2")

    base_qs = get_role_queryset(rol)

    buscar_nombre = request.GET.get("buscar_nombre", "").strip()
    buscar_cedula = request.GET.get("buscar_cedula", "").strip()

    usuarios_filtrados = base_qs
    if buscar_nombre:
        usuarios_filtrados = usuarios_filtrados.filter(nombre__icontains=buscar_nombre)
    if buscar_cedula:
        usuarios_filtrados = usuarios_filtrados.filter(cedula__icontains=buscar_cedula)

    filtros_busqueda = {
        "buscar_nombre": buscar_nombre,
        "buscar_cedula": buscar_cedula,
    }

    datos_reporte = construir_datos_reporte(request, rol, base_qs)
    datos_estadisticos = construir_datos_estadisticos(request, rol)

    paginator = Paginator(usuarios_filtrados, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = get_role_context(
        rol,
        {
            "usuarios": page_obj,
            "page_obj": page_obj,
            "filtros_busqueda": filtros_busqueda,
            **datos_reporte,
            **datos_estadisticos,
        },
    )

    return render(request, f"crud/{rol}/index.html", context)


@login_required
def role_report_pdf(request, rol):
    if not validar_admin(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "El rol solicitado no es válido")
        return redirect("index2")

    base_qs = get_role_queryset(rol)
    datos_reporte = construir_datos_reporte(request, rol, base_qs)

    filtros_reporte = datos_reporte["filtros_reporte"]
    columnas_reporte = datos_reporte["columnas_reporte"]
    usuarios_reporte = datos_reporte["usuarios_reporte"]
    movimientos_reporte = datos_reporte["movimientos_reporte"]
    usuario_reporte = datos_reporte["usuario_reporte"]
    texto_periodo_reporte = datos_reporte["texto_periodo_reporte"]
    incluir_movimientos = datos_reporte["incluir_movimientos"]

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="reporte_{rol}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = construir_styles_pdf()
    elements = []

    elements.append(
        Paragraph(
            f"Reporte de {TITULOS_ROL.get(rol, rol.title())}",
            styles["TituloCustom"],
        )
    )
    elements.append(
        Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["SubtituloCustom"],
        )
    )
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(construir_tabla_resumen_filtros(filtros_reporte))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(
        Paragraph(
            f"<b>Total de registros encontrados:</b> {usuarios_reporte.count()}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.35 * cm))
    elements.append(construir_tabla_usuarios_reporte(usuarios_reporte, columnas_reporte))

    if incluir_movimientos:
        elements.append(Spacer(1, 0.7 * cm))
        elements.append(Paragraph("Movimientos encontrados", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * cm))

        if usuario_reporte:
            elements.append(
                Paragraph(
                    f"<b>Usuario:</b> {usuario_reporte.nombre_completo}<br/>"
                    f"<b>Cédula:</b> {usuario_reporte.cedula}<br/>"
                    f"<b>Período:</b> {texto_periodo_reporte}",
                    styles["Normal"],
                )
            )
        else:
            elements.append(
                Paragraph(
                    f"<b>Período:</b> {texto_periodo_reporte}",
                    styles["Normal"],
                )
            )

        elements.append(Spacer(1, 0.3 * cm))
        elements.append(construir_tabla_movimientos(movimientos_reporte))

    doc.build(elements)
    return response


@login_required
def role_stats_pdf(request, rol):
    if not validar_admin(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "El rol solicitado no es válido")
        return redirect("index2")

    datos = construir_datos_estadisticos(request, rol)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="reporte_estadistico_{rol}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = construir_styles_pdf()
    elements = []

    elements.append(
        Paragraph(
            f"Reporte estadístico de {TITULOS_ROL.get(rol, rol.title())}",
            styles["TituloCustom"],
        )
    )
    elements.append(
        Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["SubtituloCustom"],
        )
    )
    elements.append(Spacer(1, 0.3 * cm))

    periodo = [
        ["Fecha inicio", datos["fecha_inicio"] or "Sin filtro"],
        ["Fecha fin", datos["fecha_fin"] or "Sin filtro"],
    ]
    tabla_periodo = Table(periodo, colWidths=[5 * cm, 8 * cm])
    tabla_periodo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(tabla_periodo)
    elements.append(Spacer(1, 0.4 * cm))

    resumen = [
        ["Total usuarios", str(datos["total_usuarios"]), "Total movimientos", str(datos["total_movimientos"])],
        ["Ingresos", str(datos["total_ingresos"]), "Salidas", str(datos["total_salidas"])],
        ["Dentro actualmente", str(datos["total_dentro"]), "Sin movimientos", str(datos["usuarios_sin_movimientos"])],
        ["Conteo hoy", str(datos["conteo_hoy"]), "Conteo semana", str(datos["conteo_semana"])],
        ["Conteo mes", str(datos["conteo_mes"]), "Prom. ingresos/día", str(datos["promedio_ingresos_dia"])],
        ["Prom. movimientos/día", str(datos["promedio_movimientos_dia"]), "", ""],
    ]

    tabla_resumen = Table(resumen, colWidths=[4 * cm, 3 * cm, 4 * cm, 3 * cm])
    tabla_resumen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(tabla_resumen)
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("Horas pico", styles["Heading2"]))
    horas_data = [["Hora", "Total movimientos"]]
    for item in datos["horas_pico"]:
        horas_data.append([f'{item["hora"]}:00', str(item["total"])])
    if len(horas_data) == 1:
        horas_data.append(["Sin datos", "0"])

    tabla_horas = Table(horas_data, colWidths=[6 * cm, 6 * cm], repeatRows=1)
    tabla_horas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(tabla_horas)
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(Paragraph("Usuarios dentro actualmente", styles["Heading2"]))
    dentro_data = [["Nombre", "Cédula", "Último movimiento"]]
    for usuario in datos["dentro"]:
        dentro_data.append([
            usuario.nombre_completo,
            usuario.cedula,
            usuario.ultima_fecha.strftime("%Y-%m-%d %H:%M") if usuario.ultima_fecha else "-",
        ])
    if len(dentro_data) == 1:
        dentro_data.append(["No hay personas dentro", "", ""])

    tabla_dentro = Table(dentro_data, colWidths=[8 * cm, 5 * cm, 6 * cm], repeatRows=1)
    tabla_dentro.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(tabla_dentro)
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(Paragraph("Usuarios más frecuentes", styles["Heading2"]))
    freq_data = [["Nombre", "Cédula", "Total movimientos"]]
    for usuario in datos["usuarios_frecuentes"]:
        freq_data.append([
            usuario.nombre_completo,
            usuario.cedula,
            str(usuario.total_movimientos),
        ])
    if len(freq_data) == 1:
        freq_data.append(["Sin datos", "", "0"])

    tabla_freq = Table(freq_data, colWidths=[8 * cm, 5 * cm, 5 * cm], repeatRows=1)
    tabla_freq.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(tabla_freq)
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(Paragraph("Usuarios menos frecuentes", styles["Heading2"]))
    menos_data = [["Nombre", "Cédula", "Total movimientos"]]
    for usuario in datos["usuarios_menos"]:
        menos_data.append([
            usuario.nombre_completo,
            usuario.cedula,
            str(usuario.total_movimientos),
        ])
    if len(menos_data) == 1:
        menos_data.append(["Sin datos", "", "0"])

    tabla_menos = Table(menos_data, colWidths=[8 * cm, 5 * cm, 5 * cm], repeatRows=1)
    tabla_menos.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(tabla_menos)

    doc.build(elements)
    return response


@login_required
def role_create(request, rol):
    if not validar_admin(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "El rol solicitado no es válido")
        return redirect("index2")

    form_data = {}

    if request.method == "POST":
        form_data = extraer_form_data(request)

        error = validar_form_usuario(form_data, rol)
        if error:
            messages.error(request, error)
            return render(
                request,
                f"crud/{rol}/create.html",
                get_role_context(rol, {"form_data": form_data}),
            )

        nuevo_rol = "vigilante" if rol == "vigilantes" else "persona"

        crear_usuario_desde_form_data(
            form_data,
            rol_sistema=nuevo_rol,
            subrol=rol,
            registrado_por=request.user,
            activo=True,
        )

        messages.success(
            request,
            f"{ROL_SINGULAR.get(rol, rol).capitalize()} creado correctamente",
        )
        return redirect(f"{rol}.index")

    return render(
        request,
        f"crud/{rol}/create.html",
        get_role_context(rol, {"form_data": form_data}),
    )


@login_required
def role_edit(request, rol, user_id):
    if not validar_admin(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "El rol solicitado no es válido")
        return redirect("index2")

    usuario = get_object_or_404(Usuario, id=user_id, subrol=rol)

    if request.method == "POST":
        form_data = extraer_form_data(request)

        error = validar_form_usuario(form_data, rol, usuario_id=usuario.id)
        if error:
            messages.error(request, error)
            poblar_usuario_desde_form(usuario, form_data, rol)
            return render(
                request,
                f"crud/{rol}/edit.html",
                get_role_context(rol, {"usuario": usuario}),
            )

        poblar_usuario_desde_form(usuario, form_data, rol)
        usuario.save()

        messages.success(
            request,
            f"{ROL_SINGULAR.get(rol, rol).capitalize()} actualizado correctamente",
        )
        return redirect(f"{rol}.index")

    return render(
        request,
        f"crud/{rol}/edit.html",
        get_role_context(rol, {"usuario": usuario}),
    )


@login_required
@require_POST
def role_toggle_estado(request, rol, user_id, activar):
    if request.user.rol != "admin":
        return JsonResponse(
            {"success": False, "message": "No autorizado"},
            status=403,
        )

    if not validar_rol_valido(rol):
        return JsonResponse(
            {"success": False, "message": "Rol inválido"},
            status=400,
        )

    usuario = get_object_or_404(Usuario, id=user_id, subrol=rol)
    usuario.activo = activar
    usuario.save(update_fields=["activo"])

    toggle_url_name = f"{rol}.inactivar" if activar else f"{rol}.activar"

    return JsonResponse(
        {
            "success": True,
            "message": f"Registro {'activado' if activar else 'inactivado'} correctamente",
            "activo": usuario.activo,
            "toggle_url": reverse(toggle_url_name, args=[usuario.id]),
        }
    )


# =========================
# API DATOS DASHBOARD
# =========================
@login_required
def dashboard_data(request):
    hoy = date.today()

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


@login_required
def carga_masiva_view(request):
    if request.user.rol != "admin":
        messages.error(request, "Solo el administrador puede realizar cargas masivas")
        return redirigir_por_rol(request.user)

    if request.method == "POST":
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
                messages.error(
                    request, f"Faltan columnas obligatorias: {', '.join(faltantes)}"
                )
                return render(request, "carga_masiva.html")

            creados = 0
            actualizados = 0
            sin_cambios = 0
            errores = []

            for fila_num, fila in enumerate(reader, start=2):
                try:
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
                        "tipo_usuario": normalizar_tipo_usuario(
                            (fila.get("tipo_usuario") or "").strip()
                        ),
                        "codigo_vigilante": (fila.get("codigo_vigilante") or "").strip(),
                    }

                    tipo_persona = (fila.get("tipo_persona") or "").strip().lower()

                    error = validar_nombre(form_data["nombre"], "nombre", True)
                    if error:
                        raise ValueError(error)

                    error = validar_nombre(form_data["apellido"], "apellido", False)
                    if error:
                        raise ValueError(error)

                    error = validar_cedula(form_data["cedula"])
                    if error:
                        raise ValueError(error)

                    if form_data["email"]:
                        error = validar_email(form_data["email"], False)
                        if error:
                            raise ValueError(error)

                    if form_data["telefono"]:
                        error = validar_telefono(form_data["telefono"], False)
                        if error:
                            raise ValueError(error)

                    error = validar_genero(form_data["genero"], obligatorio=False)
                    if error:
                        raise ValueError(error)

                    error = validar_tipo_usuario(form_data["tipo_usuario"], obligatorio=False)
                    if error:
                        raise ValueError(error)

                    if not tipo_persona:
                        raise ValueError("La columna tipo_persona es obligatoria")

                    if tipo_persona not in ROLES_VALIDOS:
                        raise ValueError(f"Tipo de persona no válido: {tipo_persona}")

                    if form_data["fecha_nacimiento"]:
                        _, error = parse_fecha(
                            form_data["fecha_nacimiento"],
                            obligatoria=False,
                        )
                        if error:
                            raise ValueError("La fecha_nacimiento debe tener formato YYYY-MM-DD")

                    rol = "vigilante" if tipo_persona == "vigilantes" else "persona"

                    if rol == "vigilante" and not form_data["codigo_vigilante"]:
                        raise ValueError("El código del vigilante es obligatorio")

                    with transaction.atomic():
                        usuario_existente = Usuario.objects.filter(
                            cedula=form_data["cedula"]
                        ).first()

                        if form_data["email"]:
                            email_qs = Usuario.objects.filter(email=form_data["email"])
                            if usuario_existente:
                                email_qs = email_qs.exclude(id=usuario_existente.id)
                            if email_qs.exists():
                                raise ValueError("El correo ya está registrado en otro usuario")

                        if usuario_existente:
                            fecha_nueva, _ = parse_fecha(
                                form_data["fecha_nacimiento"],
                                obligatoria=False,
                            )

                            cambios = False

                            if (usuario_existente.nombre or "") != (form_data["nombre"] or ""):
                                cambios = True
                            elif (usuario_existente.apellido or "") != (form_data["apellido"] or ""):
                                cambios = True
                            elif (usuario_existente.email or "") != (form_data["email"] or ""):
                                cambios = True
                            elif (usuario_existente.telefono or "") != (form_data["telefono"] or ""):
                                cambios = True
                            elif (usuario_existente.direccion or "") != (form_data["direccion"] or ""):
                                cambios = True
                            elif (usuario_existente.genero or "") != (form_data["genero"] or ""):
                                cambios = True
                            elif usuario_existente.fecha_nacimiento != fecha_nueva:
                                cambios = True
                            elif (usuario_existente.cargo or "") != (form_data["cargo"] or ""):
                                cambios = True
                            elif (usuario_existente.tipo_usuario or "") != (form_data["tipo_usuario"] or ""):
                                cambios = True
                            elif (usuario_existente.rol or "") != rol:
                                cambios = True
                            elif (usuario_existente.subrol or "") != tipo_persona:
                                cambios = True
                            elif bool(usuario_existente.activo) is not True:
                                cambios = True
                            elif tipo_persona == "vigilantes" and (
                                (usuario_existente.codigo_vigilante or "") != (form_data["codigo_vigilante"] or "")
                            ):
                                cambios = True
                            elif tipo_persona != "vigilantes" and usuario_existente.codigo_vigilante:
                                cambios = True

                            if cambios:
                                poblar_usuario_desde_form(
                                    usuario_existente,
                                    form_data,
                                    tipo_persona,
                                )
                                usuario_existente.rol = rol
                                usuario_existente.subrol = tipo_persona
                                usuario_existente.registrado_por = request.user
                                usuario_existente.activo = True

                                if tipo_persona != "vigilantes":
                                    usuario_existente.codigo_vigilante = None

                                usuario_existente.save()
                                actualizados += 1
                            else:
                                sin_cambios += 1

                        else:
                            crear_usuario_desde_form_data(
                                form_data,
                                rol_sistema=rol,
                                subrol=tipo_persona,
                                registrado_por=request.user,
                                activo=True,
                            )
                            creados += 1

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

        except Exception as e:
            messages.error(request, f"Error procesando el archivo: {str(e)}")
            return render(request, "carga_masiva.html")

    return render(request, "carga_masiva.html")