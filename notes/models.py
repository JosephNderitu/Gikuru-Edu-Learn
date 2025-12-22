from django.db import models
from django.conf import settings
from courses.models import Subject
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

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

### book models ###
class Book(models.Model):
    """Model for storing books with APA7 citation format"""
    
    # Basic information
    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    
    # APA7 Citation Fields
    author_first_name = models.CharField(max_length=200, help_text="Author's first name")
    author_last_name = models.CharField(max_length=200, help_text="Author's last name")
    
    # Optional additional authors (for multiple authors)
    additional_authors = models.TextField(
        blank=True, 
        null=True, 
        help_text="Additional authors (comma separated): Smith, J., Johnson, K."
    )
    
    # Publication details
    publication_year = models.PositiveIntegerField(
        help_text="Year of publication (e.g., 2023)"
    )
    
    edition = models.PositiveIntegerField(
        default=1,
        help_text="Edition number (e.g., 5 for 5th edition)"
    )
    
    publisher = models.CharField(max_length=500)
    
    # Identifiers
    isbn = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="ISBN (International Standard Book Number)"
    )
    
    
    
    url = models.URLField(
        blank=True, 
        null=True,
        help_text="Direct link to book if available online"
    )
    
    # Course association
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name="books",
        help_text="Course this book is assigned to"
    )
    
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="Teacher who added this book"
    )
    
    # Files
    cover_image = models.ImageField(
        upload_to='books/covers/', 
        blank=True, 
        null=True,
        help_text="Book cover image"
    )
    
    pdf_file = models.FileField(
        upload_to='books/pdfs/',
        validators=[FileExtensionValidator(['pdf'])],
        help_text="PDF version of the book (PDF only)"
    )
    
    # Description
    description = models.TextField(blank=True, null=True)
    
    # Metadata
    pages = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    
    # Status
    is_required = models.BooleanField(
        default=False,
        help_text="Is this book required reading?"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Book"
        verbose_name_plural = "Books"
    
    def __str__(self):
        return f"{self.title} - {self.author_last_name}"
    
    def clean(self):
        """Custom validation"""
        # Ensure publication year is not in the future
        from datetime import datetime
        current_year = datetime.now().year
        if self.publication_year > current_year + 1:  # Allow 1 year in future for pre-orders
            raise ValidationError(
                f'Publication year cannot be in the future. Current year is {current_year}.'
            )
        
        # Ensure ISBN format if provided
        if self.isbn:
            # Remove any hyphens or spaces
            isbn_clean = self.isbn.replace('-', '').replace(' ', '')
            if not (len(isbn_clean) == 10 or len(isbn_clean) == 13):
                raise ValidationError(
                    'ISBN must be 10 or 13 digits long.'
                )
            if not isbn_clean.isdigit():
                raise ValidationError(
                    'ISBN must contain only numbers.'
                )
    
    def get_apa7_citation(self):
        """Generate APA7 citation string"""
        # Format author name
        author = f"{self.author_last_name}, {self.author_first_name[0]}."
        
        # Add additional authors if any
        if self.additional_authors:
            authors = self.additional_authors.split(',')
            for author_name in authors:
                if author_name.strip():
                    # Assuming format "Lastname, F." or "Lastname, Firstname"
                    parts = author_name.strip().split(',')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()[0] if parts[1].strip() else ''
                        author += f", {last_name}, {first_name}."
        
        # Format title
        title = self.title
        if self.subtitle:
            title += f": {self.subtitle}"
        
        # Edition
        edition_text = ""
        if self.edition > 1:
            if self.edition == 2:
                edition_text = " (2nd ed.)"
            elif self.edition == 3:
                edition_text = " (3rd ed.)"
            else:
                edition_text = f" ({self.edition}th ed.)"
        
        # Publisher
        publisher_text = f"{self.publisher}."
        
        return f"{author} ({self.publication_year}). *{title}*{edition_text}. {publisher_text}"
    
    def get_short_title(self):
        """Get shortened title for display"""
        if len(self.title) > 50:
            return self.title[:47] + "..."
        return self.title
    
    def get_file_size(self):
        """Get human-readable file size"""
        if self.pdf_file:
            size_bytes = self.pdf_file.size
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        return "N/A"