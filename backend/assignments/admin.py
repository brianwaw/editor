from django.contrib import admin
from .models import Assignment, Submission, Language

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'extension', 'icon')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "created_by", "created_at")
    list_filter = ("language", "created_by")
    search_fields = ("title",)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "status", "created_at")
    list_filter = ("status", "assignment__language")
    search_fields = ("student__username", "assignment__title")
    readonly_fields = ("created_at", "updated_at")
