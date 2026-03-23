import uuid
from django.db import models
from django.contrib.auth.models import User
from typing_tracker.models import TypingSession

class Language(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    extension = models.CharField(max_length=20)
    icon = models.FileField(upload_to='language_icons/', null=True, blank=True)

    def __str__(self):
        return self.name

class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, related_name="assignments")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_assignments")
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.language.name if self.language else 'No Language'})"

class Submission(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("graded", "Graded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    
    # Each submission is 1:1 linked with a TypingSession tracking its history.
    typing_session = models.OneToOneField(TypingSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="submission")
    
    # Store the latest state of the code so the editor can resume
    current_code = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("assignment", "student")

    def __str__(self):
        return f"{self.student.username} -> {self.assignment.title}"
