from django.urls import path
from . import views_media

urlpatterns = [
    path('compressed/', views_media.compression_callback, name='compression_callback'),
    path('upload/', views_media.create_multimedia, name='create_multimedia'),
    path('get-upload-url/', views_media.get_upload_url, name='get_upload_url'),
]