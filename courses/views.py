from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import Subject, Enrollment
from .forms import SubjectForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 

from notes.models import Assignment, Submission, ClassMaterial
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

@login_required
def teacher_subjects(request):
    if request.user.role != 'teacher':
        messages.error(request, "Access denied. Teachers only.")
        return redirect('dashboard')

    subjects_list = Subject.objects.filter(teacher=request.user).order_by('-created_at')
    
    # Calculate statistics
    total_students = Enrollment.objects.filter(subject__teacher=request.user).count()
    active_courses = subjects_list.count()
    average_students = total_students // active_courses if active_courses > 0 else 0
    max_students = 50  # You can make this dynamic based on your requirements
    
    # Pagination - 6 subjects per page
    paginator = Paginator(subjects_list, 6)
    page = request.GET.get('page')
    
    try:
        subjects = paginator.page(page)
    except PageNotAnInteger:
        subjects = paginator.page(1)
    except EmptyPage:
        subjects = paginator.page(paginator.num_pages)
        
    return render(request, 'courses/teacher/teacher_subjects.html', {
        'subjects': subjects,
        'total_students': total_students,
        'active_courses': active_courses,
        'average_students': average_students,
        'max_students': max_students
    })


@login_required
def add_subject(request):
    if request.user.role != 'teacher':
        messages.error(request, "Access denied. Teachers only.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.teacher = request.user
            subject.save()
            messages.success(request, 'Subject created successfully!')
            return redirect('teacher_subjects')
    else:
        form = SubjectForm()
    return render(request, 'courses/teacher/add_subject.html', {'form': form})


@login_required
def student_subject_list(request):
    if request.user.role != 'student':
        messages.error(request, "Access denied. Students only.")
        return redirect('dashboard')

    # Get all subjects with related teacher and enrollment data
    subjects = Subject.objects.all().select_related('teacher').prefetch_related('enrollments')
    
    # Handle search query
    search_query = request.GET.get('q', '')
    if search_query:
        subjects = subjects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(teacher__username__icontains=search_query) |
            Q(teacher__first_name__icontains=search_query) |
            Q(teacher__last_name__icontains=search_query)
        )
    
    # Handle filters
    available_only = request.GET.get('available') == 'true'
    if available_only:
        # Filter out courses the student is already enrolled in
        enrolled_subject_ids = Enrollment.objects.filter(
            student=request.user
        ).values_list('subject_id', flat=True)
        subjects = subjects.exclude(id__in=enrolled_subject_ids)
    
    popular_first = request.GET.get('popular') == 'true'
    if popular_first:
        subjects = subjects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count', '-created_at')
    else:
        subjects = subjects.order_by('-created_at')
    
    # Get enrolled subjects for the current user
    enrolled_subjects = Enrollment.objects.filter(
        student=request.user
    ).values_list('subject_id', flat=True)
    
    # Add pagination
    paginator = Paginator(subjects, 10)  # Show 10 subjects per page
    page = request.GET.get('page')
    
    try:
        subjects_page = paginator.page(page)
    except PageNotAnInteger:
        subjects_page = paginator.page(1)
    except EmptyPage:
        subjects_page = paginator.page(paginator.num_pages)
    
    return render(request, 'courses/students/student_subject_list.html', {
        'subjects': subjects_page,
        'enrolled_subjects': enrolled_subjects,
        'search_query': search_query,
    })

@login_required
def enroll_subject(request, subject_id):
    if request.user.role != 'student':
        messages.error(request, "Access denied. Students only.")
        return redirect('dashboard')

    subject = get_object_or_404(Subject, id=subject_id)
    Enrollment.objects.get_or_create(student=request.user, subject=subject)
    messages.success(request, f"You have enrolled in {subject.title}")
    return redirect('student_subject_list')

# Teacher: View Subject
@login_required
def view_subject_teacher(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)
    enrollments_list = subject.enrollments.all()
    
    # Get assignments for this subject with pagination
    assignments_list = Assignment.objects.filter(
        subject=subject
    ).order_by('-created_at')
    
    # Get materials for this subject
    materials = ClassMaterial.objects.filter(
        subject=subject,
        teacher=request.user
    ).order_by('-created_at')
    
    # Get assignment statistics
    total_assignments = assignments_list.count()
    assignments_with_submissions = Assignment.objects.filter(
        subject=subject,
        submissions__isnull=False
    ).distinct().count()
    
    # Pagination for assignments
    assignment_page = request.GET.get('assignment_page', 1)
    assignment_paginator = Paginator(assignments_list, 4)  # 10 assignments per page
    try:
        assignments = assignment_paginator.page(assignment_page)
    except PageNotAnInteger:
        assignments = assignment_paginator.page(1)
    except EmptyPage:
        assignments = assignment_paginator.page(assignment_paginator.num_pages)
    
    # Pagination for students
    student_page = request.GET.get('student_page', 1)
    student_paginator = Paginator(enrollments_list, 10)  # 10 students per page
    try:
        enrollments = student_paginator.page(student_page)
    except PageNotAnInteger:
        enrollments = student_paginator.page(1)
    except EmptyPage:
        enrollments = student_paginator.page(student_paginator.num_pages)
    
    return render(request, 'courses/teacher/view_subject.html', {
        'subject': subject,
        'enrollments': enrollments,
        'assignments': assignments,
        'materials': materials, 
        'total_assignments': total_assignments,
        'assignments_with_submissions': assignments_with_submissions,
    })

# Teacher: Edit Subject
@login_required
def edit_subject_teacher(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('teacher_subjects')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'courses/teacher/edit_subject.html', {'form': form, 'subject': subject})

# Teacher: Delete Subject
@login_required
def delete_subject_teacher(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('teacher_subjects')
    return render(request, 'courses/teacher/delete_subject.html', {'subject': subject})

# Student: Unenroll from Subject
@login_required
def unenroll_subject(request, subject_id):
    if request.user.role != 'student':
        messages.error(request, "Access denied. Students only.")
        return redirect('dashboard')

    subject = get_object_or_404(Subject, id=subject_id)
    enrollment = get_object_or_404(Enrollment, student=request.user, subject=subject)
    
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, f"You have unenrolled from {subject.title}")
        return redirect('dashboard')
    
    return redirect('dashboard')


@login_required
def view_subject_student(request, subject_id):
    if request.user.role != 'student':
        messages.error(request, "Access denied. Students only.")
        return redirect('dashboard')

    subject = get_object_or_404(Subject, id=subject_id)
    is_enrolled = Enrollment.objects.filter(student=request.user, subject=subject).exists()
    
    if not is_enrolled:
        messages.error(request, "You are not enrolled in this subject.")
        return redirect('dashboard')
    
    # Get enrollment date to filter assignments
    enrollment = Enrollment.objects.get(student=request.user, subject=subject)
    
    # Get assignments created after enrollment and not too far in the future
    assignments = Assignment.objects.filter(
        subject=subject,
        created_at__gte=enrollment.date_enrolled,
        due_date__lte=timezone.now() + timedelta(days=90)  # Show assignments due within 90 days
    ).order_by('-created_at')
    
    # Get materials for this subject
    materials = ClassMaterial.objects.filter(
        subject=subject,
        created_at__gte=enrollment.date_enrolled
    ).order_by('-created_at')
    
    # Get all submissions by this student for these assignments
    submissions = Submission.objects.filter(
        student=request.user,
        assignment__in=assignments
    )
    
    # Attach each submission directly onto its assignment
    submission_map = {s.assignment_id: s for s in submissions}
    
    now = timezone.now()
    for assignment in assignments:
        assignment.submission = submission_map.get(assignment.id, None)
        assignment.is_overdue = assignment.due_date < now
        assignment.is_urgent = (assignment.due_date > now and 
                              assignment.due_date - now < timedelta(hours=24))
    
    # Categorize assignments
    pending_assignments = [a for a in assignments if not a.submission and not a.is_overdue]
    submitted_assignments = [a for a in assignments if a.submission]
    overdue_assignments = [a for a in assignments if a.is_overdue and not a.submission]
    
    # Pagination
    tab = request.GET.get('tab', 'pending')
    page_number = request.GET.get('page', 1)
    
    if tab == 'submitted':
        assignments_list = submitted_assignments
        empty_message = "No assignments submitted yet"
        empty_description = "Your submitted assignments will appear here"
    elif tab == 'overdue':
        assignments_list = overdue_assignments
        empty_message = "No overdue assignments"
        empty_description = "You're doing great! No overdue assignments."
    else:  # pending
        assignments_list = pending_assignments
        empty_message = "No pending assignments"
        empty_description = "All your assignments are up to date!"
    
    paginator = Paginator(assignments_list, 10)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'courses/students/view_subject.html', {
        'subject': subject,
        'assignments': page_obj,
        'materials': materials, 
        'now': now,
        'current_tab': tab,
        'pending_count': len(pending_assignments),
        'submitted_count': len(submitted_assignments),
        'overdue_count': len(overdue_assignments),
        'empty_message': empty_message,
        'empty_description': empty_description,
    })

from django.shortcuts import render
from django.db.models import Count
import random

def popular_courses_view(request):
    """
    Renders the popular courses section with dynamic data
    """
    # Get popular courses with enrollment counts
    courses = Subject.objects.annotate(
        student_count=Count('enrollments')
    ).order_by('-student_count')[:4]  # Get top 4 courses
    
    # Color schemes for dynamic styling
    color_schemes = [
        {'from': 'from-indigo-500', 'to': 'to-indigo-600', 'text': 'text-indigo-700'},
        {'from': 'from-pink-500', 'to': 'to-rose-500', 'text': 'text-pink-600'},
        {'from': 'from-emerald-500', 'to': 'to-teal-500', 'text': 'text-emerald-600'},
        {'from': 'from-purple-500', 'to': 'to-fuchsia-500', 'text': 'text-purple-600'},
        {'from': 'from-blue-500', 'to': 'to-cyan-500', 'text': 'text-blue-600'},
        {'from': 'from-amber-500', 'to': 'to-orange-500', 'text': 'text-amber-600'},
        {'from': 'from-red-500', 'to': 'to-pink-500', 'text': 'text-red-600'},
        {'from': 'from-green-500', 'to': 'to-lime-500', 'text': 'text-green-600'},
    ]
    
    # Prepare courses data
    courses_data = []
    for course in courses:
        # Get teacher name
        teacher_name = f"{course.teacher.first_name} {course.teacher.last_name}".strip()
        if not teacher_name:
            teacher_name = course.teacher.username
        
        # Select random color
        color = random.choice(color_schemes)
        
        # Determine category (simple logic based on title)
        title_lower = course.title.lower()
        if any(word in title_lower for word in ['web', 'development', 'programming', 'code', 'software']):
            category = 'Development'
        elif any(word in title_lower for word in ['marketing', 'digital', 'social', 'brand', 'advertising']):
            category = 'Marketing'
        elif any(word in title_lower for word in ['data', 'machine', 'learning', 'ai', 'analytics', 'python']):
            category = 'Data Science'
        elif any(word in title_lower for word in ['design', 'ui', 'ux', 'graphic', 'figma', 'adobe']):
            category = 'Design'
        elif any(word in title_lower for word in ['business', 'finance', 'management', 'entrepreneur']):
            category = 'Business'
        elif any(word in title_lower for word in ['science', 'math', 'physics', 'chemistry']):
            category = 'Science'
        else:
            category = 'General'
        
        # Generate static values (you can make these fields later)
        hours_options = [28, 32, 42, 56, 64, 72]
        lessons_options = [94, 112, 156, 186, 200, 240]
        rating_options = [4.7, 4.8, 4.9, 5.0]
        
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'teacher_name': teacher_name,
            'category': category,
            'color_from': color['from'],
            'color_to': color['to'],
            'text_color': color['text'],
            'student_count': course.student_count or 0,
            'hours': random.choice(hours_options),
            'lessons': random.choice(lessons_options),
            'rating': random.choice(rating_options),
            'description': course.description[:100] + '...' if course.description else '',
        })
    
    context = {
        'popular_courses': courses_data,
    }
    
    return render(request, 'courses/popular_courses_section.html', context)