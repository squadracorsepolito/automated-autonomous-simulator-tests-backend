from .models import Rosbags

def clean_missing_files():
    rosbags = Rosbags.objects.all()
    for r in rosbags:
        # Check if the associated file exists physically
        if r.rosbag_file and not r.rosbag_file.storage.exists(r.rosbag_file.name):
            print(f"Missing file for Rosbag {r.id}, clearing the field")
            r.rosbag_file = None
            r.save(update_fields=['rosbag_file'])