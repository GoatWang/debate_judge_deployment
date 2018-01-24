from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path('download/(?P<filename>.+)/', views.download, name='download'),
    re_path('downloadsample/', views.downloadsample, name='downloadsample'),
]
