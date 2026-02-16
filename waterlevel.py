import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class WaterLevelApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Smart Water Level Monitor - Gauge")
        self.geometry("700x650")
        self.resizable(False, False)

        self.serial_port = None
        self.running = False
        self.tank_height = 1000
        self.current_percentage = 0

        self.create_ui()

    # ---------------- UI ---------------- #
    def create_ui(self):

        title = ctk.CTkLabel(self, text="Water Level Monitor",
                             font=("Arial", 28, "bold"))
        title.pack(pady=20)

        # COM Port
        self.port_menu = ctk.CTkComboBox(self,
                                         values=self.get_ports(),
                                         width=200)
        self.port_menu.pack(pady=10)

        self.connect_btn = ctk.CTkButton(self,
                                         text="Connect Serial",
                                         command=self.connect_serial)
        self.connect_btn.pack(pady=10)

        # Tank Height
        self.height_entry = ctk.CTkEntry(self,
                                         placeholder_text="Enter Tank Height (cm)",
                                         width=250)
        self.height_entry.pack(pady=15)

        self.set_btn = ctk.CTkButton(self,
                                     text="Set Tank Height",
                                     command=self.set_height)
        self.set_btn.pack(pady=5)

        self.percent_label = ctk.CTkLabel(self,
                                          text="Water Level: -- %",
                                          font=("Arial", 24, "bold"))
        self.percent_label.pack(pady=15)

        # -------- Gauge Figure -------- #
        self.fig, self.ax = plt.subplots(figsize=(5, 5),
                                         subplot_kw={'projection': 'polar'})
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack()

        self.draw_gauge(0)

        self.status_label = ctk.CTkLabel(self,
                                         text="Status: Not Connected",
                                         text_color="red")
        self.status_label.pack(pady=10)

    # ---------------- SERIAL PORTS ---------------- #
    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    # ---------------- CONNECT ---------------- #
    def connect_serial(self):
        port = self.port_menu.get()
        if not port:
            return

        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.running = True
            self.status_label.configure(text="Status: Connected",
                                        text_color="green")

            threading.Thread(target=self.read_serial, daemon=True).start()

        except:
            self.status_label.configure(text="Connection Failed",
                                        text_color="red")

    # ---------------- SET HEIGHT ---------------- #
    def set_height(self):
        try:
            self.tank_height = float(self.height_entry.get())
        except:
            self.tank_height = 0

    # ---------------- READ SERIAL ---------------- #
    def read_serial(self):
        while self.running:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode().strip()
                    distance = float(data)

                    self.process_data(distance)

            except:
                pass

            time.sleep(1)

    # ---------------- PROCESS DATA ---------------- #
    def process_data(self, distance):

        if self.tank_height == 0:
            return

        water_level = self.tank_height - distance
        percentage = (water_level / self.tank_height) * 100
        percentage = max(0, min(percentage, 100))

        self.current_percentage = percentage

        self.percent_label.configure(
            text=f"Water Level: {round(percentage, 1)} %")

        self.draw_gauge(percentage)

    # ---------------- DRAW GAUGE ---------------- #
    def draw_gauge(self, percentage):

        self.ax.clear()
        self.ax.set_theta_offset(np.pi)
        self.ax.set_theta_direction(-1)
        self.ax.set_ylim(0, 10)
        self.ax.set_yticklabels([])
        self.ax.set_xticklabels([])
        self.ax.grid(False)

        # Color zones
        zones = [
            (0, 30, "red"),
            (30, 70, "orange"),
            (70, 100, "green")
        ]

        for start, end, color in zones:
            self.ax.barh(5,
                         np.deg2rad((end - start) * 1.8),
                         left=np.deg2rad(start * 1.8),
                         height=3,
                         color=color,
                         alpha=0.4)

        # Needle
        angle = np.deg2rad(percentage * 1.8)
        self.ax.plot([angle, angle], [0, 8], linewidth=4)

        self.ax.set_title("Water Level Gauge", pad=20)

        self.canvas.draw_idle()


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    app = WaterLevelApp()
    app.mainloop()
