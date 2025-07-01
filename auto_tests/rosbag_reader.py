from pathlib import Path
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg


class RosbagReader:
    def __init__(self, bag_path: Path, msg_path: Path, custom_msgs: list[str]):
        self.bag_path = bag_path
        self.typestore = get_typestore(Stores.ROS2_FOXY)

        # Registro tipi custom
        for msg_name in custom_msgs:
            msg_file = msg_path / f"{msg_name}.msg"
            msg_def = msg_file.read_text()
            types = get_types_from_msg(msg_def, f"interfaces/msg/{msg_name}")
            self.typestore.register(types)

    def extract_data(self, max_messages=100, sample_step: int = 4):
        data = []
        allowed_topics = {
            "/vehicle_state_optimized",
            "/vehicle_state_measure",
            "/vehicle_cmd",
            "/state",
            "/lap",
            "/map",
            "/active_cones",
            "/global_trajectory",
            "/predicted_trajectory",
        }
        count = 0

        with Reader(self.bag_path) as reader:

            json_data = {
                    "x": "",
                    "y": "",
                    "yaw": "",
                    "v_y": "",
                    "yaw_r": "",
                    "s": "",
                    "v_s": "",
                    "speed": "",
                    "delta": "",
                    "throttle": "",
                    "state": "",
                    "lap": "",
                    "map_cones": [],
                    "active_cones": [],
                    "waypoint_array": [],
                    "green_points": [],
                }
            
            for conn, timestamp, rawdata in reader.messages():
                if conn.topic not in allowed_topics:
                    continue

                try:
                    msg = self.typestore.deserialize_cdr(rawdata, conn.msgtype)
                except Exception:
                    # Ignora messaggi non deserializzabili
                    continue

                if conn.topic == "/vehicle_state_optimized":
                    json_data["x"] = getattr(msg, "x", "")
                    json_data["y"] = getattr(msg, "y", "")
                    json_data["yaw"] = getattr(msg, "yaw", "")
                    json_data["v_y"] = getattr(msg, "v_y", "")
                    json_data["yaw_r"] = getattr(msg, "yaw_r", "")

                    if count % sample_step == 0:
                        # Aggiungi solo ogni sample_step messaggio
                        data.append(json_data)

                elif conn.topic == "/vehicle_state_measure":
                    json_data["s"] = getattr(msg, "s", "")
                    json_data["v_s"] = getattr(msg, "v_s", "")
                    json_data["delta"] = getattr(msg, "delta", "")
                    json_data["throttle"] = getattr(msg, "d", "")

                elif conn.topic == "/vehicle_cmd":
                    json_data["speed"] = getattr(msg, "vs", "")

                elif conn.topic == "/state":
                    json_data["state"] = getattr(msg, "data", "")

                elif conn.topic == "/lap":
                    json_data["lap"] = getattr(msg, "data", "")

                elif conn.topic == "/map":
                    json_data["map_cones"] = [
                        {"x": c.x, "y": c.y, "color": c.color, "id": c.id} for c in getattr(msg, "data", [])
                    ]

                elif conn.topic == "/active_cones":
                    json_data["active_cones"] = [
                        {"x": c.x, "y": c.y, "color": c.color, "id": c.id} for c in getattr(msg, "data", [])
                    ]

                elif conn.topic == "/global_trajectory":
                    json_data["waypoint_array"] = [
                        {"x": w.x, "y": w.y, "vel_ref": w.vel_ref} for w in getattr(msg, "data", [])
                    ]

                elif conn.topic == "/predicted_trajectory":
                    json_data["green_points"] = [
                        {"x": w.x, "y": w.y, "vel_ref": w.vel_ref} for w in getattr(msg, "data", [])
                    ]

                
                count += 1

                # if count >= max_messages:
                #     break
        
        return data
