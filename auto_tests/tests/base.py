from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from automated_tests_backend import settings
from auto_tests.models import Rosbags

class BaseRosbagTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Utente di test
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.user.is_staff = True
        cls.user.save()

        # Token
        cls.token, _ = Token.objects.get_or_create(user=cls.user)

        # COMMENT THIS LINE TO WORK ONLY WITH ROSBAG
        settings.JSON_FIELD_ENCODED = False

        # Oggetto Rosbag
        cls.rosbag = Rosbags.objects.create(
            id=67,
            track_name="TestTrack",
            mission_name="TestMission",
            avg_lap_time=10.0,
            rosbag_file='rosbags/test_67/output_rosbag_67.bag',
            json_file='rosbags/test_67/data_67.json',
            db_file='rosbags/test_67/ros2_bag_interfaces_included_0.db3',
            yaml_file='rosbags/test_67/metadata.yaml',
        )

    # Test fixture created; avoid noisy prints in test output