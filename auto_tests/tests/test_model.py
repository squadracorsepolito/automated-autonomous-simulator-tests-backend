from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from auto_tests.models import Rosbags
import tempfile

@override_settings(MEDIA_ROOT=tempfile.gettempdir())  # use temporary directory
class RosbagModelTest(TestCase):

    def setUp(self):
        self.rosbag = Rosbags.objects.create(
            track_name="TestTrack",
            mission_name="TestMission",
            avg_lap_time=12.5,
        )

    def test_create_rosbag(self):
        """Test basic creation"""
        self.assertEqual(self.rosbag.track_name, "TestTrack")
        self.assertEqual(self.rosbag.mission_name, "TestMission")
        self.assertEqual(self.rosbag.avg_lap_time, 12.5)
        self.assertFalse(self.rosbag.is_successful)  # default False
        self.assertEqual(self.rosbag.number_of_evaluated_cones_yellow, 0)

    def test_str_method(self):
        """Test __str__ output"""
        self.assertEqual(
            str(self.rosbag),
            "TestMission on TestTrack - Fail"
        )

        # Change status to successful and test again
        self.rosbag.is_successful = True
        self.assertEqual(str(self.rosbag), "TestMission on TestTrack - Success")

    def test_filefields_assignment(self):
        """Assign fake files to FileField without writing to real disk"""
        fake_rosbag = SimpleUploadedFile(f"fake_{self.rosbag.id}.bag", b"content")
        fake_json = SimpleUploadedFile(f"data_{self.rosbag.id}.json", b"{}")
        # Use the FieldFile.save() helper to ensure the storage backend is used
        self.rosbag.rosbag_file.save(fake_rosbag.name, fake_rosbag, save=False)
        self.rosbag.json_file.save(fake_json.name, fake_json, save=False)
        self.rosbag.save()

        # The stored name should include the uploaded filename (check basename)
        import os
        basename = os.path.basename(str(self.rosbag.rosbag_file))
        stem, ext = os.path.splitext(basename)
        self.assertTrue(stem.startswith("fake"))
        self.assertEqual(ext, ".bag")

        basename_json = os.path.basename(str(self.rosbag.json_file))
        stem_j, ext_j = os.path.splitext(basename_json)
        self.assertTrue(stem_j.startswith("data"))
        self.assertEqual(ext_j, ".json")

    def test_default_values(self):
        """Check default values of numeric and boolean fields"""
        self.assertEqual(self.rosbag.number_of_evaluated_cones_blue, 0)
        self.assertEqual(self.rosbag.number_of_evaluated_cones_unknown, 0)
        self.assertFalse(self.rosbag.is_successful)
        self.assertIsNone(self.rosbag.number_of_laps_completed)