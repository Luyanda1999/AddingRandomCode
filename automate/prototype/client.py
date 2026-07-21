# client.py - Run this on your PC to query the target PC
import socket
import json
import argparse
import sys
from datetime import datetime

class SystemInfoClient:
    def __init__(self, host, port=5000):
        self.host = host
        self.port = port
        self.timeout = 10
    
    def get_system_info(self):
        """Connect to the server and get system information"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.timeout)
            
            print(f"Connecting to {self.host}:{self.port}...")
            client_socket.connect((self.host, self.port))
            
            # Receive data
            data = client_socket.recv(16384).decode('utf-8')
            
            # Parse JSON
            info = json.loads(data)
            return info
            
        except socket.timeout:
            return {
                'status': 'error',
                'message': f'Connection timeout to {self.host}:{self.port}'
            }
        except socket.error as e:
            return {
                'status': 'error',
                'message': f'Connection error: {str(e)}'
            }
        except json.JSONDecodeError:
            return {
                'status': 'error',
                'message': 'Invalid response from server'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }
        finally:
            client_socket.close()
    
    def display_info(self, info):
        """Display system information in a readable format"""
        if info.get('status') == 'error':
            print(f"❌ Error: {info.get('message', 'Unknown error')}")
            return
        
        print("\n" + "="*70)
        print(f"📊 SYSTEM INFORMATION - {info.get('timestamp', 'N/A')}")
        print("="*70)
        
        # Device Information
        print("\n🖥️  DEVICE INFORMATION")
        print("-"*50)
        print(f"  Device Name: {info.get('device_name', 'N/A')}")
        print(f"  Hostname: {info.get('hostname', 'N/A')}")
        print(f"  OS: {info.get('os', 'N/A')}")
        print(f"  OS Version: {info.get('os_version', 'N/A')}")
        print(f"  Platform: {info.get('platform', 'N/A')}")
        
        # Storage Information - Show all drives
        storage = info.get('storage', {})
        devices = storage.get('devices', [])
        
        print("\n💾 STORAGE INFORMATION (ALL DRIVES)")
        print("-"*50)
        
        if devices:
            for device in devices:
                drive = device.get('drive', 'Unknown')
                drive_type = device.get('type', 'Unknown')
                total = device.get('total', 0)
                used = device.get('used', 0)
                free = device.get('free', 0)
                percent = device.get('usage_percent', 0)
                
                print(f"\n  📁 {drive} ({drive_type})")
                print(f"     Total: {total:.2f} GB")
                print(f"     Used:  {used:.2f} GB ({percent:.1f}%)")
                print(f"     Free:  {free:.2f} GB")
                
                # Create a simple bar chart for this drive
                if total > 0:
                    bar_length = 30
                    used_ratio = used / total
                    used_chars = int(bar_length * used_ratio)
                    free_chars = bar_length - used_chars
                    bar = "█" * used_chars + "░" * free_chars
                    print(f"     [{bar}]")
            
            # Overall storage summary
            print("\n  📊 OVERALL STORAGE SUMMARY")
            total_all = storage.get('total', 0)
            used_all = storage.get('used', 0)
            free_all = storage.get('free', 0)
            percent_all = storage.get('usage_percent', 0)
            
            print(f"     Total: {total_all:.2f} GB")
            print(f"     Used:  {used_all:.2f} GB ({percent_all:.1f}%)")
            print(f"     Free:  {free_all:.2f} GB")
            
            if total_all > 0:
                bar_length = 40
                used_ratio = used_all / total_all
                used_chars = int(bar_length * used_ratio)
                free_chars = bar_length - used_chars
                bar = "█" * used_chars + "░" * free_chars
                print(f"     [{bar}]")
        else:
            print("  No storage devices found")
        
        # Memory Information
        memory = info.get('memory', {})
        print("\n🧠 MEMORY INFORMATION")
        print("-"*50)
        print(f"  Total: {memory.get('total', 0):.2f} GB")
        print(f"  Used:  {memory.get('used', 0):.2f} GB ({memory.get('usage_percent', 0):.1f}%)")
        print(f"  Free:  {memory.get('free', 0):.2f} GB")
        
        # CPU Information
        cpu = info.get('cpu', {})
        print("\n⚡ CPU INFORMATION")
        print("-"*50)
        print(f"  Usage: {cpu.get('percent', 0):.1f}%")
        print(f"  Cores: {cpu.get('cores', 0)}")
        
        print("\n" + "="*70)

def main():
    parser = argparse.ArgumentParser(description='Get system information from a remote PC')
    parser.add_argument('host', help='IP address or hostname of the target PC')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Port number (default: 5000)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Connection timeout in seconds (default: 10)')
    
    args = parser.parse_args()
    
    client = SystemInfoClient(args.host, args.port)
    client.timeout = args.timeout
    
    print(f"🔍 Querying system information from {args.host}:{args.port}...")
    info = client.get_system_info()
    
    client.display_info(info)
    
    if info.get('status') == 'error':
        sys.exit(1)

if __name__ == "__main__":
    main()