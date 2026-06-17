from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from accounts.models import User


class RoleRequiredMixin:
    """Mixin that restricts access to views based on user role."""

    required_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if (
            self.required_roles
            and request.user.role not in self.required_roles
            and not request.user.is_superuser
        ):
            raise PermissionDenied("You do not have permission to access this page.")

        return super().dispatch(request, *args, **kwargs)


class SupervisorRequiredMixin(LoginRequiredMixin, RoleRequiredMixin):
    """Restrict view access to supervisor staff."""

    required_roles = (User.Role.SUPERVISOR,)


class ChefRequiredMixin(LoginRequiredMixin, RoleRequiredMixin):
    """Restrict view access to chef staff."""

    required_roles = (User.Role.CHEF,)


class WaiterRequiredMixin(LoginRequiredMixin, RoleRequiredMixin):
    """Restrict view access to waiter staff."""

    required_roles = (User.Role.WAITER,)
