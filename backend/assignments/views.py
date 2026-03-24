from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Assignment, Submission, Language
from .serializers import AssignmentSerializer, SubmissionSerializer, LanguageSerializer, UserSerializer, TypingSessionSerializer
from typing_tracker.models import TypingSession

class IsLecturerConstraint(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class LanguageListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        languages = Language.objects.all()
        return Response(LanguageSerializer(languages, many=True).data)

class AssignmentListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        assignments = Assignment.objects.all().order_by('-created_at')
        serializer = AssignmentSerializer(assignments, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Only lecturers can create assignments."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignmentDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        data = AssignmentSerializer(assignment, context={'request': request}).data
        
        # If lecturer, return assignment + all submissions (or unattempted status)
        if request.user.is_staff:
            students = User.objects.filter(is_staff=False)
            all_statuses = []
            for student in students:
                sub = assignment.submissions.filter(student=student).first()
                if sub:
                    has_typed = bool((sub.current_code and sub.current_code.strip()) or getattr(sub.typing_session, "has_started_typing", False))
                    status = 'submitted' if sub.status == 'submitted' else ('draft' if has_typed else 'unattempted')
                    all_statuses.append({
                        'student': UserSerializer(student).data,
                        'status': status,
                        'current_code': sub.current_code,
                        'updated_at': sub.updated_at,
                        'typing_session': TypingSessionSerializer(sub.typing_session).data if getattr(sub, 'typing_session', None) else None,
                    })
                else:
                    all_statuses.append({
                        'student': UserSerializer(student).data,
                        'status': 'unattempted',
                        'current_code': '',
                        'updated_at': None,
                        'typing_session': None,
                    })
            return Response({
                "assignment": data,
                "submissions": all_statuses
            })
            
        # If student, return assignment + their own submission (if any)
        submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
        return Response({
            "assignment": AssignmentSerializer(assignment).data,
            "submission": SubmissionSerializer(submission).data if submission else None
        })

class AssignmentSessionView(views.APIView):
    """
    Called by the student to start or resume working on an assignment.
    Finds or creates the Submission and returns its linked TypingSession ID.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        if request.user.is_staff:
            return Response({"error": "Lecturers cannot start coding sessions for assignments."}, status=status.HTTP_403_FORBIDDEN)
            
        assignment = get_object_or_404(Assignment, pk=pk)
        
        # Find or create Submission
        submission, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=request.user,
            defaults={"status": "draft"}
        )
        
        # Find or create TypingSession for this Submission
        if not submission.typing_session:
            t_session = TypingSession.objects.create(
                user=request.user,
                language=assignment.language
            )
            submission.typing_session = t_session
            submission.save()
            
        return Response({
            "session_id": str(submission.typing_session.session_id),
            "current_code": submission.current_code,
            "language": assignment.language.name.lower() if assignment.language else "python",
            "language_name": assignment.language.name if assignment.language else "Python",
            "language_icon": assignment.language.icon.url if (assignment.language and assignment.language.icon) else None,
            "assignment_title": assignment.title,
            "due_date": assignment.due_date,
            "status": submission.status
        })

class SyncSubmissionCodeView(views.APIView):
    """
    Called periodically or on explicit save to update the Submission.current_code.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        submission = get_object_or_404(Submission, assignment=assignment, student=request.user)
        
        if submission.status == 'submitted':
            return Response({"error": "Assignment already submitted"}, status=status.HTTP_400_BAD_REQUEST)
            
        submission.current_code = request.data.get("code", "")
        # Optionally mark as submitted if requested
        if request.data.get("status") == "submitted":
            submission.status = "submitted"
            
        submission.save()
        return Response({"status": "code updated", "status_flag": submission.status})
