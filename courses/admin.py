from django.contrib import admin
from .models import Subject, Enrollment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'created_at')
    list_filter = ('created_at', 'teacher')
    search_fields = ('title', 'description', 'teacher__username')
    ordering = ('-created_at',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'date_enrolled')
    list_filter = ('date_enrolled', 'subject')
    search_fields = ('student__username', 'subject__title')
    ordering = ('-date_enrolled',)
