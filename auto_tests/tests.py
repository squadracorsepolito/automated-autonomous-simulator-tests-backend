from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from pathlib import Path
from auto_tests.models import Rosbags


class RosbagDownloadTest(TestCase):
    def setUp(self):
        relative_dir = Path("media/rosbags/test_67") # <-- cambia se necessario
        msg_dir = relative_dir.resolve()    
        print(f"Using media directory: {msg_dir}")

        # Crea un utente di test
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user.is_staff = True  # se la view richiede admin
        self.user.save()

        # Genera il token
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client = Client(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Percorso file di test
        self.file_name = 'output_rosbag_67.bag'
        self.folder_path = msg_dir  # modifica con il path corretto

        # Crea un file di test se non esiste
        (self.folder_path / self.file_name).touch(exist_ok=True)

        self.rosbag = Rosbags.objects.create(
            id=67,
            track_name="TestTrack",
            mission_name="TestMission",
            avg_lap_time=10.0,
            rosbag_file=f'rosbags/test_67/{self.file_name}',  # deve corrispondere alla posizione reale del file
        )
        print(f"Rosbag creato: {self.rosbag.rosbag_file}")
        print(f"ID Rosbag creato: {self.rosbag.id}")

    def test_download_rosbag(self):
        print("STO TESTANDO\n\n")
        url = f'/api/rosbags/{self.rosbag.id}/detail'  # modifica con l'ID del rosbag
        response = self.client.get(url, follow=True)

        # Controllo status
        self.assertEqual(response.status_code, 200)
        # Controllo che il file sia presente nella risposta
        content_disposition = response.get('Content-Disposition')
        self.assertIsNotNone(content_disposition)
        self.assertIn(self.file_name, content_disposition)
        
        # Salvo localmente il file ricevuto (opzionale)
        # Scrivi il file in streaming
        downloaded_file = f'media/test/downloaded_{self.file_name}'
        with open(downloaded_file, 'wb') as f:
            for chunk in response.streaming_content:
                f.write(chunk)
        print(f"File scaricato come {downloaded_file}")
