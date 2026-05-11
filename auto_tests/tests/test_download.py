from django.test import Client
from pathlib import Path
from auto_tests.tests.base import BaseRosbagTest


class RosbagDownloadTest(BaseRosbagTest):

    def setUp(self):
        self.client = Client(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create a simple media folder for the test
        self.folder_path = Path("media/rosbags/test_67").resolve()
        self.folder_path.mkdir(parents=True, exist_ok=True)

        self.json_file_name = 'data_67.json'
        self.rosbag_file_name = 'output_rosbag_67.bag'

        # Create placeholder files if they don't exist
        (self.folder_path / self.json_file_name).touch(exist_ok=True)
        (self.folder_path / self.rosbag_file_name).touch(exist_ok=True)


    def test_download_rosbag(self):

        url = f'/api/rosbags/{self.rosbag.id}/ros'
        response = self.client.get(url, follow=True)

        # Check status
        self.assertEqual(response.status_code, 200)
        # Check that the file is present in the response
        content_disposition = response.get('Content-Disposition')
        self.assertIsNotNone(content_disposition)
        self.assertIn(self.rosbag_file_name, content_disposition)

        # Save the received file locally
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

        # Save the received file locally
        # Write the file in streaming
        downloaded_file = f'media/test/downloaded_{self.json_file_name}'
        with open(downloaded_file, 'wb') as f:
            for chunk in response.streaming_content:
                f.write(chunk)
        print(f"File downloaded as {downloaded_file}")
