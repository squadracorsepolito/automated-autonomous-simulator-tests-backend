# auto_tests/serializers.py
from rest_framework import serializers
from .models import Rosbags
import zipfile
from pathlib import Path
from django.conf import settings

class RosbagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rosbags
        fields = '__all__'  # all fields from the model

    def create(self, validated_data):
        instance = super().create(validated_data)

        # Estrai i file dal validated_data, se ci sono
        yaml_file = validated_data.pop('yaml_file', None)
        db_file = validated_data.pop('db_file', None)
        rosbag_file = validated_data.get('rosbag_file', None)

        # Prima creo l'istanza senza i file per ottenere l'id
        instance = Rosbags.objects.create(**validated_data)

        # Ora, se ci sono file yaml e db, li salvo *dopo* che instance ha id
        if yaml_file:
            instance.yaml_file.save(yaml_file.name, yaml_file, save=False)
        if db_file:
            instance.db_file.save(db_file.name, db_file, save=False)
        if rosbag_file:
            # Nel caso sia zip, lascia che la parte zip nel serializer gestisca extraction ecc.
            instance.rosbag_file = rosbag_file

        # Salvo l'istanza con i file aggiornati
        instance.save()


        if not instance.rosbag_file:
            return instance

        file_path = Path(instance.rosbag_file.path)

        if zipfile.is_zipfile(file_path):
            extract_dir = Path(settings.MEDIA_ROOT) / f'rosbags/test_{instance.id}'
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # get the list of all files
                all_files = zip_ref.namelist()

                # extract removing the common root folder (if exists)
                root_folder = None
                # If all files start with the same folder, that's root_folder
                if all_files:
                    root_folder = all_files[0].split('/')[0]

                    # check if all start with root_folder/
                    if not all(f.startswith(root_folder + '/') for f in all_files):
                        root_folder = None

                for file in all_files:
                    if root_folder:
                        # remove the root folder from the path
                        relative_path = Path(file).relative_to(root_folder)
                    else:
                        relative_path = Path(file)

                    target_path = extract_dir / relative_path

                    if file.endswith('/'):  # it's a directory
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(file) as source_file, open(target_path, 'wb') as target_file:
                            target_file.write(source_file.read())

            yaml_file = next(extract_dir.glob("*.yaml"), None)
            db_file = next(extract_dir.glob("*.db*"), None)

            if yaml_file:
                instance.yaml_file.name = f'rosbags/test_{instance.id}/{yaml_file.name}'
            if db_file:
                instance.db_file.name = f'rosbags/test_{instance.id}/{db_file.name}'

            instance.save(update_fields=['yaml_file', 'db_file'])

            # Elimina lo zip usando il metodo di Django
            instance.rosbag_file.delete(save=False)
            instance.rosbag_file = None
            instance.save(update_fields=['rosbag_file'])
        else:
            dir = Path(settings.MEDIA_ROOT) / f'rosbags/test_{instance.id}'

        return instance