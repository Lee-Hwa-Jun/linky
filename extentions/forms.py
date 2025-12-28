from django import forms

from .models import Inquiry


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ("extension", "category", "title", "content")
        widgets = {
            "extension": forms.Select(attrs={"class": "text-black w-full rounded-lg border-gray-200"}),
            "category": forms.Select(attrs={"class": "text-black w-full rounded-lg border-gray-200"}),
            "title": forms.TextInput(attrs={"class": "text-black w-full rounded-lg border-gray-200"}),
            "content": forms.Textarea(
                attrs={"class": "text-black w-full rounded-lg border-gray-200", "rows": 5}
            ),
        }
