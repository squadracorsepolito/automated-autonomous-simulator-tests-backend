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
from django.http import JsonResponse, FileResponse
import json

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
    try:
        instance = get_object_or_404(Rosbags, pk=pk)
        folder_path = Path(settings.MEDIA_ROOT) / "rosbags" / f"test_{pk}"
        msg_path = Path(settings.BASE_DIR) / "msg"  # msg directory

        if not folder_path.exists():
            return JsonResponse({"error": "Cartella rosbag non trovata"}, status=404)
        
        if not msg_path.exists():
            return JsonResponse({"error": "Cartella msg non trovata"}, status=404)

        # Se esiste file JSON nel db, ritorna il suo contenuto direttamente
        if instance.json_file and instance.json_file.storage.exists(instance.json_file.name):
            # Apri e leggi il file JSON salvato
            with instance.json_file.open("r") as f:
                data = f.read()
            # Restituisci come JsonResponse
            return JsonResponse(json.loads(data), safe=False)

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
        # data = reader.extract_data()
        output_path = reader.test_typestore(pk)  # Esegui il test del typestore

        # Salva il JSON nel campo json_file
        # json_string = json.dumps(data, indent=4)
        # instance.json_file.save(f"data_{pk}.json", ContentFile(json_string), save=True)
        if not output_path.exists():
            return Response({"error": "Errore nella conversione"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return FileResponse(open(output_path, 'rb'), as_attachment=True, filename=f'output_rosbag_{pk}.bag')
        # return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": f"Errore lettura rosbag: {str(e)}"}, status=500)