from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/<int:user_id>/', views.chat, name='chat'),
]
