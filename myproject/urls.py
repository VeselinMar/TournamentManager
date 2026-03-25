from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("rest/", include("rest_framework.urls")),
    path('', include('tournamentapp.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('sponsors/', include('sponsors.urls')),
    path('', include('vendors.urls')),
    path('', include('programme.urls')),
    path('', include('announcements.urls')),
    path('api/', include([
        path('', include('tournamentapp.api.urls')),
        path('', include('vendors.api.urls')),
        path('', include('programme.api.urls')),
        path('', include('announcements.api.urls')),
    ])),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
