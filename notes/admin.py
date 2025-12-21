from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Assignment, Submission, ClassMaterial
from django.db import models  # Import models for submission_summary aggregation

class SubmissionInline(admin.TabularInline):
    """Inline admin for viewing submissions within an assignment"""
    model = Submission
    extra = 0
    readonly_fields = ('student', 'submitted_at', 'submission_preview', 'grade_status')
    fields = ('student', 'submitted_at', 'grade', 'submission_preview', 'grade_status')
    can_delete = False
    
    def submission_preview(self, obj):
        """Show preview of submission with link to full details"""
        if obj.pk:
            url = reverse('admin:notes_submission_change', args=[obj.pk])
            if obj.file:
                return format_html(
                    '<a href="{}" target="_blank">📎 View File</a> | '
                    '<a href="{}">Edit Submission</a>',
                    obj.file.url, url
                )
            elif obj.answer:
                preview = obj.answer[:50] + '...' if len(obj.answer) > 50 else obj.answer
                return format_html('<a href="{}">{}</a>', url, preview)
            return format_html('<a href="{}">View Details</a>', url)
        return '-'
    submission_preview.short_description = 'Submission'
    
    def grade_status(self, obj):
        """Visual indicator for grading status"""
        if obj.grade is not None:
            color = '#28a745' if obj.grade >= 70 else '#dc3545' if obj.grade < 50 else '#ffc107'
            return format_html(
                '<span style="color: {}; font-weight: bold;">✓ Graded</span>',
                color
            )
        return format_html('<span style="color: #6c757d;">⏳ Pending</span>')
    grade_status.short_description = 'Status'

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Assignment model"""
    
    list_display = ('title', 'subject_link', 'teacher', 'due_date', 'submission_count', 'created_at', 'status_badge')
    list_filter = ('subject', 'teacher', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'subject__title', 'teacher__username')
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at', 'submission_summary')
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('subject', 'teacher', 'title', 'description')
        }),
        ('Timeline', {
            'fields': ('due_date', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Attachments', {
            'fields': ('attachment',),
            'description': 'Optional: Upload reference materials (PDF, images, DOCX, etc.)'
        }),
        ('Submission Overview', {
            'fields': ('submission_summary',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SubmissionInline]
    
    def subject_link(self, obj):
        """Clickable link to the subject"""
        url = reverse('admin:courses_subject_change', args=[obj.subject.pk])
        return format_html('<a href="{}">{}</a>', url, obj.subject.title)
    subject_link.short_description = 'Subject'
    subject_link.admin_order_field = 'subject__title'
    
    def submission_count(self, obj):
        """Display count of submissions"""
        count = obj.submissions.count()
        graded = obj.submissions.filter(grade__isnull=False).count()
        return format_html(
            '<span style="font-weight: bold;">{}</span> '
            '<span style="color: #6c757d;">({} graded)</span>',
            count, graded
        )
    submission_count.short_description = 'Submissions'
    
    def status_badge(self, obj):
        """Visual badge for assignment status"""
        from django.utils import timezone
        now = timezone.now()
        
        if now > obj.due_date:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">OVERDUE</span>'
            )
        elif (obj.due_date - now).days <= 2:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">DUE SOON</span>'
            )
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">ACTIVE</span>'
        )
    status_badge.short_description = 'Status'
    
    def submission_summary(self, obj):
        """Detailed submission statistics"""
        if not obj.pk:
            return "Save assignment to view submission statistics"
            
        total = obj.submissions.count()
        graded = obj.submissions.filter(grade__isnull=False).count()
        pending = total - graded
        
        if total == 0:
            return mark_safe('<p style="color: #6c757d;">No submissions yet</p>')
        
        avg_grade = obj.submissions.filter(grade__isnull=False).aggregate(
            avg=models.Avg('grade')
        )['avg']
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h4 style="margin-top: 0;">Submission Statistics</h4>
            <ul style="list-style: none; padding: 0;">
                <li>📊 <strong>Total Submissions:</strong> {total}</li>
                <li>✅ <strong>Graded:</strong> {graded}</li>
                <li>⏳ <strong>Pending Review:</strong> {pending}</li>
                {f'<li>📈 <strong>Average Grade:</strong> {avg_grade:.2f}%</li>' if avg_grade else ''}
            </ul>
        </div>
        """
        return mark_safe(html)
    submission_summary.short_description = 'Statistics'

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Submission model"""
    
    list_display = ('student', 'assignment_link', 'submitted_at', 'grade_display', 'grading_status')
    list_filter = ('assignment__subject', 'submitted_at', 'grade')
    search_fields = ('student__username', 'assignment__title', 'comment', 'answer', 'feedback')
    date_hierarchy = 'submitted_at'
    readonly_fields = ('submitted_at', 'file_preview')
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('assignment', 'student', 'submitted_at')
        }),
        ('Student Submission', {
            'fields': ('file', 'file_preview', 'answer', 'comment'),
            'description': 'Content submitted by the student'
        }),
        ('Teacher Grading', {
            'fields': ('grade', 'feedback'),
            'classes': ('wide',),
            'description': 'Add grade (0-100) and feedback for the student'
        }),
    )
    
    def assignment_link(self, obj):
        """Clickable link to the assignment"""
        url = reverse('admin:notes_assignment_change', args=[obj.assignment.pk])
        return format_html('<a href="{}">{}</a>', url, obj.assignment.title)
    assignment_link.short_description = 'Assignment'
    assignment_link.admin_order_field = 'assignment__title'
    
    def grade_display(self, obj):
        """Formatted grade display"""
        if obj.grade is not None:
            color = '#28a745' if obj.grade >= 70 else '#dc3545' if obj.grade < 50 else '#ffc107'
            grade_value = f"{obj.grade:.1f}"
            return format_html(
                '<span style="color: {}; font-weight: bold; font-size: 14px;">{}%</span>',
                color, grade_value
            )
        return format_html('<span style="color: #6c757d;">Not graded</span>')
    grade_display.short_description = 'Grade'
    grade_display.admin_order_field = 'grade'
    
    def grading_status(self, obj):
        """Badge for grading status"""
        if obj.grade is not None and obj.feedback:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ COMPLETE</span>'
            )
        elif obj.grade is not None:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">⚠ NO FEEDBACK</span>'
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">⏳ PENDING</span>'
        )
    grading_status.short_description = 'Status'
    
    def file_preview(self, obj):
        """Preview or download link for submitted file"""
        if obj.file:
            file_url = obj.file.url
            file_name = obj.file.name.split('/')[-1]
            file_ext = file_name.split('.')[-1].lower()
            
            # Image preview
            if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                return format_html(
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width: 200px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;"/>'
                    '</a><br><small>{}</small>',
                    file_url, file_url, file_name
                )
            # File download link
            return format_html(
                '<a href="{}" target="_blank" style="padding: 5px 10px; background: #007bff; '
                'color: white; text-decoration: none; border-radius: 3px;">📥 Download {}</a>',
                file_url, file_name
            )
        return format_html('<span style="color: #6c757d;">No file attached</span>')
    file_preview.short_description = 'Submitted File'

@admin.register(ClassMaterial)
class ClassMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'teacher', 'created_at', 'has_file')
    list_filter = ('subject', 'teacher', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = 'File attached'