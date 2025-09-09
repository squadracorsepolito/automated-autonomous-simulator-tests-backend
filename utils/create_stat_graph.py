import sqlite3
import pandas as pd
import numpy as np
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

# Creare una figura con tutti i subplot in un'unica schermata
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Data Dashboard", fontsize=20, fontweight='bold')

# -----------------------------
# Analisi Coni Rilevati per Colore
# -----------------------------
cone_data = {
    'Yellow': df['number_of_evaluated_cones_yellow'].sum(),
    'Blue': df['number_of_evaluated_cones_blue'].sum(),
    'Unknown': df['number_of_evaluated_cones_unknown'].sum()
}

colors = ['#FFD700', '#4169E1', '#808080']  # Giallo, Blu, Grigio
wedges, texts, autotexts = ax1.pie(cone_data.values(), labels=cone_data.keys(), 
                                   colors=colors, autopct='%1.1f%%', startangle=90)

ax1.set_title("Distribution of Detected Cones by Color", fontsize=14, fontweight='bold')
# Aumentare la dimensione del testo delle percentuali
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(11)
    autotext.set_fontweight('bold')
# Aumentare la dimensione delle etichette
for text in texts:
    text.set_fontsize(12)

# -----------------------------
# Histogram of Average Lap Time
# -----------------------------
ax2.hist(df['avg_lap_time'], bins=10, color='salmon', edgecolor='black')
ax2.set_title("Distribution of Average Lap Time", fontsize=14, fontweight='bold')
ax2.set_xlabel("Average Lap Time (s)", fontsize=12)
ax2.set_ylabel("Frequency", fontsize=12)
ax2.tick_params(axis='both', which='major', labelsize=11)
ax2.grid(axis='y', linestyle='--', alpha=0.7)

# -----------------------------
# Correlazione Coni Totali vs Tempo Medio Giro
# -----------------------------
df['total_cones'] = df['number_of_evaluated_cones_yellow'] + df['number_of_evaluated_cones_blue'] + df['number_of_evaluated_cones_unknown']

# Rimuovere eventuali valori NaN per il scatter plot
clean_data = df.dropna(subset=['total_cones', 'avg_lap_time'])

scatter = ax3.scatter(clean_data['total_cones'], clean_data['avg_lap_time'], 
                     alpha=0.6, s=60, c='purple', edgecolors='black', linewidth=0.5)

ax3.set_title("Correlation: Total Cones vs Average Lap Time", fontsize=14, fontweight='bold')
ax3.set_xlabel("Total Detected Cones", fontsize=12)
ax3.set_ylabel("Average Lap Time (s)", fontsize=12)
ax3.tick_params(axis='both', which='major', labelsize=11)
ax3.grid(True, linestyle='--', alpha=0.7)

# Aggiungere una linea di tendenza se ci sono abbastanza punti
if len(clean_data) > 1:
    x_values = clean_data['total_cones'].values
    y_values = clean_data['avg_lap_time'].values
    z = np.polyfit(x_values, y_values, 1)
    p = np.poly1d(z)
    ax3.plot(x_values, p(x_values), 
             "r--", alpha=0.8, linewidth=2, label=f'Trend line')

# -----------------------------
# Comparison of Average Lap Times by Mission
# -----------------------------
missions = df['mission_name'].unique()
avg_times = [df[df['mission_name'] == m]['avg_lap_time'].mean() for m in missions]

ax4.bar(missions, avg_times, color='lightgreen', edgecolor='black')
ax4.set_title("Average Lap Time by Mission", fontsize=14, fontweight='bold')
ax4.set_xlabel("Mission", fontsize=12)
ax4.set_ylabel("Average Lap Time (s)", fontsize=12)
ax4.tick_params(axis='x', rotation=45, labelsize=11)
ax4.tick_params(axis='y', labelsize=11)
ax4.grid(axis='y', linestyle='--', alpha=0.7)

# Regolare la spaziatura tra i subplot
plt.tight_layout()
plt.show()