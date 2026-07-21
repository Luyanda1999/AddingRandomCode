# enhanced_client.py - Query multiple servers for storage and auto-run info
import socket
import json
import time
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class EnhancedClient:
    def __init__(self, timeout=30, max_workers=5):  # Increased timeout
        self.timeout = timeout
        self.max_workers = max_workers
    
    def recv_all(self, sock):
        """Receive all data from socket with proper handling"""
        data = b''
        sock.settimeout(self.timeout)
        
        while True:
            try:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                data += chunk
                
                # Try to see if we have complete JSON
                try:
                    # Try to decode and parse what we have so far
                    json.loads(data.decode('utf-8'))
                    # If we can parse it, we have all the data
                    break
                except json.JSONDecodeError:
                    # Not complete yet, continue receiving
                    continue
                except UnicodeDecodeError:
                    # Still receiving partial data
                    continue
                    
            except socket.timeout:
                # If we have some data, it might be complete
                if data:
                    try:
                        json.loads(data.decode('utf-8'))
                        break
                    except:
                        pass
                raise
                
        return data
    
    def query_single_server(self, server_string):
        """Query a single server"""
        # Parse server string
        if ':' in server_string:
            host, port = server_string.split(':')
            port = int(port)
        else:
            host, port = server_string, 5000
        
        start_time = time.time()
        
        try:
            # Create socket and connect
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.timeout)
            
            print(f"  Connecting to {host}:{port}...", end='', flush=True)
            client_socket.connect((host, port))
            print(" connected!", flush=True)
            
            # Receive all data
            print(f"  Receiving data (timeout: {self.timeout}s)...", end='', flush=True)
            data = self.recv_all(client_socket)
            client_socket.close()
            
            print(f" received {len(data)} bytes!", flush=True)
            
            # Check if we got any data
            if not data:
                return {
                    'server': server_string,
                    'host': host,
                    'port': port,
                    'status': 'error',
                    'error': 'No data received',
                    'response_time': round(time.time() - start_time, 2)
                }
            
            # Parse response
            try:
                decoded_data = data.decode('utf-8')
                info = json.loads(decoded_data)
                
                return {
                    'server': server_string,
                    'host': host,
                    'port': port,
                    'status': 'success',
                    'data': info,
                    'response_time': round(time.time() - start_time, 2)
                }
            except json.JSONDecodeError as e:
                preview = data[:500].decode('utf-8', errors='ignore') + '...' if len(data) > 500 else data.decode('utf-8', errors='ignore')
                return {
                    'server': server_string,
                    'host': host,
                    'port': port,
                    'status': 'error',
                    'error': f'Invalid JSON: {str(e)}',
                    'raw_data': preview,
                    'response_time': round(time.time() - start_time, 2)
                }
                
        except socket.timeout:
            print(" timeout!", flush=True)
            return {
                'server': server_string,
                'host': host,
                'port': port,
                'status': 'error',
                'error': 'Connection timeout - data transfer may be too large',
                'response_time': round(time.time() - start_time, 2)
            }
        except ConnectionRefusedError:
            print(" connection refused!", flush=True)
            return {
                'server': server_string,
                'host': host,
                'port': port,
                'status': 'error',
                'error': 'Connection refused - server not running or wrong port',
                'response_time': round(time.time() - start_time, 2)
            }
        except Exception as e:
            print(f" error: {str(e)}", flush=True)
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
                error_msg = f" - {result.get('error', '')}" if result['status'] == 'error' else ''
                print(f"{status} {result['server']} ({result.get('response_time', 0):.2f}s){error_msg}")
        
        return results
    
    def create_bar(self, percentage, width=20):
        """Create a visual bar"""
        filled = int(width * percentage / 100)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def display_results(self, results):
        """Display comprehensive results"""
        print("\n" + "="*100)
        print(f"📊 SYSTEM INFORMATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        success_results = [r for r in results if r['status'] == 'success']
        error_results = [r for r in results if r['status'] == 'error']
        
        # Show errors
        if error_results:
            print(f"\n❌ FAILED: {len(error_results)} servers")
            for r in error_results:
                print(f"  • {r['server']}: {r.get('error', 'Unknown error')}")
                if 'raw_data' in r:
                    print(f"    Raw data preview: {r['raw_data'][:200]}...")
        
        # Show detailed results
        if success_results:
            print(f"\n✅ SUCCESSFUL: {len(success_results)} servers\n")
            
            for idx, r in enumerate(success_results, 1):
                info = r['data']
                
                print(f"{'='*100}")
                print(f"🖥️  SERVER #{idx}: {r['server']} (Response: {r['response_time']}s)")
                print(f"{'='*100}")
                
                # Check if we got valid data
                if info.get('status') == 'error':
                    print(f"  ❌ Server returned error: {info.get('message', 'Unknown error')}")
                    print()
                    continue
                
                # Basic info
                print(f"  Device Name: {info.get('device_name', 'N/A')}")
                print(f"  OS: {info.get('os', 'N/A')} {info.get('os_version', '')}")
                
                # Local IPs
                local_ips = info.get('local_ips', [])
                if local_ips:
                    print(f"  Local IPs: {', '.join(local_ips)}")
                
                # CPU info
                cpu = info.get('cpu', {})
                if cpu:
                    print(f"  CPU: {cpu.get('percent', 0):.1f}% ({cpu.get('cores', 0)} cores)")
                
                # Memory info
                memory = info.get('memory', {})
                if memory and memory.get('total_gb', 0) > 0:
                    print(f"  Memory: {memory.get('used_gb', 0):.2f} / {memory.get('total_gb', 0):.2f} GB ({memory.get('usage_percent', 0):.1f}%)")
                
                # Storage/Drives
                storage = info.get('storage', {})
                devices = storage.get('devices', [])
                
                if devices:
                    print(f"\n  💾 STORAGE DRIVES ({len(devices)} found):")
                    print(f"  {'Drive':<12} {'Type':<12} {'Total GB':<12} {'Used GB':<12} {'Free GB':<12} {'Usage':<10}")
                    print(f"  {'-'*80}")
                    
                    for device in devices:
                        drive = device.get('drive', 'Unknown')
                        drive_type = device.get('type', 'Unknown')
                        total = device.get('total_gb', 0)
                        used = device.get('used_gb', 0)
                        free = device.get('free_gb', 0)
                        percent = device.get('usage_percent', 0)
                        
                        bar = self.create_bar(percent, 20)
                        
                        print(f"  {drive:<12} {drive_type:<12} {total:<12.2f} {used:<12.2f} {free:<12.2f} {percent:>5.1f}% {bar}")
                    
                    print(f"\n  📊 OVERALL STORAGE:")
                    print(f"  Total: {storage.get('total_gb', 0):.2f} GB")
                    print(f"  Used:  {storage.get('used_gb', 0):.2f} GB ({storage.get('usage_percent', 0):.1f}%)")
                    print(f"  Free:  {storage.get('free_gb', 0):.2f} GB")
                else:
                    print(f"\n  💾 No storage devices found")
                
                # Auto-run information (Windows only)
                auto_run = info.get('auto_run', {})
                if auto_run:
                    print(f"\n  🔍 AUTO-RUN INFORMATION:")
                    
                    # Startup items
                    startup_items = auto_run.get('startup_items', [])
                    print(f"  • Startup Items: {len(startup_items)}")
                    if startup_items:
                        for item in startup_items[:5]:
                            print(f"    - {item.get('name', 'Unknown')} ({item.get('location', 'Registry')})")
                        if len(startup_items) > 5:
                            print(f"    ... and {len(startup_items) - 5} more")
                    
                    # Running services
                    services = auto_run.get('running_services', [])
                    print(f"  • Running Services: {len(services)}")
                    if services:
                        for service in services[:5]:
                            print(f"    - {service.get('name', 'Unknown')} ({service.get('status', 'N/A')})")
                        if len(services) > 5:
                            print(f"    ... and {len(services) - 5} more")
                    
                    # Scheduled tasks
                    tasks = auto_run.get('scheduled_tasks', [])
                    print(f"  • Scheduled Tasks: {len(tasks)}")
                    if tasks:
                        for task in tasks[:3]:
                            print(f"    - {task.get('name', 'Unknown')} ({task.get('status', 'N/A')})")
                        if len(tasks) > 3:
                            print(f"    ... and {len(tasks) - 3} more")
                    
                    # Running processes
                    processes = auto_run.get('running_processes', [])
                    print(f"  • Running Processes: {len(processes)}")
                    if processes:
                        for proc in processes[:3]:
                            print(f"    - {proc.get('name', 'Unknown')} (PID: {proc.get('pid', 'N/A')})")
                        if len(processes) > 3:
                            print(f"    ... and {len(processes) - 3} more")
                else:
                    print(f"\n  🔍 Auto-run information not available (non-Windows system)")
                
                print()  # Blank line between servers

def main():
    parser = argparse.ArgumentParser(description='Query multiple servers for storage and auto-run info')
    parser.add_argument('servers', nargs='*', help='Server addresses (IP:PORT or just IP)')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Default port (default: 5000)')
    parser.add_argument('-t', '--timeout', type=int, default=30, help='Timeout in seconds (default: 30)')
    parser.add_argument('-w', '--workers', type=int, default=3, help='Max concurrent workers (default: 3)')
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
    elif args.servers:
        servers = args.servers
    else:
        print("❌ Please specify at least one server or use -f to read from file")
        print("Example: python enhanced_client.py 192.168.1.100:5000")
        print("Example: python enhanced_client.py -f servers.txt")
        return
    
    # Format servers
    formatted_servers = []
    for server in servers:
        if ':' not in server:
            formatted_servers.append(f"{server}:{args.port}")
        else:
            formatted_servers.append(server)
    
    print(f"⏱️  Timeout set to {args.timeout} seconds")
    print(f"📊 Maximum concurrent workers: {args.workers}")
    
    # Query
    client = EnhancedClient(timeout=args.timeout, max_workers=args.workers)
    results = client.query_multiple_parallel(formatted_servers)
    client.display_results(results)
    
    # Summary
    success = len([r for r in results if r['status'] == 'success'])
    errors = len([r for r in results if r['status'] == 'error'])
    print(f"\n📊 SUMMARY: {success} successful, {errors} failed out of {len(results)} total")

if __name__ == "__main__":
    main()