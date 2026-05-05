from django.db import models

def rosbag_upload_path(instance, filename):
    return f'rosbags/test_{instance.id}/{filename}'

class Rosbags(models.Model):
    track_name = models.CharField(max_length=100)  # Track name
    mission_name = models.CharField(max_length=100)  # Mission name
    number_of_laps_completed = models.IntegerField(null=True, blank=True)  # Number of laps completed
    number_of_evaluated_cones_yellow = models.IntegerField(default=0)  # Yellow cones evaluated
    number_of_evaluated_cones_blue = models.IntegerField(default=0)  # Blue cones evaluated
    number_of_evaluated_cones_unknown = models.IntegerField(default=0)  # Unknown cones evaluated
    is_successful = models.BooleanField(default=False)  # Whether the mission was successful
    zip_file = models.FileField(upload_to='temp_zips/', null=True, blank=True)  # Temporary zip file
    rosbag_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True)  # ROS bag file
    db_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True)  # Database file from rosbag
    yaml_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True)  # YAML metadata file
    json_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True)  # JSON representation file
    avg_lap_time = models.FloatField()  # Average lap time in seconds
    timestamp = models.DateTimeField(auto_now_add=True)  # Creation timestamp

    def __str__(self):
        return f"{self.mission_name} on {self.track_name} - {'Success' if self.is_successful else 'Fail'}"
