from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='replay-index'),
    path('<str:replay_id>/', views.analytics, name='replay-analytics'),
]
