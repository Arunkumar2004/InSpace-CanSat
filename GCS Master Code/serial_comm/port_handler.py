
# serial_comm/port_handler.py
print("[DEBUG] Loaded serial_comm/port_handler.py")
__all__ = ["SerialHandler"]

import serial
import serial.tools.list_ports
import threading
import queue
import time
import json
from config import settings
import random

class SerialHandler:
    def __init__(self):
        self.serial_port = None
        self.running = False
        self.thread = None
        self.data_queue = queue.Queue()
        self._dummy_battery = 100.0  # For slow, monotonic battery decrease

    def list_available_ports(self):
        """Lists all available COM ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port=settings.SERIAL_PORT, baud=settings.BAUD_RATE):
        """Attempts to connect to the given port"""
        try:
            self.serial_port = serial.Serial(port, baudrate=baud, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.thread.start()
            print(f"[✓] Connected to {port} at {baud} baud.")
            return True
        except serial.SerialException as e:
            print(f"[X] Serial connection failed: {e}")
            return False

    def disconnect(self):
        """Gracefully disconnect from serial port"""
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("[!] Serial port closed.")

    def read_serial_data(self):
        """Reads incoming serial data"""
        while self.running:
            try:
                if settings.USE_DUMMY_DATA:
                    time.sleep(1)
                    dummy_data = self.generate_dummy_packet()
                    self.data_queue.put(dummy_data)
                elif self.serial_port and self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    # Try JSON first
                    try:
                        data = json.loads(line)
                        self.data_queue.put(data)
                    except json.JSONDecodeError:
                        # If not JSON, try as CSV (handled in get_data)
                        if line:
                            self.data_queue.put(line)
            except Exception as e:
                print(f"[!] Serial Read Error: {e}")

    def get_data(self):
        line = None
        if not self.data_queue.empty():
            line = self.data_queue.get()
        if not line:
            return None

        # If the data is already a dict (from dummy or JSON), return as is
        if isinstance(line, dict):
            return line

        # If it's a CSV string, parse into a dict
        try:
            vals = str(line).strip().split(',')
            # Arduino output: voltage,gps_lat,gps_lon,altitude,temperature,pressure,vertical_speed,current,gyro_x,gyro_y,gyro_z,battery,time
            return {
                "voltage": float(vals[0]),
                "gps": {"lat": float(vals[1]), "lon": float(vals[2])},
                "altitude": float(vals[3]),
                "temperature": float(vals[4]),
                "pressure": float(vals[5]),
                "vertical_speed": float(vals[6]),
                "current": float(vals[7]),
                "gyro": {"x": float(vals[8]), "y": float(vals[9]), "z": float(vals[10])},
                "battery": float(vals[11]),
                "time": vals[12]
            }
        except Exception as e:
            print("Parse error:", e, "Raw:", line)
            return None


    def generate_dummy_packet(self):
        """Realistic CanSat mission profile dummy data with event logging"""
        # State variables for mission profile
        if not hasattr(self, '_dummy_battery'):
            self._dummy_battery = 100.0
        if not hasattr(self, '_dummy_altitude'):
            self._dummy_altitude = 1000.0
        if not hasattr(self, '_dummy_velocity'):
            self._dummy_velocity = 0.0
        if not hasattr(self, '_dummy_phase'):
            self._dummy_phase = 0
        if not hasattr(self, '_dummy_last_time'):
            self._dummy_last_time = time.time()
        if not hasattr(self, '_dummy_events_logged'):
            self._dummy_events_logged = set()
        # Time step
        now = time.time()
        dt = now - self._dummy_last_time
        self._dummy_last_time = now
        # Mission phases:
        # 0: Ejection (free fall, >15m/s)
        # 1: Primary parachute deployed (15m/s)
        # 2: Secondary parachute deployed (2m/s)
        # 3: Expansion
        # 4: Audiobeacon
        # 5: Landed
        # Altitude descent logic
        if self._dummy_phase == 0:
            # Free fall, velocity increases rapidly to ~50m/s, then stabilize
            self._dummy_velocity = min(self._dummy_velocity + 30*dt, 50)
            self._dummy_altitude -= self._dummy_velocity * dt
            if self._dummy_altitude <= 950 and 1 not in self._dummy_events_logged:
                # Parachute deploys at ~1-2s after ejection
                self._dummy_phase = 1
                self._dummy_velocity = 15
                self._dummy_events_logged.add(1)
                self._log_event("[MISSION] Primary parachute deployed!")
        elif self._dummy_phase == 1:
            # Primary chute descent
            self._dummy_velocity = 15
            self._dummy_altitude -= self._dummy_velocity * dt
            if self._dummy_altitude <= 500 and 2 not in self._dummy_events_logged:
                self._dummy_phase = 2
                self._dummy_velocity = 2
                self._dummy_events_logged.add(2)
                self._log_event("[MISSION] Secondary parachute deployed!")
                self._popup_event("Secondary parachute deployed successfully!")
        elif self._dummy_phase == 2:
            # Secondary chute descent
            self._dummy_velocity = 2
            self._dummy_altitude -= self._dummy_velocity * dt
            if self._dummy_altitude <= 450 and 3 not in self._dummy_events_logged:
                self._dummy_phase = 3
                self._dummy_events_logged.add(3)
                self._log_event("[MISSION] CanSat expansion mechanism completed.")
            if self._dummy_altitude <= 20 and 4 not in self._dummy_events_logged:
                self._dummy_phase = 4
                self._dummy_events_logged.add(4)
                self._log_event("[MISSION] Audio beacons activated.")
        elif self._dummy_phase == 3:
            # Expansion, continue descent
            self._dummy_velocity = 2
            self._dummy_altitude -= self._dummy_velocity * dt
            if self._dummy_altitude <= 20 and 4 not in self._dummy_events_logged:
                self._dummy_phase = 4
                self._dummy_events_logged.add(4)
                self._log_event("[MISSION] Audio beacons activated.")
        elif self._dummy_phase == 4:
            # Audio beacon, continue descent
            self._dummy_velocity = 2
            self._dummy_altitude -= self._dummy_velocity * dt
            if self._dummy_altitude <= 0:
                self._dummy_altitude = 0
                self._dummy_velocity = 0
                self._dummy_phase = 5
        else:
            self._dummy_velocity = 0
            self._dummy_altitude = 0
        # Battery decreases slowly
        self._dummy_battery = max(self._dummy_battery - 0.005*dt, 0.0)
        # Simulate other sensors based on altitude/velocity
        # For India: 1000m ~18-22°C, ground ~28-35°C
        temperature = 28 + (self._dummy_altitude/1000)*(-8) + random.uniform(-1,1)  # 1000m: ~20°C, 0m: ~28-35°C
        pressure = 1013.25 * pow(1 - (0.0065 * self._dummy_altitude) / 288.15, 5.255) + random.uniform(-1,1)
        gyro = {
            "x": round(random.uniform(-2, 2), 2),
            "y": round(random.uniform(-2, 2), 2),
            "z": round(random.uniform(-2, 2), 2)
        }
        gps = {
            "lat": round(13.000000 + (1000-self._dummy_altitude)*0.0001 + random.uniform(-0.00005,0.00005), 6),
            "lon": round(80.200000 + (1000-self._dummy_altitude)*0.0001 + random.uniform(-0.00005,0.00005), 6),
            "sat": random.randint(7, 12)
        }
        return {
            "temperature": round(temperature, 2),
            "pressure": round(pressure, 2),
            "altitude": round(self._dummy_altitude, 2),
            "vertical_speed": round(self._dummy_velocity, 2),
            "gyro": gyro,
            "gps": gps,
            "battery": round(self._dummy_battery, 2),
            "time": time.strftime("%H:%M:%S")
        }

    def _log_event(self, msg):
        # Log to GCS mission log if available
        try:
            from main import CanSatGCSApp
            if CanSatGCSApp.instance is not None:
                CanSatGCSApp.instance._log(msg)
        except Exception:
            pass

    def _popup_event(self, msg):
        # Popup to GCS if available
        try:
            import main
            if hasattr(main, 'app') and hasattr(main.app, 'root'):
                from tkinter import messagebox
                messagebox.showinfo("Mission Event", msg, parent=main.app.root)
        except Exception:
            pass

