from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from applications.users.models import UserRole, User

def partner_required_session(viewfunc):
    @wraps(viewfunc)
    def _wrapped(request, *args, **kwargs):
        uid = request.session.get('user_id')
        if not uid:
            return redirect(reverse('users:login'))
        try:
            u = User.objects.get(pk=uid, estado=True)
        except User.DoesNotExist:
            return redirect(reverse('users:login'))
        if u.rol != UserRole.PARTNER:
            # si no es partner lo envío al listado público
            return redirect(reverse('field:list'))
        request.gp_user = u
        return viewfunc(request, *args, **kwargs)
    return _wrapped
