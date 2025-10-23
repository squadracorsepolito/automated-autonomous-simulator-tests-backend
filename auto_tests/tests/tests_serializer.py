from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers as drf_serializers
import tempfile
from unittest.mock import patch
import io
import zipfile		
import os

from auto_tests.serializers import RosbagSerializer
from auto_tests.tests.base import BaseRosbagTest


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class RosbagSerializerTest(BaseRosbagTest):

	def test_validate_accepts_zip(self):
		"""Providing only a ZIP file should be accepted by validate()."""
		serializer = RosbagSerializer()
		data = {'zip_file': SimpleUploadedFile('test.zip', b'zipcontent')}
		validated = serializer.validate(data)
		self.assertIs(validated, data)

	def test_validate_accepts_yaml_and_db(self):
		"""Providing both YAML and DB files should be accepted by validate()."""
		serializer = RosbagSerializer()
		data = {
			'yaml_file': SimpleUploadedFile('metadata.yaml', b'{}'),
			'db_file': SimpleUploadedFile('ros2_bag.db', b'bin')
		}
		validated = serializer.validate(data)
		self.assertIs(validated, data)

	def test_validate_accepts_nothing(self):
		"""Providing no files at all should be accepted (handled later by view/logic)."""
		serializer = RosbagSerializer()
		data = {}
		validated = serializer.validate(data)
		self.assertIs(validated, data)

	def test_validate_rejects_partial_inputs(self):
		"""Providing only YAML or only DB should raise a ValidationError."""
		serializer = RosbagSerializer()
		# Only YAML
		with self.assertRaises(drf_serializers.ValidationError):
			serializer.validate({'yaml_file': SimpleUploadedFile('metadata.yaml', b'{}')})

		# Only DB
		with self.assertRaises(drf_serializers.ValidationError):
			serializer.validate({'db_file': SimpleUploadedFile('ros2_bag.db', b'bin')})

	def test_create_with_yaml_and_db_saves_files(self):
		"""Ensure create() saves provided YAML and DB files on the instance.

		Patch out heavy rosbag/json processing so the test focuses on file handling.
		"""
		payload = {
			'track_name': 'TrackX',
			'mission_name': 'MissionY',
			'avg_lap_time': 7.5,
			'yaml_file': SimpleUploadedFile('metadata.yaml', b'meta'),
			'db_file': SimpleUploadedFile('ros2_bag_interfaces_included_0.db3', b'dbcontent')
		}

		serializer = RosbagSerializer(data=payload)
		self.assertTrue(serializer.is_valid(), msg=getattr(serializer, 'errors', None))

		# Patch both rosbag_serializer and json_serializer to avoid heavy processing
		with patch.object(RosbagSerializer, 'rosbag_serializer', return_value=f"rosbags/test_1/output_rosbag_1.bag"), \
			 patch.object(RosbagSerializer, 'json_serializer', return_value=SimpleUploadedFile('data_1.json', b"{}")):
			instance = serializer.save()

		# Instance should be persisted and files assigned
		self.assertIsNotNone(instance.pk)
		# Allow for storage backends that append unique suffixes to filenames
		yaml_basename = os.path.basename(str(instance.yaml_file))
		yaml_stem, yaml_ext = os.path.splitext(yaml_basename)
		self.assertTrue(yaml_stem.startswith('metadata'))
		self.assertEqual(yaml_ext, '.yaml')

		db_basename = os.path.basename(str(instance.db_file))
		self.assertIn('ros2_bag_interfaces_included_0', db_basename)
		self.assertTrue(db_basename.endswith('.db3'))
		# Since we didn't provide a ZIP, zip_file should be empty/None
		self.assertFalse(instance.zip_file)

	def test_create_with_zip_extracts_and_assigns_yaml_db(self):
		"""Create with a ZIP file containing metadata.yaml and a DB file; assert they get assigned."""
		# Build an in-memory zip with metadata.yaml and a dummy db file
		buf = io.BytesIO()
		with zipfile.ZipFile(buf, 'w') as zf:
			zf.writestr('root_folder/metadata.yaml', 'key: value')
			zf.writestr('root_folder/ros2_bag_interfaces_included_0.db3', b'dbbytes')
		buf.seek(0)

		zip_file = SimpleUploadedFile('test_rosbag.zip', buf.read(), content_type='application/zip')

		payload = {
			'track_name': 'ZipTrack',
			'mission_name': 'ZipMission',
			'avg_lap_time': 5.0,
			'zip_file': zip_file,
		}

		serializer = RosbagSerializer(data=payload)
		self.assertTrue(serializer.is_valid(), msg=getattr(serializer, 'errors', None))

		# Patch rosbag_serializer/json_serializer to avoid invoking RosbagReader
		with patch.object(RosbagSerializer, 'rosbag_serializer', return_value=f"rosbags/test_2/output_rosbag_2.bag"), \
			 patch.object(RosbagSerializer, 'json_serializer', return_value=SimpleUploadedFile('data_2.json', b"{}")):
			instance = serializer.save()

		# After save, zip should have been removed and yaml/db assigned
		self.assertIsNotNone(instance.pk)
		self.assertTrue(bool(instance.yaml_file), "yaml_file should be set after extracting zip")
		self.assertTrue(bool(instance.db_file), "db_file should be set after extracting zip")
		# zip_file should be cleared
		self.assertFalse(instance.zip_file)

