# from django.shortcuts import render

# views.py
from rest_framework.decorators import api_view, permission_classes, parser_classes # For creating API views
from rest_framework.permissions import IsAuthenticated # For authentication and permissions
from rest_framework.response import Response # For returning responses
from rest_framework.parsers import MultiPartParser, FormParser # For handling file uploads
from rest_framework.generics import ListAPIView # For generic list views
from rest_framework import status # For HTTP status codes
from .permissions import IsStaffUser # Import custom permission
from .models import Rosbags # Import the Rosbags model
from .serializers import RosbagSerializer # Import the serializer for Rosbags
from .rosbag_reader import RosbagReader  # Import the utility class to read rosbag files
from .clean import clean_missing_files  # Import the cleaning function
from .utils import compress_full_data  # Import shared utility functions

# Django REST framework API view to expose rosbag data as JSON
from django.shortcuts import get_object_or_404 # For retrieving objects
from pathlib import Path # For handling file paths
from django.conf import settings # For accessing settings
from django.http import JsonResponse, FileResponse  # For file responses
from django.core.files.base import ContentFile # For file handling
import json # For JSON operations
import shutil # For file operations

# View to list all Rosbags and clean up missing files
class RosbagsListView(ListAPIView): # Class for listing Rosbags 
    """
    View to list all Rosbags with the ability to clean up missing files.   
    """
    # This view will return a paginated list of Rosbags
    queryset = Rosbags.objects.all()
    serializer_class = RosbagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        clean_missing_files()  # Richiamiamo la funzione prima di restituire i dati
        return super().get_queryset()


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def delete_rosbag(request, pk):
    """
    Deletes a Rosbag instance and its associated files.
    """
    rosbag = get_object_or_404(Rosbags, pk=int(pk))
    
    file_path = rosbag.db_file.path if rosbag.db_file else None  # Get the file path of the db_file if it exists

    if file_path:
        folder = Path(file_path).parent  # using pathlib
        try:
            shutil.rmtree(folder)  # Delete the entire folder containing the rosbag files

            rosbag.delete()

        except Exception as e:
            return Response({'message': f'Error while deleting Rosbag {pk}'}, status=status.HTTP_204_NO_CONTENT)

    return Response({'message': f'Rosbag {pk} successfully deleted'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def update_rosbag(request, pk):
    """
    Updates a Rosbag instance with the provided data.
    Supports both full updates (PUT) and partial updates (PATCH).
    """
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
    """
    Uploads a new Rosbag instance with the provided data.
    Expects a multipart/form-data request with the necessary files.
    """
    serializer = RosbagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated, IsStaffUser])
# @parser_classes([MultiPartParser, FormParser])
# def upload_files(request):
#     yaml_file = request.FILES.get('yaml_file')
#     db_file = request.FILES.get('db_file')

#     if not yaml_file or not db_file:
#         return Response({"detail": "yaml_file and db_file are required."}, status=status.HTTP_400_BAD_REQUEST)

#     serializer = RosbagSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def rosbag_json(request, pk):
    """
    Returns the JSON representation of a Rosbag instance.
    If the JSON file is already stored in the database, it returns that.
    Otherwise, it processes the rosbag file and generates the JSON.
    """
    try:
        instance = get_object_or_404(Rosbags, pk=pk)
        folder_path = Path(settings.MEDIA_ROOT) / "rosbags" / f"test_{pk}"
        msg_path = Path(settings.BASE_DIR) / "msg"  # msg directory

        if not folder_path.exists():
            return JsonResponse({"error": "rosbag folder not found"}, status=404)
        
        if not msg_path.exists():
            return JsonResponse({"error": "msg folder not found"}, status=404)
        
        if settings.JSON_FIELD_ENCODED:
        # Se esiste file JSON nel db, ritorna il suo contenuto direttamente
            if instance.json_file and instance.json_file.storage.exists(instance.json_file.name):
                # Apri e leggi il file JSON salvato
                with instance.json_file.open("r") as f:
                    data = f.read()
                # Restituisci come JsonResponse
                return JsonResponse(json.loads(data), safe=False)

        if instance.rosbag_file and instance.rosbag_file.storage.exists(instance.rosbag_file.name):
            # Se esiste il file rosbag, prova a convertirlo
            file_name = f"output_rosbag_{pk}.bag"
            return FileResponse(open(Path(folder_path / file_name), 'rb'), as_attachment=True, filename=file_name)

        # Altrimenti crea il JSON con il RosbagReader
        custom_msgs = [
            "State",
            "ConeArray",
            "Cone",
            "Waypoint",
            "WaypointArray",
            "VehicleState",
            "VehicleCmd",
        ]

        reader = RosbagReader(folder_path, msg_path, custom_msgs)
        data = reader.extract_data()

        # Apply compression to reduce file size
        compressed_data = compress_full_data(data)

        # Salva il JSON compresso nel campo json_file
        json_string = json.dumps(compressed_data)
        instance.json_file.save(f"data_{pk}.json", ContentFile(json_string), save=True)

        return JsonResponse(compressed_data, safe=False)

    except Exception as e:
        return JsonResponse({"error": f"Error while reading: {str(e)}"}, status=500)