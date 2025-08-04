from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, FileResponse
from django.core.files.base import ContentFile
from django.conf import settings

from pathlib import Path
import shutil
import json

from .models import Rosbags
from .serializers import RosbagSerializer
from .permissions import IsStaffUser
from .clean import clean_missing_files
from .rosbag_reader import RosbagReader
from .utils import compress_full_data


class RosbagViewSet(ModelViewSet):
    queryset = Rosbags.objects.all().order_by('-timestamp')
    serializer_class = RosbagSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        clean_missing_files()
        return super().get_queryset()

    def perform_destroy(self, instance):
        """Override default delete to also remove associated files"""
        if instance.db_file:
            folder = Path(instance.db_file.path).parent
            if folder.exists():
                shutil.rmtree(folder)
        instance.delete()

    @action(detail=True, methods=["get"], url_path="detail")
    def get_json(self, request, pk=None):
        """
        Custom action: GET /rosbags/{pk}/detail/
        Generates or returns cached JSON from rosbag data, or ros file
        """
        try:
            instance = self.get_object()
            folder_path = Path(settings.MEDIA_ROOT) / "rosbags" / f"test_{pk}"
            msg_path = Path(settings.BASE_DIR) / "msg"

            if not folder_path.exists():
                return JsonResponse({"error": "rosbag folder not found"}, status=404)
            if not msg_path.exists():
                return JsonResponse({"error": "msg folder not found"}, status=404)

            # If JSON already saved in DB, return it
            if settings.JSON_FIELD_ENCODED:
                if instance.json_file and instance.json_file.storage.exists(instance.json_file.name):
                    with instance.json_file.open("r") as f:
                        data = f.read()
                    return JsonResponse(json.loads(data), safe=False)

            # If rosbag exists, return the raw file
            if instance.rosbag_file and instance.rosbag_file.storage.exists(instance.rosbag_file.name):
                file_name = f"output_rosbag_{pk}.bag"
                return FileResponse(open(Path(folder_path / file_name), 'rb'), as_attachment=True, filename=file_name)

            # Otherwise, parse rosbag
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
            compressed_data = compress_full_data(data)

            # Save JSON file to DB
            json_string = json.dumps(compressed_data)
            instance.json_file.save(f"data_{pk}.json", ContentFile(json_string), save=True)

            return JsonResponse(compressed_data, safe=False)

        except Exception as e:
            return JsonResponse({"error": f"Error while reading: {str(e)}"}, status=500)
