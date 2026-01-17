from django.urls import path
from .api_views import *

urlpatterns = [
    path('subjects/', subject_list_api, name='api_subjects'),
    path('student/assignments/', student_assignments_api, name='api_student_assignments'),
    path('student/enrollments/', student_enrollments_api, name='api_student_enrollments'),
    path('popular-courses/', popular_courses_api, name='api_popular_courses'),
    path('teacher/subjects/', teacher_subjects_api, name='api_teacher_subjects'),
]

