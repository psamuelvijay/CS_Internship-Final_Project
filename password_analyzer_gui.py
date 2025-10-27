#!/usr/bin/env python3
"""
Professional Password Analyzer & Wordlist Generator GUI
--------------------------------------------------------
A modern, visually appealing Tkinter interface with dark theme, real-time
password analysis, and custom wordlist generation.

Author: Samuel Vijay
Version: 2.0
Date: 2025-10-27
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
from datetime import datetime
import re

# Try importing backend logic
try:
    from password_analyzer import (
        generate_from_parts,
        analyze_password,
        save_wordlist,
        expand_years,
        permutations_case,
    )
except ImportError:
    # --- Fallback stubs (if password_analyzer.py not present) ---
    def generate_from_parts(parts, years=None, max_words=20000, add_reversed=False, add_repeats=False):
        words = []
        for p in parts:
            words.extend({p, p.lower(), p.capitalize()})
        return list(words)[:max_words]

    def analyze_password(pwd, user_inputs=None):
        return {"score": 0, "crack_times_display": {}, "feedback": {"suggestions": []}}

    def save_wordlist(words, outpath="wordlist.txt", gzip_out=False):
        with open(outpath, "w", encoding="utf-8") as f:
            f.writelines(w + "\n" for w in words)
        return outpath

    def expand_years(y): return []
    def permutations_case(w): return [w, w.lower(), w.capitalize()]


# ---------------- TOOLTIP CLASS ----------------
class ToolTip:
    """Custom tooltip popup for widgets"""

    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#2d2d2d", foreground="#ffffff",
            relief="solid", borderwidth=1, font=("Segoe UI", 9),
            wraplength=200
        )
        label.pack(ipadx=5, ipady=3)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# ---------------- PASSWORD STRENGTH BAR ----------------
class PasswordStrengthIndicator:
    """Displays real-time strength updates for a password"""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=(5, 0))

        ttk.Label(self.frame, text="Strength:", font=("Segoe UI", 9)).pack(side="left")
        self.strength_bar = tk.Canvas(self.frame, height=20, width=200, bg="#1a1a1a", highlightthickness=0)
        self.strength_bar.pack(side="left", padx=(10, 0))
        self.score_label = ttk.Label(self.frame, text="", font=("Segoe UI", 9, "bold"))
        self.score_label.pack(side="left", padx=(10, 0))

    def update_strength(self, score):
        colors = ["#ff4444", "#ff8800", "#ffaa00", "#88cc00", "#44ff44"]
        labels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
        score = max(0, min(score, 4))
        width = (score + 1) * 40
        self.strength_bar.delete("all")
        self.strength_bar.create_rectangle(0, 0, width, 20, fill=colors[score], outline="")
        self.strength_bar.create_rectangle(0, 0, 200, 20, outline="#444444", width=1)
        self.score_label.config(text=f"{labels[score]} ({score}/4)")


# ---------------- MODERN BUTTON ----------------
class ModernButton(ttk.Button):
    """Custom hover-style button"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind("<Enter>", lambda e: self.configure(style="Hover.TButton"))
        self.bind("<Leave>", lambda e: self.configure(style="TButton"))


# ---------------- PROGRESS DIALOG ----------------
class ProgressDialog:
    """Non-blocking progress window for background tasks"""

    def __init__(self, parent, title="Processing", message="Please wait..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg="#1a1a1a")

        tk.Label(self.dialog, text=message, bg="#1a1a1a", fg="#ffffff", font=("Segoe UI", 10)).pack(pady=20)
        self.progress = ttk.Progressbar(self.dialog, mode="indeterminate")
        self.progress.pack(pady=10, padx=20, fill="x")
        self.progress.start()
        ttk.Button(self.dialog, text="Cancel", command=self.cancel).pack(pady=10)
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        self.destroy()

    def destroy(self):
        self.progress.stop()
        self.dialog.destroy()


# ---------------- MAIN GUI APP ----------------
class PasswordAnalyzerGUI:
    """Main application class"""

    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_styles()
        self.setup_vars()
        self.build_ui()
        self.load_settings()

    def setup_window(self):
        self.root.title("Password Analyzer & Wordlist Generator")
        self.root.geometry("1000x800")
        self.root.minsize(800, 700)
        self.root.configure(bg="#1a1a1a")
        x = (self.root.winfo_screenwidth() // 2) - 500
        y = (self.root.winfo_screenheight() // 2) - 400
        self.root.geometry(f"1000x800+{x}+{y}")

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#1a1a1a")
        style.configure("TLabel", background="#1a1a1a", foreground="#ffffff")
        style.configure("TButton", background="#2d2d2d", foreground="#ffffff")
        style.configure("Hover.TButton", background="#404040", foreground="#ffffff")
        style.configure("TNotebook", background="#1a1a1a")
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#ffffff", padding=[20, 10])
        style.map("TNotebook.Tab", background=[("selected", "#404040")])

    def setup_vars(self):
        self.pwd_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.pet_var = tk.StringVar()
        self.fav_var = tk.StringVar()
        self.dob_var = tk.StringVar()
        self.years_var = tk.StringVar()
        self.maxwords_var = tk.StringVar(value="20000")
        self.gzip_var = tk.BooleanVar()
        self.rev_var = tk.BooleanVar()
        self.repeat_var = tk.BooleanVar()
        self.show_pwd_var = tk.BooleanVar()

    def build_ui(self):
        main = ttk.Frame(self.root, padding="15")
        main.pack(fill="both", expand=True)

        tk.Label(main, text="Password Analyzer & Wordlist Generator", font=("Segoe UI", 16, "bold"),
                 bg="#1a1a1a", fg="#ffffff").pack(pady=(0, 20))

        self.tabs = ttk.Notebook(main)
        self.tabs.pack(fill="both", expand=True)
        self.build_analysis_tab()
        self.build_generator_tab()
        self.build_output_section(main)

    # ---------------- Tabs ----------------
    def build_analysis_tab(self):
        tab = ttk.Frame(self.tabs, padding="15")
        self.tabs.add(tab, text="Password Analysis")

        pwd_section = ttk.LabelFrame(tab, text="Password Input", padding="10")
        pwd_section.pack(fill="x", pady=(0, 10))

        entry_frame = ttk.Frame(pwd_section)
        entry_frame.pack(fill="x")
        ttk.Label(entry_frame, text="Password:", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        entry_inner = ttk.Frame(entry_frame)
        entry_inner.pack(fill="x", pady=(5, 0))
        self.pwd_entry = ttk.Entry(entry_inner, textvariable=self.pwd_var, show="*", font=("Segoe UI", 10))
        self.pwd_entry.pack(side="left", fill="x", expand=True)
        ttk.Checkbutton(entry_inner, text="Show", variable=self.show_pwd_var,
                        command=self.toggle_pwd).pack(side="right", padx=(10, 0))
        self.strength_indicator = PasswordStrengthIndicator(pwd_section)

        info_section = ttk.LabelFrame(tab, text="Personal Information", padding="10")
        info_section.pack(fill="x", pady=(0, 10))
        self.create_input(info_section, "Names:", self.name_var, "e.g., John, Jane")
        self.create_input(info_section, "Pets:", self.pet_var, "e.g., Fluffy, Rex")
        self.create_input(info_section, "Favorites:", self.fav_var, "e.g., pizza, music")
        self.create_input(info_section, "DOB/Dates:", self.dob_var, "e.g., 1990, 20010101")

        ModernButton(tab, text="Analyze Password", command=self.analyze_password).pack(pady=15)

    def build_generator_tab(self):
        tab = ttk.Frame(self.tabs, padding="15")
        self.tabs.add(tab, text="Wordlist Generator")

        section = ttk.LabelFrame(tab, text="Input Data", padding="10")
        section.pack(fill="x", pady=(0, 10))
        self.create_input(section, "Names:", self.name_var, "Enter names separated by commas")
        self.create_input(section, "Pets:", self.pet_var, "Enter pet names separated by commas")
        self.create_input(section, "Favorites:", self.fav_var, "Enter favorite things separated by commas")
        self.create_input(section, "DOB/Dates:", self.dob_var, "Enter DOB or years")
        self.create_input(section, "Years:", self.years_var, "Enter years or range (e.g., 1990 2025)")

        opts = ttk.LabelFrame(tab, text="Generation Options", padding="10")
        opts.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(opts, text="Add reversed variants", variable=self.rev_var).pack(side="left")
        ttk.Checkbutton(opts, text="Add repeats", variable=self.repeat_var).pack(side="left", padx=(20, 0))
        ttk.Checkbutton(opts, text="Compress output (.gz)", variable=self.gzip_var).pack(side="left", padx=(20, 0))

        maxf = ttk.Frame(opts)
        maxf.pack(fill="x", pady=(10, 0))
        ttk.Label(maxf, text="Max words:").pack(side="left")
        ttk.Entry(maxf, textvariable=self.maxwords_var, width=10).pack(side="left", padx=(10, 0))

        ModernButton(tab, text="Generate Wordlist", command=self.generate_wordlist).pack(pady=15)

    def build_output_section(self, parent):
        frame = ttk.LabelFrame(parent, text="Output", padding="10")
        frame.pack(fill="both", expand=True, pady=(15, 0))
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True)
        self.output = tk.Text(text_frame, height=10, font=("Consolas", 9),
                              bg="#0d1117", fg="#ffffff", insertbackground="#ffffff", wrap="word")
        scroll = ttk.Scrollbar(text_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        ModernButton(frame, text="Clear Output", command=lambda: self.output.delete(1.0, tk.END)).pack(anchor="e", pady=(10, 0))

    # ---------------- Helpers ----------------
    def create_input(self, parent, label, var, tip):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=3)
        ttk.Label(frame, text=label).pack(anchor="w")
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(fill="x", pady=(2, 0))
        ToolTip(entry, tip)
        return entry

    def toggle_pwd(self):
        self.pwd_entry.configure(show="" if self.show_pwd_var.get() else "*")

    def collect_inputs(self):
        vals = []
        for v in [self.name_var, self.pet_var, self.fav_var, self.dob_var]:
            vals.extend(x.strip() for x in v.get().replace(",", " ").split() if x.strip())
        return vals

    def analyze_password(self):
        pwd = self.pwd_var.get().strip()
        if not pwd:
            messagebox.showwarning("Missing Input", "Please enter a password.")
            return
        try:
            data = analyze_password(pwd, user_inputs=self.collect_inputs())
            self.display_analysis(data, pwd)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def display_analysis(self, data, pwd):
        self.output.delete(1.0, tk.END)
        out = [
            "=" * 60,
            "PASSWORD ANALYSIS RESULTS",
            "=" * 60,
            f"Password: {'*' * len(pwd)}",
            f"Score: {data.get('score', 'N/A')}/4",
            "",
            "CRACK TIME ESTIMATES:"
        ]
        for k, v in data.get("crack_times_display", {}).items():
            out.append(f"  {k}: {v}")
        fb = data.get("feedback", {})
        if fb.get("warning"):
            out.append(f"\nWARNING: {fb['warning']}")
        if fb.get("suggestions"):
            out.append("\nSUGGESTIONS:")
            out.extend(f"  • {s}" for s in fb["suggestions"])
        self.output.insert(tk.END, "\n".join(out) + "\n" + "=" * 60)

    def generate_wordlist(self):
        inputs = self.collect_inputs()
        if not inputs:
            messagebox.showwarning("Missing Data", "Please provide personal info for wordlist.")
            return
        try:
            max_words = int(self.maxwords_var.get().strip() or 20000)
        except ValueError:
            max_words = 20000
        progress = ProgressDialog(self.root, "Generating Wordlist", "Generating custom wordlist...")

        def task():
            try:
                words = generate_from_parts(inputs, max_words=max_words,
                                            add_reversed=self.rev_var.get(),
                                            add_repeats=self.repeat_var.get())
                if progress.cancelled:
                    return
                ext = ".gz" if self.gzip_var.get() else ".txt"
                path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[("Text", "*.txt"), ("Gzip", "*.gz")])
                if path:
                    save_wordlist(words, path, gzip_out=self.gzip_var.get())
                    self.root.after(0, lambda: self.output.insert(tk.END, f"\n✓ Saved {len(words)} words to {path}\n"))
            finally:
                self.root.after(0, progress.destroy)

        threading.Thread(target=task, daemon=True).start()

    def load_settings(self):
        try:
            with open("gui_settings.json", "r") as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(self, f"{k}_var"):
                    getattr(self, f"{k}_var").set(v)
        except Exception:
            pass

    def save_settings(self):
        data = {k: getattr(self, f"{k}_var").get() for k in
                ["name", "pet", "fav", "dob", "years", "maxwords", "gzip", "rev", "repeat", "show_pwd"]}
        with open("gui_settings.json", "w") as f:
            json.dump(data, f, indent=2)


def main():
    root = tk.Tk()
    app = PasswordAnalyzerGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_settings(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
