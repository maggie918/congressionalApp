import tkinter as tk
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk
import subprocess
import threading
import sys
import os
import pygame
from datetime import datetime

PYTHON_SCRIPT = "/Users/maggielu/Desktop/detectVideo.py"
CROPPED_IMAGE_PATH = "/Users/maggielu/Desktop/detectedImage.png"
ICON_PATH = "/Users/maggielu/Desktop/icon.png"
SOUND_PATH = "/Users/maggielu/Desktop/emergencySound.mp3"
SHIELD_PATH = "/Users/maggielu/Desktop/realShield.png"
ACTIVE_SHIELD_PATH = "/Users/maggielu/Desktop/activeShield.png"

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 700

class MoveToSafetyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MoveToSafety")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg="#FFF6F6")

        # Replace Python rocket icon with your shield icon
        if os.path.exists(SHIELD_PATH):
            shield_icon = PhotoImage(file=SHIELD_PATH)
            self.root.iconphoto(True, shield_icon)

        pygame.mixer.init()
        self.monitoring = False
        self.process = None
        self.recent_alerts = []

        self.create_home_ui()

    # --- Rounded rectangle helper ---
    def round_rect(self, canvas, x1, y1, x2, y2, r=40, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    # --- Rounded card ---
    def create_rounded_card(self, master, width=360, height=120, bg="#FFFFFF", radius=40):
        canvas = tk.Canvas(master, width=width, height=height, bg=master['bg'], highlightthickness=0)
        canvas.pack(pady=10)
        self.round_rect(canvas, 0, 0, width, height, r=radius, fill=bg, outline="")
        return canvas

    # --- Rounded button ---
    def make_button(self, master, text, bg, fg, command, width=300, height=50, radius=25):
        canvas = tk.Canvas(master, width=width, height=height, bg=master['bg'], highlightthickness=0)
        canvas.pack(pady=10)
        rect = self.round_rect(canvas, 0, 0, width, height, r=radius, fill=bg, outline="")

        lbl = tk.Label(canvas, text=text, bg=bg, fg=fg, font=("Segoe UI", 14, "bold"))
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        def on_enter(e):
            if bg == "#60A160":
                canvas.itemconfig(rect, fill="#528C50")
                lbl['bg'] = "#528C50"
            elif bg == "#DC2626":
                canvas.itemconfig(rect, fill="#B91C1C")
                lbl['bg'] = "#B91C1C"
            elif bg == "#E5E7EB":
                canvas.itemconfig(rect, fill="#D1D5DB")
                lbl['bg'] = "#D1D5DB"

        def on_leave(e):
            canvas.itemconfig(rect, fill=bg)
            lbl['bg'] = bg

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)
        lbl.bind("<Button-1>", lambda e: command())

        return lbl

    # --- Home UI ---
    def create_home_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        header = tk.Frame(self.root, bg="#FFF6F6")
        header.pack(pady=20)

        # Shield logo above title
        if os.path.exists(SHIELD_PATH):
            img = Image.open(SHIELD_PATH).resize((50, 50))
            icon_photo = ImageTk.PhotoImage(img)
            tk.Label(header, image=icon_photo, bg="#FFF6F6").pack()
            self.root.shield_img = icon_photo

        tk.Label(header, text="MoveToSafety", font=("Segoe UI", 20, "bold"),
                 fg="#991B1B", bg="#FFF6F6").pack(pady=5)

        # Move this text between header and green card
        tk.Label(self.root, text="Real-time emergency alerts",
                 font=("Segoe UI", 11), fg="#374151", bg="#FFF6F6").pack(pady=5)

        # Active Protection Box
        active_card = self.create_rounded_card(self.root, height=90, bg="#ECFDF5", radius=25)
        if os.path.exists(ACTIVE_SHIELD_PATH):
            img = Image.open(ACTIVE_SHIELD_PATH).resize((50, 50))
            shield_photo = ImageTk.PhotoImage(img)
            active_card.create_image(60, 45, image=shield_photo, anchor="center")
            self.root.active_shield_img = shield_photo

        active_card.create_text(120, 25, text="Active Protection", font=("Segoe UI", 14, "bold"), fill="#047857", anchor="w")
        active_card.create_text(120, 55, text="You're receiving real-time safety alerts", font=("Segoe UI", 11), fill="#065F46", anchor="w")

        # Recent Alerts Box
        recent_card = self.create_rounded_card(self.root, height=200, bg="#FFFFFF", radius=30)
        recent_card.create_text(20, 20, text="Recent Alerts", font=("Segoe UI", 13, "bold"), fill="#111827", anchor="w")
        if not self.recent_alerts:
            recent_card.create_text(180, 100, text="⚠️ No alerts received yet", font=("Segoe UI", 12), fill="#6B7280", anchor="center")
        else:
            y = 50
            for alert in reversed(self.recent_alerts[-4:]):
                recent_card.create_text(20, y, text=f"• {alert}", font=("Segoe UI", 10), fill="#374151", anchor="w")
                y += 30

        # Monitoring button
        self.monitor_btn = self.make_button(
            self.root, "🚨 START MONITORING 🚨", "#60A160", "white", self.start_monitoring
        )

        # Report Danger button
        self.make_button(
            self.root, "⚠️ REPORT DANGER ⚠️", "#DC2626", "white", lambda: self.show_alert_screen(report=True)
        )

    # --- Start/Stop monitoring methods ---
    def start_monitoring(self):
        if not messagebox.askyesno("Permission", "Allow MoveToSafety to access your location?"):
            return
        if not messagebox.askyesno("Permission", "Allow MoveToSafety to send you notifications?"):
            return
        if not messagebox.askyesno("Start Monitoring", "Click YES to start detection."):
            return

        self.monitoring = True
        threading.Thread(target=self.launch_detection, daemon=True).start()
        messagebox.showinfo("Monitoring", "MoveToSafety is now monitoring for threats.")

        # Change button to Stop Monitoring
        self.monitor_btn.config(text="🛑 STOP MONITORING 🛑")
        self.monitor_btn.bind("<Button-1>", lambda e: self.stop_monitoring())

    def stop_monitoring(self):
        self.monitoring = False
        self.stop_detection()
        messagebox.showinfo("Stopped", "Monitoring stopped.")
        self.create_home_ui()

    # --- Detection ---
    def launch_detection(self):
        try:
            self.process = subprocess.Popen([sys.executable, PYTHON_SCRIPT],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            threading.Thread(target=self.read_stdout, args=(self.process,), daemon=True).start()
            threading.Thread(target=self.read_stderr, args=(self.process,), daemon=True).start()
        except Exception as e:
            print(f"Error launching detection: {e}")

    def stop_detection(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None

    def read_stdout(self, process):
        for line in process.stdout:
            if "✅ Shooter tightly cropped image saved at:" in line:
                self.show_alert_screen()

    def read_stderr(self, process):
        for line in process.stderr:
            print(f"Python error: {line}", end="")

    # --- Alert Screen ---
    def show_alert_screen(self, report=False):
        for widget in self.root.winfo_children():
            widget.destroy()

        alert_type = "MOVE AWAY FROM BUILDING B"
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.recent_alerts.append(f"{timestamp} - {alert_type}")

        flash = tk.Label(self.root, bg="#DC2626")
        flash.place(relwidth=1, relheight=1)

        def flash_bg():
            current = flash.cget("bg")
            flash.configure(bg="black" if current == "#DC2626" else "#DC2626")
            if hasattr(self, "flashing") and self.flashing:
                self.root.after(200, flash_bg)

        self.flashing = True
        flash_bg()

        if os.path.exists(SOUND_PATH):
            try:
                pygame.mixer.music.load(SOUND_PATH)
                pygame.mixer.music.play(-1)
            except:
                pass

        tk.Label(self.root, text="⚠️ ALERT ⚠️", font=("Segoe UI", 24, "bold"), fg="white", bg="#DC2626").pack(pady=10)
        tk.Label(self.root, text=f"🔥 {alert_type} 🔥", font=("Segoe UI", 18, "bold"),
                 fg="#FACC15", bg="#DC2626").pack(pady=5)

        location_message = "Shooter detected in building B! Move away from Building B!" if not report else "Danger reported in your area! Call 911 immediately."
        tk.Label(self.root, text=location_message,
                 font=("Segoe UI", 14, "bold"), fg="white", bg="#DC2626", wraplength=350, justify="center").pack(pady=5)

        if not report and os.path.exists(CROPPED_IMAGE_PATH):
            img = Image.open(CROPPED_IMAGE_PATH)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=tk_img, bg="#DC2626").pack(pady=10)
            self.root.alert_img = tk_img

        tk.Label(self.root, text="TAKE COVER IMMEDIATELY!",
                 font=("Segoe UI", 16, "bold"), fg="black", bg="#FACC15",
                 padx=20, pady=10).pack(pady=10)

        footer_frame = tk.Frame(self.root, bg="#991B1B")
        footer_frame.pack(side="bottom", fill="x")
        self.make_button(footer_frame, "⬅️ RETURN TO HOME", "#E5E7EB", "#111827", self.go_home_from_alert, width=WINDOW_WIDTH-20)

    def go_home_from_alert(self):
        self.flashing = False
        pygame.mixer.music.stop()
        self.create_home_ui()


if __name__ == "__main__":
    root = tk.Tk()
    app = MoveToSafetyApp(root)
    root.mainloop()
