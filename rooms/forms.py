from django import forms

from rooms.models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ("room_number",)
        widgets = {
            "room_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 101",
                }
            ),
        }
