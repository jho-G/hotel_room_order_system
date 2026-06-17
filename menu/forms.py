from django import forms

from menu.models import Category, MenuItem


class StaffFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = field.widget.attrs.get("class", "")
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = f"{css_class} form-check-input".strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = f"{css_class} form-select".strip()
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["class"] = f"{css_class} form-control".strip()
            else:
                field.widget.attrs["class"] = f"{css_class} form-control".strip()


class CategoryForm(StaffFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Main Course"}),
        }


class MenuItemForm(StaffFormMixin, forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ("category", "name", "description", "price", "image", "available")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }
