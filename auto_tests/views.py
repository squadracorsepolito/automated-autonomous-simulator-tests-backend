from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

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
        """
        Delete Rosbag instance and its folder safely.
        Works even if some files are missing or open.
        """
        folder = None

        # Search for folder from existing files
        for f in [instance.rosbag_file, instance.json_file, instance.db_file]:
            if f and hasattr(f, "path"):
                folder = Path(f.path).parent
                break

        # If not found, build folder by convention
        if not folder:
            folder = Path(settings.MEDIA_ROOT) / f"rosbags/test_{instance.id}"

        # Close any open files (on Windows this can block rmtree)
        for f in [instance.rosbag_file, instance.json_file, instance.db_file]:
            if f and hasattr(f, "close"):
                try:
                    f.close()
                except Exception:
                    pass

        # Delete the folder (ignore errors)
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)

        # Delete the object from the DB
        instance.delete()

    @action(detail=True, methods=["get"],  url_path=r"(?P<file_type>json|ros)")
    def get_details(self, request, pk=None, file_type=None):
        """
        Custom action: GET /rosbags/{pk}/json/ or /rosbags/{pk}/ros/
        Generates or returns cached JSON from rosbag data, or ROS file
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
            if file_type == "json":
                if instance.json_file and instance.json_file.storage.exists(instance.json_file.name):
                    file_name = f"data_{pk}.json"
                    return FileResponse(open(Path(folder_path / file_name), 'rb'),as_attachment=True, filename=file_name)
            elif file_type == "ros":
                # If rosbag exists, return the raw file
                if instance.rosbag_file and instance.rosbag_file.storage.exists(instance.rosbag_file.name):
                    file_name = f"output_rosbag_{pk}.bag"
                    return FileResponse(open(Path(folder_path / file_name), 'rb'), as_attachment=True, filename=file_name)

            # Otherwise create the JSON with the RosbagReader
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
            
            if file_type == "json":
                data = reader.extract_data()
                compressed_data = compress_full_data(data)
                # Save JSON file to DB
                json_string = json.dumps(compressed_data)
                file_name = f"data_{pk}.json"
                instance.json_file.save(file_name, ContentFile(json_string), save=True)
        
            elif file_type == "ros":
                file_name = f"output_rosbag_{pk}.bag"
                # Save ROS bag file to DB
                reader.test_typestore(pk)
                instance.rosbag_file.save(file_name, ContentFile(data), save=True)

            return FileResponse(open(Path(folder_path / file_name), 'rb'),as_attachment=True, filename=file_name)

        except Exception as e:
            return JsonResponse({"error": f"Error while reading: {str(e)}"}, status=500)
