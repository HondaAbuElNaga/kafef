from django.urls import path
from . import views

urlpatterns = [
    # الصفحة الرئيسية (الجديدة)
    path('', views.home, name='home'),

    # مسار قائمة الامتحانات (نقلناه هنا)
    path('exams/', views.exam_list, name='exam_list'),
    path('exam/<int:exam_id>/', views.take_exam, name='take_exam'),

    # مسارات الدورات
    path('courses/', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('lesson/<int:lesson_id>/play/', views.lesson_player, name='lesson_player'),
]