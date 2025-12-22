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
    
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('books/<int:book_id>/delete/', views.delete_book, name='delete_book'),

]
