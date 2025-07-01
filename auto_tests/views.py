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
from .rosbag_reader import RosbagReader  # Import the utility class to read rosbag files
from .clean import clean_missing_files  # Import the cleaning function

# Django REST framework API view to expose rosbag data as JSON
from django.shortcuts import get_object_or_404
from pathlib import Path
from django.conf import settings

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rosbags_list(request):
    clean_missing_files()  # Clean up any missing files before listing
    prodotti = Rosbags.objects.all()
    serializer = RosbagSerializer(prodotti, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def delete_rosbag(request, pk):
    rosbag = get_object_or_404(Rosbags, pk=pk)
    rosbag.delete()
    return Response({'message': f'Rosbag {pk} eliminato con successo'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def update_rosbag(request, pk):
    rosbag = get_object_or_404(Rosbags, pk=pk)
    partial = request.method == 'PATCH'  # PATCH = aggiornamento parziale

    serializer = RosbagSerializer(rosbag, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def upload_rosbags(request):
    serializer = RosbagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def upload_files(request):
    yaml_file = request.FILES.get('yaml_file')
    db_file = request.FILES.get('db_file')

    if not yaml_file or not db_file:
        return Response({"detail": "yaml_file and db_file are required."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = RosbagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rosbag_json(request, pk):
    """
    API endpoint that returns JSON with topics and sample messages from a rosbag.
    URL: /api/rosbags/<pk>/
    """
    clean_missing_files()  # Clean up any missing files before processing
    rosbag_obj = get_object_or_404(Rosbags, pk=pk)
    bag_name = Path(rosbag_obj.rosbag_file.name).stem
    reader = RosbagReader()

    # Gather topics
    topics = reader.read_topics(bag_name)

    # Gather a few messages per topic (e.g., 10 each)
    data = {'topics': topics, 'messages': []}
    for topic in topics:
        msgs = []
        for msg in reader.read_messages(bag_name, topic_filter=topic['topic'], max_messages=10):
            # Ensure serializable
            payload = msg['msg']
            msg_str = str(payload) if not isinstance(payload, (str, bytes)) else payload
            msgs.append({'timestamp': msg['timestamp'], 'msg': msg_str})
        data['messages'].append({'topic': topic['topic'], 'samples': msgs})

    return Response(data)