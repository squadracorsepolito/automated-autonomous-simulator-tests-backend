from django.db import models

def rosbag_upload_path(instance, filename):
    return f'rosbags/test_{instance.id}/{filename}'

class Rosbags(models.Model):
    track_name = models.CharField(max_length=100)  # track name
    mission_name = models.CharField(max_length=100)  # mission name
    number_of_laps_completed = models.IntegerField(null=True, blank=True)  # number of laps completed
    number_of_evaluated_cones_yellow = models.IntegerField(default=0)  # yellow cones evaluated
    number_of_evaluated_cones_blue = models.IntegerField(default=0)  # blue cones evaluated
    number_of_evaluated_cones_unknown = models.IntegerField(default=0)  # unknown cones evaluated
    is_successful = models.BooleanField(default=False)  # Success or not
    zip_file = models.FileField(upload_to='temp_zips/', null=True, blank=True)
    rosbag_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True)
    db_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True) # Rosbag file (media/rosbags folder)
    yaml_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True) # Rosbag file (media/rosbags folder)
    json_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True) # Rosbag file (media/rosbags folder)
    avg_lap_time = models.FloatField()  # Average lap time (float)
    timestamp = models.DateTimeField(auto_now_add=True)  # Creation timestamp (automatic)

    def __str__(self):
        return f"{self.mission_name} on {self.track_name} - {'Success' if self.is_successful else 'Fail'}"
