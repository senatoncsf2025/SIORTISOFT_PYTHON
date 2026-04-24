import re
from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle

from ..models import Usuario


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
        "correo_url_name": f"{rol}.enviar_correo",
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
        from django.utils import timezone

        hoy = timezone.localdate()
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
        "tipo_usuario": normalizar_tipo_usuario(request.POST.get("tipo_usuario", "").strip()),
        "codigo_vigilante": request.POST.get("codigo_vigilante", "").strip(),
    }


def construir_contexto_registro_interno(request, extra=None):
    context = extraer_form_data(request)
    context["rol"] = request.POST.get("rol", "").strip()

    if extra:
        context.update(extra)

    return context


def validar_form_usuario(form_data, rol, usuario_id=None):
    for error in [
        validar_nombre(form_data["nombre"], "nombre", True),
        validar_nombre(form_data["apellido"], "apellido", False),
        validar_cedula(form_data["cedula"]),
        validar_email(form_data["email"], False),
        validar_telefono(form_data["telefono"], False),
        parse_fecha(form_data["fecha_nacimiento"], obligatoria=False)[1],
        validar_genero(form_data["genero"], obligatorio=False),
        validar_tipo_usuario(form_data["tipo_usuario"], obligatorio=False),
    ]:
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
    else:
        usuario.codigo_vigilante = None

    return usuario


def validar_form_registro_interno(form_data, rol_login, password, password2):
    for error in [
        validar_nombre(form_data["nombre"], "nombre", True),
        validar_nombre(form_data["apellido"], "apellido", False),
        validar_cedula(form_data["cedula"]),
        validar_email(form_data["email"], True),
        validar_telefono(form_data["telefono"], True),
        validar_genero(form_data["genero"], obligatorio=True),
        parse_fecha(
            form_data["fecha_nacimiento"],
            obligatoria=True,
            validar_mayoria_edad=True,
        )[1],
        validar_tipo_usuario(form_data["tipo_usuario"], obligatorio=True),
        validar_rol_login(rol_login),
        validar_password_registro(password, password2),
    ]:
        if error:
            return error

    if not form_data["direccion"]:
        return "La dirección es obligatoria"

    if rol_login == "vigilante" and not form_data["codigo_vigilante"]:
        return "El código del vigilante es obligatorio"

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
        codigo_vigilante=form_data["codigo_vigilante"] if subrol == "vigilantes" else None,
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


def construir_tabla_resumen_filtros(filtros_reporte):
    movimientos_label = "Todos"

    if filtros_reporte["incluir_ingresos"] == "1" and filtros_reporte["incluir_salidas"] == "1":
        movimientos_label = "Ingresos y salidas"
    elif filtros_reporte["incluir_ingresos"] == "1":
        movimientos_label = "Solo ingresos"
    elif filtros_reporte["incluir_salidas"] == "1":
        movimientos_label = "Solo salidas"

    resumen_filtros = [
        ["Nombre", filtros_reporte["reporte_nombre"] or "Todos", "Apellido", filtros_reporte["reporte_apellido"] or "Todos"],
        ["Cédula", filtros_reporte["reporte_cedula"] or "Todas", "Email", filtros_reporte["reporte_email"] or "Todos"],
        ["Teléfono", filtros_reporte["reporte_telefono"] or "Todos", "Estado", filtros_reporte["reporte_estado"] or "Todos"],
        ["Género", filtros_reporte["reporte_genero"] or "Todos", "Tipo usuario", filtros_reporte["reporte_tipo_usuario"] or "Todos"],
        ["Fecha desde", filtros_reporte["reporte_fecha_desde"] or "Sin filtro", "Movimientos", movimientos_label],
    ]

    table = Table(resumen_filtros, colWidths=[3 * cm, 7 * cm, 3 * cm, 7 * cm])
    table.setStyle(
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

    return table


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
        data.append(["No hay datos para el reporte"] + [""] * max(len(headers) - 1, 0))

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
    mov_data = [
        [
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
        ]
    ]

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

    table = Table(
        mov_data,
        colWidths=[
            2.8 * cm,
            3.6 * cm,
            2.4 * cm,
            2.1 * cm,
            1.8 * cm,
            2.4 * cm,
            1.5 * cm,
            2.5 * cm,
            5.8 * cm,
            3.1 * cm,
        ],
        repeatRows=1,
    )

    table.setStyle(
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

    return table