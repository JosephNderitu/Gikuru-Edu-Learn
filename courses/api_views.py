from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Subject
from notes.models import Assignment, Submission
from courses.models import Enrollment, Subject
from rest_framework.permissions import AllowAny
from django.db.models import Count

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subject_list_api(request):
    subjects = Subject.objects.all().values(
        'id', 'title', 'description'
    )
    return Response({
        'count': subjects.count(),
        'data': list(subjects)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_assignments_api(request):
    user = request.user

    # Get all assignments related to subjects the student is enrolled in
    assignments = Assignment.objects.filter(
        subject__enrollments__student=user
    ).distinct()

    # Attach submission status
    data = []
    for assignment in assignments:
        submitted = Submission.objects.filter(
            assignment=assignment,
            student=user
        ).exists()
        data.append({
            'id': assignment.id,
            'title': assignment.title,
            'subject': assignment.subject.title,
            'due_date': assignment.due_date,
            'submitted': submitted,
        })

    return Response({
        'count': len(data),
        'assignments': data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_enrollments_api(request):
    user = request.user

    enrollments = Enrollment.objects.filter(student=user).select_related('subject')

    data = [
        {
            'subject_id': e.subject.id,
            'subject_title': e.subject.title,
            'date_enrolled': e.date_enrolled
        }
        for e in enrollments
    ]

    return Response({
        'count': len(data),
        'enrollments': data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def popular_courses_api(request):
    courses = Subject.objects.annotate(
        student_count=Count('enrollments')
    ).order_by('-student_count')[:5]  # Top 5 popular courses

    data = [
        {
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'teacher': c.teacher.username,
            'enrollment_count': c.student_count
        }
        for c in courses
    ]

    return Response({
        'count': len(data),
        'popular_courses': data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_subjects_api(request):
    user = request.user
    if user.role != 'teacher':
        return Response({'error': 'Access denied'}, status=403)

    subjects = Subject.objects.filter(teacher=user)

    data = [
        {
            'id': s.id,
            'title': s.title,
            'description': s.description,
            'created_at': s.created_at
        }
        for s in subjects
    ]

    return Response({
        'count': len(data),
        'subjects': data
    })
