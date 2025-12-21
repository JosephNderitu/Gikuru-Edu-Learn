from django.db import models
from django.conf import settings
from courses.models import Subject

User = settings.AUTH_USER_MODEL

class Assignment(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_assignments')

    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()

    # Optional file from teacher (PDF, image, DOCX, etc.)
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject.title}"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_submissions')

    submitted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    comment = models.TextField(blank=True, null=True)  # NEW field for student comments
    answer = models.TextField(blank=True, null=True)

    # Teacher grading
    grade = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} → {self.assignment.title}"

class ClassMaterial(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="materials")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # OPTIONAL fields
    file = models.FileField(upload_to="materials/files/", blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
