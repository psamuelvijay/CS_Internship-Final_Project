#!/usr/bin/env python3
"""
Professional Password Analyzer & Wordlist Generator GUI
A modern, visually appealing Tkinter interface with dark theme and advanced features.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
from datetime import datetime
import re

# Import backend functions from password_analyzer.py
try:
    from password_analyzer import generate_from_parts, analyze_password, save_wordlist, expand_years, permutations_case
except Exception:
    # Fallback stubs (shouldn't be used if password_analyzer.py is present)
    def generate_from_parts(parts, years=None, max_words=20000, add_reversed=False, add_repeats=False):
        words = []
        for p in parts:
            words.append(p)
            words.append(p.lower())
            words.append(p.capitalize())
        return words
    
    def analyze_password(pwd, user_inputs=None):
        return {"score": 0, "crack_times_display": {}, "feedback": {"suggestions": []}}
    
    def save_wordlist(words, outpath="wordlist.txt", gzip_out=False):
        with open(outpath, "w", encoding="utf-8") as f:
            for w in words:
                f.write(w + "\n")
        return outpath
    
    def expand_years(y): return []
    def permutations_case(w): return [w, w.lower(), w.capitalize()]


class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tooltip_window = None

    def enter(self, event=None):
        self.show_tooltip()

    def leave(self, event=None):
        self.hide_tooltip()

    def show_tooltip(self):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                        background="#2d2d2d", foreground="#ffffff",
                        relief='solid', borderwidth=1, font=("Segoe UI", 9),
                        wraplength=200)
        label.pack(ipadx=5, ipady=3)

    def hide_tooltip(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()


class PasswordStrengthIndicator:
    """Real-time password strength indicator"""
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=(5, 0))
        
        self.strength_label = ttk.Label(self.frame, text="Strength:", font=("Segoe UI", 9))
        self.strength_label.pack(side="left")
        
        self.strength_bar = tk.Canvas(self.frame, height=20, width=200, bg="#1a1a1a", highlightthickness=0)
        self.strength_bar.pack(side="left", padx=(10, 0))
        
        self.score_label = ttk.Label(self.frame, text="", font=("Segoe UI", 9, "bold"))
        self.score_label.pack(side="left", padx=(10, 0))

    def update_strength(self, score):
        """Update the strength indicator based on score (0-4)"""
        self.strength_bar.delete("all")
        
        colors = ["#ff4444", "#ff8800", "#ffaa00", "#88cc00", "#44ff44"]
        labels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
        
        if score < 0 or score > 4:
            score = 0
        
        # Draw strength bar
        width = 200
        bar_width = (score + 1) * (width / 5)
        
        self.strength_bar.create_rectangle(0, 0, bar_width, 20, fill=colors[score], outline="")
        self.strength_bar.create_rectangle(0, 0, width, 20, outline="#444444", width=1)
        
        # Update score label
        self.score_label.config(text=f"{labels[score]} ({score}/4)")


class ModernButton(ttk.Button):
    """Custom button with hover effects"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, event):
        self.configure(style="Hover.TButton")
        
    def on_leave(self, event):
        self.configure(style="TButton")


class ProgressDialog:
    """Modal progress dialog for long operations"""
    def __init__(self, parent, title="Processing", message="Please wait..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        # Configure dialog styling
        self.dialog.configure(bg="#1a1a1a")
        
        # Message label
        msg_label = tk.Label(self.dialog, text=message, font=("Segoe UI", 10),
                           bg="#1a1a1a", fg="#ffffff")
        msg_label.pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill="x")
        self.progress.start()
        
        # Cancel button
        cancel_btn = ttk.Button(self.dialog, text="Cancel", command=self.cancel)
        cancel_btn.pack(pady=10)
        
        self.cancelled = False
        
    def cancel(self):
        self.cancelled = True
        self.dialog.destroy()
        
    def destroy(self):
        self.progress.stop()
        self.dialog.destroy()


class PasswordAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_styles()
        self.setup_variables()
        self.create_widgets()
        self.load_settings()
        self.setup_validation()
        
    def setup_window(self):
        """Configure the main window"""
        self.root.title("Password Analyzer & Wordlist Generator - Professional Edition")
        self.root.geometry("1000x800")
        self.root.configure(bg="#1a1a1a")
        self.root.minsize(800, 700)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1000x800+{x}+{y}")
        
    def setup_styles(self):
        """Configure modern dark theme styles"""
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        
        # Configure colors for dark theme
        self.style.configure("TFrame", background="#1a1a1a")
        self.style.configure("TLabel", background="#1a1a1a", foreground="#ffffff", font=("Segoe UI", 9))
        self.style.configure("TButton", background="#2d2d2d", foreground="#ffffff", font=("Segoe UI", 9))
        self.style.configure("Hover.TButton", background="#404040", foreground="#ffffff")
        self.style.configure("TEntry", fieldbackground="#2d2d2d", foreground="#ffffff", font=("Segoe UI", 9))
        self.style.configure("TCheckbutton", background="#1a1a1a", foreground="#ffffff", font=("Segoe UI", 9))
        self.style.configure("TCombobox", fieldbackground="#2d2d2d", foreground="#ffffff", font=("Segoe UI", 9))
        
        # Configure notebook tabs
        self.style.configure("TNotebook", background="#1a1a1a", tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#ffffff", padding=[20, 10])
        self.style.map("TNotebook.Tab", background=[("selected", "#404040"), ("active", "#353535")])
        
    def setup_variables(self):
        """Initialize all tkinter variables"""
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
        
    def create_widgets(self):
        """Create and layout all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(self.main_frame, text="Password Analyzer & Wordlist Generator",
                             font=("Segoe UI", 16, "bold"), bg="#1a1a1a", fg="#ffffff")
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Password Analysis Tab
        self.create_password_analysis_tab()
        
        # Wordlist Generator Tab
        self.create_wordlist_generator_tab()

        # Output area
        self.create_output_area()
        
    def create_password_analysis_tab(self):
        """Create the password analysis tab"""
        self.analysis_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.analysis_frame, text="Password Analysis")
        
        # Password input section
        pwd_section = ttk.LabelFrame(self.analysis_frame, text="Password Input", padding="10")
        pwd_section.pack(fill="x", pady=(0, 10))
        
        # Password entry with show/hide toggle
        pwd_frame = ttk.Frame(pwd_section)
        pwd_frame.pack(fill="x")
        
        ttk.Label(pwd_frame, text="Password:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        entry_frame = ttk.Frame(pwd_frame)
        entry_frame.pack(fill="x", pady=(5, 0))
        
        self.pwd_entry = ttk.Entry(entry_frame, textvariable=self.pwd_var, show="*", font=("Segoe UI", 10))
        self.pwd_entry.pack(side="left", fill="x", expand=True)
        
        self.show_pwd_btn = ttk.Checkbutton(entry_frame, text="Show", variable=self.show_pwd_var,
                                          command=self.toggle_password_visibility)
        self.show_pwd_btn.pack(side="right", padx=(10, 0))
        
        # Password strength indicator
        self.strength_indicator = PasswordStrengthIndicator(pwd_section)
        
        # Personal information section
        info_section = ttk.LabelFrame(self.analysis_frame, text="Personal Information (for better analysis)", padding="10")
        info_section.pack(fill="x", pady=(0, 10))
        
        # Create input fields with tooltips
        self.create_input_field(info_section, "Names:", self.name_var, 
                              "Enter names separated by commas (e.g., John, Jane, Smith)")
        self.create_input_field(info_section, "Pets:", self.pet_var,
                              "Enter pet names separated by commas (e.g., Fluffy, Rex)")
        self.create_input_field(info_section, "Favorites:", self.fav_var,
                              "Enter favorite things separated by commas (e.g., pizza, music)")
        self.create_input_field(info_section, "DOB/Dates:", self.dob_var,
                              "Enter dates separated by commas (e.g., 1990, 20010101)")
        
        # Analyze button
        self.analyze_btn = ModernButton(self.analysis_frame, text="Analyze Password",
                                      command=self.analyze_password, style="TButton")
        self.analyze_btn.pack(pady=15)
        
    def create_wordlist_generator_tab(self):
        """Create the wordlist generator tab"""
        self.generator_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.generator_frame, text="Wordlist Generator")
        
        # Input section
        input_section = ttk.LabelFrame(self.generator_frame, text="Input Data", padding="10")
        input_section.pack(fill="x", pady=(0, 10))
        
        # Create input fields
        self.create_input_field(input_section, "Names:", self.name_var,
                              "Enter names separated by commas")
        self.create_input_field(input_section, "Pets:", self.pet_var,
                              "Enter pet names separated by commas")
        self.create_input_field(input_section, "Favorites:", self.fav_var,
                              "Enter favorite things separated by commas")
        self.create_input_field(input_section, "DOB/Dates:", self.dob_var,
                              "Enter dates separated by commas")
        self.create_input_field(input_section, "Years:", self.years_var,
                              "Enter years or year range (e.g., 1990 2025 or 2018,2019)")
        
        # File import section
        import_section = ttk.LabelFrame(self.generator_frame, text="Import Additional Words", padding="10")
        import_section.pack(fill="x", pady=(0, 10))
        
        import_btn = ModernButton(import_section, text="Import from File",
                                command=self.import_wordlist)
        import_btn.pack(anchor="w")
        
        # Options section
        options_section = ttk.LabelFrame(self.generator_frame, text="Generation Options", padding="10")
        options_section.pack(fill="x", pady=(0, 10))
        
        # Checkboxes
        cb_frame1 = ttk.Frame(options_section)
        cb_frame1.pack(fill="x", pady=(0, 10))
        
        ttk.Checkbutton(cb_frame1, text="Add reversed variants", variable=self.rev_var).pack(side="left")
        ttk.Checkbutton(cb_frame1, text="Add repeats (word+word)", variable=self.repeat_var).pack(side="left", padx=(20, 0))
        
        cb_frame2 = ttk.Frame(options_section)
        cb_frame2.pack(fill="x", pady=(0, 10))
        
        ttk.Checkbutton(cb_frame2, text="Compress output (.gz)", variable=self.gzip_var).pack(side="left")
        
        # Max words setting
        max_frame = ttk.Frame(options_section)
        max_frame.pack(fill="x")
        
        ttk.Label(max_frame, text="Max words:").pack(side="left")
        self.maxwords_entry = ttk.Entry(max_frame, textvariable=self.maxwords_var, width=10)
        self.maxwords_entry.pack(side="left", padx=(10, 0))
        
        # Generate button
        self.generate_btn = ModernButton(self.generator_frame, text="Generate Wordlist",
                                       command=self.generate_wordlist, style="TButton")
        self.generate_btn.pack(pady=15)
        
    def create_input_field(self, parent, label_text, var, tooltip_text):
        """Create a labeled input field with tooltip"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=3)
        
        label = ttk.Label(frame, text=label_text, font=("Segoe UI", 9))
        label.pack(anchor="w")
        
        entry = ttk.Entry(frame, textvariable=var, font=("Segoe UI", 9))
        entry.pack(fill="x", pady=(2, 0))
        
        # Add tooltip
        ToolTip(entry, tooltip_text)
        
        return entry
        
    def create_output_area(self):
        """Create the output text area"""
        output_frame = ttk.LabelFrame(self.main_frame, text="Output", padding="10")
        output_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(output_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.output_text = tk.Text(text_frame, height=10, width=80, font=("Consolas", 9),
                                  bg="#0d1117", fg="#ffffff", insertbackground="#ffffff",
                                  selectbackground="#264f78", wrap="word")
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        self.output_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Clear button
        clear_btn = ModernButton(output_frame, text="Clear Output", command=self.clear_output)
        clear_btn.pack(anchor="e", pady=(10, 0))
        
    def setup_validation(self):
        """Setup input validation and button state management"""
        # Bind validation events
        self.pwd_var.trace('w', self.validate_inputs)
        self.name_var.trace('w', self.validate_inputs)
        self.pet_var.trace('w', self.validate_inputs)
        self.fav_var.trace('w', self.validate_inputs)
        self.dob_var.trace('w', self.validate_inputs)
        
        # Initial validation
        self.validate_inputs()
        
    def validate_inputs(self, *args):
        """Validate inputs and enable/disable buttons accordingly"""
        # Check if password analysis is possible
        has_password = bool(self.pwd_var.get().strip())
        self.analyze_btn.config(state="normal" if has_password else "disabled")
        
        # Check if wordlist generation is possible
        has_inputs = any([
            self.name_var.get().strip(),
            self.pet_var.get().strip(),
            self.fav_var.get().strip(),
            self.dob_var.get().strip()
        ])
        self.generate_btn.config(state="normal" if has_inputs else "disabled")
        
        # Update password strength in real-time
        if has_password:
            self.update_password_strength()
            
    def update_password_strength(self):
        """Update password strength indicator in real-time"""
        password = self.pwd_var.get().strip()
        if password:
            user_inputs = self.collect_user_inputs()
            try:
                analysis = analyze_password(password, user_inputs=user_inputs)
                score = analysis.get('score', 0)
                self.strength_indicator.update_strength(score)
            except Exception:
                self.strength_indicator.update_strength(0)
        else:
            self.strength_indicator.update_strength(0)
            
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_pwd_var.get():
            self.pwd_entry.configure(show="")
        else:
            self.pwd_entry.configure(show="*")
            
    def collect_user_inputs(self):
        """Collect all user inputs for analysis"""
        inputs = []
        for var in [self.name_var, self.pet_var, self.fav_var, self.dob_var]:
            value = var.get().strip()
            if value:
                inputs.extend([x.strip() for x in value.replace(",", " ").split() if x.strip()])
        return inputs
        
    def analyze_password(self):
        """Analyze password strength"""
        password = self.pwd_var.get().strip()
        if not password:
            messagebox.showwarning("Input Required", "Please enter a password to analyze.")
            return
            
        user_inputs = self.collect_user_inputs()
        
        try:
            analysis = analyze_password(password, user_inputs=user_inputs)
            self.display_analysis_results(analysis, password)
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error analyzing password: {str(e)}")
            
    def display_analysis_results(self, analysis, password):
        """Display password analysis results"""
        self.clear_output()
        self.print_output("=" * 60)
        self.print_output(f"PASSWORD ANALYSIS RESULTS")
        self.print_output("=" * 60)
        self.print_output(f"Password: {'*' * len(password)}")
        self.print_output(f"Score: {analysis.get('score', 'N/A')}/4")
        self.print_output("")
        
        # Crack times
        self.print_output("CRACK TIME ESTIMATES:")
        crack_times = analysis.get("crack_times_display", {})
        for attack_type, time in crack_times.items():
            self.print_output(f"  {attack_type}: {time}")
        self.print_output("")
        
        # Feedback
        feedback = analysis.get("feedback", {})
        if feedback.get("warning"):
            self.print_output(f"WARNING: {feedback['warning']}")
            self.print_output("")
            
        suggestions = feedback.get("suggestions", [])
        if suggestions:
            self.print_output("SUGGESTIONS:")
            for suggestion in suggestions:
                self.print_output(f"  • {suggestion}")
        self.print_output("=" * 60)
        
    def generate_wordlist(self):
        """Generate wordlist in a separate thread"""
        inputs = self.collect_user_inputs()
        if not inputs:
            messagebox.showwarning("Input Required", 
                                 "Please provide at least one name, pet, favorite, or date to generate a wordlist.")
            return
            
        # Parse years
        years_text = self.years_var.get().strip()
        years = []
        if years_text:
            try:
                tokens = years_text.replace(",", " ").split()
                if len(tokens) == 2:
                    years = expand_years(tokens)
                else:
                    years = [int(t) for t in tokens]
            except Exception:
                years = []
                
        # Parse max words
        try:
            max_words = int(self.maxwords_var.get().strip())
        except ValueError:
            max_words = 20000
            
        # Show progress dialog
        progress = ProgressDialog(self.root, "Generating Wordlist", "Generating wordlist... Please wait.")
        
        def worker():
            try:
                words = generate_from_parts(
                    inputs, 
                    years=years, 
                    max_words=max_words,
                    add_reversed=self.rev_var.get(),
                    add_repeats=self.repeat_var.get()
                )
                
                if progress.cancelled:
                    return
                    
                # Ask for save location
                file_types = [("Text files", "*.txt"), ("Gzip files", "*.gz")]
                default_name = "wordlist.txt"
                if self.gzip_var.get():
                    default_name = "wordlist.gz"
                    
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".txt" if not self.gzip_var.get() else ".gz",
                    filetypes=file_types,
                    initialfile=default_name
                )
                
                if file_path and not progress.cancelled:
                    # Ensure correct extension
                    if self.gzip_var.get() and not file_path.endswith(".gz"):
                        file_path += ".gz"
                        
                    save_wordlist(words, outpath=file_path, gzip_out=self.gzip_var.get())
                    
                    self.root.after(0, lambda: self.print_output(f"✓ Generated {len(words)} words"))
                    self.root.after(0, lambda: self.print_output(f"✓ Saved to: {file_path}"))
                    self.root.after(0, lambda: self.print_output("=" * 60))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Generation Error", f"Error generating wordlist: {str(e)}"))
            finally:
                self.root.after(0, progress.destroy)

        threading.Thread(target=worker, daemon=True).start()

    def import_wordlist(self):
        """Import additional words from a file"""
        file_path = filedialog.askopenfilename(
            title="Select wordlist file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    words = [line.strip() for line in f if line.strip()]
                    
                # Add words to the names field
                current_names = self.name_var.get().strip()
                if current_names:
                    new_words = ", ".join(words[:50])  # Limit to first 50 words
                    self.name_var.set(current_names + ", " + new_words)
                else:
                    self.name_var.set(", ".join(words[:50]))
                    
                self.print_output(f"✓ Imported {len(words)} words from {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Import Error", f"Error importing file: {str(e)}")
                
    def print_output(self, text):
        """Print text to output area"""
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)

    def clear_output(self):
        """Clear the output area"""
        self.output_text.delete(1.0, tk.END)
        
    def save_settings(self):
        """Save current settings to file"""
        settings = {
            "name": self.name_var.get(),
            "pet": self.pet_var.get(),
            "favorite": self.fav_var.get(),
            "dob": self.dob_var.get(),
            "years": self.years_var.get(),
            "maxwords": self.maxwords_var.get(),
            "gzip": self.gzip_var.get(),
            "reversed": self.rev_var.get(),
            "repeats": self.repeat_var.get(),
            "show_password": self.show_pwd_var.get()
        }
        
        try:
            with open("gui_settings.json", "w") as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass  # Silently fail if can't save settings
            
    def load_settings(self):
        """Load settings from file"""
        try:
            with open("gui_settings.json", "r") as f:
                settings = json.load(f)
                
            self.name_var.set(settings.get("name", ""))
            self.pet_var.set(settings.get("pet", ""))
            self.fav_var.set(settings.get("favorite", ""))
            self.dob_var.set(settings.get("dob", ""))
            self.years_var.set(settings.get("years", ""))
            self.maxwords_var.set(settings.get("maxwords", "20000"))
            self.gzip_var.set(settings.get("gzip", False))
            self.rev_var.set(settings.get("reversed", False))
            self.repeat_var.set(settings.get("repeats", False))
            self.show_pwd_var.set(settings.get("show_password", False))
            
        except Exception:
            pass  # Silently fail if can't load settings
            
    def on_closing(self):
        """Handle window closing"""
        self.save_settings()
        self.root.destroy()


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = PasswordAnalyzerGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()