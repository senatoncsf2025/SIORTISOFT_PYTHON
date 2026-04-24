from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .common import (
    TITULOS_ROL,
    construir_styles_pdf,
    construir_tabla_movimientos,
    construir_tabla_resumen_filtros,
    construir_tabla_usuarios_reporte,
    get_role_queryset,
    redirigir_por_rol,
    validar_admin,
    validar_rol_valido,
)
from .report_data import construir_datos_estadisticos, construir_datos_reporte


@login_required
def role_report_pdf(request, rol):
    if not validar_admin(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "El rol solicitado no es válido")
        return redirect("index2")

    base_qs = get_role_queryset(rol)
    datos_reporte = construir_datos_reporte(request, rol, base_qs)

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

    elements.append(Paragraph(f"Reporte de {TITULOS_ROL.get(rol, rol.title())}", styles["TituloCustom"]))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["SubtituloCustom"]))
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(construir_tabla_resumen_filtros(datos_reporte["filtros_reporte"]))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(
        Paragraph(
            f"<b>Total de registros encontrados:</b> {datos_reporte['usuarios_reporte'].count()}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.35 * cm))
    elements.append(
        construir_tabla_usuarios_reporte(
            datos_reporte["usuarios_reporte"],
            datos_reporte["columnas_reporte"],
        )
    )

    if datos_reporte["incluir_movimientos"]:
        elements.append(Spacer(1, 0.7 * cm))
        elements.append(Paragraph("Movimientos encontrados", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * cm))

        usuario_reporte = datos_reporte["usuario_reporte"]

        if usuario_reporte:
            elements.append(
                Paragraph(
                    f"<b>Usuario:</b> {usuario_reporte.nombre_completo}<br/>"
                    f"<b>Cédula:</b> {usuario_reporte.cedula}<br/>"
                    f"<b>Período:</b> {datos_reporte['texto_periodo_reporte']}",
                    styles["Normal"],
                )
            )
        else:
            elements.append(
                Paragraph(
                    f"<b>Período:</b> {datos_reporte['texto_periodo_reporte']}",
                    styles["Normal"],
                )
            )

        elements.append(Spacer(1, 0.3 * cm))
        elements.append(construir_tabla_movimientos(datos_reporte["movimientos_reporte"]))

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
    secciones = datos["secciones_estadistico"]

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

    elements.append(Paragraph(f"Reporte estadístico de {TITULOS_ROL.get(rol, rol.title())}", styles["TituloCustom"]))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["SubtituloCustom"]))
    elements.append(Spacer(1, 0.3 * cm))

    fecha_inicio_label = datos["fecha_inicio_obj"].strftime("%Y-%m-%d") if datos.get("fecha_inicio_obj") else "Sin filtro"
    fecha_fin_label = datos["fecha_fin_obj"].strftime("%Y-%m-%d") if datos.get("fecha_fin_obj") else "Sin filtro"

    tabla_periodo = Table(
        [
            ["Fecha inicio", fecha_inicio_label],
            ["Fecha fin", fecha_fin_label],
        ],
        colWidths=[5 * cm, 8 * cm],
    )
    tabla_periodo.setStyle(_estilo_tabla_basica())
    elements.append(tabla_periodo)
    elements.append(Spacer(1, 0.4 * cm))

    if datos["error_fecha_estadistica"]:
        elements.append(Paragraph(f"<b>Observación:</b> {datos['error_fecha_estadistica']}", styles["Normal"]))
        elements.append(Spacer(1, 0.3 * cm))

    resumen = [
        ["Total usuarios", str(datos["total_usuarios"]), "Total movimientos", str(datos["total_movimientos"])],
        ["Ingresos", str(datos["total_ingresos"]), "Salidas", str(datos["total_salidas"])],
        ["Dentro actualmente", str(datos["total_dentro"]), "Sin movimientos", str(datos["usuarios_sin_movimientos"])],
        ["Conteo hoy", str(datos["conteo_hoy"]), "Conteo semana", str(datos["conteo_semana"])],
        ["Conteo mes", str(datos["conteo_mes"]), "Prom. ingresos/día", str(datos["promedio_ingresos_dia"])],
        ["Prom. movimientos/día", str(datos["promedio_movimientos_dia"]), "", ""],
    ]

    tabla_resumen = Table(resumen, colWidths=[4 * cm, 3 * cm, 4 * cm, 3 * cm])
    tabla_resumen.setStyle(_estilo_tabla_basica())
    elements.append(tabla_resumen)
    elements.append(Spacer(1, 0.5 * cm))

    if secciones["mostrar_conteos_actuales"]:
        elements.append(Paragraph("Conteos actuales", styles["Heading2"]))
        elements.append(_crear_tabla_simple([["Hoy", str(datos["conteo_hoy"])], ["Semana", str(datos["conteo_semana"])], ["Mes", str(datos["conteo_mes"])]], [6 * cm, 6 * cm]))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_horas_pico"]:
        data = [["Hora", "Total movimientos"]]
        for item in datos["horas_pico"]:
            data.append([f'{item["hora"]}:00' if item["hora"] is not None else "Sin hora", str(item["total"])])
        if len(data) == 1:
            data.append(["Sin datos", "0"])

        elements.append(Paragraph("Horas pico", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [6 * cm, 6 * cm], "#334155"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_ingresos_por_dia"]:
        data = [["Fecha", "Total"]]
        for item in datos["ingresos_por_dia"]:
            data.append([item["dia"].strftime("%Y-%m-%d") if item["dia"] else "Sin fecha", str(item["total"])])
        if len(data) == 1:
            data.append(["Sin datos", "0"])

        elements.append(Paragraph("Ingresos por día", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [6 * cm, 6 * cm], "#0f766e"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_salidas_por_dia"]:
        data = [["Fecha", "Total"]]
        for item in datos["salidas_por_dia"]:
            data.append([item["dia"].strftime("%Y-%m-%d") if item["dia"] else "Sin fecha", str(item["total"])])
        if len(data) == 1:
            data.append(["Sin datos", "0"])

        elements.append(Paragraph("Salidas por día", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [6 * cm, 6 * cm], "#92400e"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_dentro"]:
        data = [["Nombre", "Cédula", "Último movimiento"]]
        for usuario in datos["dentro"]:
            data.append(
                [
                    usuario.nombre_completo,
                    usuario.cedula,
                    usuario.ultima_fecha.strftime("%Y-%m-%d %H:%M") if usuario.ultima_fecha else "-",
                ]
            )
        if len(data) == 1:
            data.append(["No hay personas dentro", "", ""])

        elements.append(Paragraph("Usuarios dentro actualmente", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [8 * cm, 5 * cm, 6 * cm], "#0f766e"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_usuarios_frecuentes"]:
        data = [["Nombre", "Cédula", "Total movimientos"]]
        for usuario in datos["usuarios_frecuentes"]:
            data.append([usuario.nombre_completo, usuario.cedula, str(usuario.total_movimientos)])
        if len(data) == 1:
            data.append(["Sin datos", "", "0"])

        elements.append(Paragraph("Usuarios más frecuentes", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [8 * cm, 5 * cm, 5 * cm], "#1d4ed8"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_usuarios_menos"]:
        data = [["Nombre", "Cédula", "Total movimientos"]]
        for usuario in datos["usuarios_menos"]:
            data.append([usuario.nombre_completo, usuario.cedula, str(usuario.total_movimientos)])
        if len(data) == 1:
            data.append(["Sin datos", "", "0"])

        elements.append(Paragraph("Usuarios menos frecuentes", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [8 * cm, 5 * cm, 5 * cm], "#7c3aed"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_distribucion_genero"]:
        data = [["Género", "Total"]]
        for item in datos["distribucion_genero"]:
            data.append([item["genero"] or "Sin definir", str(item["total"])])
        if len(data) == 1:
            data.append(["Sin datos", "0"])

        elements.append(Paragraph("Distribución por género", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [8 * cm, 5 * cm], "#475569"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_distribucion_tipo_usuario"]:
        data = [["Tipo usuario", "Total"]]
        for item in datos["distribucion_tipo_usuario"]:
            data.append([item["tipo_usuario"] or "Sin definir", str(item["total"])])
        if len(data) == 1:
            data.append(["Sin datos", "0"])

        elements.append(Paragraph("Distribución por tipo de usuario", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [8 * cm, 5 * cm], "#334155"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_ultimos_movimientos"]:
        data = [["Fecha", "Usuario", "Cédula", "Tipo", "Registrado por"]]
        for movimiento in datos["ultimos_movimientos"]:
            data.append(
                [
                    movimiento.fecha.strftime("%Y-%m-%d %H:%M") if movimiento.fecha else "-",
                    movimiento.usuario.nombre_completo if movimiento.usuario else "-",
                    movimiento.usuario.cedula if movimiento.usuario else "-",
                    movimiento.tipo.capitalize() if movimiento.tipo else "-",
                    movimiento.registrado_por.nombre_completo if movimiento.registrado_por else "-",
                ]
            )
        if len(data) == 1:
            data.append(["Sin datos", "", "", "", ""])

        elements.append(Paragraph("Últimos movimientos", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [4 * cm, 6 * cm, 4 * cm, 3 * cm, 6 * cm], "#0f172a"))
        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_comparacion"]:
        data = [
            ["Tipo", "Ayer", "Hoy", "Diferencia", "Porcentaje"],
            ["Ingresos", str(datos["ingresos_ayer"]), str(datos["ingresos_hoy"]), str(datos["dif_ingresos"]), f'{datos["porc_ingresos"]}%'],
            ["Salidas", str(datos["salidas_ayer"]), str(datos["salidas_hoy"]), str(datos["dif_salidas"]), f'{datos["porc_salidas"]}%'],
        ]

        elements.append(Paragraph("Comparación de ayer vs hoy", styles["Heading2"]))
        elements.append(_crear_tabla_con_header(data, [5 * cm, 4 * cm, 4 * cm, 4 * cm, 4 * cm], "#0f172a"))

    doc.build(elements)
    return response


def _estilo_tabla_basica():
    return TableStyle(
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


def _crear_tabla_simple(data, col_widths):
    table = Table(data, colWidths=col_widths)
    table.setStyle(_estilo_tabla_basica())
    return table


def _crear_tabla_con_header(data, col_widths, color_header):
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(color_header)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table