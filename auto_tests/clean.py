from .models import Rosbags

def clean_missing_files():
    rosbags = Rosbags.objects.all()
    for r in rosbags:
        # Check if the associated file exists physically
        if r.zip_file and not r.zip_file.storage.exists(r.zip_file.name):
            print(f"Missing file for Rosbag {r.id}, clearing the field")
            r.zip_file = None
            r.save(update_fields=['zip_file'])