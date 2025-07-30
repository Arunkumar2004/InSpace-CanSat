# dummy_data.py
# Fallback data generator for CanSat GCS
import random
import time

def generate_dummy_data():
    """
    Simulates incoming telemetry data.
    Replace or modify as needed for testing GUI/serial integration.
    """
    while True:
        sensor1 = round(random.uniform(20.0, 30.0), 2)
        sensor2 = round(random.uniform(800.0, 1200.0), 2)
        sensor3 = round(random.uniform(0.0, 100.0), 2)
        yield f"{sensor1},{sensor2},{sensor3}"
        time.sleep(1)
