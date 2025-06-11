from django.shortcuts import render

# views.py
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .permissions import IsStaffUser # Import custom permission
from .models import Rosbags
from .serializers import RosbagSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rosbags_list(request):
    prodotti = Rosbags.objects.all()
    serializer = RosbagSerializer(prodotti, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def upload_rosbags(request):
    serializer = RosbagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
