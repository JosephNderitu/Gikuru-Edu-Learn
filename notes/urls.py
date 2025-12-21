from django.urls import path
from . import views

urlpatterns = [
    # TEACHER
    path('teacher/assignments/create/', views.create_assignment, name='create_assignment'),
    path('teacher/assignments/<int:pk>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('teacher/submission/<int:pk>/grade/', views.grade_submission, name='grade_submission'),

    # STUDENT
    path('student/assignments/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    
    # MATERIAL UPLOAD
    path("materials/upload/", views.upload_material, name="upload_material"),
    path('edit/<int:material_id>/', views.edit_material, name='edit_material'),
    path('delete/<int:material_id>/', views.delete_material, name='delete_material'),

]
