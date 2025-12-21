from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.files.base import ContentFile
from PIL import Image
import io
import os

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Contact Information Fields
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Education fields
    education = models.JSONField(default=list, blank=True)  # Store list of education entries
    
    # Areas of expertise
    expertise = models.JSONField(default=list, blank=True)  # Store list of expertise areas
    interests = models.JSONField(default=list, blank=True)  # Store list of learning interests
    
    def compress_image(self, image):
        """Compress image to target size (150-200KB) while maintaining quality"""
        try:
            # Open image
            img = Image.open(image)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Set target dimensions (optimized for profile pictures)
            max_size = (500, 500)  # Good balance between quality and file size
            
            # Resize if necessary while maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Create in-memory file
            output = io.BytesIO()
            
            # Optimize JPEG quality to achieve target file size
            quality = 85  # Start with good quality
            img.save(output, format='JPEG', quality=quality, optimize=True)
            
            # If still too large, reduce quality further
            file_size = output.tell()
            max_file_size = 200 * 1024  # 200KB in bytes
            
            if file_size > max_file_size:
                # Calculate required quality reduction
                quality = max(60, int(quality * (max_file_size / file_size)))
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
            
            # Prepare file for saving
            compressed_file = ContentFile(output.getvalue())
            
            # Generate filename
            filename = os.path.splitext(image.name)[0] + '_compressed.jpg'
            
            return filename, compressed_file
        
        except Exception as e:
            # If compression fails, return original
            print(f"Image compression failed: {e}")
            return image.name, image
            
        except Exception as e:
            # If compression fails, return original
            print(f"Image compression failed: {e}")
            return image.name, image

    def save(self, *args, **kwargs):
        # Prevent non-superusers from saving themselves as admin
        if not self.is_superuser and self.role == 'admin':
            self.role = 'student'
            
        # Compress profile picture if it's being updated
        if self.profile_picture and hasattr(self.profile_picture, 'file'):
            # Check if this is a new image or existing one
            try:
                original = User.objects.get(pk=self.pk)
                if original.profile_picture != self.profile_picture:
                    # New image uploaded - compress it
                    filename, compressed_file = self.compress_image(self.profile_picture)
                    self.profile_picture.save(filename, compressed_file, save=False)
            except User.DoesNotExist:
                # New user - compress the image
                filename, compressed_file = self.compress_image(self.profile_picture)
                self.profile_picture.save(filename, compressed_file, save=False)
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def get_display_name(self):
        """Get display name - use custom first/last name if available, otherwise username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username