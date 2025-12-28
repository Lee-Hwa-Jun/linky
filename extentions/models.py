from django.db import models


class Extension(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=200)
    install_url = models.URLField()
    guide_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class Inquiry(models.Model):
    CATEGORY_CHOICES = [
        ("feature", "기능 추가 건의"),
        ("bug", "오류 문의"),
        ("usage", "사용방법 문의"),
        ("other", "기타"),
    ]

    extension = models.ForeignKey(
        Extension,
        on_delete=models.CASCADE,
        related_name="inquiries",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=120)
    content = models.TextField()
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.extension.name} - {self.title}"

    def masked_ip(self) -> str:
        if ":" in self.ip_address:
            parts = self.ip_address.split(":")
            if len(parts) > 2:
                return ":".join(parts[:2] + ["****", "****"])
            return "****:****"
        parts = self.ip_address.split(".")
        if len(parts) == 4:
            return ".".join([parts[0], parts[1], "***", "***"])
        return "***.***.***.***"
