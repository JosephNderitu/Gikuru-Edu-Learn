from django.db.models import Count
from courses.models import Subject, Enrollment
import random

def popular_courses(request):
    # Get popular courses based on enrollment count
    popular_courses = Subject.objects.annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-enrollment_count')[:8]  # Get top 8 popular courses
    
    # Define color gradients for different categories
    color_gradients = [
        {'from': 'from-indigo-500', 'to': 'to-indigo-600', 'text': 'text-indigo-700'},
        {'from': 'from-pink-500', 'to': 'to-rose-500', 'text': 'text-pink-600'},
        {'from': 'from-emerald-500', 'to': 'to-teal-500', 'text': 'text-emerald-600'},
        {'from': 'from-purple-500', 'to': 'to-fuchsia-500', 'text': 'text-purple-600'},
        {'from': 'from-blue-500', 'to': 'to-cyan-500', 'text': 'text-blue-600'},
        {'from': 'from-amber-500', 'to': 'to-orange-500', 'text': 'text-amber-600'},
        {'from': 'from-red-500', 'to': 'to-pink-500', 'text': 'text-red-600'},
        {'from': 'from-green-500', 'to': 'to-lime-500', 'text': 'text-green-600'},
    ]
    
    # Prepare courses data with random colors
    courses_data = []
    for course in popular_courses:
        # Select a random color gradient
        color = random.choice(color_gradients)
        
        # For demo purposes, let's categorize by teacher's name or generate categories
        # You can modify this logic based on your actual data
        if course.teacher.first_name and course.teacher.last_name:
            teacher_name = f"{course.teacher.first_name} {course.teacher.last_name}"
        else:
            teacher_name = course.teacher.username
            
        # Generate a category based on some logic
        categories = ['Development', 'Marketing', 'Data Science', 'Design', 'Business', 'Science', 'Arts', 'Technology']
        category = random.choice(categories)
        
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'teacher_name': teacher_name,
            'enrollment_count': course.enrollment_count,
            'category': category,
            'color_from': color['from'],
            'color_to': color['to'],
            'text_color': color['text'],
            'description': course.description if course.description else f"Learn {course.title} from expert instructors",
        })
    
    return {'popular_courses': courses_data[:4]}  # Only return first 4 for the grid