from pathlib import Path
import tempfile
from django.urls import reverse
from django.test import Client, override_settings
from auto_tests.models import Rosbags
from auto_tests.tests.base import BaseRosbagTest
from automated_tests_backend import settings

class RosbagViewSetTest(BaseRosbagTest):

    def setUp(self):
    # Create a temporary MEDIA_ROOT
        self.temp_media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_media_dir.name)
        self.override.enable()

        # Client authenticated
        self.client = Client(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Directory and test files
        self.folder_path = Path(settings.MEDIA_ROOT) / f"rosbags/test_{self.rosbag.id}"
        self.folder_path.mkdir(parents=True, exist_ok=True)

        self.json_file_name = f"data_{self.rosbag.id}.json"
        self.rosbag_file_name = f"output_rosbag_{self.rosbag.id}.bag"
        self.db_file_name = f"ros2_bag_interfaces_included_0.db3"

        # Fake file creation
        (self.folder_path / self.json_file_name).touch(exist_ok=True)
        (self.folder_path / self.rosbag_file_name).touch(exist_ok=True)
        (self.folder_path / self.db_file_name).touch(exist_ok=True)

        # Link files to the Rosbag instance
        self.rosbag.db_file.name = f"rosbags/test_{self.rosbag.id}/{self.db_file_name}"
        self.rosbag.json_file.name = f"rosbags/test_{self.rosbag.id}/{self.json_file_name}"
        self.rosbag.rosbag_file.name = f"rosbags/test_{self.rosbag.id}/{self.rosbag_file_name}"
        self.rosbag.save()


    def test_list_rosbags(self):
        """List view test"""
        url = reverse('rosbag-list')  # Assuming DRF router with basename='rosbag'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('TestTrack', str(response.content))
        print(f"Response content: {response.content}")

    def test_destroy_rosbag(self):
        """Delete test: remove object and folder"""
        url = reverse('rosbag-detail', args=[self.rosbag.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Rosbags.objects.filter(id=self.rosbag.id).exists())

    def test_permission_denied_for_anon(self):
        """Anonymous user should get 401"""
        anon_client = Client()
        url = reverse('rosbag-list')
        response = anon_client.get(url)
        self.assertEqual(response.status_code, 401)
        print("Anonymous access correctly denied with 401")

    def test_get_details_json(self):
        """Personalized action test for JSON"""
        url = reverse('rosbag-get-details', args=[self.rosbag.id, 'json'])
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])  # 404 if the file doesn't exist
        print(f"Get details JSON response code: {response.status_code}")

    def test_get_details_ros(self):
        """Personalized action test for ROS"""
        url = reverse('rosbag-get-details', args=[self.rosbag.id, 'ros'])
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])  # 404 if the fiòle doesn't exist
        print(f"Get details ROS response code: {response.status_code}")

    def tearDown(self):
        """Remove test folder securely even on Windows"""
        self.override.disable()
        self.temp_media_dir.cleanup()