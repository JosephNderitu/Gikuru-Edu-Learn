from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Assignment, Submission, ClassMaterial, Book
from django.db import models
from django.contrib import messages

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
    
# notes/admin.py book model admin
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin configuration for Book model"""
    
    # List display configuration
    list_display = [
        'title_preview', 
        'author_display', 
        'subject_display', 
        'teacher_display',
        'publication_year',
        'is_required_badge',
        'file_preview',
        'created_at_short'
    ]
    
    list_display_links = ['title_preview', 'author_display']
    
    # Filter options
    list_filter = [
        'is_required',
        'subject',
        'teacher',
        'publication_year',
        'language',
        'created_at'
    ]
    
    # Search configuration
    search_fields = [
        'title',
        'subtitle',
        'author_first_name',
        'author_last_name',
        'additional_authors',
        'description',
        'isbn',
        'publisher'
    ]
    
    # Fieldsets for detail view
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 
                'subtitle',
                ('author_first_name', 'author_last_name'),
                'additional_authors'
            ),
            'description': 'Enter the basic details of the book'
        }),
        ('Publication Details', {
            'fields': (
                ('publication_year', 'edition'),
                'publisher',
                'isbn',
                'url',
                ('pages', 'language')
            ),
            'description': 'Publication and identification information'
        }),
        ('Course Association', {
            'fields': (
                'subject',
                'teacher',
                'is_required'
            ),
            'description': 'Link this book to a course and teacher'
        }),
        ('Files & Media', {
            'fields': (
                'cover_image',
                'cover_image_preview',
                'pdf_file',
                'file_info'
            ),
            'description': 'Upload book files and cover image'
        }),
        ('Description', {
            'fields': ('description',),
            'description': 'Detailed description of the book'
        }),
        ('Metadata', {
            'fields': (
                ('created_at', 'updated_at'),
                'apa_citation'
            ),
            'description': 'Automatically generated metadata',
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = [
        'cover_image_preview',
        'file_info',
        'apa_citation',
        'created_at',
        'updated_at'
    ]
    
    # Date hierarchy
    date_hierarchy = 'created_at'
    
    # Actions
    actions = [
        'mark_as_required',
        'mark_as_recommended',
        'generate_citation_report'
    ]
    
    # Custom ordering
    ordering = ['-created_at']
    
    # Autocomplete fields
    autocomplete_fields = ['subject', 'teacher']
    
    # Custom list filters
    list_select_related = ['subject', 'teacher']
    
    # Items per page
    list_per_page = 25
    
    # Custom methods for list display
    def title_preview(self, obj):
        """Display shortened title with icon"""
        short_title = obj.get_short_title()
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<span style="margin-right: 8px;">📚</span>'
            '<span style="font-weight: 500;">{}</span>'
            '</div>',
            short_title
        )
    title_preview.short_description = 'Title'
    title_preview.admin_order_field = 'title'
    
    def author_display(self, obj):
        """Display author in Lastname, F. format"""
        return f"{obj.author_last_name}, {obj.author_first_name[0]}."
    author_display.short_description = 'Author'
    author_display.admin_order_field = 'author_last_name'
    
    def subject_display(self, obj):
        """Display subject with link"""
        url = reverse('admin:courses_subject_changelist')
        return format_html(
            '<a href="{}?q={}" style="color: #4F46E5;">{}</a>',
            url,
            obj.subject.id,
            obj.subject.title
        )
    subject_display.short_description = 'Subject'
    
    def teacher_display(self, obj):
        """Display teacher with email"""
        return format_html(
            '{}<br><small style="color: #6B7280;">{}</small>',
            obj.teacher.get_full_name() or obj.teacher.username,
            obj.teacher.email
        )
    teacher_display.short_description = 'Teacher'
    
    def is_required_badge(self, obj):
        """Display required status as badge"""
        if obj.is_required:
            return format_html(
                '<span style="background-color: #F59E0B; color: white; '
                'padding: 2px 8px; border-radius: 12px; font-size: 12px; '
                'font-weight: 500;">Required</span>'
            )
        return format_html(
            '<span style="background-color: #6B7280; color: white; '
            'padding: 2px 8px; border-radius: 12px; font-size: 12px; '
            'font-weight: 500;">Recommended</span>'
        )
    is_required_badge.short_description = 'Status'
    
    def file_preview(self, obj):
        """Display file information"""
        if obj.pdf_file:
            file_size = obj.get_file_size()
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<span style="margin-right: 4px;">📄</span>'
                '<span style="font-size: 12px; color: #6B7280;">{}</span>'
                '</div>',
                file_size
            )
        return format_html(
            '<span style="color: #9CA3AF; font-size: 12px;">No file</span>'
        )
    file_preview.short_description = 'File'
    
    def created_at_short(self, obj):
        """Display short date format"""
        return obj.created_at.strftime('%b %d, %Y')
    created_at_short.short_description = 'Added'
    created_at_short.admin_order_field = 'created_at'
    
    # Custom methods for detail view
    def cover_image_preview(self, obj):
        """Display cover image preview"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 300px; '
                'border-radius: 8px; border: 1px solid #E5E7EB;" />',
                obj.cover_image.url
            )
        return format_html(
            '<div style="width: 200px; height: 300px; background: #F3F4F6; '
            'display: flex; align-items: center; justify-content: center; '
            'border-radius: 8px; border: 1px dashed #D1D5DB;">'
            '<span style="color: #9CA3AF;">No cover image</span>'
            '</div>'
        )
    cover_image_preview.short_description = 'Cover Preview'
    
    def file_info(self, obj):
        """Display file information"""
        if obj.pdf_file:
            return format_html(
                '<div style="background: #F9FAFB; padding: 12px; border-radius: 6px;">'
                '<div style="display: flex; align-items: center; margin-bottom: 8px;">'
                '<span style="margin-right: 8px;">📄</span>'
                '<strong>PDF File:</strong>'
                '</div>'
                '<div style="margin-left: 24px;">'
                '<div>Size: {}</div>'
                '<div><a href="{}" target="_blank">Download PDF</a></div>'
                '</div>'
                '</div>',
                obj.get_file_size(),
                obj.pdf_file.url
            )
        return format_html(
            '<div style="color: #9CA3AF; font-style: italic;">No PDF file uploaded</div>'
        )
    file_info.short_description = 'File Information'
    
    def apa_citation(self, obj):
        """Display APA7 citation"""
        citation = obj.get_apa7_citation()
        return format_html(
            '<div style="background: #F0F9FF; padding: 16px; border-radius: 8px; '
            'border-left: 4px solid #3B82F6; font-family: monospace; '
            'white-space: pre-wrap; word-wrap: break-word;">'
            '<strong style="color: #1E40AF; margin-bottom: 8px; display: block;">'
            'APA7 Citation:</strong>'
            '{}'
            '</div>',
            citation
        )
    apa_citation.short_description = 'APA7 Citation'
    
    # Custom admin actions
    def mark_as_required(self, request, queryset):
        """Mark selected books as required reading"""
        updated = queryset.update(is_required=True)
        self.message_user(
            request,
            f'{updated} book(s) marked as required reading.',
            messages.SUCCESS
        )
    mark_as_required.short_description = "Mark selected books as required"
    
    def mark_as_recommended(self, request, queryset):
        """Mark selected books as recommended reading"""
        updated = queryset.update(is_required=False)
        self.message_user(
            request,
            f'{updated} book(s) marked as recommended reading.',
            messages.SUCCESS
        )
    mark_as_recommended.short_description = "Mark selected books as recommended"
    
    def generate_citation_report(self, request, queryset):
        """Generate citation report for selected books"""
        report_lines = []
        for book in queryset:
            citation = book.get_apa7_citation()
            report_lines.append(f"{book.title}:")
            report_lines.append(f"  {citation}")
            report_lines.append("")  # Empty line between books
        
        response_text = "\n".join(report_lines)
        
        # For simplicity, just show in message
        # In production, you might want to generate a downloadable file
        self.message_user(
            request,
            f'Generated citations for {queryset.count()} book(s). '
            f'Check the detailed view for each book.',
            messages.INFO
        )
        
        # You could also return a downloadable text file:
        # response = HttpResponse(response_text, content_type='text/plain')
        # response['Content-Disposition'] = 'attachment; filename="citations.txt"'
        # return response
    generate_citation_report.short_description = "Generate citation report"
    
    # Custom form configuration
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add custom help text
        form.base_fields['publication_year'].help_text = (
            'Year of publication (e.g., 2023). '
            'Future years beyond next year are not allowed.'
        )
        form.base_fields['isbn'].help_text = (
            '10 or 13 digit ISBN (International Standard Book Number). '
            'Hyphens and spaces will be removed during validation.'
        )
        form.base_fields['pdf_file'].help_text = (
            'Upload PDF file only. Maximum file size depends on server configuration.'
        )
        
        return form
    
    # Custom save method
    def save_model(self, request, obj, form, change):
        """Custom save logic"""
        if not change:  # If creating a new book
            # Auto-assign teacher if not set
            if not obj.teacher_id:
                obj.teacher = request.user
        
        # Run clean method to validate ISBN and publication year
        obj.full_clean()
        
        super().save_model(request, obj, form, change)
    
    # Custom changelist view
    def changelist_view(self, request, extra_context=None):
        """Add custom context to changelist"""
        extra_context = extra_context or {}
        extra_context['total_books'] = Book.objects.count()
        extra_context['required_books'] = Book.objects.filter(is_required=True).count()
        return super().changelist_view(request, extra_context=extra_context)
    
