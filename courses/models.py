from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Subject(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject')  # prevent duplicate enrollments

    def __str__(self):
        return f"{self.student.username} → {self.subject.title}"
    
# courses/models.py - Add these models
class CourseProgress(models.Model):
    """Track student progress in a course"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progress')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='progress_records')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progress')
    
    # Progress metrics
    assignments_completed = models.IntegerField(default=0)
    total_assignments = models.IntegerField(default=0)
    materials_viewed = models.IntegerField(default=0)
    total_materials = models.IntegerField(default=0)
    
    # Completion status
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Progress percentage (0-100)
    progress_percentage = models.IntegerField(default=0)
    
    # Last activity
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'subject')
    
    def __str__(self):
        return f"{self.student.username} - {self.subject.title} ({self.progress_percentage}%)"
    
    def calculate_progress(self):
        """Calculate progress percentage"""
        if self.total_assignments > 0:
            assignment_progress = (self.assignments_completed / self.total_assignments) * 100
        else:
            assignment_progress = 0
        
        if self.total_materials > 0:
            material_progress = (self.materials_viewed / self.total_materials) * 100
        else:
            material_progress = 0
        
        # Weighted average (70% assignments, 30% materials)
        self.progress_percentage = int((assignment_progress * 0.7) + (material_progress * 0.3))
        
        # Mark as completed if progress is 100%
        if self.progress_percentage >= 100 and not self.is_completed:
            self.is_completed = True
            self.completion_date = timezone.now()
        elif self.progress_percentage < 100 and self.is_completed:
            self.is_completed = False
            self.completion_date = None
        
        self.save()


class MaterialView(models.Model):
    """Track which materials a student has viewed"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='material_views')
    material = models.ForeignKey('notes.ClassMaterial', on_delete=models.CASCADE, related_name='views')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='material_tracking')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'material')
    
    def __str__(self):
        return f"{self.student.username} viewed {self.material.title}"

class AssignmentProgress(models.Model):
    """Detailed assignment progress tracking"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_progress')
    assignment = models.ForeignKey('notes.Assignment', on_delete=models.CASCADE, related_name='progress')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignment_tracking')
    
    # Status flags
    has_submitted = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    grade = models.FloatField(null=True, blank=True)
    
    # Pass/fail criteria
    is_passed = models.BooleanField(default=False)
    passing_grade = models.FloatField(default=50.0)  # Minimum grade to pass
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'assignment')
    
    def __str__(self):
        status = "Passed" if self.is_passed else "Failed" if self.is_graded else "Not Submitted"
        return f"{self.student.username} - {self.assignment.title} ({status})"
    
    def update_status(self):
        """Update pass/fail status based on grade"""
        if self.grade and self.grade >= self.passing_grade:
            self.is_passed = True
        else:
            self.is_passed = False
        self.save()
