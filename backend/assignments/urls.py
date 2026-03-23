from django.urls import path
from .views import AssignmentListView, AssignmentDetailView, AssignmentSessionView, SyncSubmissionCodeView, LanguageListView

urlpatterns = [
    path('languages/', LanguageListView.as_view(), name='language-list'),
    # list all / create new assignment
    path('', AssignmentListView.as_view(), name='assignment-list'),
    
    # view single assignment details (and submissions if staff)
    path('<uuid:pk>/', AssignmentDetailView.as_view(), name='assignment-detail'),
    
    # join/resume assignment session (Student only)
    path('<uuid:pk>/session/', AssignmentSessionView.as_view(), name='assignment-session'),
    
    # save code to submission
    path('<uuid:pk>/sync/', SyncSubmissionCodeView.as_view(), name='assignment-sync-code'),
]
