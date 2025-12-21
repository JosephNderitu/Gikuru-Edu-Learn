from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import UserRegisterForm, TeacherProfileForm, StudentProfileForm
from django.contrib.auth.decorators import login_required
from courses.models import Subject, Enrollment
from notes.models import Assignment, Submission
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 
import json

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_view(request):
    user = request.user

    # Admin → Django admin
    if user.is_superuser or user.role == 'admin':
        return redirect('/admin/')

    # Teacher Dashboard
    elif user.role == 'teacher':
        subjects = Subject.objects.filter(teacher=user)
        subjects_list = Subject.objects.filter(teacher=request.user).order_by('-created_at')
        
        # Pagination - 6 subjects per page
        paginator = Paginator(subjects_list, 5)
        page = request.GET.get('page')
        
        try:
            subjects = paginator.page(page)
        except PageNotAnInteger:
            subjects = paginator.page(1)
        except EmptyPage:
            subjects = paginator.page(paginator.num_pages)

        total_enrollments = Enrollment.objects.filter(
            subject__teacher=user
        ).count()

        return render(request, 'accounts/teacher_dashboard.html', {
            'subjects': subjects,
            'total_enrollments': total_enrollments,
        })

    # Student Dashboard
    else:
        # Get enrolled subjects with pagination
        enrollments_list = Enrollment.objects.filter(student=user).select_related('subject').order_by('-date_enrolled')
        
        paginator = Paginator(enrollments_list, 5)
        page = request.GET.get('page')
        
        try:
            enrolled_subjects = paginator.page(page)
        except PageNotAnInteger:
            enrolled_subjects = paginator.page(1)
        except EmptyPage:
            enrolled_subjects = paginator.page(paginator.num_pages)

        # Count available subjects (subjects not enrolled in)
        total_subjects = Subject.objects.count()
        enrolled_count = user.enrollments.count()
        available_subjects_count = total_subjects - enrolled_count
        
        # Get active assignments for alert system
        now = timezone.now()
        urgent_assignments = []
        
        for enrollment in enrollments_list:
            # Get assignments due in 48 hours or less, not submitted, not overdue
            assignments_due_soon = Assignment.objects.filter(
                subject=enrollment.subject,
                due_date__gt=now,  # Not overdue
                due_date__lte=now + timedelta(hours=48),  # Due in 48 hours or less
                created_at__gte=enrollment.date_enrolled
            ).exclude(
                submissions__student=user  # Not submitted
            )
            
            if assignments_due_soon.exists():
                # Get very urgent assignments (due in 24 hours or less)
                very_urgent_assignments = assignments_due_soon.filter(
                    due_date__lte=now + timedelta(hours=24)
                )
                
                urgent_assignments.append({
                    'subject': enrollment.subject,
                    'total_count': assignments_due_soon.count(),
                    'very_urgent_count': very_urgent_assignments.count(),
                    'has_very_urgent': very_urgent_assignments.exists()
                })

        return render(request, 'accounts/student_dashboard.html', {
            'enrolled_subjects': enrolled_subjects,
            'available_subjects_count': available_subjects_count,
            'urgent_assignments': urgent_assignments,
            'has_urgent_assignments': len(urgent_assignments) > 0,
        })

@login_required
def teacher_profile(request):
    if request.user.role != 'teacher':
        messages.error(request, "Access denied. Teachers only.")
        return redirect('dashboard')

    teacher = request.user
    
    # Calculate stats
    subjects_count = Subject.objects.filter(teacher=teacher).count()
    total_enrollments = Enrollment.objects.filter(subject__teacher=teacher).count()
    
    if request.method == 'POST':
        # REMOVED DEBUG PRINT STATEMENTS FOR SECURITY
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            # Save the basic form data first
            teacher = form.save(commit=False)
            
            # Handle education entries - only update if provided
            education_json = request.POST.get('education_entries')
            if education_json and education_json != '[]':
                try:
                    education_data = json.loads(education_json)
                    # REMOVED DEBUG PRINT
                    teacher.education = [edu for edu in education_data if edu.get('degree') and edu.get('school') and edu.get('year')]
                except json.JSONDecodeError as e:
                    # REMOVED DEBUG PRINT
                    # Don't overwrite existing education data if there's an error
                    pass  # Silently handle the error
            
            # Handle expertise entries - only update if provided  
            expertise_json = request.POST.get('expertise_entries')
            if expertise_json and expertise_json != '[]':
                try:
                    expertise_data = json.loads(expertise_json)
                    # REMOVED DEBUG PRINT
                    teacher.expertise = [skill for skill in expertise_data if skill.strip()]
                except json.JSONDecodeError as e:
                    # REMOVED DEBUG PRINT
                    # Don't overwrite existing expertise data if there's an error
                    pass  # Silently handle the error
            
            teacher.save()
            # REMOVED DEBUG PRINT
            messages.success(request, 'Profile updated successfully!')
            return redirect('teacher_profile')
        else:
            # REMOVED DEBUG PRINT
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherProfileForm(instance=teacher)

    return render(request, 'accounts/teacher_profile.html', {
        'teacher': teacher,
        'form': form,
        'subjects_count': subjects_count,
        'total_enrollments': total_enrollments,
    })
    
@login_required
def student_profile(request):
    if request.user.role != 'student':
        messages.error(request, "Access denied. Students only.")
        return redirect('dashboard')

    student = request.user
    
    # Calculate stats
    enrolled_subjects_count = Enrollment.objects.filter(student=student).count()
    completed_courses_count = 0  # You can implement course completion logic later
    learning_hours = 0  # You can implement learning hours tracking later
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            # Save the basic form data first
            student = form.save(commit=False)
            
            # Handle education entries - only update if provided
            education_json = request.POST.get('education_entries')
            if education_json and education_json != '[]':
                try:
                    education_data = json.loads(education_json)
                    student.education = [edu for edu in education_data if edu.get('degree') and edu.get('school') and edu.get('year')]
                except json.JSONDecodeError:
                    # Don't overwrite existing education data if there's an error
                    pass
            
            # Handle interests entries - only update if provided  
            interests_json = request.POST.get('interests_entries')
            if interests_json and interests_json != '[]':
                try:
                    interests_data = json.loads(interests_json)
                    student.interests = [interest for interest in interests_data if interest.strip()]
                except json.JSONDecodeError:
                    # Don't overwrite existing interests data if there's an error
                    pass
            
            student.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'accounts/student_profile.html', {
        'student': student,
        'form': form,
        'enrolled_subjects_count': enrolled_subjects_count,
        'completed_courses_count': completed_courses_count,
        'learning_hours': learning_hours,
    })