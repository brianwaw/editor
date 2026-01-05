from django.urls import path
from .views import SaveSnippetView

urlpatterns = [
    path('save/', SaveSnippetView.as_view(), name='save_snippet'),
]
