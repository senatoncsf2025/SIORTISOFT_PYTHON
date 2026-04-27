from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .common import (
    TITULOS_ROL,
    redirigir_por_rol,
    validar_admin,
    validar_rol_valido,
)
from .report_data import construir_datos_estadisticos, construir_datos_reporte


# =========================================================
# HELPERS PDF
# =========================================================
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

    if not headers:
        return ["Información"], [["Información"], ["No seleccionaste columnas para mostrar"]]

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
            vehiculo = getattr(usuario, "vehiculo", None)
            row.append(vehiculo.placa if vehiculo else "-")

        if columnas_reporte["mostrar_pc"]:
            computador = getattr(usuario, "computador", None)
            row.append(computador.serial if computador else "-")

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

    mov_table = Table(
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


def construir_tabla_basica(
    data,
    col_widths,
    *,
    header_color=None,
    repeat_rows=0,
    bold_columns=None,
):
    if bold_columns is None:
        bold_columns = []

    table = Table(data, colWidths=col_widths, repeatRows=repeat_rows)

    style = [
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    if header_color:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    else:
        style.append(("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")))

    for col in bold_columns:
        style.append(("FONTNAME", (col, 0), (col, -1), "Helvetica-Bold"))

    table.setStyle(TableStyle(style))

    return table


# =========================================================
# PDF REPORTE NORMAL
# =========================================================
@login_required
def role_report_pdf(request, rol):
    if not validar_admin(request):
        return redirigir_por_rol(request.user)

    if not validar_rol_valido(rol):
        messages.error(request, "El rol solicitado no es válido")
        return redirect("index2")

    datos_reporte = construir_datos_reporte(request, rol)

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


# =========================================================
# PDF REPORTE ESTADÍSTICO
# =========================================================
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

    fecha_inicio_label = (
        datos["fecha_inicio_obj"].strftime("%Y-%m-%d")
        if datos.get("fecha_inicio_obj")
        else "Sin filtro"
    )

    fecha_fin_label = (
        datos["fecha_fin_obj"].strftime("%Y-%m-%d")
        if datos.get("fecha_fin_obj")
        else "Sin filtro"
    )

    periodo = [
        ["Fecha inicio", fecha_inicio_label],
        ["Fecha fin", fecha_fin_label],
    ]

    elements.append(
        construir_tabla_basica(
            periodo,
            [5 * cm, 8 * cm],
            bold_columns=[0],
        )
    )

    elements.append(Spacer(1, 0.4 * cm))

    if datos["error_fecha_estadistica"]:
        elements.append(
            Paragraph(
                f"<b>Observación:</b> {datos['error_fecha_estadistica']}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 0.3 * cm))

    resumen = [
        ["Total usuarios", str(datos["total_usuarios"]), "Total movimientos", str(datos["total_movimientos"])],
        ["Ingresos", str(datos["total_ingresos"]), "Salidas", str(datos["total_salidas"])],
        ["Dentro actualmente", str(datos["total_dentro"]), "Sin movimientos", str(datos["usuarios_sin_movimientos"])],
        ["Conteo hoy", str(datos["conteo_hoy"]), "Conteo semana", str(datos["conteo_semana"])],
        ["Conteo mes", str(datos["conteo_mes"]), "Prom. ingresos/día", str(datos["promedio_ingresos_dia"])],
        ["Prom. movimientos/día", str(datos["promedio_movimientos_dia"]), "", ""],
    ]

    elements.append(
        construir_tabla_basica(
            resumen,
            [4 * cm, 3 * cm, 4 * cm, 3 * cm],
            bold_columns=[0, 2],
        )
    )

    elements.append(Spacer(1, 0.5 * cm))

    if secciones["mostrar_conteos_actuales"]:
        elements.append(Paragraph("Conteos actuales", styles["Heading2"]))

        conteos_data = [
            ["Hoy", str(datos["conteo_hoy"])],
            ["Semana", str(datos["conteo_semana"])],
            ["Mes", str(datos["conteo_mes"])],
        ]

        elements.append(
            construir_tabla_basica(
                conteos_data,
                [6 * cm, 6 * cm],
                bold_columns=[0],
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_horas_pico"]:
        elements.append(Paragraph("Horas pico", styles["Heading2"]))

        horas_data = [["Hora", "Total movimientos"]]

        for item in datos["horas_pico"]:
            hora_label = f'{item["hora"]}:00' if item["hora"] is not None else "Sin hora"
            horas_data.append([hora_label, str(item["total"])])

        if len(horas_data) == 1:
            horas_data.append(["Sin datos", "0"])

        elements.append(
            construir_tabla_basica(
                horas_data,
                [6 * cm, 6 * cm],
                header_color="#334155",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_ingresos_por_dia"]:
        elements.append(Paragraph("Ingresos por día", styles["Heading2"]))

        ingresos_data = [["Fecha", "Total"]]

        for item in datos["ingresos_por_dia"]:
            fecha_dia = item["dia"].strftime("%Y-%m-%d") if item["dia"] else "Sin fecha"
            ingresos_data.append([fecha_dia, str(item["total"])])

        if len(ingresos_data) == 1:
            ingresos_data.append(["Sin datos", "0"])

        elements.append(
            construir_tabla_basica(
                ingresos_data,
                [6 * cm, 6 * cm],
                header_color="#0f766e",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_salidas_por_dia"]:
        elements.append(Paragraph("Salidas por día", styles["Heading2"]))

        salidas_data = [["Fecha", "Total"]]

        for item in datos["salidas_por_dia"]:
            fecha_dia = item["dia"].strftime("%Y-%m-%d") if item["dia"] else "Sin fecha"
            salidas_data.append([fecha_dia, str(item["total"])])

        if len(salidas_data) == 1:
            salidas_data.append(["Sin datos", "0"])

        elements.append(
            construir_tabla_basica(
                salidas_data,
                [6 * cm, 6 * cm],
                header_color="#92400e",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_dentro"]:
        elements.append(Paragraph("Usuarios dentro actualmente", styles["Heading2"]))

        dentro_data = [["Nombre", "Cédula", "Último movimiento"]]

        for usuario in datos["dentro"]:
            dentro_data.append(
                [
                    usuario.nombre_completo,
                    usuario.cedula,
                    usuario.ultima_fecha.strftime("%Y-%m-%d %H:%M") if usuario.ultima_fecha else "-",
                ]
            )

        if len(dentro_data) == 1:
            dentro_data.append(["No hay personas dentro", "", ""])

        elements.append(
            construir_tabla_basica(
                dentro_data,
                [8 * cm, 5 * cm, 6 * cm],
                header_color="#0f766e",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_usuarios_frecuentes"]:
        elements.append(Paragraph("Usuarios más frecuentes", styles["Heading2"]))

        freq_data = [["Nombre", "Cédula", "Total movimientos"]]

        for usuario in datos["usuarios_frecuentes"]:
            freq_data.append(
                [
                    usuario.nombre_completo,
                    usuario.cedula,
                    str(usuario.total_movimientos),
                ]
            )

        if len(freq_data) == 1:
            freq_data.append(["Sin datos", "", "0"])

        elements.append(
            construir_tabla_basica(
                freq_data,
                [8 * cm, 5 * cm, 5 * cm],
                header_color="#1d4ed8",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_usuarios_menos"]:
        elements.append(Paragraph("Usuarios menos frecuentes", styles["Heading2"]))

        menos_data = [["Nombre", "Cédula", "Total movimientos"]]

        for usuario in datos["usuarios_menos"]:
            menos_data.append(
                [
                    usuario.nombre_completo,
                    usuario.cedula,
                    str(usuario.total_movimientos),
                ]
            )

        if len(menos_data) == 1:
            menos_data.append(["Sin datos", "", "0"])

        elements.append(
            construir_tabla_basica(
                menos_data,
                [8 * cm, 5 * cm, 5 * cm],
                header_color="#7c3aed",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_distribucion_genero"]:
        elements.append(Paragraph("Distribución por género", styles["Heading2"]))

        genero_data = [["Género", "Total"]]

        for item in datos["distribucion_genero"]:
            genero_data.append([item["genero"] or "Sin definir", str(item["total"])])

        if len(genero_data) == 1:
            genero_data.append(["Sin datos", "0"])

        elements.append(
            construir_tabla_basica(
                genero_data,
                [8 * cm, 5 * cm],
                header_color="#475569",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_distribucion_tipo_usuario"]:
        elements.append(Paragraph("Distribución por tipo de usuario", styles["Heading2"]))

        tipo_data = [["Tipo usuario", "Total"]]

        for item in datos["distribucion_tipo_usuario"]:
            tipo_data.append([item["tipo_usuario"] or "Sin definir", str(item["total"])])

        if len(tipo_data) == 1:
            tipo_data.append(["Sin datos", "0"])

        elements.append(
            construir_tabla_basica(
                tipo_data,
                [8 * cm, 5 * cm],
                header_color="#334155",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_ultimos_movimientos"]:
        elements.append(Paragraph("Últimos movimientos", styles["Heading2"]))

        ultimos_data = [["Fecha", "Usuario", "Cédula", "Tipo", "Registrado por"]]

        for movimiento in datos["ultimos_movimientos"]:
            ultimos_data.append(
                [
                    movimiento.fecha.strftime("%Y-%m-%d %H:%M") if movimiento.fecha else "-",
                    movimiento.usuario.nombre_completo if movimiento.usuario else "-",
                    movimiento.usuario.cedula if movimiento.usuario else "-",
                    movimiento.tipo.capitalize() if movimiento.tipo else "-",
                    movimiento.registrado_por.nombre_completo if movimiento.registrado_por else "-",
                ]
            )

        if len(ultimos_data) == 1:
            ultimos_data.append(["Sin datos", "", "", "", ""])

        elements.append(
            construir_tabla_basica(
                ultimos_data,
                [4 * cm, 6 * cm, 4 * cm, 3 * cm, 6 * cm],
                header_color="#0f172a",
                repeat_rows=1,
            )
        )

        elements.append(Spacer(1, 0.4 * cm))

    if secciones["mostrar_comparacion"]:
        elements.append(Paragraph("Comparación de ayer vs hoy", styles["Heading2"]))

        comparacion_data = [
            ["Tipo", "Ayer", "Hoy", "Diferencia", "Porcentaje"],
            [
                "Ingresos",
                str(datos["ingresos_ayer"]),
                str(datos["ingresos_hoy"]),
                str(datos["dif_ingresos"]),
                f'{datos["porc_ingresos"]}%',
            ],
            [
                "Salidas",
                str(datos["salidas_ayer"]),
                str(datos["salidas_hoy"]),
                str(datos["dif_salidas"]),
                f'{datos["porc_salidas"]}%',
            ],
        ]

        elements.append(
            construir_tabla_basica(
                comparacion_data,
                [5 * cm, 4 * cm, 4 * cm, 4 * cm, 4 * cm],
                header_color="#0f172a",
                repeat_rows=1,
            )
        )

    doc.build(elements)
    return response