# system_monitor_gui.py - Dark theme GUI for system monitoring
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import socket
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import your existing modules
from enhanced_server import EnhancedSystemInfoServer
from enhanced_client import EnhancedClient
from enhanced_client_continuous import EnhancedContinuousClient


# ============================================================
# DARK THEME COLOR PALETTE
# ============================================================
class DarkColors:
    BG_DARKEST   = "#0d0d0d"   # window background
    BG_DARK      = "#1a1a1a"   # frames
    BG_MEDIUM    = "#242424"   # inputs, listbox
    BG_LIGHT     = "#2e2e2e"   # hover states
    BG_HIGHLIGHT = "#3a3a3a"   # selected
    FG_PRIMARY   = "#e8e8e8"   # main text
    FG_SECONDARY = "#a0a0a0"   # muted text
    FG_DIM       = "#707070"   # very muted
    ACCENT       = "#00d9ff"   # cyan accent
    ACCENT_HOVER = "#00b8d9"
    SUCCESS      = "#00ff88"   # green
    ERROR        = "#ff4757"   # red
    WARNING      = "#ffa502"   # orange
    BORDER       = "#333333"
    SELECT_BG    = "#005f7f"


class SystemMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor - Network Information")
        self.root.geometry("1200x800")
        self.root.configure(bg=DarkColors.BG_DARKEST)
        
        # Variables
        self.server = None
        self.server_running = False
        self.monitoring = False
        self.monitor_thread = None
        self.continuous_client = None
        
        # Apply dark theme
        self.setup_styles()
        
        # Create GUI
        self.create_menu()
        self.create_main_layout()
        
        # Status bar
        self.status_bar = tk.Label(
            root, text="Ready", relief=tk.FLAT, anchor=tk.W,
            bg=DarkColors.BG_DARK, fg=DarkColors.FG_SECONDARY,
            padx=10, pady=4, font=('Segoe UI', 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load saved servers
        self.load_server_list()
    
    def setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        
        # Use 'clam' as base - it's the most themeable
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        
        # --- Notebook (tabs) ---
        style.configure('TNotebook',
                        background=DarkColors.BG_DARKEST,
                        borderwidth=0,
                        tabmargins=[2, 5, 2, 0])
        style.configure('TNotebook.Tab',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.FG_SECONDARY,
                        padding=[16, 8],
                        font=('Segoe UI', 10),
                        borderwidth=0)
        style.map('TNotebook.Tab',
                  background=[('selected', DarkColors.BG_MEDIUM),
                              ('active', DarkColors.BG_LIGHT)],
                  foreground=[('selected', DarkColors.ACCENT),
                              ('active', DarkColors.FG_PRIMARY)])
        
        # --- Frames ---
        style.configure('TFrame', background=DarkColors.BG_DARK)
        style.configure('Card.TFrame', background=DarkColors.BG_DARK)
        style.configure('Dark.TFrame', background=DarkColors.BG_DARKEST)
        
        # --- LabelFrame ---
        style.configure('TLabelframe',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.ACCENT,
                        bordercolor=DarkColors.BORDER,
                        lightcolor=DarkColors.BORDER,
                        darkcolor=DarkColors.BORDER,
                        borderwidth=1,
                        relief='solid')
        style.configure('TLabelframe.Label',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.ACCENT,
                        font=('Segoe UI', 10, 'bold'))
        
        # --- Labels ---
        style.configure('TLabel',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.FG_PRIMARY,
                        font=('Segoe UI', 9))
        style.configure('Dark.TLabel',
                        background=DarkColors.BG_DARKEST,
                        foreground=DarkColors.FG_PRIMARY)
        style.configure('Header.TLabel',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.ACCENT,
                        font=('Segoe UI', 12, 'bold'))
        style.configure('Muted.TLabel',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.FG_SECONDARY,
                        font=('Segoe UI', 9))
        style.configure('Success.TLabel',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.SUCCESS,
                        font=('Segoe UI', 10, 'bold'))
        style.configure('Error.TLabel',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.ERROR,
                        font=('Segoe UI', 10, 'bold'))
        style.configure('Warning.TLabel',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.WARNING)
        
        # --- Buttons ---
        style.configure('TButton',
                        background=DarkColors.BG_MEDIUM,
                        foreground=DarkColors.FG_PRIMARY,
                        bordercolor=DarkColors.BORDER,
                        focuscolor=DarkColors.ACCENT,
                        font=('Segoe UI', 9),
                        padding=[12, 6],
                        relief='flat',
                        borderwidth=1)
        style.map('TButton',
                  background=[('active', DarkColors.BG_LIGHT),
                              ('pressed', DarkColors.BG_HIGHLIGHT),
                              ('disabled', DarkColors.BG_DARK)],
                  foreground=[('active', DarkColors.ACCENT),
                              ('pressed', DarkColors.ACCENT),
                              ('disabled', DarkColors.FG_DIM)],
                  bordercolor=[('active', DarkColors.ACCENT)])
        
        # Accent button (primary action)
        style.configure('Accent.TButton',
                        background=DarkColors.ACCENT,
                        foreground=DarkColors.BG_DARKEST,
                        font=('Segoe UI', 9, 'bold'),
                        padding=[12, 6],
                        relief='flat',
                        borderwidth=0)
        style.map('Accent.TButton',
                  background=[('active', DarkColors.ACCENT_HOVER),
                              ('pressed', DarkColors.ACCENT_HOVER),
                              ('disabled', DarkColors.BG_MEDIUM)],
                  foreground=[('disabled', DarkColors.FG_DIM)])
        
        # Danger button
        style.configure('Danger.TButton',
                        background=DarkColors.ERROR,
                        foreground="#ffffff",
                        font=('Segoe UI', 9, 'bold'),
                        padding=[12, 6],
                        relief='flat',
                        borderwidth=0)
        style.map('Danger.TButton',
                  background=[('active', '#ff6b7a'),
                              ('pressed', '#d63447'),
                              ('disabled', DarkColors.BG_MEDIUM)],
                  foreground=[('disabled', DarkColors.FG_DIM)])
        
        # --- Entry ---
        style.configure('TEntry',
                        fieldbackground=DarkColors.BG_MEDIUM,
                        foreground=DarkColors.FG_PRIMARY,
                        insertcolor=DarkColors.ACCENT,
                        bordercolor=DarkColors.BORDER,
                        lightcolor=DarkColors.BORDER,
                        darkcolor=DarkColors.BORDER,
                        padding=6,
                        relief='flat')
        style.map('TEntry',
                  fieldbackground=[('focus', DarkColors.BG_LIGHT)],
                  bordercolor=[('focus', DarkColors.ACCENT)])
        
        # --- Checkbutton / Radiobutton ---
        style.configure('TCheckbutton',
                        background=DarkColors.BG_DARK,
                        foreground=DarkColors.FG_PRIMARY,
                        focuscolor=DarkColors.ACCENT)
        style.map('TCheckbutton',
                  background=[('active', DarkColors.BG_DARK)],
                  foreground=[('active', DarkColors.ACCENT)])
        
        # --- Progressbar ---
        style.configure('TProgressbar',
                        background=DarkColors.ACCENT,
                        troughcolor=DarkColors.BG_MEDIUM,
                        bordercolor=DarkColors.BG_MEDIUM,
                        lightcolor=DarkColors.ACCENT,
                        darkcolor=DarkColors.ACCENT,
                        thickness=8)
        
        # --- Scrollbar ---
        style.configure('Vertical.TScrollbar',
                        background=DarkColors.BG_MEDIUM,
                        troughcolor=DarkColors.BG_DARK,
                        bordercolor=DarkColors.BG_DARK,
                        arrowcolor=DarkColors.FG_SECONDARY,
                        relief='flat')
        style.map('Vertical.TScrollbar',
                  background=[('active', DarkColors.ACCENT),
                              ('pressed', DarkColors.ACCENT_HOVER)])
        style.configure('Horizontal.TScrollbar',
                        background=DarkColors.BG_MEDIUM,
                        troughcolor=DarkColors.BG_DARK,
                        bordercolor=DarkColors.BG_DARK,
                        arrowcolor=DarkColors.FG_SECONDARY,
                        relief='flat')
        
        # --- Combobox ---
        style.configure('TCombobox',
                        fieldbackground=DarkColors.BG_MEDIUM,
                        background=DarkColors.BG_MEDIUM,
                        foreground=DarkColors.FG_PRIMARY,
                        arrowcolor=DarkColors.ACCENT,
                        bordercolor=DarkColors.BORDER)
        style.map('TCombobox',
                  fieldbackground=[('readonly', DarkColors.BG_MEDIUM)],
                  foreground=[('readonly', DarkColors.FG_PRIMARY)])
        
        # --- Separator ---
        style.configure('TSeparator',
                        background=DarkColors.BORDER)
    
    def create_menu(self):
        """Create menu bar with dark theme"""
        menubar = tk.Menu(
            self.root,
            bg=DarkColors.BG_DARK,
            fg=DarkColors.FG_PRIMARY,
            activebackground=DarkColors.ACCENT,
            activeforeground=DarkColors.BG_DARKEST,
            tearoff=0,
            borderwidth=0
        )
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0,
                            bg=DarkColors.BG_DARK, fg=DarkColors.FG_PRIMARY,
                            activebackground=DarkColors.ACCENT,
                            activeforeground=DarkColors.BG_DARKEST,
                            borderwidth=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Server List", command=self.load_servers_from_file)
        file_menu.add_command(label="Save Server List", command=self.save_servers_to_file)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0,
                            bg=DarkColors.BG_DARK, fg=DarkColors.FG_PRIMARY,
                            activebackground=DarkColors.ACCENT,
                            activeforeground=DarkColors.BG_DARKEST,
                            borderwidth=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Clear Log", command=self.clear_log)
        view_menu.add_command(label="Clear Results", command=self.clear_results)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0,
                            bg=DarkColors.BG_DARK, fg=DarkColors.FG_PRIMARY,
                            activebackground=DarkColors.ACCENT,
                            activeforeground=DarkColors.BG_DARKEST,
                            borderwidth=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_main_layout(self):
        """Create the main GUI layout"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self.create_server_tab()
        self.create_client_tab()
        self.create_monitor_tab()
        self.create_results_tab()
    
    def _make_log_widget(self, parent, height=15):
        """Helper to create a dark themed ScrolledText"""
        text = scrolledtext.ScrolledText(
            parent,
            height=height,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg=DarkColors.BG_DARKEST,
            fg=DarkColors.FG_PRIMARY,
            insertbackground=DarkColors.ACCENT,
            selectbackground=DarkColors.SELECT_BG,
            selectforeground=DarkColors.FG_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=8
        )
        return text
    
    def create_server_tab(self):
        """Create server control tab"""
        server_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(server_frame, text="🖥️  Server")
        
        # Server controls
        control_frame = ttk.LabelFrame(server_frame, text=" Server Control ", padding=15)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Port selection
        port_frame = ttk.Frame(control_frame)
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value="5000")
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        port_entry.pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.server_status_label = ttk.Label(
            status_frame, text="● Stopped",
            foreground=DarkColors.ERROR,
            background=DarkColors.BG_DARK,
            font=('Segoe UI', 10, 'bold')
        )
        self.server_status_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_server_btn = ttk.Button(
            button_frame, text="▶  Start Server",
            command=self.start_server, style='Accent.TButton'
        )
        self.start_server_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_server_btn = ttk.Button(
            button_frame, text="■  Stop Server",
            command=self.stop_server, state=tk.DISABLED,
            style='Danger.TButton'
        )
        self.stop_server_btn.pack(side=tk.LEFT, padx=5)
        
        # Server log
        log_frame = ttk.LabelFrame(server_frame, text=" Server Log ", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.server_log = self._make_log_widget(log_frame, height=15)
        self.server_log.pack(fill=tk.BOTH, expand=True)
    
    def create_client_tab(self):
        """Create client query tab"""
        client_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(client_frame, text="🔍  Client Query")
        
        # Server list
        list_frame = ttk.LabelFrame(client_frame, text=" Servers ", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons for server list management
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="+ Add Server", command=self.add_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="− Remove Selected", command=self.remove_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✕ Clear All", command=self.clear_servers).pack(side=tk.LEFT, padx=2)
        
        # Server listbox
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.server_listbox = tk.Listbox(
            listbox_frame,
            height=8,
            selectmode=tk.EXTENDED,
            bg=DarkColors.BG_DARKEST,
            fg=DarkColors.FG_PRIMARY,
            selectbackground=DarkColors.SELECT_BG,
            selectforeground=DarkColors.ACCENT,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=DarkColors.BORDER,
            highlightcolor=DarkColors.ACCENT,
            font=('Consolas', 10),
            activestyle='none'
        )
        self.server_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL,
                                 command=self.server_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.server_listbox.config(yscrollcommand=scrollbar.set)
        
        # Query controls
        query_frame = ttk.LabelFrame(client_frame, text=" Query Controls ", padding=10)
        query_frame.pack(fill=tk.X, padx=10, pady=10)
        
        controls_frame = ttk.Frame(query_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(controls_frame, text="Timeout (s):").pack(side=tk.LEFT, padx=5)
        self.timeout_var = tk.StringVar(value="10")
        ttk.Entry(controls_frame, textvariable=self.timeout_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(controls_frame, text="Workers:").pack(side=tk.LEFT, padx=5)
        self.workers_var = tk.StringVar(value="10")
        ttk.Entry(controls_frame, textvariable=self.workers_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Query buttons
        query_btn_frame = ttk.Frame(query_frame)
        query_btn_frame.pack(fill=tk.X, pady=10)
        
        self.query_btn = ttk.Button(
            query_btn_frame, text="🔍  Query Selected",
            command=self.query_selected_servers, style='Accent.TButton'
        )
        self.query_btn.pack(side=tk.LEFT, padx=5)
        
        self.query_all_btn = ttk.Button(
            query_btn_frame, text="⚡  Query All",
            command=self.query_all_servers, style='Accent.TButton'
        )
        self.query_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.query_progress = ttk.Progressbar(query_frame, mode='indeterminate')
        self.query_progress.pack(fill=tk.X, pady=5)
        
        # Quick add server
        quick_frame = ttk.LabelFrame(query_frame, text=" Quick Add Server ", padding=5)
        quick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quick_frame, text="Address:").pack(side=tk.LEFT, padx=5)
        self.quick_add_var = tk.StringVar()
        quick_add_entry = ttk.Entry(quick_frame, textvariable=self.quick_add_var, width=30)
        quick_add_entry.pack(side=tk.LEFT, padx=5)
        quick_add_entry.bind('<Return>', lambda e: self.quick_add_server())
        
        ttk.Button(quick_frame, text="+ Add", command=self.quick_add_server).pack(side=tk.LEFT, padx=5)
    
    def create_monitor_tab(self):
        """Create continuous monitoring tab"""
        monitor_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(monitor_frame, text="📊  Monitor")
        
        controls_frame = ttk.LabelFrame(monitor_frame, text=" Monitoring Controls ", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        settings_frame = ttk.Frame(controls_frame)
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text="Interval (s):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="300")
        ttk.Entry(settings_frame, textvariable=self.interval_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(settings_frame, text="Log Directory:").pack(side=tk.LEFT, padx=5)
        self.log_dir_var = tk.StringVar(value=".")
        ttk.Entry(settings_frame, textvariable=self.log_dir_var, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(settings_frame, text="Browse", command=self.browse_log_dir).pack(side=tk.LEFT, padx=5)
        
        monitor_btn_frame = ttk.Frame(controls_frame)
        monitor_btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_monitor_btn = ttk.Button(
            monitor_btn_frame, text="▶  Start Monitoring",
            command=self.start_monitoring, style='Accent.TButton'
        )
        self.start_monitor_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_monitor_btn = ttk.Button(
            monitor_btn_frame, text="■  Stop Monitoring",
            command=self.stop_monitoring, state=tk.DISABLED,
            style='Danger.TButton'
        )
        self.stop_monitor_btn.pack(side=tk.LEFT, padx=5)
        
        status_frame = ttk.LabelFrame(controls_frame, text=" Status ", padding=5)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.monitor_status_label = ttk.Label(
            status_frame, text="● Not running",
            background=DarkColors.BG_DARK,
            foreground=DarkColors.FG_SECONDARY,
            font=('Segoe UI', 10, 'bold')
        )
        self.monitor_status_label.pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(monitor_frame, text=" Monitor Log ", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.monitor_log = self._make_log_widget(log_frame, height=15)
        self.monitor_log.pack(fill=tk.BOTH, expand=True)
    
    def create_results_tab(self):
        """Create results display tab"""
        results_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(results_frame, text="📋  Results")
        
        self.results_text = self._make_log_widget(results_frame)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(results_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="✕ Clear Results", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Export Results", command=self.export_results).pack(side=tk.LEFT, padx=5)
    
    # ==================== SERVER METHODS ====================
    def start_server(self):
        try:
            port = int(self.port_var.get())
            
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            try:
                test_socket.connect(('localhost', port))
                test_socket.close()
                messagebox.showerror("Port Error", f"Port {port} is already in use")
                return
            except:
                pass
            
            self.server = EnhancedSystemInfoServer(port=port)
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.server_running = True
            self.server_status_label.config(text="● Running", foreground=DarkColors.SUCCESS)
            self.start_server_btn.config(state=tk.DISABLED)
            self.stop_server_btn.config(state=tk.NORMAL)
            
            self.log_server_message(f"✅ Server started on port {port}")
            self.update_status(f"Server running on port {port}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def _run_server(self):
        try:
            self.server.start_server()
        except Exception as e:
            self.log_server_message(f"❌ Server error: {e}")
            self.root.after(0, self.stop_server)
    
    def stop_server(self):
        if self.server:
            self.server.running = False
        
        self.server_running = False
        self.server_status_label.config(text="● Stopped", foreground=DarkColors.ERROR)
        self.start_server_btn.config(state=tk.NORMAL)
        self.stop_server_btn.config(state=tk.DISABLED)
        
        self.log_server_message("🛑 Server stopped")
        self.update_status("Server stopped")
    
    def log_server_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.server_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.server_log.see(tk.END)
    
    # ==================== CLIENT METHODS ====================
    def add_server(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Server")
        dialog.geometry("350x180")
        dialog.configure(bg=DarkColors.BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Server Address:", bg=DarkColors.BG_DARK,
                 fg=DarkColors.FG_PRIMARY, font=('Segoe UI', 10)).pack(pady=15)
        
        addr_var = tk.StringVar()
        addr_entry = tk.Entry(
            dialog, textvariable=addr_var, width=30,
            bg=DarkColors.BG_MEDIUM, fg=DarkColors.FG_PRIMARY,
            insertbackground=DarkColors.ACCENT, relief=tk.FLAT,
            font=('Consolas', 10)
        )
        addr_entry.pack(pady=5, ipady=4)
        addr_entry.focus()
        
        tk.Label(dialog, text="Example: 192.168.1.100:5000 or 192.168.1.100",
                 bg=DarkColors.BG_DARK, fg=DarkColors.FG_DIM,
                 font=('Segoe UI', 8)).pack()
        
        def add_and_close():
            address = addr_var.get().strip()
            if address:
                self.server_listbox.insert(tk.END, address)
                self.save_server_list()
                dialog.destroy()
            else:
                messagebox.showwarning("Error", "Please enter a server address")
        
        ttk.Button(dialog, text="Add", command=add_and_close,
                   style='Accent.TButton').pack(pady=10)
        addr_entry.bind('<Return>', lambda e: add_and_close())
    
    def quick_add_server(self):
        address = self.quick_add_var.get().strip()
        if address:
            if address not in self.server_listbox.get(0, tk.END):
                self.server_listbox.insert(tk.END, address)
                self.save_server_list()
                self.quick_add_var.set("")
                self.update_status(f"Added server: {address}")
            else:
                messagebox.showwarning("Duplicate", "Server already in list")
    
    def remove_server(self):
        selected = self.server_listbox.curselection()
        if selected:
            for index in reversed(selected):
                self.server_listbox.delete(index)
            self.save_server_list()
            self.update_status("Removed selected servers")
        else:
            messagebox.showwarning("No Selection", "Please select a server to remove")
    
    def clear_servers(self):
        if messagebox.askyesno("Clear All", "Remove all servers from list?"):
            self.server_listbox.delete(0, tk.END)
            self.save_server_list()
            self.update_status("Cleared all servers")
    
    def load_servers_from_file(self):
        filename = filedialog.askopenfilename(
            title="Load Server List",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    servers = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                self.server_listbox.delete(0, tk.END)
                for server in servers:
                    self.server_listbox.insert(tk.END, server)
                self.save_server_list()
                self.update_status(f"Loaded {len(servers)} servers from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load servers: {e}")
    
    def save_servers_to_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save Server List",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                servers = list(self.server_listbox.get(0, tk.END))
                with open(filename, 'w') as f:
                    f.write("# Server list\n")
                    f.write(f"# Generated: {datetime.now()}\n")
                    f.write("# Format: IP:PORT or IP\n\n")
                    for server in servers:
                        f.write(f"{server}\n")
                self.update_status(f"Saved {len(servers)} servers to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save servers: {e}")
    
    def load_server_list(self):
        try:
            default_file = "servers.txt"
            if os.path.exists(default_file):
                with open(default_file, 'r') as f:
                    servers = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                for server in servers:
                    self.server_listbox.insert(tk.END, server)
                self.update_status(f"Loaded {len(servers)} servers from {default_file}")
        except:
            pass
    
    def save_server_list(self):
        try:
            servers = list(self.server_listbox.get(0, tk.END))
            with open("servers.txt", 'w') as f:
                f.write("# Server list\n")
                f.write(f"# Generated: {datetime.now()}\n")
                f.write("# Format: IP:PORT or IP\n\n")
                for server in servers:
                    f.write(f"{server}\n")
        except:
            pass
    
    def query_selected_servers(self):
        selected = self.server_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select servers to query")
            return
        servers = [self.server_listbox.get(i) for i in selected]
        self._query_servers(servers)
    
    def query_all_servers(self):
        servers = list(self.server_listbox.get(0, tk.END))
        if not servers:
            messagebox.showwarning("No Servers", "No servers in list")
            return
        self._query_servers(servers)
    
    def _query_servers(self, servers):
        try:
            timeout = int(self.timeout_var.get())
            workers = int(self.workers_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid timeout or workers value")
            return
        
        self.query_btn.config(state=tk.DISABLED)
        self.query_all_btn.config(state=tk.DISABLED)
        self.query_progress.start()
        
        def query_thread():
            try:
                client = EnhancedClient(timeout=timeout, max_workers=workers)
                results = client.query_multiple_parallel(servers)
                self.root.after(0, self._display_query_results, results, servers)
            except Exception as e:
                self.root.after(0, self._query_error, str(e))
        
        thread = threading.Thread(target=query_thread, daemon=True)
        thread.start()
    
    def _display_query_results(self, results, servers):
        self.query_progress.stop()
        self.query_btn.config(state=tk.NORMAL)
        self.query_all_btn.config(state=tk.NORMAL)
        
        self.notebook.select(3)
        self.results_text.delete(1.0, tk.END)
        
        display = []
        display.append("=" * 100)
        display.append(f"📊 SYSTEM INFORMATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        display.append("=" * 100)
        
        success_count = len([r for r in results if r['status'] == 'success'])
        error_count = len([r for r in results if r['status'] == 'error'])
        
        display.append(f"\n📊 Query Results: {success_count} successful, {error_count} failed out of {len(results)} total")
        
        for r in results:
            if r['status'] == 'success':
                info = r['data']
                display.append(f"\n{'='*80}")
                display.append(f"🖥️  SERVER: {r['server']} (Response: {r['response_time']:.2f}s)")
                display.append(f"{'='*80}")
                
                if info.get('status') == 'error':
                    display.append(f"  ❌ Server returned error: {info.get('message', 'Unknown error')}")
                    continue
                
                display.append(f"  Device: {info.get('device_name', 'N/A')}")
                display.append(f"  OS: {info.get('os', 'N/A')} {info.get('os_version', '')}")
                
                local_ips = info.get('local_ips', [])
                if local_ips:
                    display.append(f"  IPs: {', '.join(local_ips)}")
                
                cpu = info.get('cpu', {})
                if cpu:
                    display.append(f"  CPU: {cpu.get('percent', 0):.1f}% ({cpu.get('cores', 0)} cores)")
                
                memory = info.get('memory', {})
                if memory and memory.get('total_gb', 0) > 0:
                    display.append(f"  Memory: {memory.get('used_gb', 0):.2f} / {memory.get('total_gb', 0):.2f} GB ({memory.get('usage_percent', 0):.1f}%)")
                
                storage = info.get('storage', {})
                if storage and storage.get('devices'):
                    display.append(f"\n  💾 Storage:")
                    display.append(f"    Total: {storage.get('total_gb', 0):.2f} GB")
                    display.append(f"    Used:  {storage.get('used_gb', 0):.2f} GB ({storage.get('usage_percent', 0):.1f}%)")
                    display.append(f"    Free:  {storage.get('free_gb', 0):.2f} GB")
                
                auto_run = info.get('auto_run', {})
                if auto_run:
                    display.append(f"\n  🔍 Auto-Run:")
                    display.append(f"    Startup Items: {len(auto_run.get('startup_items', []))}")
                    display.append(f"    Running Services: {len(auto_run.get('running_services', []))}")
                    display.append(f"    Scheduled Tasks: {len(auto_run.get('scheduled_tasks', []))}")
                    display.append(f"    Running Processes: {len(auto_run.get('running_processes', []))}")
            else:
                display.append(f"\n❌ {r['server']}: {r.get('error', 'Unknown error')}")
        
        # Insert with color tags
        self.results_text.insert(tk.END, "\n".join(display))
        
        # Optional: colorize success/error lines
        self.results_text.tag_config('success', foreground=DarkColors.SUCCESS)
        self.results_text.tag_config('error', foreground=DarkColors.ERROR)
        
        self.update_status(f"Query completed: {success_count} successful, {error_count} failed")
    
    def _query_error(self, error):
        self.query_progress.stop()
        self.query_btn.config(state=tk.NORMAL)
        self.query_all_btn.config(state=tk.NORMAL)
        messagebox.showerror("Query Error", f"Failed to query servers: {error}")
    
    # ==================== MONITORING METHODS ====================
    def browse_log_dir(self):
        directory = filedialog.askdirectory(title="Select Log Directory")
        if directory:
            self.log_dir_var.set(directory)
    
    def start_monitoring(self):
        servers = list(self.server_listbox.get(0, tk.END))
        if not servers:
            messagebox.showwarning("No Servers", "No servers in list")
            return
        
        try:
            interval = int(self.interval_var.get())
            if interval < 10:
                messagebox.showwarning("Interval", "Interval should be at least 10 seconds")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid interval value")
            return
        
        self.monitoring = True
        self.start_monitor_btn.config(state=tk.DISABLED)
        self.stop_monitor_btn.config(state=tk.NORMAL)
        self.monitor_status_label.config(text="● Running", foreground=DarkColors.SUCCESS)
        
        self.monitor_thread = threading.Thread(
            target=self._run_monitoring,
            args=(servers, interval),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.log_monitor_message("✅ Monitoring started")
        self.update_status("Monitoring started")
    
    def _run_monitoring(self, servers, interval):
        try:
            client = EnhancedContinuousClient(timeout=10, max_workers=10)
            self.continuous_client = client
            
            iteration = 0
            while self.monitoring:
                iteration += 1
                self.root.after(0, self.log_monitor_message,
                              f"📊 Iteration #{iteration} starting...")
                
                results = []
                formatted_servers = []
                for server in servers:
                    if ':' not in server:
                        formatted_servers.append(f"{server}:5000")
                    else:
                        formatted_servers.append(server)
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(client.query_single_server, s): s
                              for s in formatted_servers}
                    
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        status = '✅' if result['status'] == 'success' else '❌'
                        self.root.after(0, self.log_monitor_message,
                                      f"  {status} {result['server']} ({result.get('response_time', 0):.2f}s)")
                
                log_file = client.save_results(results, self.log_dir_var.get())
                success = len([r for r in results if r['status'] == 'success'])
                errors = len([r for r in results if r['status'] == 'error'])
                
                self.root.after(0, self.log_monitor_message,
                              f"📄 Iteration #{iteration} completed: {success} successful, {errors} failed")
                self.root.after(0, self.log_monitor_message,
                              f"💾 Log saved: {log_file}")
                
                if self.monitoring:
                    self.root.after(0, self.log_monitor_message,
                                  f"⏳ Waiting {interval} seconds...")
                    for _ in range(interval):
                        if not self.monitoring:
                            break
                        time.sleep(1)
                        
        except Exception as e:
            self.root.after(0, self.log_monitor_message,
                          f"❌ Monitoring error: {e}")
            self.root.after(0, self.stop_monitoring)
    
    def stop_monitoring(self):
        self.monitoring = False
        self.monitor_status_label.config(text="● Stopped", foreground=DarkColors.ERROR)
        self.start_monitor_btn.config(state=tk.NORMAL)
        self.stop_monitor_btn.config(state=tk.DISABLED)
        
        if self.continuous_client:
            self.continuous_client.running = False
        
        self.log_monitor_message("🛑 Monitoring stopped")
        self.update_status("Monitoring stopped")
    
    def log_monitor_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.monitor_log.see(tk.END)
    
    # ==================== RESULTS METHODS ====================
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
        self.update_status("Results cleared")
    
    def export_results(self):
        content = self.results_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("No Results", "No results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.update_status(f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {e}")
    
    def clear_log(self):
        current_tab = self.notebook.select()
        if current_tab:
            tab_id = self.notebook.index(current_tab)
            if tab_id == 0:
                self.server_log.delete(1.0, tk.END)
            elif tab_id == 2:
                self.monitor_log.delete(1.0, tk.END)
    
    def update_status(self, message):
        self.status_bar.config(text=message)
    
    # ==================== HELP METHODS ====================
    def show_documentation(self):
        doc_text = """
📚 SYSTEM MONITOR - USER GUIDE

Server Tab:
- Start/Stop the system info server
- The server provides system information to clients
- Port can be changed before starting

Client Query Tab:
- Add servers to monitor (format: IP:PORT or IP)
- Query selected or all servers
- Results appear in the Results tab
- Adjust timeout and workers for performance

Monitor Tab:
- Continuous monitoring with configurable interval
- Results saved to log files automatically
- Monitor progress shown in real-time

Results Tab:
- Detailed system information displayed
- Export results to file
- Clear results for new queries

Tips:
1. Add multiple servers for network-wide monitoring
2. Use continuous monitoring for tracking changes
3. Save server lists for easy reuse
4. Lower timeout = faster (quick mode auto-enabled)
        """
        messagebox.showinfo("Documentation", doc_text)
    
    def show_about(self):
        about_text = """
🔧 System Monitor v1.0

A comprehensive network monitoring tool for Windows systems.

Features:
- Remote system information collection
- Storage and auto-run monitoring
- Continuous monitoring with logging
- Multi-server parallel queries

Created with Python and tkinter
        """
        messagebox.showinfo("About", about_text)


def main():
    root = tk.Tk()
    app = SystemMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()