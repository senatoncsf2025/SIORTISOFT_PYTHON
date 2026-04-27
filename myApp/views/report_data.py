from datetime import date, timedelta

from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce, ExtractHour, TruncDate
from django.utils import timezone

from .common import (
    get_role_queryset,
    normalizar_genero,
    normalizar_tipo_usuario,
    parse_fecha,
)
from ..models import Movimiento, Usuario


def obtener_filtros_reporte(request):
    return {
        "reporte_nombre": request.GET.get("reporte_nombre", "").strip(),
        "reporte_apellido": request.GET.get("reporte_apellido", "").strip(),
        "reporte_cedula": request.GET.get("reporte_cedula", "").strip(),
        "reporte_email": request.GET.get("reporte_email", "").strip(),
        "reporte_telefono": request.GET.get("reporte_telefono", "").strip(),
        "reporte_estado": request.GET.get("reporte_estado", "").strip(),
        "reporte_genero": normalizar_genero(
            request.GET.get("reporte_genero", "").strip()
        ),
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


def obtener_secciones_estadistico(request):
    return {
        "mostrar_conteos_actuales": _checkbox_get(request, "mostrar_conteos_actuales", False),
        "mostrar_horas_pico": _checkbox_get(request, "mostrar_horas_pico", False),
        "mostrar_ingresos_por_dia": _checkbox_get(request, "mostrar_ingresos_por_dia", False),
        "mostrar_salidas_por_dia": _checkbox_get(request, "mostrar_salidas_por_dia", False),
        "mostrar_usuarios_frecuentes": _checkbox_get(request, "mostrar_usuarios_frecuentes", False),
        "mostrar_usuarios_menos": _checkbox_get(request, "mostrar_usuarios_menos", False),
        "mostrar_dentro": _checkbox_get(request, "mostrar_dentro", False),
        "mostrar_distribucion_genero": _checkbox_get(request, "mostrar_distribucion_genero", False),
        "mostrar_distribucion_tipo_usuario": _checkbox_get(request, "mostrar_distribucion_tipo_usuario", False),
        "mostrar_ultimos_movimientos": _checkbox_get(request, "mostrar_ultimos_movimientos", False),
        "mostrar_comparacion": _checkbox_get(request, "mostrar_comparacion", False),
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

    movimientos_filtrados = movimientos_filtrados.select_related("usuario", "registrado_por")

    subquery_total_movimientos = Movimiento.objects.filter(usuario=OuterRef("pk"))

    if fecha_inicio:
        subquery_total_movimientos = subquery_total_movimientos.filter(fecha__date__gte=fecha_inicio)

    if fecha_fin:
        subquery_total_movimientos = subquery_total_movimientos.filter(fecha__date__lte=fecha_fin)

    subquery_total_movimientos = (
        subquery_total_movimientos
        .values("usuario")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )

    usuarios_con_total = usuarios.annotate(
        total_movimientos=Coalesce(
            Subquery(subquery_total_movimientos, output_field=IntegerField()),
            Value(0, output_field=IntegerField()),
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
        "-total_movimientos",
        "nombre",
        "apellido",
    )[:5]

    usuarios_menos = usuarios_con_total.order_by(
        "total_movimientos",
        "nombre",
        "apellido",
    )[:5]

    usuarios_sin_movimientos = usuarios_con_total.filter(total_movimientos=0).count()

    ultimo_movimiento_usuario = Movimiento.objects.filter(usuario=OuterRef("pk"))

    if fecha_inicio:
        ultimo_movimiento_usuario = ultimo_movimiento_usuario.filter(fecha__date__gte=fecha_inicio)

    if fecha_fin:
        ultimo_movimiento_usuario = ultimo_movimiento_usuario.filter(fecha__date__lte=fecha_fin)

    ultimo_movimiento_usuario = ultimo_movimiento_usuario.order_by("-fecha")

    dentro = (
        usuarios.annotate(
            ultimo_tipo=Subquery(ultimo_movimiento_usuario.values("tipo")[:1]),
            ultima_fecha=Subquery(ultimo_movimiento_usuario.values("fecha")[:1]),
        )
        .filter(ultimo_tipo="ingreso")
        .order_by("nombre", "apellido")
    )

    total_dentro = dentro.count()

    hoy = timezone.localdate()
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
        movimientos_filtrados.select_related("usuario", "registrado_por")
        .order_by("-fecha")[:10]
    )

    secciones_estadistico = obtener_secciones_estadistico(request)
    estadistico_generado = bool(request.GET.get("generar_estadistico"))

    hoy_local = timezone.localdate()
    ayer_local = hoy_local - timedelta(days=1)

    ingresos_hoy = Movimiento.objects.filter(
        usuario__in=usuarios,
        fecha__date=hoy_local,
        tipo="ingreso",
    ).count()

    ingresos_ayer = Movimiento.objects.filter(
        usuario__in=usuarios,
        fecha__date=ayer_local,
        tipo="ingreso",
    ).count()

    salidas_hoy = Movimiento.objects.filter(
        usuario__in=usuarios,
        fecha__date=hoy_local,
        tipo="salida",
    ).count()

    salidas_ayer = Movimiento.objects.filter(
        usuario__in=usuarios,
        fecha__date=ayer_local,
        tipo="salida",
    ).count()

    dif_ingresos = ingresos_hoy - ingresos_ayer
    dif_salidas = salidas_hoy - salidas_ayer

    def calcular_porcentaje(actual, anterior):
        if anterior == 0:
            return 100 if actual > 0 else 0

        return round(((actual - anterior) / anterior) * 100, 2)

    porc_ingresos = calcular_porcentaje(ingresos_hoy, ingresos_ayer)
    porc_salidas = calcular_porcentaje(salidas_hoy, salidas_ayer)

    return {
        "fecha_inicio": fecha_inicio_txt,
        "fecha_fin": fecha_fin_txt,
        "fecha_inicio_obj": fecha_inicio,
        "fecha_fin_obj": fecha_fin,
        "error_fecha_estadistica": error_fecha_estadistica,
        "estadistico_generado": estadistico_generado,
        "secciones_estadistico": secciones_estadistico,
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
        "ingresos_hoy": ingresos_hoy,
        "ingresos_ayer": ingresos_ayer,
        "salidas_hoy": salidas_hoy,
        "salidas_ayer": salidas_ayer,
        "dif_ingresos": dif_ingresos,
        "dif_salidas": dif_salidas,
        "porc_ingresos": porc_ingresos,
        "porc_salidas": porc_salidas,
    }