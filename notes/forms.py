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