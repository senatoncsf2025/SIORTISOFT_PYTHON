from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .common import (
    ROLES_VALIDOS,
    ROL_SINGULAR,
    TITULOS_ROL,
    crear_usuario_desde_form_data,
    extraer_form_data,
    get_role_context,
    get_role_queryset,
    normalizar_genero,
    normalizar_tipo_usuario,
    poblar_usuario_desde_form,
    redirigir_por_rol,
    validar_admin,
    validar_form_usuario,
    validar_rol_valido,
)
from .report_data import construir_datos_estadisticos, construir_datos_reporte
from ..models import Usuario


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
# CRUD ADMIN
# =========================================================
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