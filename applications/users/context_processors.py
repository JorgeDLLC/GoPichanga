import logging
from .models import User

log = logging.getLogger(__name__)

def auth_session(request):
    uid = request.session.get("user_id")

    # Log de diagnóstico (verás esto en la consola del runserver)
    log.debug("[auth_session] uid=%s", uid)

    if not uid:
        return {"gp_is_auth": False, "gp_current_user": None, "gp_current_role": None}

    # No filtramos por 'estado' para evitar falsos negativos mientras pruebas.
    user = User.objects.filter(pk=uid).only("id", "nombre", "rol").first()

    # Más logs de diagnóstico
    log.debug("[auth_session] user_found=%s", bool(user))

    if not user:
        # si la sesión apunta a un id inexistente, seguimos marcando NO autenticado
        return {"gp_is_auth": False, "gp_current_user": None, "gp_current_role": None}

    return {
        "gp_is_auth": True,
        "gp_current_user": user,
        "gp_current_role": user.rol,
    }
