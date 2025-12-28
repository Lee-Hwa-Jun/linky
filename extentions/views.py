from django.utils import timezone
from django.views import View
from django.shortcuts import render

from .forms import InquiryForm
from .models import Extension, Inquiry


def _get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class ExtentionsHomeView(View):
    template_name = "extentions/index.html"

    def get(self, request):
        extensions = Extension.objects.all()
        inquiries = Inquiry.objects.select_related("extension")[:20]
        form = InquiryForm()
        return render(
            request,
            self.template_name,
            {
                "extensions": extensions,
                "inquiries": inquiries,
                "form": form,
            },
        )

    def post(self, request):
        extensions = Extension.objects.all()
        inquiries = Inquiry.objects.select_related("extension")[:20]
        form = InquiryForm(request.POST)
        error_message = None
        if form.is_valid():
            client_ip = _get_client_ip(request)
            today = timezone.localdate()
            already_submitted = Inquiry.objects.filter(
                ip_address=client_ip, created_at__date=today
            ).exists()
            if already_submitted:
                error_message = "하루에 1회만 문의를 남길 수 있어요."
            else:
                inquiry = form.save(commit=False)
                inquiry.ip_address = client_ip
                inquiry.save()
                form = InquiryForm()
        return render(
            request,
            self.template_name,
            {
                "extensions": extensions,
                "inquiries": inquiries,
                "form": form,
                "error_message": error_message,
            },
        )

# Create your views here.
