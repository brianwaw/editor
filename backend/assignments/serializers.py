from rest_framework import serializers
from .models import Assignment, Submission, Language
from typing_tracker.models import TypingSession
from django.contrib.auth.models import User
from django.db.models import Q

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'is_staff']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'extension', 'icon']

class AssignmentSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    language = LanguageSerializer(read_only=True)
    language_id = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(), source='language', write_only=True
    )
    user_submission_status = serializers.SerializerMethodField()
    submitted_count = serializers.SerializerMethodField()
    draft_count = serializers.SerializerMethodField()
    not_attempted_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'language', 'language_id', 'created_by', 
            'due_date', 'created_at', 'user_submission_status', 
            'submitted_count', 'draft_count', 'not_attempted_count'
        ]

    def get_user_submission_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submission = obj.submissions.filter(student=request.user).first()
            if submission:
                if submission.status == 'submitted':
                    return 'submitted'
                # Check for either hard-saved code OR an active live-typing session.
                if (submission.current_code and submission.current_code.strip()) or getattr(submission.typing_session, 'has_started_typing', False):
                    return 'draft'
        return 'not_attempted'

    def get_submitted_count(self, obj):
        return obj.submissions.filter(status='submitted').count()

    def get_draft_count(self, obj):
        return obj.submissions.filter(status='draft').filter(
            (Q(current_code__isnull=False) & ~Q(current_code__exact='')) | Q(typing_session__has_started_typing=True)
        ).count()

    def get_not_attempted_count(self, obj):
        total_students = User.objects.filter(is_staff=False).count()
        submitted = self.get_submitted_count(obj)
        drafts = self.get_draft_count(obj)
        return max(0, total_students - (submitted + drafts))

class TypingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypingSession
        fields = ['session_id', 'is_flagged', 'burst_count', 'requires_human_review']

class SubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    typing_session = TypingSessionSerializer(read_only=True)
    
    class Meta:
        model = Submission
        fields = ['id', 'assignment', 'student', 'status', 'typing_session', 'current_code', 'updated_at']
