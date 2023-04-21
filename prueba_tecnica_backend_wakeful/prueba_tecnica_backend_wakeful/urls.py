from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from users.views import landing

admin.autodiscover()


urlpatterns = [
    path("", landing, name="root"),
    path("admin/", admin.site.urls),
    re_path(r"^auth/", include("trench.urls"), name="mfa"),
    re_path(r"^auth/", include("trench.urls.jwt"), name="jwt_tokens"),
    path("users/", include("users.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
