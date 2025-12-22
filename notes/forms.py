from django import forms
from .models import Assignment, Submission, ClassMaterial

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['subject', 'title', 'description', 'due_date', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['answer', 'file', 'comment']
        widgets = {
            'answer': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your answer…'}),
        }
        labels = {
            'file': 'Upload File (optional)',
        }

class ClassMaterialForm(forms.ModelForm):
    class Meta:
        model = ClassMaterial
        fields = ['subject', 'title', 'description', 'file', 'video_url', 'external_link']
        
##### book forms #####
# notes/forms.py - Add this form
from django import forms
from .models import Book
from datetime import datetime

class BookForm(forms.ModelForm):
    """Form for adding/editing books"""
    
    class Meta:
        model = Book
        fields = [
            'subject', 'title', 'subtitle', 
            'author_first_name', 'author_last_name', 'additional_authors',
            'publication_year', 'edition', 'publisher',
            'isbn', 'url',
            'cover_image', 'pdf_file', 'description',
            'pages', 'language', 'is_required'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subtitle (optional)'
            }),
            'author_first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., John'
            }),
            'author_last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Smith'
            }),
            'additional_authors': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional authors, one per line:\nDoe, J.\nJohnson, K.'
            }),
            'publication_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': datetime.now().year + 1
            }),
            'edition': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Oxford University Press'
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 978-3-16-148410-0'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., https://example.com/book'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief description of the book'
            }),
            'pages': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'language': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., English, Spanish, French'
            }),
        }
        help_texts = {
            'additional_authors': 'Format: Lastname, F. (e.g., Smith, J.)',
            'publication_year': f'Year must be between 1900 and {datetime.now().year + 1}',
            'isbn': 'International Standard Book Number (optional)',
        }
    
    def clean_publication_year(self):
        year = self.cleaned_data['publication_year']
        current_year = datetime.now().year
        if year < 1900:
            raise forms.ValidationError('Publication year cannot be before 1900.')
        if year > current_year + 1:
            raise forms.ValidationError(f'Publication year cannot be in the future beyond {current_year + 1}.')
        return year
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and hasattr(self.user, 'role') and self.user.role == 'teacher':
            # Only show subjects taught by this teacher
            from courses.models import Subject
            self.fields['subject'].queryset = Subject.objects.filter(teacher=self.user)