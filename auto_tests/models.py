from django.db import models

def rosbag_upload_path(instance, filename):
    return f'rosbags/test_{instance.id}/{filename}'

class Rosbags(models.Model):
    track_name = models.CharField(max_length=100)  # Nome pista
    mission_name = models.CharField(max_length=100)  # Nome missione
    number_of_laps_completed = models.IntegerField(null=True, blank=True)  # Numero giri completati
    number_of_evaluated_cones_yellow = models.IntegerField()  # Coni gialli valutati
    number_of_evaluated_cones_blue = models.IntegerField()  # Coni blu valutati
    is_successful = models.BooleanField(default=False)  # Successo o meno
    rosbag_file = models.FileField(upload_to='temp_zips/', null=True, blank=True)
    db_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True) # File rosbag (cartella media/rosbags)
    yaml_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True) # File rosbag (cartella media/rosbags)
    json_file = models.FileField(upload_to=rosbag_upload_path, null=True, blank=True) # File rosbag (cartella media/rosbags)
    avg_lap_time = models.FloatField()  # Tempo medio giro (float)
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp creazione (automatico)

    def __str__(self):
        return f"{self.mission_name} on {self.track_name} - {'Success' if self.is_successful else 'Fail'}"
