from functools import wraps

from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Decorator that restricts view access to users with specific roles."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login

                return redirect_to_login(request.get_full_path())

            if request.user.role not in roles:
                raise PermissionDenied("You do not have permission to access this page.")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
