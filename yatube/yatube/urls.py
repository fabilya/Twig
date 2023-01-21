from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

handler404 = 'core.views.page_not_found'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls', namespace='about')),
    path('', include('posts.urls', namespace='post')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )