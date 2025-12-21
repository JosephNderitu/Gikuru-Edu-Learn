from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import mark_safe, format_html
from django.utils.safestring import mark_safe
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom Admin Panel for User model with comprehensive field visibility and elegant presentation."""

    # Fields displayed in the admin users list
    list_display = (
        'profile_pic_preview', 
        'username', 
        'get_display_name',
        'email', 
        'role', 
        'profession_preview',
        'is_active_badge',
        'is_staff_badge',
        'date_joined_short',
    )

    list_display_links = ('profile_pic_preview', 'username', 'get_display_name')

    list_filter = (
        'role', 
        'is_staff', 
        'is_superuser', 
        'is_active',
        'date_joined'
    )

    search_fields = ('username', 'email', 'first_name', 'last_name', 'profession', 'phone_number')

    ordering = ('-date_joined',)

    readonly_fields = (
        'last_login', 
        'date_joined', 
        'profile_picture_preview',
        'education_preview',
        'expertise_preview',
        'user_info_summary'
    )

    # Custom fieldsets with better organization
    fieldsets = (
        ("👤 User Identification", {
            'fields': (
                'user_info_summary',
                'username', 
                'email', 
                'password'
            ),
            'classes': ('collapse',)
        }),

        ("📝 Personal Information", {
            'fields': (
                'first_name',
                'last_name', 
                'profession',
                'bio',
            )
        }),

        ("📞 Contact Details", {
            'fields': ('phone_number',),
            'classes': ('collapse',)
        }),

        ("🖼️ Profile Media", {
            'fields': (
                'profile_picture',
                'profile_picture_preview',
            ),
            'classes': ('collapse',)
        }),

        ("🎓 Education Background", {
            'fields': ('education', 'education_preview'),
            'description': "Stored as JSON format. Edit with caution.",
            'classes': ('collapse',)
        }),

        ("🌟 Areas of Expertise", {
            'fields': ('expertise', 'expertise_preview'),
            'description': "Stored as JSON format. Edit with caution.",
            'classes': ('collapse',)
        }),

        ("🔐 Account Role & Permissions", {
            'fields': (
                'role',
                'is_active', 
                'is_staff', 
                'is_superuser',
                'groups', 
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),

        ("📅 System Information", {
            'fields': (
                'last_login', 
                'date_joined'
            ),
            'classes': ('collapse',)
        }),
    )

    # Fieldsets for creating new user
    add_fieldsets = (
        ("👤 Create New User Account", {
            'classes': ('wide',),
            'fields': (
                'username', 
                'email', 
                'first_name',
                'last_name',
                'role',
                'password1', 
                'password2',
            ),
        }),
        ("🔐 Account Permissions (Optional)", {
            'classes': ('wide', 'collapse'),
            'fields': (
                'is_active', 
                'is_staff', 
                'is_superuser'
            ),
        }),
    )

    # CUSTOM METHODS FOR BETTER DISPLAY

    def profile_pic_preview(self, obj):
        if obj.profile_picture:
            return mark_safe(
                f'<img src="{obj.profile_picture.url}" width="45" height="45" style="border-radius:50%;border:2px solid #e2e8f0;object-fit:cover;"/>'
            )
        return mark_safe(
            '<div style="width:45px;height:45px;border-radius:50%;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;border:2px solid #e2e8f0;">'
            f'<span style="font-size:12px;">{obj.username[0].upper() if obj.username else "U"}</span>'
            '</div>'
        )
    profile_pic_preview.short_description = "Profile"
    profile_pic_preview.admin_order_field = 'username'

    def get_display_name(self, obj):
        return obj.get_display_name()
    get_display_name.short_description = "Display Name"
    get_display_name.admin_order_field = 'first_name'

    def profession_preview(self, obj):
        if obj.profession:
            return format_html(
                '<span style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:500;">{}</span>',
                obj.profession
            )
        return format_html(
            '<span style="color:#6b7280;font-style:italic;font-size:11px;">Not set</span>'
        )
    profession_preview.short_description = "Profession"

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;padding:4px 8px;border-radius:6px;font-size:11px;font-weight:600;">✓ Active</span>'
            )
        return format_html(
            '<span style="background:#fecaca;color:#991b1b;padding:4px 8px;border-radius:6px;font-size:11px;font-weight:600;">✗ Inactive</span>'
        )
    is_active_badge.short_description = "Status"

    def is_staff_badge(self, obj):
        if obj.is_staff:
            return format_html(
                '<span style="background:#fef3c7;color:#92400e;padding:4px 8px;border-radius:6px;font-size:11px;font-weight:600;">👑 Staff</span>'
            )
        return format_html(
            '<span style="color:#6b7280;font-size:11px;">User</span>'
        )
    is_staff_badge.short_description = "Type"

    def date_joined_short(self, obj):
        return obj.date_joined.strftime("%b %d, %Y")
    date_joined_short.short_description = "Joined"
    date_joined_short.admin_order_field = 'date_joined'

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return mark_safe(
                f'<img src="{obj.profile_picture.url}" width="150" height="150" style="border-radius:8px;border:2px solid #e2e8f0;object-fit:cover;"/>'
            )
        return mark_safe(
            '<div style="width:150px;height:150px;border-radius:8px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-size:48px;font-weight:bold;border:2px solid #e2e8f0;">'
            f'<span>{obj.username[0].upper() if obj.username else "U"}</span>'
            '</div>'
        )
    profile_picture_preview.short_description = "Profile Picture Preview"

    def education_preview(self, obj):
        if obj.education and len(obj.education) > 0:
            education_html = []
            for edu in obj.education[:3]:  # Show first 3 entries
                degree = edu.get('degree', 'N/A')
                school = edu.get('school', 'N/A')
                year = edu.get('year', 'N/A')
                education_html.append(
                    f"<div style='margin-bottom:8px;padding:8px;background:#f8fafc;border-radius:6px;border-left:3px solid #3b82f6;'>"
                    f"<strong>{degree}</strong><br>"
                    f"<small>{school} • {year}</small>"
                    f"</div>"
                )
            if len(obj.education) > 3:
                education_html.append(f"<small style='color:#6b7280;'>+ {len(obj.education) - 3} more entries</small>")
            return mark_safe("".join(education_html))
        return mark_safe("<span style='color:#6b7280;font-style:italic;'>No education entries</span>")
    education_preview.short_description = "Education Preview"

    def expertise_preview(self, obj):
        if obj.expertise and len(obj.expertise) > 0:
            expertise_html = []
            for skill in obj.expertise[:8]:  # Show first 8 skills
                expertise_html.append(
                    f"<span style='display:inline-block;background:#e0f2fe;color:#0369a1;padding:2px 8px;margin:2px;border-radius:12px;font-size:11px;'>{skill}</span>"
                )
            if len(obj.expertise) > 8:
                expertise_html.append(f"<br><small style='color:#6b7280;'>+ {len(obj.expertise) - 8} more skills</small>")
            return mark_safe("".join(expertise_html))
        return mark_safe("<span style='color:#6b7280;font-style:italic;'>No expertise listed</span>")
    expertise_preview.short_description = "Expertise Preview"

    def user_info_summary(self, obj):
        """Display a summary of user information"""
        summary = []
        if obj.first_name or obj.last_name:
            summary.append(f"<strong>Name:</strong> {obj.get_display_name()}")
        if obj.profession:
            summary.append(f"<strong>Profession:</strong> {obj.profession}")
        if obj.phone_number:
            summary.append(f"<strong>Phone:</strong> {obj.phone_number}")
        if obj.role:
            role_color = {
                'admin': '#ef4444',
                'teacher': '#3b82f6', 
                'student': '#10b981'
            }.get(obj.role, '#6b7280')
            summary.append(
                f"<strong>Role:</strong> <span style='color:{role_color};font-weight:600;text-transform:capitalize;'>{obj.role}</span>"
            )
        
        if summary:
            return mark_safe("<div style='padding:12px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;'>" + "<br>".join(summary) + "</div>")
        return mark_safe("<span style='color:#6b7280;font-style:italic;'>No additional information</span>")
    user_info_summary.short_description = "User Summary"

    # ACTIONS
    actions = ['activate_users', 'deactivate_users', 'make_teachers', 'make_students']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')
    deactivate_users.short_description = "Deactivate selected users"

    def make_teachers(self, request, queryset):
        updated = queryset.update(role='teacher')
        self.message_user(request, f'{updated} users were set as teachers.')
    make_teachers.short_description = "Set selected users as teachers"

    def make_students(self, request, queryset):
        updated = queryset.update(role='student')
        self.message_user(request, f'{updated} users were set as students.')
    make_students.short_description = "Set selected users as students"

    # SECURITY: Prevent staff from promoting themselves or others
    def save_model(self, request, obj, form, change):
        # Prevent non-superusers from assigning admin role
        if not request.user.is_superuser:
            if 'role' in form.cleaned_data and form.cleaned_data['role'] == 'admin':
                obj.role = 'student'  # downgrade automatically
        super().save_model(request, obj, form, change)

#===================================================================================================================
# Note: The above code customizes the Django admin interface for the User model,
# providing enhanced visibility, better organization, and security measures to prevent
#======END OF USER MODER============================================================================================