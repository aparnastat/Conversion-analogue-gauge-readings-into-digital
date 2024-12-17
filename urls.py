from django.contrib import admin
from django.urls import path
from gauge_app.views import landing_page, upload_video
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing_page'),  
    path('upload/', upload_video, name='upload_video'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
