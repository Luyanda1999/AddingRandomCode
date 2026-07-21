# enhanced_server.py - Run this on PCs you want to monitor
import socket
import json
import platform
import os
import sys
import subprocess
import winreg
import threading
import shutil
from datetime import datetime
from pathlib import Path

class EnhancedSystemInfoServer:
    def __init__(self, port=5000):
        self.host = '0.0.0.0'  # Listen on all interfaces
        self.port = port
        self.running = True
        
    def get_local_ips(self):
        """Get all local IP addresses using only built-in libraries"""
        ips = []
        try:
            # Method 1: Get hostname and resolve
            hostname = socket.gethostname()
            try:
                for ip in socket.gethostbyname_ex(hostname)[2]:
                    if not ip.startswith('127.'):
                        ips.append(ip)
            except:
                pass
            
            # Method 2: Use ipconfig on Windows
            if platform.system() == 'Windows':
                try:
                    result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'IPv4 Address' in line or 'IP Address' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                ip = parts[1].strip()
                                if ip and not ip.startswith('127.') and not ip.startswith('169.254.'):
                                    ips.append(ip)
                except:
                    pass
            else:
                try:
                    result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'inet ' in line and '127.0.0.1' not in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'inet' and i + 1 < len(parts):
                                    ip = parts[i + 1]
                                    if not ip.startswith('127.'):
                                        ips.append(ip)
                except:
                    pass
            
        except Exception as e:
            print(f"Warning: Could not get all IPs: {e}")
        
        # Remove duplicates and filter out invalid IPs
        valid_ips = []
        for ip in set(ips):
            if ip and not ip.startswith('127.') and not ip.startswith('169.254.'):
                parts = ip.split('.')
                if len(parts) == 4:
                    try:
                        valid = all(0 <= int(p) <= 255 for p in parts)
                        if valid:
                            valid_ips.append(ip)
                    except:
                        pass
        
        return valid_ips if valid_ips else ['localhost']
    
    def get_auto_run_info(self):
        """Get auto-run information (startup items, services, tasks, processes)"""
        auto_run_data = {
            "startup_items": [],
            "running_services": [],
            "scheduled_tasks": [],
            "running_processes": []
        }
        
        # Only run on Windows
        if platform.system() != 'Windows':
            return auto_run_data
        
        # 1. Get startup items from registry
        try:
            startup_locations = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
            ]
            
            for hive, path in startup_locations:
                try:
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            if isinstance(value, bytes):
                                value = "<binary data>"
                            auto_run_data["startup_items"].append({
                                "name": name,
                                "path": str(value),
                                "location": path,
                                "hive": "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
                            })
                            i += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(key)
                except:
                    pass
        except:
            pass
        
        # 2. Get startup folder items
        try:
            startup_folders = [
                os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup'),
                os.path.join(os.getenv('PROGRAMDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup'),
                os.path.join(os.getenv('ALLUSERSPROFILE'), r'Microsoft\Windows\Start Menu\Programs\Startup')
            ]
            
            for folder in startup_folders:
                if folder and os.path.exists(folder):
                    for file in os.listdir(folder):
                        if file.lower().endswith(('.exe', '.lnk', '.bat', '.cmd', '.vbs', '.ps1')):
                            auto_run_data["startup_items"].append({
                                "name": file,
                                "path": os.path.join(folder, file),
                                "location": "Startup Folder",
                                "hive": "N/A"
                            })
        except:
            pass
        
        # 3. Get running services
        try:
            result = subprocess.run(['sc', 'query', 'state=all'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            lines = result.stdout.split('\n')
            current_service = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('SERVICE_NAME:'):
                    if current_service and 'name' in current_service:
                        status = current_service.get('STATE', '')
                        status_parts = status.split()
                        status_text = ' '.join(status_parts[1:]) if len(status_parts) > 1 else status
                        
                        if 'RUNNING' in status_text.upper():
                            auto_run_data["running_services"].append({
                                "name": current_service.get('name', 'Unknown'),
                                "status": status_text,
                                "type": current_service.get('TYPE', 'Unknown')
                            })
                    name = line.split(':', 1)[1].strip()
                    current_service = {'name': name}
                elif ':' in line and current_service:
                    key, value = line.split(':', 1)
                    current_service[key.strip()] = value.strip()
            
            if current_service and 'name' in current_service:
                status = current_service.get('STATE', '')
                status_parts = status.split()
                status_text = ' '.join(status_parts[1:]) if len(status_parts) > 1 else status
                
                if 'RUNNING' in status_text.upper():
                    auto_run_data["running_services"].append({
                        "name": current_service.get('name', 'Unknown'),
                        "status": status_text,
                        "type": current_service.get('TYPE', 'Unknown')
                    })
        except:
            pass
        
        # 4. Get scheduled tasks (only enabled ones) - Reduce data by limiting
        try:
            result = subprocess.run(['schtasks', '/query', '/fo', 'csv', '/v'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                headers = self._parse_csv_line(lines[0].strip())
                count = 0
                max_tasks = 50  # Limit to 50 tasks to keep data manageable
                
                for i in range(1, len(lines)):
                    if count >= max_tasks:
                        break
                    if lines[i].strip():
                        values = self._parse_csv_line(lines[i].strip())
                        if len(values) >= len(headers):
                            task_info = dict(zip(headers, values))
                            status = task_info.get('Status', '').strip('"')
                            
                            if status in ['Ready', 'Running']:
                                auto_run_data["scheduled_tasks"].append({
                                    "name": task_info.get('TaskName', 'Unknown').strip('"'),
                                    "status": status,
                                    "schedule": task_info.get('Schedule', 'N/A').strip('"')[:50],  # Truncate long schedules
                                    "last_run": task_info.get('Last Run Time', 'N/A').strip('"'),
                                    "next_run": task_info.get('Next Run Time', 'N/A').strip('"'),
                                    "task_path": task_info.get('Task To Run', 'N/A').strip('"')[:100]  # Truncate long paths
                                })
                                count += 1
        except:
            pass
        
        # 5. Get running processes (top 50 to keep data manageable)
        try:
            result = subprocess.run(['tasklist', '/v', '/fo', 'csv'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                headers = self._parse_csv_line(lines[0].strip())
                count = 0
                max_processes = 50  # Limit to 50 processes
                
                for i in range(1, len(lines)):
                    if count >= max_processes:
                        break
                    if lines[i].strip():
                        values = self._parse_csv_line(lines[i].strip())
                        if len(values) >= len(headers):
                            proc_info = dict(zip(headers, values))
                            name = proc_info.get('Image Name', '').strip('"')
                            
                            if name and name.lower() not in ['', 'system idle process']:
                                auto_run_data["running_processes"].append({
                                    "pid": proc_info.get('PID', 'Unknown').strip('"'),
                                    "name": name,
                                    "memory_usage": proc_info.get('Mem Usage', 'N/A').strip('"'),
                                    "status": proc_info.get('Status', 'Unknown').strip('"'),
                                    "user": proc_info.get('User Name', 'N/A').strip('"')[:50]  # Truncate long usernames
                                })
                                count += 1
        except:
            pass
        
        return auto_run_data
    
    def _parse_csv_line(self, line):
        """Simple CSV parser for quoted fields"""
        result = []
        current = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                result.append(current.strip())
                current = ""
            else:
                current += char
        
        if current:
            result.append(current.strip())
        
        return result
    
    def get_all_storage_devices(self):
        """Get storage information for all drives"""
        storage_devices = []
        
        try:
            if platform.system() == 'Windows':
                import string
                from ctypes import windll
                
                drives = []
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drives.append(letter + ':')
                    bitmask >>= 1
                
                for drive in drives:
                    try:
                        if os.path.exists(drive + '\\'):
                            total, used, free = self.get_windows_disk_usage(drive)
                            if total > 0:
                                drive_type = self.get_drive_type(drive)
                                storage_devices.append({
                                    'drive': drive,
                                    'type': drive_type,
                                    'total_gb': round(total / (1024**3), 2),
                                    'used_gb': round(used / (1024**3), 2),
                                    'free_gb': round(free / (1024**3), 2),
                                    'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                                })
                    except:
                        continue
            else:
                try:
                    with open('/proc/mounts', 'r') as f:
                        mounts = f.readlines()
                    
                    for mount in mounts:
                        parts = mount.split()
                        if len(parts) >= 2:
                            device = parts[0]
                            mount_point = parts[1]
                            
                            if device.startswith('dev') or device.startswith('sys') or device.startswith('proc'):
                                continue
                            
                            try:
                                total, used, free = shutil.disk_usage(mount_point)
                                if total > 0:
                                    storage_devices.append({
                                        'drive': mount_point,
                                        'type': device,
                                        'total_gb': round(total / (1024**3), 2),
                                        'used_gb': round(used / (1024**3), 2),
                                        'free_gb': round(free / (1024**3), 2),
                                        'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                                    })
                            except:
                                continue
                except:
                    total, used, free = shutil.disk_usage('/')
                    if total > 0:
                        storage_devices.append({
                            'drive': '/',
                            'type': 'root',
                            'total_gb': round(total / (1024**3), 2),
                            'used_gb': round(used / (1024**3), 2),
                            'free_gb': round(free / (1024**3), 2),
                            'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                        })
            
            total_all = sum(d['total_gb'] for d in storage_devices)
            used_all = sum(d['used_gb'] for d in storage_devices)
            free_all = sum(d['free_gb'] for d in storage_devices)
            
            return {
                'devices': storage_devices,
                'total_gb': round(total_all, 2),
                'used_gb': round(used_all, 2),
                'free_gb': round(free_all, 2),
                'usage_percent': round((used_all / total_all) * 100, 1) if total_all > 0 else 0
            }
            
        except Exception as e:
            return {
                'devices': [],
                'total_gb': 0,
                'used_gb': 0,
                'free_gb': 0,
                'usage_percent': 0,
                'error': str(e)
            }
    
    def get_drive_type(self, drive):
        """Get drive type on Windows"""
        try:
            from ctypes import windll
            drive_types = {
                0: "Unknown",
                1: "No Root Directory",
                2: "Removable",
                3: "Fixed",
                4: "Remote",
                5: "CD-ROM",
                6: "RAM Disk"
            }
            drive_type = windll.kernel32.GetDriveTypeW(drive + '\\')
            return drive_types.get(drive_type, "Unknown")
        except:
            return "Unknown"
    
    def get_windows_disk_usage(self, drive):
        """Get disk usage on Windows"""
        try:
            total, used, free = shutil.disk_usage(drive + '\\')
            return total, used, free
        except:
            return 0, 0, 0
    
    def get_memory_info(self):
        """Get memory information"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                from ctypes import wintypes
                
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", wintypes.DWORD),
                        ("dwMemoryLoad", wintypes.DWORD),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                
                memoryStatus = MEMORYSTATUSEX()
                memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus)):
                    total = memoryStatus.ullTotalPhys / (1024**3)
                    available = memoryStatus.ullAvailPhys / (1024**3)
                    used = total - available
                    
                    return {
                        'total_gb': round(total, 2),
                        'used_gb': round(used, 2),
                        'free_gb': round(available, 2),
                        'usage_percent': memoryStatus.dwMemoryLoad
                    }
            else:
                try:
                    with open('/proc/meminfo', 'r') as f:
                        lines = f.readlines()
                    
                    mem_info = {}
                    for line in lines:
                        parts = line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip().split()[0]
                            mem_info[key] = int(value) * 1024
                    
                    total = mem_info.get('MemTotal', 0) / (1024**3)
                    available = mem_info.get('MemAvailable', mem_info.get('MemFree', 0)) / (1024**3)
                    used = total - available
                    
                    return {
                        'total_gb': round(total, 2),
                        'used_gb': round(used, 2),
                        'free_gb': round(available, 2),
                        'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                    }
                except:
                    pass
        except:
            pass
        
        return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'usage_percent': 0}
    
    def get_cpu_info(self):
        """Get CPU information"""
        try:
            cpu_count = os.cpu_count() or 0
            cpu_percent = 0
            
            if platform.system() == 'Windows':
                try:
                    result = subprocess.run(['wmic', 'cpu', 'get', 'loadpercentage'], 
                                          capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        for line in reversed(lines):
                            if line.strip() and line.strip().replace(' ', '').isdigit():
                                cpu_percent = int(line.strip())
                                break
                except:
                    pass
            else:
                try:
                    with open('/proc/stat', 'r') as f:
                        line = f.readline()
                        parts = line.split()
                        if len(parts) > 4:
                            user = int(parts[1])
                            nice = int(parts[2])
                            system = int(parts[3])
                            idle = int(parts[4])
                            total = user + nice + system + idle
                            cpu_percent = round(((total - idle) / total) * 100, 1) if total > 0 else 0
                except:
                    pass
            
            return {
                'percent': cpu_percent,
                'cores': cpu_count
            }
        except:
            return {'percent': 0, 'cores': 0}
    
    def get_system_info(self):
        """Collect all system information including auto-run data"""
        try:
            storage = self.get_all_storage_devices()
            memory = self.get_memory_info()
            cpu = self.get_cpu_info()
            auto_run = self.get_auto_run_info() if platform.system() == 'Windows' else {}
            local_ips = self.get_local_ips()
            
            info = {
                'device_name': platform.node(),
                'hostname': socket.gethostname(),
                'local_ips': local_ips,
                'os': platform.system(),
                'os_version': platform.version(),
                'platform': platform.platform(),
                'storage': storage,
                'memory': memory,
                'cpu': cpu,
                'auto_run': auto_run,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            return info
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def send_large_data(self, client_socket, data):
        """Send large data in chunks"""
        try:
            # Convert to JSON
            json_data = json.dumps(data)
            encoded_data = json_data.encode('utf-8')
            total_size = len(encoded_data)
            
            # Send data in chunks
            chunk_size = 8192  # 8KB chunks
            sent = 0
            
            while sent < total_size:
                chunk = encoded_data[sent:sent + chunk_size]
                sent += client_socket.send(chunk)
            
            return True
        except Exception as e:
            print(f"Error sending data: {e}")
            return False
    
    def handle_client(self, client_socket, address):
        """Handle incoming client connections"""
        try:
            print(f"Connection from {address}")
            system_info = self.get_system_info()
            
            # Get the data size for logging
            json_str = json.dumps(system_info)
            data_size = len(json_str.encode('utf-8'))
            print(f"Data size: {data_size} bytes ({data_size/1024:.1f} KB)")
            
            # Send the data
            if self.send_large_data(client_socket, system_info):
                print(f"Data sent successfully to {address}")
            else:
                print(f"Failed to send data to {address}")
                
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
    
    def start_server(self):
        """Start the server"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            
            print("="*70)
            print(f"🚀 ENHANCED SYSTEM INFO SERVER")
            print("="*70)
            print(f"📡 Server listening on port: {self.port}")
            print(f"💻 Device name: {platform.node()}")
            print()
            print("📌 Connect using these IP addresses:")
            
            local_ips = self.get_local_ips()
            if local_ips:
                for ip in local_ips:
                    if ip != 'localhost':
                        print(f"   • {ip}:{self.port}")
                print(f"   • localhost:{self.port} (local only)")
            else:
                print(f"   • localhost:{self.port} (only local access)")
            
            print()
            print("📋 Client command example:")
            if local_ips and local_ips[0] != 'localhost':
                print(f"   python enhanced_client.py {local_ips[0]}:{self.port}")
            else:
                print(f"   python enhanced_client.py localhost:{self.port}")
            print()
            print("Press Ctrl+C to stop the server")
            print("="*70)
            
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    client_handler = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_handler.daemon = True
                    client_handler.start()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error starting server: {e}")
        finally:
            server_socket.close()
            print("Server stopped")
    
    def stop_server(self):
        """Stop the server"""
        self.running = False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced System Info Server')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    
    args = parser.parse_args()
    
    # Check if port is available
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', args.port))
        test_socket.close()
    except:
        print(f"❌ Port {args.port} is already in use. Please change the port number.")
        sys.exit(1)
    
    server = EnhancedSystemInfoServer(port=args.port)
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        server.stop_server()

if __name__ == "__main__":
    main()