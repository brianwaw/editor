from rest_framework import serializers
from .models import Assignment, Submission, Language
from typing_tracker.models import TypingSession
from django.contrib.auth.models import User

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
    
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'language', 'language_id', 'created_by', 'due_date', 'created_at', 'user_submission_status']

    def get_user_submission_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submission = obj.submissions.filter(student=request.user).first()
            if submission:
                return submission.status
        return 'not_started'

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
