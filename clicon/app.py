import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys, os
from clicon.converter import convert_media, detect_media_type, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, IMAGE_EXTENSIONS
import threading

# ----------------------------
# Automatic Desktop Shortcut
# ----------------------------
try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    winshell = None

def create_shortcut():
    if not winshell:
        return
    exe_path = sys.executable
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, "Clicon.lnk")
    if not os.path.exists(shortcut_path):
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()

# ----------------------------
# Automatic Context Menu
# ----------------------------
import winreg

def register_context_menu():
    exe_path = sys.executable
    key_path = r"*\\shell\\ConvertWithClicon"
    try:
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
        winreg.SetValue(key, '', winreg.REG_SZ, "Convert To")
        cmd_key = winreg.CreateKey(key, "command")
        winreg.SetValue(cmd_key, '', winreg.REG_SZ, f'"{exe_path}" "%1"')
    except PermissionError:
        print("Admin rights required to register context menu!")

# ----------------------------
# Tkinter GUI with progress
# ----------------------------
def gui_convert(input_file):
    media_type = detect_media_type(input_file)
    file_name = os.path.basename(input_file)
    _, ext = os.path.splitext(input_file)
    ext = ext.lstrip(".").lower()

    if media_type == "audio":
        choices = AUDIO_EXTENSIONS
    elif media_type == "video":
        choices = VIDEO_EXTENSIONS
    else:
        choices = IMAGE_EXTENSIONS

    root = tk.Tk()
    root.title("Clicon")
    root.geometry("600x300")

    # Set icon
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    icon_path = os.path.join(base_path, "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    # Top frame: Info
    top_frame = tk.Frame(root, pady=10)
    top_frame.pack(fill="x")
    tk.Label(top_frame, text=f"Detected: {media_type.upper()}", anchor="w").pack(fill="x", padx=10)
    tk.Label(top_frame, text=f"Path: {input_file}", anchor="w").pack(fill="x", padx=10)
    tk.Label(top_frame, text=f"Current Format: {ext}", anchor="w").pack(fill="x", padx=10)

    # Bottom frame: Conversion
    bottom_frame = tk.Frame(root, pady=20)
    bottom_frame.pack(fill="x")
    tk.Label(bottom_frame, text="Convert to:", anchor="w").pack(fill="x", padx=10)
    combo = ttk.Combobox(bottom_frame, values=choices, state="readonly")
    combo.set(choices[0])
    combo.pack(fill="x", padx=10, pady=5)

    # Progress bar
    progress_label = tk.Label(bottom_frame, text="")
    progress_label.pack(fill="x", padx=10)
    progress_bar = ttk.Progressbar(bottom_frame, mode="indeterminate")
    progress_bar.pack(fill="x", padx=10, pady=5)

    def run_conversion():
        # Start progress
        progress_bar.start(10)
        def progress_callback(line):
            # Optional: parse FFmpeg output for more info
            progress_label.config(text=line[:80])  # truncate long lines
        try:
            output_file, thread = convert_media(input_file, combo.get(), progress_callback=progress_callback)
            thread.join()  # wait until done
            progress_bar.stop()
            messagebox.showinfo("Success", f"Saved as: {output_file}")
            root.destroy()
        except Exception as e:
            progress_bar.stop()
            messagebox.showerror("Error", str(e))

    tk.Button(bottom_frame, text="Convert", command=lambda: threading.Thread(target=run_conversion, daemon=True).start()).pack(pady=10)

    root.mainloop()

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    create_shortcut()
    register_context_menu()

    if len(sys.argv) > 1:
        gui_convert(sys.argv[1])
    else:
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select media file")
        if file_path:
            gui_convert(file_path)
        else:
            print("No file selected")