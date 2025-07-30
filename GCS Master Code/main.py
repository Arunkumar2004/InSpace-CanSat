


# --- CanSat GCS Tkinter UI with Serial/Dummy Data and Live Matplotlib Plots ---
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
import queue
import os
from config import settings
from serial_comm.port_handler import SerialHandler
from data.dummy_data import generate_dummy_data

class CanSatGCSApp:
    # Static reference for event logging from SerialHandler
    instance = None
    def __init__(self, root):
        CanSatGCSApp.instance = self
        self.recording = False
        self.csv_file = None
        self.csv_writer = None
        self.csv_fields = [
            "time", "voltage", "gps_lat", "gps_lon", "altitude", "temperature", "pressure", "vertical_speed", "current", "gyro_x", "gyro_y", "gyro_z", "battery"
        ]
        self.root = root
        self.root.title(settings.WINDOW_TITLE)
        self.root.geometry(f"{settings.WINDOW_WIDTH}x{settings.WINDOW_HEIGHT}")
        self.root.configure(bg=settings.THEME["background"])
        self.serial_handler = SerialHandler()
        self.use_dummy = False
        self.data_queue = queue.Queue()
        self.mission_log = []
        self._setup_ui()
        self._show_port_modal()

    def _setup_ui(self):
        # Header bar
        header = tk.Frame(self.root, bg="#222", height=60)
        header.pack(side="top", fill="x")
        try:
            logo_img = Image.open(settings.LOGO_PATH)
            logo_img = logo_img.resize((48, 48))
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(header, image=self.logo, bg="#222")
            logo_label.pack(side="left", padx=10, pady=5)
        except Exception:
            logo_label = tk.Label(header, text="", bg="#222")
            logo_label.pack(side="left", padx=10, pady=5)
        team_label = tk.Label(header, text=settings.TEAM_NAME, fg="#fff", bg="#222", font=("Segoe UI", 18, "bold"))
        team_label.pack(side="left", padx=10)

        # Main layout with vertical scrollbar
        container = tk.Frame(self.root, bg=settings.THEME["background"])
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg=settings.THEME["background"])
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        main = tk.Frame(canvas, bg=settings.THEME["background"])
        main.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=main, anchor="nw")

        # Use a grid for two columns of 3 graphs each, no extra space
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_columnconfigure(2, weight=0)

        # Two columns for 6 graphs (3 per column)
        self.left_figs = []
        self.left_axes = []
        self.left_canvases = []
        self.left_titles = [
            "Altitude (m)",
            "Temperature (°C)",
            "Pressure (hPa)",
            "Velocity (m/s)",
            "Voltage (V)",
            "Current (A)"
        ]
        for i, title in enumerate(self.left_titles):
            col = 0 if i < 3 else 1
            row = i if i < 3 else i - 3
            frame = tk.Frame(main, bg=settings.THEME["background"])
            frame.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            fig = Figure(figsize=(3, 2), dpi=100)
            ax = fig.add_subplot(111)
            ax.set_title(title, color="#fff", fontsize=10)
            ax.tick_params(axis='x', colors='#aaa')
            ax.tick_params(axis='y', colors='#aaa')
            fig.patch.set_facecolor(settings.THEME["background"])
            ax.set_facecolor(settings.THEME["background"])
            canvas_fig = FigureCanvasTkAgg(fig, master=frame)
            canvas_fig.get_tk_widget().pack(fill="both", expand=True)
            self.left_figs.append(fig)
            self.left_axes.append(ax)
            self.left_canvases.append(canvas_fig)

        # Center panel (Gyroscope main graph, same size as left graphs)
        center = tk.Frame(main, bg=settings.THEME["background"])
        center.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=10, pady=10)
        self.gyro_fig = Figure(figsize=(3, 2), dpi=100)
        self.gyro_ax = self.gyro_fig.add_subplot(111)
        self.gyro_ax.set_title("Gyroscope (Pitch, Roll, Yaw)", color="#fff", fontsize=10)
        self.gyro_ax.tick_params(axis='x', colors='#aaa')
        self.gyro_ax.tick_params(axis='y', colors='#aaa')
        self.gyro_fig.patch.set_facecolor(settings.THEME["background"])
        self.gyro_ax.set_facecolor(settings.THEME["background"])
        self.gyro_lines = {
            'x': self.gyro_ax.plot([], [], label='Pitch')[0],
            'y': self.gyro_ax.plot([], [], label='Roll')[0],
            'z': self.gyro_ax.plot([], [], label='Yaw')[0],
        }
        self.gyro_ax.legend(facecolor="#222", edgecolor="#222", labelcolor="#fff")
        self.gyro_canvas = FigureCanvasTkAgg(self.gyro_fig, master=center)
        self.gyro_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Right panel (mission log, map, etc.)
        right = tk.Frame(main, bg=settings.THEME["background"], width=220)
        right.grid(row=0, column=3, rowspan=3, sticky="nsew", padx=10, pady=10)
        # Camera status (check for real camera port, else show not connected)
        self.cam_status = tk.Label(right, text="Checking camera...", fg="#fff", bg="#444", font=("Consolas", 10), width=24, height=2)
        self.cam_status.pack(pady=8)
        # Time display
        self.time_label = tk.Label(right, text="--:--:--", fg="#fff", bg="#222", font=("Segoe UI", 22, "bold"), width=12)
        self.time_label.pack(pady=8)
        # Battery percentage
        self.battery_label = tk.Label(right, text="Battery: --%", fg="#fff", bg="#222", font=("Segoe UI", 14), width=18)
        self.battery_label.pack(pady=8)
        # Buttons (no Start Mission)
        btn_frame = tk.Frame(right, bg=settings.THEME["background"])
        btn_frame.pack(pady=8)
        self.btn_rec = ttk.Button(btn_frame, text="Start Recording", command=self._start_recording)
        self.btn_rec.grid(row=0, column=0, padx=2)
        self.btn_stop = ttk.Button(btn_frame, text="Stop Recording", command=self._stop_recording)
        self.btn_stop.grid(row=0, column=1, padx=2)
        # Mission log
        log_label = tk.Label(right, text="Mission Log", fg="#fff", bg=settings.THEME["background"], font=("Consolas", 10, "bold"))
        log_label.pack(pady=(10, 0))
        self.log_box = tk.Text(right, height=12, width=28, bg="#181", fg="#0f0", font=("Consolas", 9), state="disabled")
        self.log_box.pack(pady=2)
        # Map integration for GPS (real map)
        try:
            from tkintermapview import TkinterMapView
            self.map_widget = TkinterMapView(right, width=200, height=180, corner_radius=8)
            self.map_widget.set_position(0, 0)  # Default to (0,0)
            self.map_marker = self.map_widget.set_marker(0, 0, text="CanSat")
            self.map_widget.pack(pady=8)
        except ImportError:
            self.map_widget = None
            self.map_marker = None
            self.map_label = tk.Label(right, text="Map: --, --", fg="#fff", bg="#222", font=("Consolas", 10), width=28)
            self.map_label.pack(pady=8)

        # Data storage for plots
        self._check_camera_port()

    def _check_camera_port(self):
        # This is a placeholder: checks for a common camera device on Windows (e.g., video0)
        # You can expand this logic for your hardware
        # On Windows, camera devices are not files, so we just show not connected
        # For real detection, integrate OpenCV or similar
        self.cam_status.config(text="No Camera Connected", bg="#a22")
        self.data_history = {
            'Altitude (m)': [], 'Temperature (°C)': [], 'Pressure (hPa)': [], 'Velocity (m/s)': [], 'Voltage (V)': [], 'Current (A)': [],
            'gyro_x': [], 'gyro_y': [], 'gyro_z': [], 'time': [], 'gps_lat': [], 'gps_lon': [], 'battery': []
        }


    def _show_port_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Select Serial Port")
        modal.geometry("350x180")
        modal.grab_set()
        modal.transient(self.root)
        tk.Label(modal, text="Select Serial Port:", font=("Segoe UI", 12, "bold")).pack(pady=(18, 5))
        ports = self.serial_handler.list_available_ports()
        port_options = ports.copy() if ports else []
        port_options.append("Dummy Mode")
        port_var = tk.StringVar(value=port_options[0])
        combo = ttk.Combobox(modal, textvariable=port_var, values=port_options, state="readonly")
        combo.pack(pady=5)
        status_label = tk.Label(modal, text="", fg="#f00")
        status_label.pack(pady=2)

        def refresh_ports():
            ports = self.serial_handler.list_available_ports()
            port_options = ports.copy() if ports else []
            port_options.append("Dummy Mode")
            combo['values'] = port_options
            port_var.set(port_options[0])
        ttk.Button(modal, text="Refresh", command=refresh_ports).pack(pady=2)

        def try_connect():
            port = port_var.get()
            if port == "Dummy Mode":
                self._log("[INFO] Dummy mode selected.")
                self.use_dummy = True
                modal.destroy()
                self._start_data_loop()
                return
            if not port:
                self._log("[WARN] No serial ports found. Switching to dummy mode.")
                self.use_dummy = True
                modal.destroy()
                self._start_data_loop()
                return
            ok = self.serial_handler.connect(port)
            if ok:
                self._log(f"[INFO] Connected to {port}. Waiting for data...")
                # Wait up to 5 seconds, checking every 1s for serial data before switching to dummy
                self._check_data_or_dummy_retry(modal, retries=5)
            else:
                status_label.config(text="Failed to connect. Try another port.")

        ttk.Button(modal, text="Connect", command=try_connect).pack(pady=10)

    def _check_data_or_dummy_retry(self, modal, retries=5):
        data = self.serial_handler.get_data()
        if data:
            self._log("[INFO] Serial data received. Starting live mode.")
            self.use_dummy = False
            modal.destroy()
            self._start_data_loop()
        elif retries > 1:
            # Wait 1 second and try again
            modal.after(1000, lambda: self._check_data_or_dummy_retry(modal, retries-1))
        else:
            self._log("[WARN] No serial data. Switching to dummy mode.")
            self.use_dummy = True
            modal.destroy()
            self._start_data_loop()

    def _update_data(self):
        # Get data from serial or dummy
        data = None
        if self.use_dummy:
            # Try to get real data even in dummy mode, to allow switching if real data appears
            real_data = self.serial_handler.get_data()
            if real_data:
                self._log("[INFO] Serial data detected. Switching to live mode.")
                self.use_dummy = False
                data = real_data
            else:
                data = self._get_dummy_data()
        else:
            data = self.serial_handler.get_data()
            if not data:
                # If no real data, keep trying (do not switch to dummy here)
                pass
        if data:
            self._update_plots(data)
        self.root.after(settings.GRAPH_REFRESH_INTERVAL_MS, self._update_data)

    def _check_data_or_dummy(self, modal):
        # Try to get data from serial queue
        data = self.serial_handler.get_data()
        if data:
            self._log("[INFO] Serial data received. Starting live mode.")
            self.use_dummy = False
            modal.destroy()
            self._start_data_loop()
        else:
            self._log("[WARN] No serial data. Switching to dummy mode.")
            self.use_dummy = True
            modal.destroy()
            self._start_data_loop()

    def _start_data_loop(self):
        self._update_time()
        self._update_data()

    def _update_time(self):
        now = time.strftime("%H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self._update_time)

    def _update_data(self):
        # Get data from serial or dummy
        if self.use_dummy:
            data = self._get_dummy_data()
        else:
            data = self.serial_handler.get_data()
        if data:
            self._update_plots(data)
        self.root.after(settings.GRAPH_REFRESH_INTERVAL_MS, self._update_data)

    def _get_dummy_data(self):
        # Use the same format as SerialHandler.generate_dummy_packet
        return self.serial_handler.generate_dummy_packet()

    def _update_plots(self, data):
        # Update left panel plots
        for i, key in enumerate(["altitude", "temperature", "pressure", "vertical_speed", "voltage", "current"]):
            val = data.get(key, 0)
            title = self.left_titles[i]
            self.data_history[title].append(val)
            if len(self.data_history[title]) > settings.MAX_DATA_POINTS:
                self.data_history[title].pop(0)
            ax = self.left_axes[i]
            ax.clear()
            ax.plot(self.data_history[title], color=settings.THEME["graph_line"])
            ax.set_title(title, color="#fff", fontsize=10)
            ax.tick_params(axis='x', colors='#aaa')
            ax.tick_params(axis='y', colors='#aaa')
            ax.set_facecolor(settings.THEME["background"])
            self.left_canvases[i].draw()
        # Update center gyro plot
        # Accept both {'gyro': {'x':..., 'y':..., 'z':...}} and {'x':..., 'y':..., 'z':...} at top level
        gyro_data = data.get('gyro')
        if gyro_data is None and all(axis in data for axis in ['x', 'y', 'z']):
            gyro_data = {'x': data['x'], 'y': data['y'], 'z': data['z']}
        if gyro_data:
            for axis, line in zip(['x', 'y', 'z'], [self.gyro_lines['x'], self.gyro_lines['y'], self.gyro_lines['z']]):
                gyro_val = gyro_data.get(axis, 0)
                self.data_history[f'gyro_{axis}'].append(gyro_val)
                if len(self.data_history[f'gyro_{axis}']) > settings.MAX_DATA_POINTS:
                    self.data_history[f'gyro_{axis}'].pop(0)
                line.set_data(range(len(self.data_history[f'gyro_{axis}'])), self.data_history[f'gyro_{axis}'])
        self.gyro_ax.relim()
        self.gyro_ax.autoscale_view()
        self.gyro_canvas.draw()
        # Update map widget with GPS
        lat = data.get('gps', {}).get('lat', None)
        lon = data.get('gps', {}).get('lon', None)
        self.data_history['gps_lat'].append(lat if lat is not None else '--')
        self.data_history['gps_lon'].append(lon if lon is not None else '--')
        if self.map_widget and lat not in (None, '--') and lon not in (None, '--'):
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                self.map_widget.set_position(lat_f, lon_f)
                if self.map_marker:
                    self.map_marker.set_position(lat_f, lon_f)
                else:
                    self.map_marker = self.map_widget.set_marker(lat_f, lon_f, text="CanSat")
            except Exception:
                pass
        elif hasattr(self, 'map_label'):
            self.map_label.config(text=f"Map: {lat}, {lon}")
        # Update battery label
        battery = data.get('battery', '--')
        self.data_history['battery'].append(battery)
        self.battery_label.config(text=f"Battery: {battery}%")
        # Log time
        t = data.get('time', time.strftime("%H:%M:%S"))
        self.data_history['time'].append(t)

    def _log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _start_mission(self):
        self._log("[MISSION] Mission started.")

    def _start_recording(self):
        import csv
        if not self.recording:
            filename = time.strftime("recording_%Y%m%d_%H%M%S.csv")
            self.csv_file = open(filename, mode="w", newline="")
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.csv_fields)
            self.csv_writer.writeheader()
            self.recording = True
            self._log(f"[RECORD] Data recording started: {filename}")
        else:
            self._log("[RECORD] Already recording.")

    def _stop_recording(self):
        if self.recording:
            self.recording = False
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
                self.csv_writer = None
            self._log("[RECORD] Data recording stopped.")
        else:
            self._log("[RECORD] Not currently recording.")
        # (Removed block that incorrectly tried to write CSV row using undefined 'data')


if __name__ == "__main__":
    root = tk.Tk()
    app = CanSatGCSApp(root)
    root.mainloop()
