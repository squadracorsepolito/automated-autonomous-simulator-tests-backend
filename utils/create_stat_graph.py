import sqlite3
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# Define the path to the SQLite database
db_path = Path("db.sqlite3").resolve()

# Database connection
conn = sqlite3.connect(db_path)

fields = {
'track_name': True,
'mission_name': True,
'number_of_laps_completed': True,
'number_of_evaluated_cones_yellow': True,
'number_of_evaluated_cones_blue': True,
'number_of_evaluated_cones_unknown': True,
'is_successful': False,
'avg_lap_time': True,
'timestamp': False
}

selected_fields = ', '.join([field for field, include in fields.items() if include])

# Read data from a DataFrame
query = f"SELECT {selected_fields} FROM auto_tests_rosbags"
df = pd.read_sql_query(query, conn)

print(df)
conn.close()

# -----------------------------
# Histogram of completed laps
# -----------------------------
plt.figure(figsize=(10,6))
plt.hist(df['number_of_laps_completed'], bins=10, color='skyblue', edgecolor='black')
plt.title("Distribution of Completed Laps")
plt.xlabel("Number of Completed Laps")
plt.ylabel("Frequency")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# -----------------------------
# Histogram of Average Lap Time
# -----------------------------
plt.figure(figsize=(10,6))
plt.hist(df['avg_lap_time'], bins=10, color='salmon', edgecolor='black')
plt.title("Distribution of Average Lap Time")
plt.xlabel("Average Lap Time (s)")
plt.ylabel("Frequency")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# -----------------------------
# Comparison of Laps by Track Name
# -----------------------------
tracks = df['track_name'].unique()
plt.figure(figsize=(12,6))

for track in tracks:
    data = df[df['track_name'] == track]['number_of_laps_completed']
    plt.hist(data, bins=10, alpha=0.5, label=track, edgecolor='black')

plt.title("Comparison of Completed Laps by Track")
plt.xlabel("Number of Completed Laps")
plt.ylabel("Frequency")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# -----------------------------
# Comparison of Average Lap Times by Mission
# -----------------------------
missions = df['mission_name'].unique()
avg_times = [df[df['mission_name'] == m]['avg_lap_time'].mean() for m in missions]

plt.figure(figsize=(12,6))
plt.bar(missions, avg_times, color='lightgreen', edgecolor='black')
plt.title("Average Lap Time by Mission")
plt.xlabel("Mission")
plt.ylabel("Average Lap Time (s)")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()