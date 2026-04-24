from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mass_mail
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .common import ROLES_VALIDOS
from ..models import Usuario


@login_required
@require_POST
def enviar_correo(request, tipo):
    if request.user.rol != "admin":
        return JsonResponse(
            {
                "success": False,
                "message": "No autorizado",
            },
            status=403,
        )

    if tipo not in ROLES_VALIDOS:
        return JsonResponse(
            {
                "success": False,
                "message": "Rol no válido",
            },
            status=400,
        )

    asunto = request.POST.get("asunto", "").strip()
    mensaje = request.POST.get("mensaje", "").strip()

    if not asunto or not mensaje:
        return JsonResponse(
            {
                "success": False,
                "message": "Debes completar asunto y mensaje",
            },
            status=400,
        )

    usuarios = (
        Usuario.objects.filter(subrol=tipo, activo=True)
        .exclude(email__isnull=True)
        .exclude(email="")
    )

    mensajes = [
        (
            asunto,
            f"Hola {usuario.nombre}\n\n{mensaje}",
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
        )
        for usuario in usuarios
    ]

    if not mensajes:
        return JsonResponse(
            {
                "success": False,
                "message": "No hay correos válidos",
            }
        )

    try:
        send_mass_mail(mensajes, fail_silently=False)
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Error enviando correos: {str(e)}",
            },
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "message": f"Se enviaron {len(mensajes)} correos",
        }
    )