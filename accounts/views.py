from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from .models import User


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


@login_required
def post_login_redirect(request):
    """Redirect staff to their role-specific dashboard after login."""
    role_redirects = {
        User.Role.SUPERVISOR: "dashboard:supervisor",
        User.Role.CHEF: "dashboard:chef",
        User.Role.WAITER: "dashboard:waiter",
    }

    if request.user.role in role_redirects:
        return redirect(reverse(role_redirects[request.user.role]))

    if request.user.is_superuser:
        return redirect(reverse("admin:index"))

    return redirect(reverse("accounts:login"))
