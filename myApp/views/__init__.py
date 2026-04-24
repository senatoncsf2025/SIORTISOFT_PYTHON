from .auth_views import index, login_view, logout_view, register_view
from .public_views import registro_visita_view
from .dashboard_views import dashboard_view, seccion_view, dashboard_data
from .admin_views import index2, role_index, role_create, role_edit, role_toggle_estado
from .pdf_views import role_report_pdf, role_stats_pdf
from .bulk_upload_views import carga_masiva_view
from .email_views import enviar_correo