from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def home(request):
    return render(request, 'core/home.html')

# Custom error pages
def handler404(request, exception):
    """Custom 404 page"""
    return render(request, 'core/errorPages/404.html', status=404)

def handler500(request):
    """Custom 500 page"""
    return render(request, 'core/errorPages/500.html', status=500)

def handler403(request, exception):
    """Custom 403 page"""
    return render(request, 'core/errorPages/403.html', status=403)

def handler400(request, exception):
    """Custom 400 page"""
    return render(request, 'core/errorPages/400.html', status=400)