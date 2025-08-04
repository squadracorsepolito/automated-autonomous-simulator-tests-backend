# auto_tests/serializers.py
from rest_framework import serializers
from .models import Rosbags
import zipfile
from pathlib import Path
from django.conf import settings
import json
import shutil
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .rosbag_reader import RosbagReader  # Import the utility class to read rosbag files
from django.core.files.base import ContentFile
from .utils import compress_full_data  # Import shared utility functions
from django.core.files import File
from rest_framework.exceptions import ValidationError
from django.db import transaction
import shutil

class RosbagSerializer(serializers.ModelSerializer):
    zip_file = serializers.FileField(required=False, allow_null=True)
    db_file = serializers.FileField(required=False, allow_null=True)
    yaml_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Rosbags
        fields = '__all__'

    def validate(self, data):
        zip_file = data.get('zip_file')
        yaml_file = data.get('yaml_file')
        db_file = data.get('db_file')

        #CASE 1 -> if zip file is present and yaml and db are not provided data would be taken from zip.
        yaml_and_db = yaml_file and db_file                                 #CASE 2
        nothing_provided = not zip_file and not yaml_file and not db_file   #CASE nothing provided

        if zip_file or yaml_and_db or nothing_provided:
            return data

        # Invalid case: neither combination 1 nor 2
        raise serializers.ValidationError(
            "You must provide a ZIP rosbag file OR both YAML and DB files."
        )

    def json_serializer(self, pk):
        folder_path = Path(settings.MEDIA_ROOT) / "rosbags" / f"test_{pk}"
        msg_path = Path(settings.BASE_DIR) / "msg"

        if not folder_path.exists():
            raise FileNotFoundError("Rosbag folder not found")
        if not msg_path.exists():
            raise FileNotFoundError("Msg folder not found")

        custom_msgs = [
            "State", "ConeArray", "Cone", "Waypoint",
            "WaypointArray", "VehicleState", "VehicleCmd"
        ]
        
        # Initialize the RosbagReader with the folder path, msg path, and custom message types
        reader = RosbagReader(folder_path, msg_path, custom_msgs)
        data = reader.extract_data()

        # Apply compression to reduce file size
        compressed_data = compress_full_data(data)

        # Serialize the compressed data to JSON format
        json_string = json.dumps(compressed_data)

        return ContentFile(json_string)
    
    def rosbag_serializer(self, pk):
        folder_path = Path(settings.MEDIA_ROOT) / "rosbags" / f"test_{pk}"
        msg_path = Path(settings.BASE_DIR) / "msg"

        if not folder_path.exists():
            raise FileNotFoundError("Rosbag folder not found")
        if not msg_path.exists():
            raise FileNotFoundError("Msg folder not found")

        custom_msgs = [
            "State", "ConeArray", "Cone", "Waypoint",
            "WaypointArray", "VehicleState", "VehicleCmd"
        ]
        
        # Initialize the RosbagReader with the folder path, msg path, and custom message types
        reader = RosbagReader(folder_path, msg_path, custom_msgs)
        output_path = reader.test_typestore(pk)

        return output_path

    def create(self, validated_data):
        # Extract files from validated_data, if present
        yaml_file = validated_data.pop('yaml_file', None)
        db_file = validated_data.pop('db_file', None)
        zip_file = validated_data.pop('zip_file', None)

        yaml_and_db = yaml_file and db_file    
        # Ensure that at least one of the files is provided
        with transaction.atomic():
            # First create the base instance to get the ID
            instance = Rosbags.objects.create(**validated_data)

            # --- CASE 1: ZIP provided AND yaml/db NOT provided ---
            if zip_file and not yaml_and_db:

                instance.zip_file.save(zip_file.name, zip_file, save=False)
                instance.save(update_fields=["zip_file"])

                file_path = Path(instance.zip_file.path)
                if zipfile.is_zipfile(file_path):
                    extract_dir = Path(settings.MEDIA_ROOT) / f'rosbags/test_{instance.id}'
                    extract_dir.mkdir(parents=True, exist_ok=True)

                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        all_files = zip_ref.namelist()

                        root_folder = all_files[0].split('/')[0] if all_files else None
                        if not all(f.startswith(root_folder + '/') for f in all_files):
                            root_folder = None

                        for file in all_files:
                            if file.endswith('/'):
                                continue
                            relative_path = Path(file).relative_to(root_folder) if root_folder else Path(file)
                            target_path = extract_dir / relative_path
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            with zip_ref.open(file) as src, open(target_path, 'wb') as dst:
                                dst.write(src.read())

                    # Search for files
                    extracted_yaml = next(extract_dir.glob("*.yaml"), None)
                    extracted_db = next(extract_dir.glob("*.db*"), None)

                    # Check if both extracted files are present
                    if extracted_yaml and extracted_db:
                        # Save the extracted files to the instance
                        yaml_path = str(extracted_yaml.relative_to(settings.MEDIA_ROOT))
                        db_path = str(extracted_db.relative_to(settings.MEDIA_ROOT))

                        instance.yaml_file.name = yaml_path
                        instance.db_file.name   = db_path

                        # Now that the extracted files have been saved, delete the ZIP
                        instance.zip_file.delete(save=False)
                        instance.zip_file = None

                        instance.save(update_fields=['yaml_file', 'db_file', 'zip_file'])
                    else:
                        # cancella la cartella estratta perché non valida
                        if extract_dir.exists():
                            shutil.rmtree(extract_dir)
                        # Raise a clear error if files are missing
                        raise ValidationError("The extracted files do not contain the required yaml or db files.")
            # --- CASE 2: yaml/db provided (ZIP ignored) ---
            else:
                if yaml_and_db:
                    instance.yaml_file.save('metadata.yaml', yaml_file, save=False) # The rosbag2 library for python wants named metadata.yaml
                    instance.db_file.save(db_file.name, db_file, save=False)

                    instance.save(update_fields=['yaml_file', 'db_file'])
                # This part of code raise error if you do not provide anything
                # else: 
                #     #Check if the files are correctly uploaded
                #     raise ValidationError("The file required both yaml and db files.")
    
            # Serialize the JSON data
            if instance.db_file and instance.yaml_file:
                fields = []  # Fields to update in the instance
                if settings.JSON_FIELD_ENCODED:  # If JSON is enabled, serialize the data
                    fields.append('json_file')  # Add json_file to the fields to update
                    json_content = self.json_serializer(instance.pk) # Get the JSON content as a ContentFile
                    json_filename = f"data_{instance.pk}.json" # Name the JSON file

                    instance.json_file.save(json_filename, json_content, save=False) # Save the JSON file without saving the instance yet

                # Serialize the ROS bag data
                fields.append('rosbag_file')

                # Create the ROS bag file using the rosbag_serializer
                # This will create the ROS bag file in the media/rosbags/test_{pk}
                # Use the rosbag_serializer to get the path of the ROS bag file
                rosbag_path = str(self.rosbag_serializer(instance.pk)) # Get the path
                if f"output_rosbag_{instance.pk}.bag" in rosbag_path: # Name the ROS file
                    instance.rosbag_file.name = rosbag_path  # solo il path relativo al MEDIA_ROOT
                
                instance.save(update_fields=fields) # Save the instance with the new JSON file


            return instance
