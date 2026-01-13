from django.urls import path
from . import views

urlpatterns = [
    path('teacher/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/add/', views.add_subject, name='add_subject'),
    path('teacher/view/<int:subject_id>/', views.view_subject_teacher, name='view_subject'),
    path('teacher/edit/<int:subject_id>/', views.edit_subject_teacher, name='edit_subject'),
    path('teacher/delete/<int:subject_id>/', views.delete_subject_teacher, name='delete_subject'),
    
    # Student URLs
    path('student/', views.student_subject_list, name='student_subject_list'),
    path('student/enroll/<int:subject_id>/', views.enroll_subject, name='enroll_subject'),
    path('student/subject/<int:subject_id>/unenroll/', views.unenroll_subject, name='unenroll_subject'),
    path('student/subject/<int:subject_id>/view/', views.view_subject_student, name='view_subject_student'),
    path('popular-courses/', views.popular_courses_view, name='popular_courses_section'),
]
