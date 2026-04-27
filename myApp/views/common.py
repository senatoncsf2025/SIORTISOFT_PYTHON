import re
from datetime import date, datetime

from django.contrib import messages
from django.shortcuts import redirect

from ..models import Usuario


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
# HELPERS GENERALES
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


# =========================================================
# NORMALIZADORES
# =========================================================
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


# =========================================================
# VALIDACIONES
# =========================================================
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


# =========================================================
# FORMULARIOS USUARIO
# =========================================================
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
    context["generos"] = GENEROS
    context["tipos_usuario"] = TIPOS_USUARIO

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