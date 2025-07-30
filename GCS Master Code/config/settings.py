# settings.py
# Serial config, team name, and constants for CanSat GCS
TEAM_NAME = "Team Phoenix"
SERIAL_PORT = "COM3"
BAUD_RATE = 9600
# config/settings.py

"""
Global configuration settings for the CANSAT Ground Control Station (GCS).
All modules should import constants from here to maintain consistency.
"""

# Serial Communication Settings
BAUD_RATE = 9600
DEFAULT_PORT = "COM3"  # Change this as per your OS or auto-detect

# Data Logging Settings
LOG_FILE_PATH = "data/telemetry_log.csv"
LOG_HEADERS = ["Timestamp", "Altitude", "Temperature", "Pressure", "Latitude", "Longitude", "Voltage"]

# Dummy Data (for testing without live telemetry)
USE_DUMMY_DATA = False
DUMMY_UPDATE_INTERVAL_MS = 1000  # in milliseconds

# GUI Settings
WINDOW_TITLE = "Team Phoenix - CANSAT GCS"
LOGO_PATH = "assets/logo.png"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Graph Display Settings
GRAPH_REFRESH_INTERVAL_MS = 500
MAX_DATA_POINTS = 100  # Number of points to show in real-time graphs

# Theme / Color Palette
THEME = {
    "background": "#1e1e1e",
    "text": "#ffffff",
    "graph_line": "#00ffcc",
    "grid": "#444444"
}

# Others
VERSION = "1.0.0"
DEBUG = True
