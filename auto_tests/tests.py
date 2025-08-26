from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from pathlib import Path
from auto_tests.models import Rosbags
from automated_tests_backend import settings

class RosbagDownloadTest(TestCase):
    def setUp(self):
        relative_dir = Path("media/rosbags/test_67")
        msg_dir = relative_dir.resolve()    
        print(f"Using media directory: {msg_dir}")

        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user.is_staff = True  # if the view requires admin
        self.user.save()

        # Generate the token
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client = Client(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Test file paths
        self.json_file_name = 'data_67.json'
        self.rosbag_file_name = 'output_rosbag_67.bag'
        self.folder_path = msg_dir

        # Create a test file if it doesn't exist
        (self.folder_path / self.json_file_name).touch(exist_ok=True)
        (self.folder_path / self.rosbag_file_name).touch(exist_ok=True)

        # COMMENT THIS LINE TO WORK ONLY WITH ROSBAG
        settings.JSON_FIELD_ENCODED = False

        self.rosbag = Rosbags.objects.create(
            id=67,
            track_name="TestTrack",
            mission_name="TestMission",
            avg_lap_time=10.0,
            rosbag_file=f'rosbags/test_67/{self.rosbag_file_name}',
            json_file=f'rosbags/test_67/{self.json_file_name}',
        )
        print(f"ID Rosbag creato: {self.rosbag.id}")
        print(f"Rosbag creato: {self.rosbag.rosbag_file}")
        print(f"File JSON creato: {self.rosbag.json_file}")
        print("\n\n")


    def test_download_rosbag(self):

        url = f'/api/rosbags/{self.rosbag.id}/ros'
        response = self.client.get(url, follow=True)

        # Check status
        self.assertEqual(response.status_code, 200)
        # Check that the file is present in the response
        content_disposition = response.get('Content-Disposition')
        self.assertIsNotNone(content_disposition)
        self.assertIn(self.rosbag_file_name, content_disposition)

        # Save the received file locally (optional)
        # Write the file in streaming
        downloaded_file = f'media/test/downloaded_{self.rosbag_file_name}'
        with open(downloaded_file, 'wb') as f:
            for chunk in response.streaming_content:
                f.write(chunk)
        print(f"File downloaded as {downloaded_file}")
    
    def test_download_json(self):
        """
        Actually it doesn't run together with rosbag, so if you want to have the json you have to comment - settings.JSON_FIELD_ENCODED = False
        """
        
        url = f'/api/rosbags/{self.rosbag.id}/json' 
        response = self.client.get(url, follow=True)

        # Check status
        self.assertEqual(response.status_code, 200)
        # Check that the file is present in the response
        content_disposition = response.get('Content-Disposition')
        self.assertIsNotNone(content_disposition)
        self.assertIn(self.json_file_name, content_disposition)

        # Save the received file locally (optional)
        # Write the file in streaming
        downloaded_file = f'media/test/downloaded_{self.json_file_name}'
        with open(downloaded_file, 'wb') as f:
            for chunk in response.streaming_content:
                f.write(chunk)
        print(f"File downloaded as {downloaded_file}")
