from pathlib import Path
from rosbags.rosbag2 import Reader
from rosbags.serde import deserialize_cdr


class RosbagReader:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def _ros_msg_to_dict(self, msg):
        if hasattr(msg, '__slots__'):
            return {slot: getattr(msg, slot) for slot in msg.__slots__}
        return {}

    def extract_data(self):
        result = []

        with Reader(str(self.base_path)) as reader:
            connections = [c for c in reader.connections]
            print(connections)  # Debugging line to see the connections
            for conn in connections:
                for _, timestamp, rawdata in reader.messages(connections=[conn]):
                    try:
                        obj = deserialize_cdr(rawdata, conn.msgdef)
                        msg = self._ros_msg_to_dict(obj)
                        print(f"Processing message: {msg}")  # Debugging line to see the message structure
                        # Filtro solo messaggi del tipo atteso (vehicle_state)
                        if 'x' in msg and 'y' in msg:  # controllo minimo
                            parsed = {
                                "x": msg.get("x", ""),
                                "y": msg.get("y", ""),
                                "yaw": msg.get("yaw", ""),
                                "v_y": msg.get("v_y", ""),
                                "yaw_r": msg.get("yaw_rate", ""),
                                "s": msg.get("s", ""),
                                "v_s": msg.get("v_s", ""),
                                "speed": msg.get("speed", ""),
                                "delta": msg.get("delta", ""),
                                "throttle": msg.get("throttle", ""),
                                "state": msg.get("state", ""),
                                "lap": msg.get("lap", ""),
                                "map_cones": msg.get("map_cones", ""),
                                "active_cones": msg.get("active_cones", ""),
                                "waypoint_array": msg.get("waypoint_array", ""),
                                "green_points": msg.get("green_points", ""),
                                "latency": 0,
                                "Ndata": len(rawdata)
                            }
                            result.append(parsed)
                    except Exception:
                        continue

        return result
