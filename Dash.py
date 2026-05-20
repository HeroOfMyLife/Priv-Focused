import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import time
import random
import re
import math
import sys
import json
import hashlib
import os

from Core import IdentityVault 

# SETUP THEME 
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# 🔐 MASTER PASSWORD & LOGIN SYSTEM

class MasterPasswordManager:
    """Handles master password storage, verification, and recovery"""
    
    CONFIG_FILE = "kegorak_config.json"
    
    @staticmethod
    def _hash_password(password, salt):
        """Hash password with PBKDF2"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )
    
    @staticmethod   
    def setup_new_user(master_password, recovery_answer=None, recovery_question=None):
        """Create new user config with custom recovery question"""
        salt = os.urandom(32)
        password_hash = MasterPasswordManager._hash_password(master_password, salt)
        
        # Use custom question or default
        final_question = recovery_question if recovery_question else "What was your first pet's name?"
        
        config = {
            "salt": salt.hex(),
            "password_hash": password_hash.hex(),
            "recovery_question": final_question,
            "recovery_answer_hash": MasterPasswordManager._hash_password(
                recovery_answer or "default_recovery", salt
            ).hex() if recovery_answer else None,
            "created_at": time.time()
        }
        
        with open(MasterPasswordManager.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
        
        with open(MasterPasswordManager.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    
    @staticmethod
    def verify_password(master_password):
        """Check if password matches stored hash"""
        if not os.path.exists(MasterPasswordManager.CONFIG_FILE):
            return False
        
        with open(MasterPasswordManager.CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        salt = bytes.fromhex(config['salt'])
        stored_hash = bytes.fromhex(config['password_hash'])
        test_hash = MasterPasswordManager._hash_password(master_password, salt)
        
        return test_hash == stored_hash
    
    @staticmethod
    def change_password(old_password, new_password):
        """Change master password after verifying old one"""
        if not MasterPasswordManager.verify_password(old_password):
            return False, "Incorrect current password"
        
        with open(MasterPasswordManager.CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        salt = bytes.fromhex(config['salt'])
        config['password_hash'] = MasterPasswordManager._hash_password(
            new_password, salt
        ).hex()
        config['updated_at'] = time.time()
        
        with open(MasterPasswordManager.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True, "Password changed successfully"
    
    @staticmethod
    def recover_password(recovery_answer):
        """Recover access via security question (RESETS vault - warning!)"""
        if not os.path.exists(MasterPasswordManager.CONFIG_FILE):
            return False, "No account found"
        
        with open(MasterPasswordManager.CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        if not config.get('recovery_answer_hash'):
            return False, "Recovery not configured"
        
        salt = bytes.fromhex(config['salt'])
        stored_hash = bytes.fromhex(config['recovery_answer_hash'])
        # Normalize answer: lowercase + strip whitespace for matching
        test_hash = MasterPasswordManager._hash_password(
            recovery_answer.strip().lower(), salt
        )
        
        if test_hash == stored_hash:
            # ⚠️ WARNING: This resets the vault! 
            # In production, you'd decrypt with old key, re-encrypt with new
            return True, "Recovery successful - please set new password"
        
        return False, "Incorrect recovery answer"
    
    @staticmethod
    def user_exists():
        """Check if account is set up"""
        return os.path.exists(MasterPasswordManager.CONFIG_FILE)
    
    @staticmethod
    def get_recovery_question():
        """Get the configured recovery question"""
        if not os.path.exists(MasterPasswordManager.CONFIG_FILE):
            return "What was your first pet's name?"
        
        with open(MasterPasswordManager.CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        return config.get('recovery_question', "What was your first pet's name?")

# 🎭 LOGIN & SETUP DIALOGS

class LoginDialog(ctk.CTkToplevel):
    """Login screen for Kegorak"""
    def __init__(self, parent, on_success, on_signup, on_recovery=None):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.on_signup = on_signup
        self.on_recovery = on_recovery
        
        self.title("🔐 Kegorak Login")
        self.geometry("400x350")
        self.resizable(False, False)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 350) // 2
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = ctk.CTkLabel(
            self, 
            text="🎭 KEGORAK",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#00ff00"
        )
        header.pack(pady=30)
        
        subtitle = ctk.CTkLabel(
            self,
            text="Secure Identity Vault",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        subtitle.pack(pady=(0, 20))
        
        # Password entry
        ctk.CTkLabel(self, text="Master Password:", font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
        self.password_entry = ctk.CTkEntry(self, width=250, show="•", font=ctk.CTkFont(size=14))
        self.password_entry.pack(pady=5)
        self.password_entry.bind("<Return>", lambda e: self.login())
        self.password_entry.focus()
        
        # Login button
        login_btn = ctk.CTkButton(
            self, 
            text="🔓 Unlock Vault", 
            command=self.login,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            width=250
        )
        login_btn.pack(pady=20)
        
        # Recovery & Signup links
        link_frame = ctk.CTkFrame(self, fg_color="transparent")
        link_frame.pack(pady=10)
        
        ctk.CTkButton(
            link_frame,
            text="🔑 Forgot Password?",
            command=self.recover_password,
            fg_color="transparent",
            text_color="#3498db",
            hover_color="#2980b9",
            width=150
        ).pack(side="left", padx=10)
        
        if not MasterPasswordManager.user_exists():
            ctk.CTkButton(
                link_frame,
                text="✨ Create Account",
                command=self.on_signup,
                fg_color="transparent",
                text_color="#9b59b6",
                hover_color="#8e44ad",
                width=150
            ).pack(side="right", padx=10)
    
    def login(self):
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Input Required", "Please enter your master password")
            return
        
        if MasterPasswordManager.verify_password(password):
            self.sound_click()
            self.destroy()
            self.on_success(password)
        else:
            self.sound_error()
            messagebox.showerror("Access Denied", "Incorrect master password")
            self.password_entry.delete(0, tk.END)
    
    def recover_password(self):
        """Open recovery dialog with proper callback"""
        if self.on_recovery:
            self.on_recovery()
    
    def sound_click(self):
        try: import winsound; winsound.Beep(800, 50)
        except: pass
    
    def sound_error(self):
        try: import winsound; winsound.Beep(300, 200)
        except: pass

class SignupDialog(ctk.CTkToplevel):
    """New user setup with show/hide password toggles"""
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.parent = parent
        self.on_complete = on_complete
        
        self.title("✨ Create Kegorak Account")
        self.geometry("420x580")  # Increased from 450 to 580
        self.resizable(False, False)
        self.grab_set()
        
        # Password visibility states
        self.show_master = False
        self.show_confirm = False
        self.show_recovery = False
        
        self.setup_ui()
    
    def setup_ui(self):
        ctk.CTkLabel(
            self,
            text="🔐 Setup Master Password",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            self,
            text="⚠️ This password CANNOT be recovered.\nStore it safely!",
            font=ctk.CTkFont(size=10),
            text_color="#e74c3c"
        ).pack(pady=(0, 20))
        
        # Master password with show/hide toggle
        master_frame = ctk.CTkFrame(self, fg_color="transparent")
        master_frame.pack(pady=(10, 5))
        
        ctk.CTkLabel(master_frame, text="Create Master Password:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 5))
        
        pass_frame1 = ctk.CTkFrame(master_frame, fg_color="transparent")
        pass_frame1.pack(fill="x")
        
        self.master_pass = ctk.CTkEntry(pass_frame1, width=280, show="•")
        self.master_pass.pack(side="left", padx=(0, 5))
        
        toggle1_btn = ctk.CTkButton(
            pass_frame1, 
            text="👁️", 
            width=40,
            command=self.toggle_master_password,
            fg_color="#34495e"
        )
        toggle1_btn.pack(side="left")
        
        # Confirm password with show/hide toggle
        confirm_frame = ctk.CTkFrame(self, fg_color="transparent")
        confirm_frame.pack(pady=(15, 5))
        
        ctk.CTkLabel(confirm_frame, text="Confirm Master Password:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 5))
        
        pass_frame2 = ctk.CTkFrame(confirm_frame, fg_color="transparent")
        pass_frame2.pack(fill="x")
        
        self.confirm_pass = ctk.CTkEntry(pass_frame2, width=280, show="•")
        self.confirm_pass.pack(side="left", padx=(0, 5))
        self.confirm_pass.bind("<Return>", lambda e: self.create_account())
        
        toggle2_btn = ctk.CTkButton(
            pass_frame2, 
            text="👁️", 
            width=40,
            command=self.toggle_confirm_password,
            fg_color="#34495e"
        )
        toggle2_btn.pack(side="left")
        
        # Recovery question (EDITABLE - not just placeholder)
        ctk.CTkLabel(self, text="Recovery Question:", font=ctk.CTkFont(size=12)).pack(pady=(25, 5))
        self.recovery_q = ctk.CTkEntry(self, width=280, placeholder_text="What was your first pet's name?")
        self.recovery_q.pack(pady=5)
        self.recovery_q.insert(0, "What was your first pet's name?")  # Pre-fill but editable
        
        # Recovery answer with show/hide toggle
        recovery_frame = ctk.CTkFrame(self, fg_color="transparent")
        recovery_frame.pack(pady=(15, 5))
        
        ctk.CTkLabel(recovery_frame, text="Recovery Answer:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 5))
        
        pass_frame3 = ctk.CTkFrame(recovery_frame, fg_color="transparent")
        pass_frame3.pack(fill="x")
        
        self.recovery_a = ctk.CTkEntry(pass_frame3, width=280, show="•")
        self.recovery_a.pack(side="left", padx=(0, 5))
        
        toggle3_btn = ctk.CTkButton(
            pass_frame3, 
            text="👁️", 
            width=40,
            command=self.toggle_recovery_password,
            fg_color="#34495e"
        )
        toggle3_btn.pack(side="left")
        
        # ✅ SUBMIT BUTTON - Now visible!
        ctk.CTkButton(
            self,
            text="✅ Create Account & Continue",
            command=self.create_account,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            width=280,
            height=40
        ).pack(pady=30)
    
    def toggle_master_password(self):
        """Toggle master password visibility"""
        self.show_master = not self.show_master
        self.master_pass.configure(show="" if self.show_master else "•")
    
    def toggle_confirm_password(self):
        """Toggle confirm password visibility"""
        self.show_confirm = not self.show_confirm
        self.confirm_pass.configure(show="" if self.show_confirm else "•")
    
    def toggle_recovery_password(self):
        """Toggle recovery answer visibility"""
        self.show_recovery = not self.show_recovery
        self.recovery_a.configure(show="" if self.show_recovery else "•")
    
    def create_account(self):
        master = self.master_pass.get()
        confirm = self.confirm_pass.get()
        recovery_q = self.recovery_q.get().strip()
        recovery_a = self.recovery_a.get().strip()
        
        if len(master) < 8:
            messagebox.showwarning("Weak Password", "Master password must be at least 8 characters")
            return
        
        if master != confirm:
            messagebox.showerror("Mismatch", "Passwords do not match")
            return
        
        # Normalize recovery answer before saving (case-insensitive, trimmed)
        recovery_normalized = recovery_a.strip().lower() if recovery_a else None
        
        if MasterPasswordManager.setup_new_user(master, recovery_normalized, recovery_q if recovery_q else None):
            self.sound_success()
            self.destroy()
            self.on_complete(master)
        else:
            messagebox.showerror("Error", "Failed to create account")
    
    def sound_success(self):
        try: 
            import winsound
            winsound.Beep(1000, 100)
            winsound.Beep(1500, 100)
        except: pass
        
class RecoveryDialog(ctk.CTkToplevel):
    """Password recovery via security question with show/hide toggle"""
    def __init__(self, parent, manager_class, on_recovery_success=None):
        super().__init__(parent)
        self.parent = parent
        self.manager = manager_class
        self.on_recovery_success = on_recovery_success
        
        self.title("🔑 Password Recovery")
        self.geometry("420x380")  # Increased height
        self.resizable(False, False)
        self.grab_set()
        
        self.show_answer = False
        
        self.setup_ui()
    
    def setup_ui(self):
        ctk.CTkLabel(
            self,
            text="⚠️ Recovery Warning",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#e74c3c"
        ).pack(pady=20)
        
        ctk.CTkLabel(
            self,
            text="Recovery will RESET your vault.\nAll saved identities will be lost.\n\nThis is a last resort option.",
            font=ctk.CTkFont(size=11),
            justify="left"
        ).pack(pady=(0, 20), padx=20)
        
        # Display the ACTUAL configured question (not hardcoded)
        question = self.manager.get_recovery_question()
        ctk.CTkLabel(
            self, 
            text=f"Question: {question}",  # Changed from "Answer:" to "Question:"
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3498db"
        ).pack(pady=10)
        
        # Answer field with show/hide toggle
        answer_frame = ctk.CTkFrame(self, fg_color="transparent")
        answer_frame.pack(pady=10)
        
        self.answer_entry = ctk.CTkEntry(answer_frame, width=280, show="•")
        self.answer_entry.pack(side="left", padx=(0, 5))
        self.answer_entry.bind("<Return>", lambda e: self.attempt_recovery())
        self.answer_entry.focus()
        
        toggle_btn = ctk.CTkButton(
            answer_frame,
            text="👁️",
            width=40,
            command=self.toggle_answer_visibility,
            fg_color="#34495e"
        )
        toggle_btn.pack(side="left")
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=self.destroy,
            fg_color="#7f8c8d",
            width=100
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="⚠️ Reset Vault",
            command=self.attempt_recovery,
            fg_color="#e74c3c",
            width=120
        ).pack(side="right", padx=10)
    
    def toggle_answer_visibility(self):
        """Toggle recovery answer visibility"""
        self.show_answer = not self.show_answer
        self.answer_entry.configure(show="" if self.show_answer else "•")
    
    def attempt_recovery(self):
        answer = self.answer_entry.get()
        success, message = self.manager.recover_password(answer)
        
        if success:
            # Reset config for new setup
            if os.path.exists(self.manager.CONFIG_FILE):
                os.remove(self.manager.CONFIG_FILE)
            messagebox.showinfo("Reset Complete", f"{message}\n\nPlease create a new account.")
            self.destroy()
            # Use callback for navigation (FIXED!)
            if self.on_recovery_success:
                self.on_recovery_success()
        else:
            messagebox.showerror("Recovery Failed", message)


class ChangePasswordDialog(ctk.CTkToplevel):
    """Change master password"""
    def __init__(self, parent, on_change):
        super().__init__(parent)
        self.parent = parent
        self.on_change = on_change
        
        self.title("🔐 Change Master Password")
        self.geometry("400x350")
        self.resizable(False, False)
        self.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        ctk.CTkLabel(
            self,
            text="Change Master Password",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=25)
        
        ctk.CTkLabel(self, text="Current Password:", font=ctk.CTkFont(size=12)).pack(pady=(15, 5))
        self.current_pass = ctk.CTkEntry(self, width=250, show="•")
        self.current_pass.pack(pady=5)
        
        ctk.CTkLabel(self, text="New Password:", font=ctk.CTkFont(size=12)).pack(pady=(15, 5))
        self.new_pass = ctk.CTkEntry(self, width=250, show="•")
        self.new_pass.pack(pady=5)
        
        ctk.CTkLabel(self, text="Confirm New Password:", font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
        self.confirm_pass = ctk.CTkEntry(self, width=250, show="•")
        self.confirm_pass.pack(pady=5)
        self.confirm_pass.bind("<Return>", lambda e: self.change_password())
        
        ctk.CTkButton(
            self,
            text="✅ Update Password",
            command=self.change_password,
            fg_color="#3498db",
            width=250
        ).pack(pady=25)
    
    def change_password(self):
        current = self.current_pass.get()
        new = self.new_pass.get()
        confirm = self.confirm_pass.get()
        
        if new != confirm:
            messagebox.showerror("Mismatch", "New passwords do not match")
            return
        
        if len(new) < 8:
            messagebox.showwarning("Weak Password", "New password must be at least 8 characters")
            return
        
        success, message = MasterPasswordManager.change_password(current, new)
        
        if success:
            self.sound_success()
            messagebox.showinfo("Success", message)
            self.destroy()
            if self.on_change:
                self.on_change(new)
        else:
            messagebox.showerror("Failed", message)
    
    def sound_success(self):
        try: 
            import winsound
            winsound.Beep(1000, 100)
            winsound.Beep(1500, 100)
        except: pass

# 🛠️ EXISTING HELPER CLASSES 

class SecurityScoreCalculator:
    COMMON_PASSWORDS = {"password", "123456", "qwerty", "admin", "password123", "monkey", "dragon"}

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
            
        if score < 40: return score, "Ass☠️", "☠️", "Weak"
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
        self.configure(text="☠️ Shred")

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
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.title("Add New Face")
        self.geometry("300x250")
        self.grab_set()
        
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

#  MAIN APPLICATION

class IdentityApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kegorak-ID Vault")
        self.geometry("800x600")
        self.vault_data = {}
        self.master_password = None
        self.sound = SoundManager()
        
        # Show login first
        self.show_login()
    
    def show_login(self):
        """Display login screen"""
        self.withdraw()  # Hide main window
        
        def on_login_success(password):
            self.master_password = password
            self.deiconify()  # Show main window
            self.setup_ui()
            self.after(1000, self.start_floating_skulls)
            self.hacker_cursor_blink()
        
        def on_signup_click():
            self.show_signup()  # Fixed: actually call signup
        
        def on_recovery_click():
            self.show_recovery()  # Fixed: call recovery method
        
        login = LoginDialog(
            self, 
            on_success=on_login_success,
            on_signup=on_signup_click,
            on_recovery=on_recovery_click  # Pass the callback
        )
        
        # If no account exists, auto-show signup
        if not MasterPasswordManager.user_exists():
            self.after(100, lambda: self.show_signup())
    
    def show_signup(self):
        """Display signup screen"""
        def on_signup_complete(password):
            self.master_password = password
            self.deiconify()
            self.setup_ui()
            self.after(1000, self.start_floating_skulls)
            self.hacker_cursor_blink()
            messagebox.showinfo("Welcome", "✅ Account created! Your vault is ready.")
        
        SignupDialog(self, on_signup_complete)
    
    def show_recovery(self):
        """Display recovery screen with proper callback flow"""
        def on_recovery_success():
            # After successful recovery, show signup to create new account
            self.show_signup()
        
        RecoveryDialog(
            self, 
            MasterPasswordManager, 
            on_recovery_success=on_recovery_success  # Pass the callback
        )
    
    def setup_ui(self):
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar.pack(side="left", fill="y")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="🎭 Kegorak", 
                                 font=ctk.CTkFont(size=20, weight="bold"), text_color="#00ff00")
        self.logo.pack(pady=30)
        
        self.btn_add = ctk.CTkButton(self.sidebar, text="+ New Face", 
                                     command=self.open_add_modal, fg_color="#2ecc71")
        self.btn_add.pack(pady=10, padx=20)
        
        self.btn_demo = ctk.CTkButton(self.sidebar, text="🎲 Load Demo", 
                                      command=self.load_demo_data, fg_color="#9b59b6")
        self.btn_demo.pack(pady=10, padx=20)
        
        self.btn_save = ctk.CTkButton(self.sidebar, text="💾 Save Vault", 
                                      command=self.save_vault, fg_color="#3498db")
        self.btn_save.pack(pady=10, padx=20)
        
        # Master Password Management
        self.btn_change_pass = ctk.CTkButton(
            self.sidebar, 
            text="🔐 Change Password", 
            command=self.open_change_password,
            fg_color="#16a085"
        )
        self.btn_change_pass.pack(pady=10, padx=20)
        
        self.btn_logout = ctk.CTkButton(
            self.sidebar,
            text="🚪 Logout",
            command=self.logout,
            fg_color="#7f8c8d"
        )
        self.btn_logout.pack(pady=10, padx=20, side="bottom")

        # Main Content
        self.main_area = ctk.CTkFrame(self, corner_radius=10, fg_color="#050505")
        self.main_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.header = ctk.CTkLabel(self.main_area, text="> root@kegorak:~$ YOUR_FACES.exe █", 
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
            "Face_1": {"username": "admin_root", "password": "password123"},      
            "Face_2": {"username": "john.doe88", "password": "Tr0ub4dor&3"},      
            "Face_3": {"username": "test_user", "password": "qwerty"},            
            "Face_4": {"username": "secure_ops", "password": "K9#mP2$vL!xQz"}     
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
        
        score, category, emoji, _ = SecurityScoreCalculator.calculate_score(details['password'])
        color = "#ff0000" if score < 40 else "#ffaa00" if score < 70 else "#00ff00"
        ctk.CTkLabel(card, text=f"{emoji} {category} [{score}/100]", text_color=color).pack(anchor="w", padx=10)
        
        bar = ctk.CTkProgressBar(card, width=300, progress_color=color)
        bar.pack(fill="x", padx=10, pady=4)
        bar.set(score / 100)

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
        if not self.master_password:
            messagebox.showerror("Error", "Not authenticated")
            return
        try:
            vault = IdentityVault(self.master_password) 
            vault.save_vault("kegorak_vault.aadi", self.vault_data)
            messagebox.showinfo("Saved", "Vault encrypted & saved to kegorak_vault.aadi")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Master Password Management
    def open_change_password(self):
        ChangePasswordDialog(self, self.on_password_changed)
    
    def on_password_changed(self, new_password):
        """Update session with new password"""
        self.master_password = new_password
        # Re-save vault with new password if needed
        if self.vault_data:
            self.save_vault()
    
    def logout(self):
        """Lock vault and return to login"""
        if messagebox.askyesno("Logout", "Lock vault and return to login screen?"):
            self.vault_data = {}
            self.master_password = None
            self.withdraw()
            self.show_login()

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
            skull.attributes('-alpha', 0.25)
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
        self.after(30, self.animate_skulls)


if __name__ == "__main__":
    app = IdentityApp()
    app.mainloop()
    app = IdentityApp()
    app.mainloop()
