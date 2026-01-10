from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('<int:exam_id>/', views.take_exam, name='take_exam'),
]