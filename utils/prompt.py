from pathlib import Path
from rosbags.rosbag1 import Reader as Rosbag1Reader

id_test = 67

# Path to the .msg
BASE_DIR = Path().resolve() # |Modify if necessary|

path = Path(BASE_DIR / f"media/rosbags/test_{id_test}/")
types_paths = Path(BASE_DIR / "msg")


max_messages = 1000
output_path = BASE_DIR / f"media/rosbags/test_{id_test}/output_rosbag_{id_test}.bag"

with Rosbag1Reader(output_path) as reader:
    print(f"Open file: {output_path}")
    print(f"Connections Number: {len(reader.connections)}")
    print(f"Message Count: {reader.message_count}")

    # Read and print first 5 messages
    count = 0
    for connection, timestamp, data in reader.messages():
        print(f"Topic: {connection.topic}, Timestamp: {timestamp}")
        count += 1
        if count >= max_messages:
            break
    print(f"Messages read from rosbag1: {count}")