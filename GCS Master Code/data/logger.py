# logger.py
# For logging/recording data in CanSat GCS
import csv
import os
from datetime import datetime

class DataLogger:
    def __init__(self, folder_path="logs"):
        self.folder_path = folder_path
        os.makedirs(self.folder_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = os.path.join(self.folder_path, f"log_{timestamp}.csv")
        self.file = open(self.file_path, mode='w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(["Timestamp", "Sensor1", "Sensor2", "Sensor3"])  # Customize headers

    def log(self, sensor1, sensor2, sensor3):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.writer.writerow([timestamp, sensor1, sensor2, sensor3])

    def close(self):
        self.file.close()
