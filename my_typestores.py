from pathlib import Path
from rosbags.typesys import get_types_from_msg, get_typestore, Stores

# 1. Crea typestore base
typestore = get_typestore(Stores.ROS2_HUMBLE)

# 2. Path ai tuoi file .msg
msg_dir = Path("C:/Users/aless/Desktop/automated-tests-backend/msg")  # <-- cambia se necessario

# 3. Registra i tipi custom
for msg_file in msg_dir.glob("*.msg"):
    print(f"Registering type from: {msg_file}")
    typename = f"interfaces/msg/{msg_file.stem}"
    source = msg_file.read_text()
    typestore.register(get_types_from_msg(source, typename))

# 4. Rendi disponibile il typestore con questo nome
nmea_typestore = typestore

#  rosbags-convert  --src C:/Users/aless/Desktop/automated-tests-backend/media/rosbags/test_1   --dst output_rosbag1.bag   --src-typestore-ref my_typestores:nmea_typestore   --dst-typestore ros1_noetic


# from rosbags.convert.commands import command
# # controlla la firma della funzione command
# help(command)

# args = {
#     "src": "C:/Users/aless/Desktop/automated-tests-backend/media/rosbags/test_1",
#     "dst": "output_rosbag1.bag",
#     "src_typestore_ref": "my_typestores:nmea_typestore",
#     "dst_typestore": "ros1_noetic"
# }

# exit_code = command(**args)
# if exit_code != 0:
#     print("Errore nella conversione")
# else:
#     print("Conversione completata")
