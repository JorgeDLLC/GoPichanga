from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

def login_required_session(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect(f"{reverse('users:login')}?next={request.get_full_path()}")
        return view_func(request, *args, **kwargs)
    return _wrapped