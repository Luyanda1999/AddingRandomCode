# server.py - Run this on the PC you want to monitor
import socket
import json
import platform
import os
import sys
from datetime import datetime
import threading
import shutil
import subprocess

class SystemInfoServer:
    #10.20.37.165
    #10.0.1.224
    def __init__(self, host='10.0.1.224', port=5000):
        self.host = host
        self.port = port
        self.running = True
        
    def get_all_storage_devices(self):
        """Get storage information for all drives/partitions"""
        storage_devices = []
        
        try:
            if platform.system() == 'Windows':
                # Get all drives on Windows
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
                        # Check if drive is ready/accessible
                        if os.path.exists(drive + '\\'):
                            total, used, free = self.get_windows_disk_usage(drive)
                            if total > 0:
                                # Get drive type
                                drive_type = self.get_drive_type(drive)
                                storage_devices.append({
                                    'drive': drive,
                                    'type': drive_type,
                                    'total': round(total / (1024**3), 2),
                                    'used': round(used / (1024**3), 2),
                                    'free': round(free / (1024**3), 2),
                                    'total_bytes': total,
                                    'used_bytes': used,
                                    'free_bytes': free,
                                    'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                                })
                    except:
                        continue
                        
            else:
                # For Linux/Mac - get all mount points
                try:
                    # Get mounted filesystems
                    with open('/proc/mounts', 'r') as f:
                        mounts = f.readlines()
                    
                    for mount in mounts:
                        parts = mount.split()
                        if len(parts) >= 2:
                            device = parts[0]
                            mount_point = parts[1]
                            
                            # Skip virtual filesystems
                            if device.startswith('dev') or device.startswith('sys') or device.startswith('proc'):
                                continue
                            
                            try:
                                total, used, free = self.get_unix_disk_usage(mount_point)
                                if total > 0:
                                    storage_devices.append({
                                        'drive': mount_point,
                                        'type': device,
                                        'total': round(total / (1024**3), 2),
                                        'used': round(used / (1024**3), 2),
                                        'free': round(free / (1024**3), 2),
                                        'total_bytes': total,
                                        'used_bytes': used,
                                        'free_bytes': free,
                                        'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                                    })
                            except:
                                continue
                                
                except:
                    # Fallback: just get root directory
                    total, used, free = self.get_unix_disk_usage('/')
                    if total > 0:
                        storage_devices.append({
                            'drive': '/',
                            'type': 'root',
                            'total': round(total / (1024**3), 2),
                            'used': round(used / (1024**3), 2),
                            'free': round(free / (1024**3), 2),
                            'total_bytes': total,
                            'used_bytes': used,
                            'free_bytes': free,
                            'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                        })
            
            # Calculate totals
            total_all = sum(d['total_bytes'] for d in storage_devices)
            used_all = sum(d['used_bytes'] for d in storage_devices)
            free_all = sum(d['free_bytes'] for d in storage_devices)
            
            return {
                'devices': storage_devices,
                'total': round(total_all / (1024**3), 2),
                'used': round(used_all / (1024**3), 2),
                'free': round(free_all / (1024**3), 2),
                'total_bytes': total_all,
                'used_bytes': used_all,
                'free_bytes': free_all,
                'usage_percent': round((used_all / total_all) * 100, 1) if total_all > 0 else 0
            }
            
        except Exception as e:
            return {
                'devices': [],
                'total': 0,
                'used': 0,
                'free': 0,
                'total_bytes': 0,
                'used_bytes': 0,
                'free_bytes': 0,
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
            import ctypes
            from ctypes import wintypes
            
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            total_free_bytes = ctypes.c_ulonglong(0)
            
            drive_path = drive + '\\'
            success = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(drive_path),
                ctypes.byref(free_bytes),
                ctypes.byref(total_bytes),
                ctypes.byref(total_free_bytes)
            )
            
            if success:
                return total_bytes.value, total_bytes.value - free_bytes.value, free_bytes.value
            else:
                # Fallback using shutil
                total, used, free = shutil.disk_usage(drive + '\\')
                return total, used, free
        except:
            try:
                total, used, free = shutil.disk_usage(drive + '\\')
                return total, used, free
            except:
                return 0, 0, 0
    
    def get_unix_disk_usage(self, path):
        """Get disk usage on Unix/Linux/Mac"""
        try:
            total, used, free = shutil.disk_usage(path)
            return total, used, free
        except:
            return 0, 0, 0
    
    def get_memory_info(self):
        """Get memory information"""
        try:
            if platform.system() == 'Windows':
                return self.get_windows_memory()
            else:
                return self.get_unix_memory()
        except Exception as e:
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'usage_percent': 0,
                'error': str(e)
            }
    
    def get_windows_memory(self):
        """Get memory info on Windows"""
        try:
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
                total = memoryStatus.ullTotalPhys
                available = memoryStatus.ullAvailPhys
                used = total - available
                percent = memoryStatus.dwMemoryLoad
                
                return {
                    'total': round(total / (1024**3), 2),
                    'used': round(used / (1024**3), 2),
                    'free': round(available / (1024**3), 2),
                    'usage_percent': percent
                }
            else:
                return {'total': 0, 'used': 0, 'free': 0, 'usage_percent': 0}
        except:
            return {'total': 0, 'used': 0, 'free': 0, 'usage_percent': 0}
    
    def get_unix_memory(self):
        """Get memory info on Unix/Linux/Mac"""
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
            
            total = mem_info.get('MemTotal', 0)
            available = mem_info.get('MemAvailable', mem_info.get('MemFree', 0))
            used = total - available
            percent = (used / total) * 100 if total > 0 else 0
            
            return {
                'total': round(total / (1024**3), 2),
                'used': round(used / (1024**3), 2),
                'free': round(available / (1024**3), 2),
                'usage_percent': round(percent, 1)
            }
        except:
            # Try using free command on Mac/Linux
            try:
                result = subprocess.run(['free', '-b'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Mem:' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            total = int(parts[1])
                            used = int(parts[2])
                            free = total - used
                            return {
                                'total': round(total / (1024**3), 2),
                                'used': round(used / (1024**3), 2),
                                'free': round(free / (1024**3), 2),
                                'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
                            }
            except:
                pass
            return {'total': 0, 'used': 0, 'free': 0, 'usage_percent': 0}
    
    def get_cpu_info(self):
        """Get CPU information"""
        try:
            cpu_count = os.cpu_count() or 0
            
            # Get CPU usage
            if platform.system() == 'Windows':
                try:
                    # Use wmic to get CPU usage
                    result = subprocess.run(['wmic', 'cpu', 'get', 'loadpercentage'], 
                                          capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        # Last line contains the value
                        for line in reversed(lines):
                            if line.strip() and line.strip().replace(' ', '').isdigit():
                                cpu_percent = int(line.strip())
                                break
                    else:
                        cpu_percent = 0
                except:
                    cpu_percent = 0
            else:
                # For Linux/Mac
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
                        else:
                            cpu_percent = 0
                except:
                    cpu_percent = 0
            
            return {
                'percent': cpu_percent,
                'cores': cpu_count
            }
        except:
            return {'percent': 0, 'cores': 0}
    
    def get_system_info(self):
        """Collect all system information"""
        try:
            storage = self.get_all_storage_devices()
            memory = self.get_memory_info()
            cpu = self.get_cpu_info()
            
            info = {
                'device_name': platform.node(),
                'hostname': socket.gethostname(),
                'os': platform.system(),
                'os_version': platform.version(),
                'platform': platform.platform(),
                'storage': storage,
                'memory': memory,
                'cpu': cpu,
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
    
    def handle_client(self, client_socket, address):
        """Handle incoming client connections"""
        try:
            print(f"Connection from {address}")
            system_info = self.get_system_info()
            response = json.dumps(system_info)
            client_socket.send(response.encode('utf-8'))
            print(f"Data sent to {address}")
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
            
            print(f"Server listening on {self.host}:{self.port}")
            print(f"Device name: {platform.node()}")
            print("Press Ctrl+C to stop")
            
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    client_handler = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
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
    port = 5000
    
    # Check if port is available
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', port))
        test_socket.close()
    except:
        print(f"Port {port} is already in use. Please change the port number.")
        sys.exit(1)
    
    server = SystemInfoServer(port=port)
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        server.stop_server()

if __name__ == "__main__":
    main()