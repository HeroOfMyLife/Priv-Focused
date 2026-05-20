import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import time
import random
import re
import math
import sys

from Core import IdentityVault 

# SETUP THEME 
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

#  HELPER CLASSES

class SecurityScoreCalculator:
    COMMON_PASSWORDS = {"password", "123456", "qwerty", "admin", "letmein", "monkey", "dragon"}

    @staticmethod
    def calculate_score(password):
        if not password: return 0, "Ass☠️", "☠️", "No password"
        
        score = 0
        length = len(password)
        if length >= 12: score += 40
        elif length >= 8: score += 25
        else: score += 10
        
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*]', password))
        score += sum([has_upper, has_lower, has_digit, has_special]) * 7
        
        if password.lower() in SecurityScoreCalculator.COMMON_PASSWORDS:
            score = 0
            
        if score < 40: return score, "Ass️", "☠️", "Weak"
        elif score < 70: return score, "Meh🤷", "🤷", "Moderate"
        else: return score, "It's Alright", "✅", "Strong"

class BreachMonitor:
    BAD_USERNAMES = {"admin", "root", "test", "user", "guest", "support", "john", "doe", "info", "sales"}

    @staticmethod
    def check(username):
        if username.lower() in BreachMonitor.BAD_USERNAMES:
            return True, {"breach": "Simulated DB Leak", "date": "2023"}
        return False, None

class HoldButton(ctk.CTkButton):
    def __init__(self, master, hold_time=3.0, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hold_time = hold_time
        self.command = command
        self.start_time = None
        self.is_holding = False
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Leave>", self.on_leave)

    def on_press(self, event):
        self.is_holding = True
        self.start_time = time.time()
        self.configure(fg_color="#c0392b")
        self.check_hold()

    def on_release(self, event):
        self.is_holding = False
        self.configure(fg_color="#e74c3c")
        self.configure(text="☠️ Shred")

    def on_leave(self, event):
        self.is_holding = False
        self.configure(fg_color="#e74c3c")
        self.configure(text="️ Shred")

    def check_hold(self):
        if not self.is_holding: return
        elapsed = time.time() - self.start_time
        progress = elapsed / self.hold_time
        if progress >= 1.0:
            self.is_holding = False
            self.configure(text="💀 DESTROYED")
            if self.command: self.command()
            self.after(1000, lambda: self.configure(text="☠️ Shred"))
        else:
            self.configure(text=f"Hold... {int(progress*100)}%")
            self.after(50, self.check_hold)

class SoundManager:
    def __init__(self):
        try:
            import winsound
            self.can_play = True
        except ImportError:
            self.can_play = False

    def play_click(self):
        if self.can_play: import winsound; winsound.Beep(800, 50)
    def play_alarm(self):
        if self.can_play: import winsound; winsound.Beep(400, 300)
    def play_shred(self):
        if self.can_play:
            import winsound
            for i in range(3): winsound.Beep(300 + (i*50), 100)

class AddFaceDialog(ctk.CTkToplevel):
    """Modal dialog to add a new identity"""
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.title("Add New Face")
        self.geometry("300x250")
        self.grab_set()  # Modal behavior
        
        ctk.CTkLabel(self, text="Username:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.entry_user = ctk.CTkEntry(self, width=200)
        self.entry_user.pack(pady=5)
        
        ctk.CTkLabel(self, text="Password:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.entry_pass = ctk.CTkEntry(self, width=200, show="*")
        self.entry_pass.pack(pady=5)
        
        ctk.CTkButton(self, text="✅ Add Face", command=self.submit, fg_color="#2ecc71").pack(pady=20)

    def submit(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()
        if user and pwd:
            self.callback(user, pwd)
            self.destroy()
        else:
            messagebox.showwarning("Input Error", "Username and Password cannot be empty!")

# MAIN APP

class IdentityApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Xandria-ID Vault")
        self.geometry("800x600")
        self.vault_data = {}
        self.sound = SoundManager()
        
        self.setup_ui()
        self.after(1000, self.start_floating_skulls)
        self.hacker_cursor_blink()

    def setup_ui(self):
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar.pack(side="left", fill="y")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="📚 XANDRIA", 
                                 font=ctk.CTkFont(size=20, weight="bold"), text_color="#00ff00")
        self.logo.pack(pady=30)
        
        self.btn_add = ctk.CTkButton(self.sidebar, text="+ New Face", 
                                     command=self.open_add_modal, fg_color="#2ecc71")
        self.btn_add.pack(pady=10, padx=20)
        
        self.btn_demo = ctk.CTkButton(self.sidebar, text=" Load Demo Data", 
                                      command=self.load_demo_data, fg_color="#9b59b6")
        self.btn_demo.pack(pady=10, padx=20)
        
        self.btn_save = ctk.CTkButton(self.sidebar, text="💾 Save Vault", 
                                      command=self.save_vault, fg_color="#3498db")
        self.btn_save.pack(pady=10, padx=20)

        # --- Main Content ---
        self.main_area = ctk.CTkFrame(self, corner_radius=10, fg_color="#050505")
        self.main_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.header = ctk.CTkLabel(self.main_area, text="> root@xandria:~$ YOUR_FACES.exe █", 
                                   font=ctk.CTkFont(family="Courier", size=24, weight="bold"),
                                   text_color="#00ff00")
        self.header.pack(pady=20)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, width=500, height=400, label_text="")
        self.scroll_frame.pack(pady=10, fill="both", expand=True)
        
        self.refresh_ui()

    # UI ACTIONS 

    def open_add_modal(self):
        self.sound.play_click()
        AddFaceDialog(self, self.add_identity)

    def add_identity(self, username, password):
        name = f"Face_{len(self.vault_data)+1}"
        self.vault_data[name] = {"username": username, "password": password}
        self.refresh_ui()

    def load_demo_data(self):
        self.sound.play_click()
        demos = {
            "Face_1": {"username": "admin_root", "password": "password123"},      # Weak + Breached
            "Face_2": {"username": "john.doe88", "password": "Tr0ub4dor&3"},      # Strong + Safe
            "Face_3": {"username": "test_user", "password": "qwerty"},            # Very Weak + Breached
            "Face_4": {"username": "secure_ops", "password": "K9#mP2$vL!xQz"}     # Very Strong + Safe
        }
        self.vault_data.update(demos)
        self.refresh_ui()
        messagebox.showinfo("Loaded", "4 demo faces loaded with varying security levels!")

    def refresh_ui(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.vault_data:
            ctk.CTkLabel(self.scroll_frame, text="[!] No faces stored. Initialize vault.", 
                         text_color="#555555", font=ctk.CTkFont(family="Courier")).pack(pady=50)
            return

        for name, details in self.vault_data.items():
            self.create_identity_card(name, details)

    def create_identity_card(self, name, details):
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=8, fg_color="#111111", border_width=1, border_color="#333333")
        card.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(card, text=f"👤 {name}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00ff00").pack(anchor="w", padx=10, pady=(8,0))
        ctk.CTkLabel(card, text=f"usr: {details['username']} | pwd: {'•'*8}", text_color="#aaaaaa", font=ctk.CTkFont(family="Courier")).pack(anchor="w", padx=10, pady=4)
        
        #Security Score Calc
        score, category, emoji, _ = SecurityScoreCalculator.calculate_score(details['password'])
        color = "#ff0000" if score < 40 else "#ffaa00" if score < 70 else "#00ff00"
        ctk.CTkLabel(card, text=f"{emoji} {category} [{score}/100]", text_color=color).pack(anchor="w", padx=10)
        
        bar = ctk.CTkProgressBar(card, width=300, progress_color=color)
        bar.pack(fill="x", padx=10, pady=4)
        bar.set(score / 100)

        #Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        ctk.CTkButton(btn_frame, text="🔍 Breach", width=90, command=lambda n=name: self.check_breach(n), fg_color="#e67e22").pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="👁️ Reveal", width=80, command=lambda n=name: self.reveal_identity(n)).pack(side="left", padx=4)
        HoldButton(btn_frame, hold_time=2.0, command=lambda n=name: self.shred_identity(n), text="☠️ Shred", fg_color="#c0392b", width=90).pack(side="right", padx=4)

    def check_breach(self, name):
        self.sound.play_click()
        username = self.vault_data[name]['username']
        is_breached, info = BreachMonitor.check(username)
        if is_breached:
            self.sound.play_alarm()
            messagebox.showerror("☠️ BREACH DETECTED", f"Username '{username}' compromised!\nSource: {info['breach']}")
        else:
            messagebox.showinfo("✅ Secure", f"Username '{username}' not in breach DB.")

    def reveal_identity(self, name):
        self.sound.play_click()
        messagebox.showinfo("Revealed", f"Password: {self.vault_data[name]['password']}")

    def shred_identity(self, name):
        self.sound.play_shred()
        if name in self.vault_data:
            del self.vault_data[name]
            self.refresh_ui()

    def save_vault(self):
        self.sound.play_click()
        try:
            vault = IdentityVault("demo_password") 
            vault.save_vault("my_vault.aadi", self.vault_data)
            messagebox.showinfo("Saved", "Vault encrypted & saved to my_vault.aadi")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def hacker_cursor_blink(self):
        current = self.header.cget("text")
        if current.endswith("█"):
            self.header.configure(text=current[:-1] + " ")
        else:
            self.header.configure(text=current.rstrip() + "█")
        self.after(500, self.hacker_cursor_blink)

    def start_floating_skulls(self):
        self.skulls = []
        icons = ["☠️", "💀", "️", "🔐"]
        for i in range(6):
            skull = ctk.CTkLabel(self.main_area, text=random.choice(icons), 
                                 font=ctk.CTkFont(size=random.randint(18, 32)))
            skull.place(x=0, y=0)
            skull.attributes('-alpha', 0.25)  # Semi-transparent
            self.skulls.append({
                'widget': skull,
                'base_x': random.randint(30, 450),
                'base_y': random.randint(30, 450),
                'phase_x': random.uniform(0, 6.28),
                'phase_y': random.uniform(0, 6.28),
                'speed': random.uniform(0.8, 1.5)
            })
        self.start_time = time.time()
        self.animate_skulls()

    def animate_skulls(self):
        current_time = time.time() - self.start_time
        for item in self.skulls:
            x = item['base_x'] + math.sin(current_time * item['speed'] + item['phase_x']) * 40
            y = item['base_y'] + math.cos(current_time * item['speed'] * 0.7 + item['phase_y']) * 25
            item['widget'].place(x=x, y=y)
        self.after(30, self.animate_skulls)  # ~30 FPS smooth animation


if __name__ == "__main__":
    app = IdentityApp()
    app.mainloop()