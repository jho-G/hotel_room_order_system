from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from accounts.mixins import SupervisorRequiredMixin
from menu.forms import CategoryForm, MenuItemForm
from menu.models import Category, MenuItem
from rooms.models import Room


class CustomerMenuView(View):
    """Customer-facing menu page linked via room QR code."""

    template_name = "menu/customer_menu.html"

    def get(self, request, token):
        room = get_object_or_404(Room, unique_token=token, is_active=True)
        categories = Category.objects.filter(items__available=True).distinct()
        menu_items = (
            MenuItem.objects.filter(available=True)
            .select_related("category")
            .order_by("category__name", "name")
        )

        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {
                "room": room,
                "room_number": room.room_number,
                "categories": categories,
                "menu_items": menu_items,
            },
        )


class CategoryListView(SupervisorRequiredMixin, ListView):
    model = Category
    template_name = "menu/category_list.html"
    context_object_name = "categories"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Menu Categories"
        context["page_subtitle"] = "Organize items by category"
        return context


class CategoryCreateView(SupervisorRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "menu/category_form.html"
    success_url = reverse_lazy("menu:category_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Category"
        context["page_subtitle"] = "Create a new menu category"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Category “{form.instance.name}” created.")
        return super().form_valid(form)


class CategoryUpdateView(SupervisorRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "menu/category_form.html"
    success_url = reverse_lazy("menu:category_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["page_subtitle"] = "Update category name"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Category “{form.instance.name}” updated.")
        return super().form_valid(form)


class CategoryDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        name = category.name
        if category.items.exists():
            messages.error(
                request,
                f"Cannot delete “{name}” while menu items are assigned to it.",
            )
            return redirect("menu:category_list")
        category.delete()
        messages.success(request, f"Category “{name}” deleted.")
        return redirect("menu:category_list")


class MenuItemListView(SupervisorRequiredMixin, ListView):
    model = MenuItem
    template_name = "menu/item_list.html"
    context_object_name = "items"

    def get_queryset(self):
        return MenuItem.objects.select_related("category").order_by(
            "category__name",
            "name",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Menu Items"
        context["page_subtitle"] = "Manage dishes, drinks, and availability"
        return context


class MenuItemCreateView(SupervisorRequiredMixin, CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "menu/item_form.html"
    success_url = reverse_lazy("menu:item_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Menu Item"
        context["page_subtitle"] = "Create a new dish or drink"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"“{form.instance.name}” added to the menu.")
        return super().form_valid(form)


class MenuItemUpdateView(SupervisorRequiredMixin, UpdateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "menu/item_form.html"
    success_url = reverse_lazy("menu:item_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["page_subtitle"] = "Update menu item details"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"“{form.instance.name}” updated.")
        return super().form_valid(form)


class MenuItemDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)
        name = item.name
        item.delete()
        messages.success(request, f"“{name}” removed from the menu.")
        return redirect("menu:item_list")


class MenuItemToggleAvailabilityView(SupervisorRequiredMixin, SingleObjectMixin, View):
    model = MenuItem

    def post(self, request, pk):
        item = self.get_object()
        item.available = not item.available
        item.save(update_fields=["available"])

        if request.headers.get("HX-Request"):
            return HttpResponse(
                f'<span class="badge availability-badge {"availability-on" if item.available else "availability-off"}">'
                f'{"Available" if item.available else "Unavailable"}</span>'
            )

        status = "available" if item.available else "unavailable"
        messages.success(request, f"“{item.name}” marked as {status}.")
        return redirect("menu:item_list")
