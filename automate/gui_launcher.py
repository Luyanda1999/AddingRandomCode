# gui_launcher.py - Simple launcher for the GUI
import sys
import os
import subprocess

def main():
    """Launch the GUI application"""
    try:
        # Try to import tkinter
        import tkinter
        # Run the main GUI
        import system_monitor_gui
        system_monitor_gui.main()
    except ImportError as e:
        print("Error: Required modules not found")
        print(f"Details: {e}")
        print("\nMake sure you have:")
        print("  - Python 3.6 or higher")
        print("  - tkinter (usually included with Python)")
        print("\nTo install tkinter on Ubuntu/Debian:")
        print("  sudo apt-get install python3-tk")
        print("\nTo install tkinter on Fedora/RHEL:")
        print("  sudo dnf install python3-tkinter")
        sys.exit(1)

if __name__ == "__main__":
    main()