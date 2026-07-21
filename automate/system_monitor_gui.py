# system_monitor_gui.py - Full GUI for system monitoring
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

# Import your existing modules
from enhanced_server import EnhancedSystemInfoServer
from enhanced_client import EnhancedClient
from enhanced_client_continuous import EnhancedContinuousClient

class SystemMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor - Network Information")
        self.root.geometry("1200x800")
        
        # Variables
        self.server = None
        self.server_running = False
        self.monitoring = False
        self.monitor_thread = None
        self.continuous_client = None
        
        # Style
        self.setup_styles()
        
        # Create GUI
        self.create_menu()
        self.create_main_layout()
        
        # Status bar
        self.status_bar = ttk.Label(root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load saved servers if any
        self.load_server_list()
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Status.TLabelframe', font=('Arial', 10, 'bold'))
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Server List", command=self.load_servers_from_file)
        file_menu.add_command(label="Save Server List", command=self.save_servers_to_file)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Clear Log", command=self.clear_log)
        view_menu.add_command(label="Clear Results", command=self.clear_results)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_main_layout(self):
        """Create the main GUI layout"""
        # Main container with notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_server_tab()
        self.create_client_tab()
        self.create_monitor_tab()
        self.create_results_tab()
        
    def create_server_tab(self):
        """Create server control tab"""
        server_frame = ttk.Frame(self.notebook)
        self.notebook.add(server_frame, text="🖥️ Server")
        
        # Server controls
        control_frame = ttk.LabelFrame(server_frame, text="Server Control", padding=10)
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
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.server_status_label = ttk.Label(status_frame, text="Stopped", 
                                            foreground="red", font=('Arial', 10, 'bold'))
        self.server_status_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_server_btn = ttk.Button(button_frame, text="Start Server", 
                                          command=self.start_server)
        self.start_server_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_server_btn = ttk.Button(button_frame, text="Stop Server", 
                                         command=self.stop_server, state=tk.DISABLED)
        self.stop_server_btn.pack(side=tk.LEFT, padx=5)
        
        # Server log
        log_frame = ttk.LabelFrame(server_frame, text="Server Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.server_log = scrolledtext.ScrolledText(log_frame, height=15, 
                                                    wrap=tk.WORD, font=('Courier', 9))
        self.server_log.pack(fill=tk.BOTH, expand=True)
        
    def create_client_tab(self):
        """Create client query tab"""
        client_frame = ttk.Frame(self.notebook)
        self.notebook.add(client_frame, text="🔍 Client Query")
        
        # Server list
        list_frame = ttk.LabelFrame(client_frame, text="Servers", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons for server list management
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add Server", command=self.add_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_servers).pack(side=tk.LEFT, padx=2)
        
        # Server listbox
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.server_listbox = tk.Listbox(listbox_frame, height=8, selectmode=tk.EXTENDED)
        self.server_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, 
                                 command=self.server_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.server_listbox.config(yscrollcommand=scrollbar.set)
        
        # Query controls
        query_frame = ttk.LabelFrame(client_frame, text="Query Controls", padding=10)
        query_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Timeout and workers
        controls_frame = ttk.Frame(query_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(controls_frame, text="Timeout (s):").pack(side=tk.LEFT, padx=5)
        self.timeout_var = tk.StringVar(value="30")
        ttk.Entry(controls_frame, textvariable=self.timeout_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(controls_frame, text="Workers:").pack(side=tk.LEFT, padx=5)
        self.workers_var = tk.StringVar(value="5")
        ttk.Entry(controls_frame, textvariable=self.workers_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Query buttons
        query_btn_frame = ttk.Frame(query_frame)
        query_btn_frame.pack(fill=tk.X, pady=5)
        
        self.query_btn = ttk.Button(query_btn_frame, text="Query Selected", 
                                   command=self.query_selected_servers)
        self.query_btn.pack(side=tk.LEFT, padx=5)
        
        self.query_all_btn = ttk.Button(query_btn_frame, text="Query All", 
                                       command=self.query_all_servers)
        self.query_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.query_progress = ttk.Progressbar(query_frame, mode='indeterminate')
        self.query_progress.pack(fill=tk.X, pady=5)
        
        # Quick add server
        quick_frame = ttk.LabelFrame(query_frame, text="Quick Add Server", padding=5)
        quick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quick_frame, text="Address:").pack(side=tk.LEFT, padx=5)
        self.quick_add_var = tk.StringVar()
        quick_add_entry = ttk.Entry(quick_frame, textvariable=self.quick_add_var, width=30)
        quick_add_entry.pack(side=tk.LEFT, padx=5)
        quick_add_entry.bind('<Return>', lambda e: self.quick_add_server())
        
        ttk.Button(quick_frame, text="Add", command=self.quick_add_server).pack(side=tk.LEFT, padx=5)
        
    def create_monitor_tab(self):
        """Create continuous monitoring tab"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📊 Monitor")
        
        # Monitor controls
        controls_frame = ttk.LabelFrame(monitor_frame, text="Monitoring Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Interval and log settings
        settings_frame = ttk.Frame(controls_frame)
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text="Interval (s):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="300")
        ttk.Entry(settings_frame, textvariable=self.interval_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(settings_frame, text="Log Directory:").pack(side=tk.LEFT, padx=5)
        self.log_dir_var = tk.StringVar(value=".")
        ttk.Entry(settings_frame, textvariable=self.log_dir_var, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(settings_frame, text="Browse", command=self.browse_log_dir).pack(side=tk.LEFT, padx=5)
        
        # Monitor buttons
        monitor_btn_frame = ttk.Frame(controls_frame)
        monitor_btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_monitor_btn = ttk.Button(monitor_btn_frame, text="Start Monitoring", 
                                           command=self.start_monitoring)
        self.start_monitor_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_monitor_btn = ttk.Button(monitor_btn_frame, text="Stop Monitoring", 
                                          command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_monitor_btn.pack(side=tk.LEFT, padx=5)
        
        # Monitor status
        status_frame = ttk.LabelFrame(controls_frame, text="Status", padding=5)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.monitor_status_label = ttk.Label(status_frame, text="Not running", 
                                             font=('Arial', 10, 'bold'))
        self.monitor_status_label.pack(side=tk.LEFT, padx=5)
        
        # Monitor log
        log_frame = ttk.LabelFrame(monitor_frame, text="Monitor Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.monitor_log = scrolledtext.ScrolledText(log_frame, height=15, 
                                                    wrap=tk.WORD, font=('Courier', 9))
        self.monitor_log.pack(fill=tk.BOTH, expand=True)
        
    def create_results_tab(self):
        """Create results display tab"""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="📋 Results")
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(results_frame, 
                                                      wrap=tk.WORD, font=('Courier', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results buttons
        btn_frame = ttk.Frame(results_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Clear Results", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self.export_results).pack(side=tk.LEFT, padx=5)
        
    # Server methods
    def start_server(self):
        """Start the server"""
        try:
            port = int(self.port_var.get())
            
            # Check if port is available
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            try:
                test_socket.connect(('localhost', port))
                test_socket.close()
                messagebox.showerror("Port Error", f"Port {port} is already in use")
                return
            except:
                pass
            
            # Start server in separate thread
            self.server = EnhancedSystemInfoServer(port=port)
            
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.server_running = True
            self.server_status_label.config(text="Running", foreground="green")
            self.start_server_btn.config(state=tk.DISABLED)
            self.stop_server_btn.config(state=tk.NORMAL)
            
            self.log_server_message(f"✅ Server started on port {port}")
            self.update_status(f"Server running on port {port}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            
    def _run_server(self):
        """Run the server in a thread"""
        try:
            self.server.start_server()
        except Exception as e:
            self.log_server_message(f"❌ Server error: {e}")
            self.root.after(0, self.stop_server)
            
    def stop_server(self):
        """Stop the server"""
        if self.server:
            self.server.running = False
            
        self.server_running = False
        self.server_status_label.config(text="Stopped", foreground="red")
        self.start_server_btn.config(state=tk.NORMAL)
        self.stop_server_btn.config(state=tk.DISABLED)
        
        self.log_server_message("🛑 Server stopped")
        self.update_status("Server stopped")
        
    def log_server_message(self, message):
        """Add message to server log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.server_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.server_log.see(tk.END)
        
    # Client methods
    def add_server(self):
        """Add a server to the list"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Server")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Server Address:").pack(pady=10)
        addr_var = tk.StringVar()
        addr_entry = ttk.Entry(dialog, textvariable=addr_var, width=30)
        addr_entry.pack(pady=5)
        addr_entry.focus()
        
        # Example label
        ttk.Label(dialog, text="Example: 192.168.1.100:5000 or 192.168.1.100", 
                 font=('Arial', 8), foreground='gray').pack()
        
        def add_and_close():
            address = addr_var.get().strip()
            if address:
                self.server_listbox.insert(tk.END, address)
                self.save_server_list()
                dialog.destroy()
            else:
                messagebox.showwarning("Error", "Please enter a server address")
                
        ttk.Button(dialog, text="Add", command=add_and_close).pack(pady=10)
        addr_entry.bind('<Return>', lambda e: add_and_close())
        
    def quick_add_server(self):
        """Quick add a server from the entry field"""
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
        """Remove selected servers"""
        selected = self.server_listbox.curselection()
        if selected:
            for index in reversed(selected):
                self.server_listbox.delete(index)
            self.save_server_list()
            self.update_status("Removed selected servers")
        else:
            messagebox.showwarning("No Selection", "Please select a server to remove")
            
    def clear_servers(self):
        """Clear all servers"""
        if messagebox.askyesno("Clear All", "Remove all servers from list?"):
            self.server_listbox.delete(0, tk.END)
            self.save_server_list()
            self.update_status("Cleared all servers")
            
    def load_servers_from_file(self):
        """Load server list from file"""
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
        """Save server list to file"""
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
        """Load saved server list from default location"""
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
        """Save server list to default location"""
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
        """Query selected servers"""
        selected = self.server_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select servers to query")
            return
            
        servers = [self.server_listbox.get(i) for i in selected]
        self._query_servers(servers)
        
    def query_all_servers(self):
        """Query all servers"""
        servers = list(self.server_listbox.get(0, tk.END))
        if not servers:
            messagebox.showwarning("No Servers", "No servers in list")
            return
        self._query_servers(servers)
        
    def _query_servers(self, servers):
        """Internal method to query servers"""
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
        """Display query results in the results tab"""
        self.query_progress.stop()
        self.query_btn.config(state=tk.NORMAL)
        self.query_all_btn.config(state=tk.NORMAL)
        
        # Switch to results tab
        self.notebook.select(3)  # Results tab index
        
        # Clear and display
        self.results_text.delete(1.0, tk.END)
        
        # Create a formatted display
        display = []
        display.append("=" * 100)
        display.append(f"📊 SYSTEM INFORMATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        display.append("=" * 100)
        
        success_count = len([r for r in results if r['status'] == 'success'])
        error_count = len([r for r in results if r['status'] == 'error'])
        
        display.append(f"\n📊 Query Results: {success_count} successful, {error_count} failed out of {len(results)} total")
        
        # Process each result
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
        
        self.results_text.insert(tk.END, "\n".join(display))
        
        # Summary notification
        self.update_status(f"Query completed: {success_count} successful, {error_count} failed")
        
    def _query_error(self, error):
        """Handle query error"""
        self.query_progress.stop()
        self.query_btn.config(state=tk.NORMAL)
        self.query_all_btn.config(state=tk.NORMAL)
        messagebox.showerror("Query Error", f"Failed to query servers: {error}")
        
    # Monitoring methods
    def browse_log_dir(self):
        """Browse for log directory"""
        directory = filedialog.askdirectory(title="Select Log Directory")
        if directory:
            self.log_dir_var.set(directory)
            
    def start_monitoring(self):
        """Start continuous monitoring"""
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
        self.monitor_status_label.config(text="Running", foreground="green")
        
        self.monitor_thread = threading.Thread(
            target=self._run_monitoring,
            args=(servers, interval),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.log_monitor_message("✅ Monitoring started")
        self.update_status("Monitoring started")
        
    def _run_monitoring(self, servers, interval):
        """Run monitoring in a thread"""
        try:
            client = EnhancedContinuousClient(timeout=30, max_workers=5)
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
                
                # Query servers
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {executor.submit(client.query_single_server, s): s 
                              for s in formatted_servers}
                    
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        status = '✅' if result['status'] == 'success' else '❌'
                        self.root.after(0, self.log_monitor_message,
                                      f"  {status} {result['server']} ({result.get('response_time', 0):.2f}s)")
                
                # Save results
                log_file = client.save_results(results, self.log_dir_var.get())
                success = len([r for r in results if r['status'] == 'success'])
                errors = len([r for r in results if r['status'] == 'error'])
                
                self.root.after(0, self.log_monitor_message,
                              f"📄 Iteration #{iteration} completed: {success} successful, {errors} failed")
                self.root.after(0, self.log_monitor_message,
                              f"💾 Log saved: {log_file}")
                
                # Wait for next interval
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
        """Stop continuous monitoring"""
        self.monitoring = False
        self.monitor_status_label.config(text="Stopped", foreground="red")
        self.start_monitor_btn.config(state=tk.NORMAL)
        self.stop_monitor_btn.config(state=tk.DISABLED)
        
        if self.continuous_client:
            self.continuous_client.running = False
            
        self.log_monitor_message("🛑 Monitoring stopped")
        self.update_status("Monitoring stopped")
        
    def log_monitor_message(self, message):
        """Add message to monitor log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.monitor_log.see(tk.END)
        
    # Results methods
    def clear_results(self):
        """Clear results display"""
        self.results_text.delete(1.0, tk.END)
        self.update_status("Results cleared")
        
    def export_results(self):
        """Export results to file"""
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
        """Clear current tab's log"""
        current_tab = self.notebook.select()
        if current_tab:
            tab_id = self.notebook.index(current_tab)
            if tab_id == 0:  # Server tab
                self.server_log.delete(1.0, tk.END)
            elif tab_id == 2:  # Monitor tab
                self.monitor_log.delete(1.0, tk.END)
                
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
        
    # Help methods
    def show_documentation(self):
        """Show documentation"""
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
4. Adjust timeout for slow networks
        """
        messagebox.showinfo("Documentation", doc_text)
        
    def show_about(self):
        """Show about dialog"""
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
    # Required imports for the monitoring thread
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    main()