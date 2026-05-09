from django.urls import path
from . import views_media

urlpatterns = [
    path('compressed/', views_media.compression_callback, name='compression_callback'),
    path('upload/', views_media.create_multimedia, name='create_multimedia'),
]