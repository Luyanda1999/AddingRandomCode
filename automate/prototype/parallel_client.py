# parallel_client_drives.py - Shows detailed drive information for each server
import socket
import json
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

class ParallelDriveInfoClient:
    def __init__(self, timeout=10, max_workers=10):
        self.timeout = timeout
        self.max_workers = max_workers
    
    def query_single_server(self, server_string):
        """Query a single server"""
        if ':' in server_string:
            host, port = server_string.split(':')
            port = int(port)
        else:
            host, port = server_string, 5000
        
        start_time = time.time()
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.timeout)
            client_socket.connect((host, port))
            data = client_socket.recv(16384).decode('utf-8')
            info = json.loads(data)
            client_socket.close()
            
            return {
                'server': server_string,
                'host': host,
                'port': port,
                'status': 'success',
                'data': info,
                'response_time': round(time.time() - start_time, 2)
            }
        except Exception as e:
            return {
                'server': server_string,
                'host': host,
                'port': port,
                'status': 'error',
                'error': str(e),
                'response_time': round(time.time() - start_time, 2)
            }
    
    def query_multiple_parallel(self, servers):
        """Query multiple servers in parallel"""
        print(f"\n🚀 Querying {len(servers)} servers in parallel...")
        print("="*70)
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_server = {
                executor.submit(self.query_single_server, server): server 
                for server in servers
            }
            
            for future in as_completed(future_to_server):
                result = future.result()
                results.append(result)
                status = '✅' if result['status'] == 'success' else '❌'
                print(f"{status} {result['server']} ({result.get('response_time', 0):.2f}s)")
        
        return results
    
    def display_detailed_results(self, results):
        """Display results with all drives for each server"""
        print("\n" + "="*90)
        print(f"📊 SYSTEM INFORMATION WITH ALL DRIVES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*90)
        
        success_results = [r for r in results if r['status'] == 'success']
        error_results = [r for r in results if r['status'] == 'error']
        
        # Show errors
        if error_results:
            print(f"\n❌ FAILED: {len(error_results)} servers")
            for r in error_results:
                print(f"  {r['server']}: {r.get('error', 'Unknown error')}")
        
        # Show detailed results
        if success_results:
            print(f"\n✅ SUCCESSFUL: {len(success_results)} servers\n")
            
            for idx, r in enumerate(success_results, 1):
                info = r['data']
                storage = info.get('storage', {})
                devices = storage.get('devices', [])
                
                print(f"{'='*90}")
                print(f"🖥️  SERVER #{idx}: {r['server']} (Response: {r['response_time']}s)")
                print(f"{'='*90}")
                
                # Basic info
                print(f"  Device Name: {info.get('device_name', 'N/A')}")
                print(f"  OS: {info.get('os', 'N/A')} {info.get('os_version', '')}")
                
                # CPU info
                cpu = info.get('cpu', {})
                print(f"  CPU: {cpu.get('percent', 0):.1f}% ({cpu.get('cores', 0)} cores)")
                
                # Memory info
                memory = info.get('memory', {})
                print(f"  Memory: {memory.get('used', 0):.2f} / {memory.get('total', 0):.2f} GB ({memory.get('usage_percent', 0):.1f}%)")
                
                # DRIVE DETAILS - THIS SHOWS ALL DRIVES
                if devices:
                    print(f"\n  💾 ALL DRIVES ({len(devices)} found):")
                    print(f"  {'Drive':<12} {'Type':<12} {'Total (GB)':<12} {'Used (GB)':<12} {'Free (GB)':<12} {'Usage':<10}")
                    print(f"  {'-'*70}")
                    
                    for device in devices:
                        drive = device.get('drive', 'Unknown')
                        drive_type = device.get('type', 'Unknown')
                        total = device.get('total', 0)
                        used = device.get('used', 0)
                        free = device.get('free', 0)
                        percent = device.get('usage_percent', 0)
                        
                        # Visual bar for this drive
                        bar = self.create_bar(percent, 20)
                        
                        print(f"  {drive:<12} {drive_type:<12} {total:<12.2f} {used:<12.2f} {free:<12.2f} {percent:>5.1f}% {bar}")
                    
                    # Overall storage summary
                    print(f"\n  📊 OVERALL STORAGE SUMMARY:")
                    print(f"  Total: {storage.get('total', 0):.2f} GB")
                    print(f"  Used:  {storage.get('used', 0):.2f} GB ({storage.get('usage_percent', 0):.1f}%)")
                    print(f"  Free:  {storage.get('free', 0):.2f} GB")
                else:
                    print(f"\n  💾 No storage devices found")
                
                print()  # Blank line between servers
    
    def create_bar(self, percentage, width=30):
        """Create a visual bar"""
        filled = int(width * percentage / 100)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

def main():
    parser = argparse.ArgumentParser(description='Query multiple servers with detailed drive info')
    parser.add_argument('servers', nargs='+', help='Server addresses (IP:PORT or just IP)')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Default port (default: 5000)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Timeout in seconds')
    parser.add_argument('-w', '--workers', type=int, default=10, help='Max concurrent workers')
    parser.add_argument('-f', '--file', type=str, help='Read servers from file')
    
    args = parser.parse_args()
    
    # Get servers
    servers = []
    if args.file:
        try:
            with open(args.file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        servers.append(line)
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            return
    else:
        servers = args.servers
    
    # Format servers
    formatted_servers = []
    for server in servers:
        if ':' not in server:
            formatted_servers.append(f"{server}:{args.port}")
        else:
            formatted_servers.append(server)
    
    # Query
    client = ParallelDriveInfoClient(timeout=args.timeout, max_workers=args.workers)
    results = client.query_multiple_parallel(formatted_servers)
    client.display_detailed_results(results)

if __name__ == "__main__":
    main()