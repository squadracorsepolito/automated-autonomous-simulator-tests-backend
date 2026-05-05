from pathlib import Path
from rosbags.typesys import get_types_from_msg, get_typestore, Stores

# 1. Create base typestore
typestore = get_typestore(Stores.ROS2_HUMBLE)

# 2. Path to .msg files
relative_dir = Path("msg")  # Change if necessary
msg_dir = relative_dir.resolve()

# 3. Register custom types
for msg_file in msg_dir.glob("*.msg"):
    print(f"Registering type from: {msg_file}")
    typename = f"interfaces/msg/{msg_file.stem}"
    source = msg_file.read_text()
    typestore.register(get_types_from_msg(source, typename))

# 4. Make typestore available with this name
nmea_typestore = typestore
