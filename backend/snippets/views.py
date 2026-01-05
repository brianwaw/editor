from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CodeSnippet
from .serializers import CodeSnippetSerializer
from authentication.auth import JWTAuthentication

class SaveSnippetView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CodeSnippetSerializer(data=request.data)
        if serializer.is_valid():
            # Associate snippet with the logged-in user
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
