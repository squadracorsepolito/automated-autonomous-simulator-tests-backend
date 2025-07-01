# auto_tests/serializers.py
from rest_framework import serializers
from .models import Rosbags
import zipfile
from pathlib import Path
from django.conf import settings

class RosbagSerializer(serializers.ModelSerializer):
    rosbag_file = serializers.FileField(required=False, allow_null=True)
    db_file = serializers.FileField(required=False, allow_null=True)
    yaml_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Rosbags
        fields = '__all__'

    def create(self, validated_data):
        # Extract files from validated_data, if present
        yaml_file = validated_data.pop('yaml_file', None)
        db_file = validated_data.pop('db_file', None)
        rosbag_file = validated_data.pop('rosbag_file', None)

        # First create the base instance to get the ID
        instance = Rosbags.objects.create(**validated_data)

        # --- CASE 1: ZIP provided AND yaml/db NOT provided ---
        if rosbag_file and not yaml_file and not db_file:

            instance.rosbag_file.save(rosbag_file.name, rosbag_file, save=False)
            instance.save(update_fields=["rosbag_file"])

            file_path = Path(instance.rosbag_file.path)
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

                if extracted_yaml:
                    instance.yaml_file.name = f'rosbags/test_{instance.id}/{extracted_yaml.name}'
                if extracted_db:
                    instance.db_file.name = f'rosbags/test_{instance.id}/{extracted_db.name}'

                instance.rosbag_file.delete(save=False)
                instance.rosbag_file = None
                instance.save(update_fields=['yaml_file', 'db_file', 'rosbag_file'])

        # --- CASE 2: yaml/db provided (ZIP ignored) ---
        else:
            if yaml_file:
                instance.yaml_file.save(yaml_file.name, yaml_file, save=False)
            if db_file:
                instance.db_file.save(db_file.name, db_file, save=False)
            instance.save(update_fields=['yaml_file', 'db_file'])

        return instance
