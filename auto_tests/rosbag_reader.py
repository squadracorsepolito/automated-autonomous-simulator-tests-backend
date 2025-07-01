# rosbag_reader.py
from pathlib import Path
from django.conf import settings
from rosbags.rosbag2 import Reader
from rosbags.serde import deserialize_cdr
import zipfile
import tempfile
import shutil

class RosbagReader:
    """
    Utility class to read ROS2 rosbag files stored in MEDIA_ROOT/rosbags as .zip archives or folders.
    """
    def __init__(self, base_dir: Path = None):
        media_root = Path(settings.MEDIA_ROOT)
        self.base_dir = base_dir or (media_root / 'rosbags')

    def list_rosbags(self) -> list[str]:
        """
        Lists available rosbags by base name (strip .zip suffix).
        """
        if not self.base_dir.exists():
            return []
        names = []
        for p in self.base_dir.iterdir():
            if p.is_dir():
                names.append(p.name)
            elif p.suffix == '.zip':
                names.append(p.stem)
        return names

    def _prepare_path(self, bag_name: str) -> Path:
        """
        Returns a directory path ready to be read by Reader.
        If a folder exists, return it.
        If a zip exists, extract to temp dir and return that dir.
        """
        folder = self.base_dir / bag_name
        zipf = self.base_dir / f"{bag_name}.zip"
        if folder.is_dir():
            return folder
        if zipf.is_file():
            # extract to temp directory
            temp_dir = Path(tempfile.mkdtemp(prefix=f"rosbag_{bag_name}_"))
            with zipfile.ZipFile(zipf, 'r') as zf:
                zf.extractall(temp_dir)
            # track temp for cleanup
            setattr(self, '_temp_dir', temp_dir)
            return temp_dir
        raise FileNotFoundError(f"Rosbag '{bag_name}' not found as folder or zip in {self.base_dir}")

    def _cleanup(self):
        """
        Cleanup any temporary extraction dir.
        """
        temp = getattr(self, '_temp_dir', None)
        if temp and temp.exists():
            shutil.rmtree(temp)
            delattr(self, '_temp_dir')

    def read_topics(self, bag_name: str) -> list[dict]:
        """
        Reads available topics and types in the specified rosbag2.
        """
        path = self._prepare_path(bag_name)
        topics_info = []
        try:
            with Reader(str(path)) as reader:
                for conn in reader.connections:
                    topics_info.append({
                        'id': conn.id,
                        'topic': conn.topic,
                        'msgtype': conn.msgtype
                    })
            return topics_info
        finally:
            self._cleanup()

    def read_messages(self, bag_name: str, topic_filter: str = None, max_messages: int = None):
        """
        Generator yielding messages from a rosbag2.
        """
        path = self._prepare_path(bag_name)
        count = 0
        try:
            with Reader(str(path)) as reader:
                for conn, timestamp, rawdata in reader.messages():
                    if topic_filter and conn.topic != topic_filter:
                        continue
                    try:
                        msg = deserialize_cdr(rawdata, conn.msgtype)
                    except Exception:
                        msg = rawdata
                    yield {'topic': conn.topic, 'timestamp': timestamp, 'msg': msg}
                    count += 1
                    if max_messages and count >= max_messages:
                        break
        finally:
            self._cleanup()

# views.py remains unchanged
