from django.db import models

class Rosbags(models.Model):
    track_name = models.CharField(max_length=100)  # Nome pista
    mission_name = models.CharField(max_length=100)  # Nome missione
    number_of_laps_completed = models.IntegerField()  # Numero giri completati
    number_of_evaluated_cones_yellow = models.IntegerField()  # Coni gialli valutati
    number_of_evaluated_cones_blue = models.IntegerField()  # Coni blu valutati
    is_successful = models.BooleanField(default=False)  # Successo o meno
    rosbag_file = models.FileField(upload_to='rosbags/', null=True, blank=True) # File rosbag (cartella media/rosbags)
    avg_lap_time = models.FloatField()  # Tempo medio giro (float)
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp creazione (automatico)

    def __str__(self):
        return f"{self.mission_name} on {self.track_name} - {'Success' if self.is_successful else 'Fail'}"
