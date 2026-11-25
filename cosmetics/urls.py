from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve
admin.site.site_title = 'Luxe Beauty'
admin.site.index_title = 'Welcome to Luxe Beauty Admin Panel'
admin.site.site_header = 'Luxe Beauty'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('mainApp.urls') ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
