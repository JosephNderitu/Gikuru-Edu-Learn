from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Assignment, Submission, ClassMaterial, Book
from .forms import AssignmentForm, SubmissionForm, ClassMaterialForm, BookForm
from courses.models import Subject, Enrollment
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q

# notes/views.py - Update create_assignment function
@login_required
def create_assignment(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')

    # Get subject from query parameter if provided
    subject_id = request.GET.get('subject')
    initial_data = {}
    if subject_id:
        try:
            subject = Subject.objects.get(id=subject_id, teacher=request.user)
            initial_data['subject'] = subject
        except Subject.DoesNotExist:
            pass

    form = AssignmentForm(request.POST or None, request.FILES or None, initial=initial_data)

    # Only subjects taught by this teacher
    form.fields['subject'].queryset = Subject.objects.filter(teacher=request.user)

    if form.is_valid():
        assignment = form.save(commit=False)
        assignment.teacher = request.user
        assignment.save()
        messages.success(request, "Assignment created successfully!")
        # Redirect back to the subject page
        return redirect('view_subject', subject_id=assignment.subject.id)

    return render(request, 'notes/teacher/assignment_create.html', {'form': form})

@login_required
def assignment_submissions(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, teacher=request.user)
    
    # Get all submissions ordered by submission date (earliest first for priority)
    all_submissions = assignment.submissions.all().order_by('submitted_at')
    
    # Categorize submissions
    graded_submissions = all_submissions.filter(grade__isnull=False)
    not_graded_submissions = all_submissions.filter(grade__isnull=True)
    
    # Get current tab and page
    tab = request.GET.get('tab', 'not_graded')
    page_number = request.GET.get('page', 1)
    
    # Select submissions based on tab
    if tab == 'graded':
        submissions_list = graded_submissions
        empty_message = "No graded submissions yet"
        empty_description = "Graded submissions will appear here"
    else:  # not_graded
        submissions_list = not_graded_submissions
        empty_message = "No submissions to grade"
        empty_description = "All submissions have been graded!"
    
    # Pagination - 15 per page
    paginator = Paginator(submissions_list, 15)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notes/teacher/submissions.html', {
        'assignment': assignment,
        'submissions': page_obj,
        'graded_count': graded_submissions.count(),
        'not_graded_count': not_graded_submissions.count(),
        'current_tab': tab,
        'empty_message': empty_message,
        'empty_description': empty_description,
    })

@login_required
def grade_submission(request, pk):
    submission = Submission.objects.get(pk=pk, assignment__teacher=request.user)

    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '')
        
        # Validate grade is at least 1
        try:
            grade_value = float(grade)
            if grade_value < 1:
                messages.error(request, "Grade must be at least 1.")
                return render(request, 'notes/teacher/grade_submission.html', {
                    'submission': submission
                })
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid grade.")
            return render(request, 'notes/teacher/grade_submission.html', {
                'submission': submission
            })
        
        submission.grade = grade_value
        submission.feedback = feedback
        submission.save()
        messages.success(request, "Submission graded.")
        return redirect('assignment_submissions', pk=submission.assignment.id)

    return render(request, 'notes/teacher/grade_submission.html', {
        'submission': submission
    })

@login_required
def submit_assignment(request, pk):
    assignment = Assignment.objects.get(pk=pk)

    # Ensure student is enrolled
    if not Enrollment.objects.filter(student=request.user, subject=assignment.subject).exists():
        messages.error(request, "You cannot submit this assignment.")
        return redirect('view_subject_student', subject_id=assignment.subject.id)

    # Prevent resubmission
    existing = Submission.objects.filter(student=request.user, assignment=assignment).first()
    if existing:
        messages.info(request, "You already submitted this assignment.")
        return redirect('view_subject_student', subject_id=assignment.subject.id)

    form = SubmissionForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        # Additional validation: either file or answer (min 200 chars) must be provided
        answer = form.cleaned_data.get('answer', '').strip()
        file = form.cleaned_data.get('file')
        
        if not file and len(answer) < 200:
            messages.error(request, "Please provide either a file upload or a written answer with at least 200 characters.")
            return render(request, 'notes/student/submit_assignment.html', {
                'form': form,
                'assignment': assignment
            })

        submission = form.save(commit=False)
        submission.student = request.user
        submission.assignment = assignment
        submission.save()
        messages.success(request, "Assignment submitted successfully!")
        return redirect('view_subject_student', subject_id=assignment.subject.id)

    return render(request, 'notes/student/submit_assignment.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
def upload_material(request):
    if request.user.role != "teacher":
        return redirect("dashboard")

    form = ClassMaterialForm(request.POST or None, request.FILES or None)
    form.fields['subject'].queryset = Subject.objects.filter(teacher=request.user)
    subject_id = request.GET.get('subject')

    # Prefill subject if subject_id is provided
    if subject_id:
        form.fields['subject'].initial = subject_id

    if form.is_valid():
        material = form.save(commit=False)
        material.teacher = request.user
        material.save()
        messages.success(request, "Material uploaded successfully!")
        return redirect('view_subject', subject_id=material.subject.id)

    return render(request, 'notes/materials/upload.html', {'form': form})

@login_required
def edit_material(request, material_id):
    if request.user.role != "teacher":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Access denied'}, status=403)
        return redirect("dashboard")

    material = get_object_or_404(ClassMaterial, id=material_id, teacher=request.user)
    
    if request.method == 'POST':
        form = ClassMaterialForm(request.POST, request.FILES, instance=material)
        form.fields['subject'].queryset = Subject.objects.filter(teacher=request.user)
        
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Material updated successfully!'})
            messages.success(request, "Material updated successfully!")
            return redirect('teacher_materials')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ClassMaterialForm(instance=material)
        form.fields['subject'].queryset = Subject.objects.filter(teacher=request.user)
        
        # If it's an AJAX request, return form HTML
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            form_html = render_to_string('notes/materials/edit_form_partial.html', {
                'form': form,
                'material': material
            }, request=request)
            return JsonResponse({'form_html': form_html})
        
        # Regular request - render full page (fallback)
        return render(request, 'notes/materials/edit_material.html', {
            'form': form,
            'material': material
        })

@login_required
def delete_material(request, material_id):
    if request.user.role != "teacher":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Access denied'}, status=403)
        return redirect("dashboard")

    material = get_object_or_404(ClassMaterial, id=material_id, teacher=request.user)
    
    if request.method == 'POST':
        material.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Material deleted successfully!'})
        messages.success(request, "Material deleted successfully!")
        return redirect('teacher_materials')
    
    # Return material info for confirmation
    material_info = {
        'title': material.title,
        'subject': material.subject.title,
        'description': material.description,
        'created_at': material.created_at.strftime('%b %d, %Y %H:%M')
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'material': material_info})
    
    # Regular request - render confirmation page (fallback)
    return render(request, 'notes/materials/delete_material.html', {
        'material': material
    })

# notes/views.py - Add these views

# Book views
@login_required
def book_list(request):
    """List all books for the current user"""
    if request.user.role == 'teacher':
        books = Book.objects.filter(teacher=request.user).order_by('-created_at')
        template = 'notes/books/teacher_book_list.html'
        
        return render(request, template, {
            'books': books,
        })
    
    else:  # student
        # Get books from enrolled subjects
        enrolled_subjects = Enrollment.objects.filter(student=request.user).values_list('subject', flat=True)
        books = Book.objects.filter(subject__in=enrolled_subjects).order_by('-created_at')
        
        # Search functionality
        search_query = request.GET.get('q', '')
        if search_query:
            books = books.filter(
                Q(title__icontains=search_query) |
                Q(subtitle__icontains=search_query) |
                Q(author_first_name__icontains=search_query) |
                Q(author_last_name__icontains=search_query) |
                Q(additional_authors__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(isbn__icontains=search_query) |
                Q(publisher__icontains=search_query) |
                Q(subject__title__icontains=search_query)
            )
        
        # Filter by status
        status = request.GET.get('status')
        if status == 'required':
            books = books.filter(is_required=True)
        elif status == 'recommended':
            books = books.filter(is_required=False)
        
        # Filter by subject
        subject_id = request.GET.get('subject')
        if subject_id:
            books = books.filter(subject_id=subject_id)
        
        # Filter by year
        year = request.GET.get('year')
        if year:
            books = books.filter(publication_year=year)
        
        # Filter by language
        language = request.GET.get('language')
        if language:
            books = books.filter(language__iexact=language)
        
        # Get unique years for filter dropdown
        year_range = sorted(set(Book.objects.filter(subject__in=enrolled_subjects)
                               .values_list('publication_year', flat=True).distinct()), reverse=True)
        
        # Statistics for the dashboard
        total_books = books.count()
        required_books = Book.objects.filter(subject__in=enrolled_subjects, is_required=True).count()
        subject_count = Subject.objects.filter(id__in=enrolled_subjects).count()
        pdf_count = Book.objects.filter(subject__in=enrolled_subjects, pdf_file__isnull=False).count()
        
        # Pagination
        paginator = Paginator(books, 15)  # 15 books per page for tabular view
        page = request.GET.get('page')
        try:
            books = paginator.page(page)
        except PageNotAnInteger:
            books = paginator.page(1)
        except EmptyPage:
            books = paginator.page(paginator.num_pages)
        
        return render(request, 'notes/books/student_book_list.html', {
            'books': books,
            'enrolled_subjects': Subject.objects.filter(id__in=enrolled_subjects),
            'year_range': year_range,
            'total_books': total_books,
            'required_books': required_books,
            'subject_count': subject_count,
            'pdf_count': pdf_count,
        })

@login_required
def add_book(request):
    """Add a new book"""
    if request.user.role != 'teacher':
        messages.error(request, "Only teachers can add books.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            book = form.save(commit=False)
            book.teacher = request.user
            book.save()
            messages.success(request, "Book added successfully!")
            
            # Redirect to book list or subject page
            if 'subject' in request.GET:
                return redirect('view_subject', subject_id=book.subject.id)
            return redirect('book_list')
    else:
        # Prefill subject if provided
        initial = {}
        subject_id = request.GET.get('subject')
        if subject_id:
            try:
                subject = Subject.objects.get(id=subject_id, teacher=request.user)
                initial['subject'] = subject
            except Subject.DoesNotExist:
                pass
        
        form = BookForm(initial=initial, user=request.user)
    
    return render(request, 'notes/books/add_book.html', {'form': form})

@login_required
def edit_book(request, book_id):
    """Edit an existing book"""
    if request.user.role != 'teacher':
        messages.error(request, "Only teachers can edit books.")
        return redirect('dashboard')
    
    book = get_object_or_404(Book, id=book_id, teacher=request.user)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Book updated successfully!")
            return redirect('book_list')
    else:
        form = BookForm(instance=book, user=request.user)
    
    return render(request, 'notes/books/edit_book.html', {'form': form, 'book': book})

@login_required
def delete_book(request, book_id):
    """Delete a book"""
    if request.user.role != 'teacher':
        messages.error(request, "Only teachers can delete books.")
        return redirect('dashboard')
    
    book = get_object_or_404(Book, id=book_id, teacher=request.user)
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Book deleted successfully!")
        return redirect('book_list')
    
    return render(request, 'notes/books/delete_book.html', {'book': book})

@login_required
def book_detail(request, book_id):
    """View book details"""
    if request.user.role == 'teacher':
        book = get_object_or_404(Book, id=book_id, teacher=request.user)
    else:  # student
        # Check if student is enrolled in the subject
        book = get_object_or_404(Book, id=book_id)
        if not Enrollment.objects.filter(student=request.user, subject=book.subject).exists():
            messages.error(request, "You are not enrolled in this course.")
            return redirect('dashboard')
    
    return render(request, 'notes/books/book_detail.html', {'book': book})
