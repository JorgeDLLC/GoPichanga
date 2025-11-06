from .models import User

class GPAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        uid = request.session.get("user_id")
        user = User.objects.filter(pk=uid).only("id","nombre","rol").first() if uid else None
        request.gp_user = user
        request.gp_role = getattr(user, "rol", None)
        request.gp_is_auth = bool(user)
        return self.get_response(request)
