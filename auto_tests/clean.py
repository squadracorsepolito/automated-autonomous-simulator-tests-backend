import logging
from .models import Rosbags

logger = logging.getLogger(__name__)

def clean_missing_files():
    """
    Clean up database entries for missing files.
    Checks if uploaded files still exist physically and removes references if not.
    """
    rosbags = Rosbags.objects.all()
    for r in rosbags:
        # Check if the associated file exists physically
        if r.zip_file and not r.zip_file.storage.exists(r.zip_file.name):
            logger.warning(f"Missing file for Rosbag {r.id}, clearing the field")
            r.zip_file = None
            r.save(update_fields=['zip_file'])