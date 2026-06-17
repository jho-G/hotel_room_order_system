from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import SupervisorRequiredMixin
from rooms.forms import RoomForm
from rooms.models import Room


class RoomListView(SupervisorRequiredMixin, ListView):
    model = Room
    template_name = "rooms/room_list.html"
    context_object_name = "rooms"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Rooms"
        context["page_subtitle"] = "Manage room QR codes and in-room menu links"
        return context


class RoomCreateView(SupervisorRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("rooms:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Room"
        context["page_subtitle"] = "Create a room and generate its QR code automatically"
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Room {form.instance.room_number} created with QR code.",
        )
        return super().form_valid(form)


class RoomUpdateView(SupervisorRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("rooms:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Room {self.object.room_number}"
        context["page_subtitle"] = "Update room details"
        context["room"] = self.object
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Room {form.instance.room_number} updated.",
        )
        return super().form_valid(form)


class RoomDeactivateView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room.is_active = False
        room.save(update_fields=["is_active"])
        messages.success(request, f"Room {room.room_number} deactivated.")
        return redirect("rooms:list")


class RoomActivateView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room.is_active = True
        room.save(update_fields=["is_active"])
        messages.success(request, f"Room {room.room_number} activated.")
        return redirect("rooms:list")


class RoomDownloadQRView(SupervisorRequiredMixin, View):
    def get(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        if not room.qr_code:
            raise Http404("QR code not found for this room.")

        return FileResponse(
            room.qr_code.open("rb"),
            as_attachment=True,
            filename=f"room_{room.room_number}_qr.png",
            content_type="image/png",
        )
