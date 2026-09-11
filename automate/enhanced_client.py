# enhanced_client.py - Optimized (GUI compatible)
import socket
import json
import time
import zlib
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class EnhancedClient:
    def __init__(self, timeout=30, max_workers=5, quick_mode=None):
        """
        timeout: socket timeout
        max_workers: parallel workers
        quick_mode: None = auto (fast), True = fast, False = detailed
        """
        self.timeout = timeout
        self.max_workers = max_workers
        # auto: use quick mode if timeout is low, otherwise detailed
        if quick_mode is None:
            self.quick_mode = timeout <= 15
        else:
            self.quick_mode = quick_mode
    
    def recv_all(self, sock):
        """
        Receive compressed data (4-byte size header + zlib payload).
        Falls back to plain JSON reading if header looks invalid (backward compat).
        """
        sock.settimeout(self.timeout)
        
        # Peek first 4 bytes
        try:
            header = b''
            while len(header) < 4:
                chunk = sock.recv(4 - len(header))
                if not chunk:
                    return b''
                header += chunk
            
            data_size = int.from_bytes(header, 'big')
            
            # Sanity check: if data_size seems too large or too small, it's likely
            # a plain JSON stream (old server). Reconstruct from header + rest.
            if data_size <= 0 or data_size > 100 * 1024 * 1024:  # >100MB is suspicious
                # Fall through to plain reading
                data = header
                while True:
                    try:
                        chunk = sock.recv(8192)
                        if not chunk:
                            break
                        data += chunk
                        try:
                            json.loads(data.decode('utf-8'))
                            return data  # plain JSON, done
                        except:
                            continue
                    except socket.timeout:
                        break
                return data
            
            # Read compressed payload
            compressed = b''
            while len(compressed) < data_size:
                chunk = sock.recv(min(8192, data_size - len(compressed)))
                if not chunk:
                    break
                compressed += chunk
            
            # Try to decompress
            try:
                return zlib.decompress(compressed)
            except zlib.error:
                # Not compressed - maybe plain JSON with a 4-byte prefix that
                # happened to look like a size. Fall back.
                full = header + compressed
                try:
                    json.loads(full.decode('utf-8'))
                    return full
                except:
                    return full
                    
        except socket.timeout:
            raise
        except Exception:
            raise
    
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
            
            print(f"  Connecting to {host}:{port}...", end='', flush=True)
            client_socket.connect((host, port))
            print(" connected!", flush=True)
            
            # Send query params (newline-terminated JSON)
            # Old servers ignore this since they don't read from socket
            params = {
                'quick': self.quick_mode,
                'include_processes': not self.quick_mode,
                'include_services': not self.quick_mode,
                'include_startup': not self.quick_mode,
                'include_tasks': False,  # always skip heavy tasks for speed
                'limit': 20
            }
            try:
                client_socket.sendall((json.dumps(params) + '\n').encode('utf-8'))
            except:
                pass
            
            print(f"  Receiving data (timeout: {self.timeout}s)...", end='', flush=True)
            data = self.recv_all(client_socket)
            client_socket.close()
            
            print(f" received {len(data)} bytes!", flush=True)
            
            if not data:
                return {
                    'server': server_string, 'host': host, 'port': port,
                    'status': 'error', 'error': 'No data received',
                    'response_time': round(time.time() - start_time, 2)
                }
            
            try:
                decoded_data = data.decode('utf-8')
                info = json.loads(decoded_data)
                
                return {
                    'server': server_string, 'host': host, 'port': port,
                    'status': 'success', 'data': info,
                    'response_time': round(time.time() - start_time, 2)
                }
            except json.JSONDecodeError as e:
                preview = (data[:500].decode('utf-8', errors='ignore') + '...'
                           if len(data) > 500 else data.decode('utf-8', errors='ignore'))
                return {
                    'server': server_string, 'host': host, 'port': port,
                    'status': 'error', 'error': f'Invalid JSON: {str(e)}',
                    'raw_data': preview,
                    'response_time': round(time.time() - start_time, 2)
                }
                
        except socket.timeout:
            print(" timeout!", flush=True)
            return {
                'server': server_string, 'host': host, 'port': port,
                'status': 'error', 'error': 'Connection timeout - data transfer may be too large',
                'response_time': round(time.time() - start_time, 2)
            }
        except ConnectionRefusedError:
            print(" connection refused!", flush=True)
            return {
                'server': server_string, 'host': host, 'port': port,
                'status': 'error', 'error': 'Connection refused - server not running or wrong port',
                'response_time': round(time.time() - start_time, 2)
            }
        except Exception as e:
            print(f" error: {str(e)}", flush=True)
            return {
                'server': server_string, 'host': host, 'port': port,
                'status': 'error', 'error': str(e),
                'response_time': round(time.time() - start_time, 2)
            }
    
    def query_multiple_parallel(self, servers):
        """Query multiple servers in parallel"""
        print(f"\n🚀 Querying {len(servers)} servers in parallel...")
        if self.quick_mode:
            print(f"⚡ Quick mode enabled for speed")
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
        
        if error_results:
            print(f"\n❌ FAILED: {len(error_results)} servers")
            for r in error_results:
                print(f"  • {r['server']}: {r.get('error', 'Unknown error')}")
                if 'raw_data' in r:
                    print(f"    Raw data preview: {r['raw_data'][:200]}...")
        
        if success_results:
            print(f"\n✅ SUCCESSFUL: {len(success_results)} servers\n")
            
            for idx, r in enumerate(success_results, 1):
                info = r['data']
                
                print(f"{'='*100}")
                print(f"🖥️  SERVER #{idx}: {r['server']} (Response: {r['response_time']}s)")
                print(f"{'='*100}")
                
                if info.get('status') == 'error':
                    print(f"  ❌ Server returned error: {info.get('message', 'Unknown error')}")
                    print()
                    continue
                
                print(f"  Device Name: {info.get('device_name', 'N/A')}")
                print(f"  OS: {info.get('os', 'N/A')} {info.get('os_version', '')}")
                
                local_ips = info.get('local_ips', [])
                if local_ips:
                    print(f"  Local IPs: {', '.join(local_ips)}")
                
                cpu = info.get('cpu', {})
                if cpu:
                    print(f"  CPU: {cpu.get('percent', 0):.1f}% ({cpu.get('cores', 0)} cores)")
                
                memory = info.get('memory', {})
                if memory and memory.get('total_gb', 0) > 0:
                    print(f"  Memory: {memory.get('used_gb', 0):.2f} / {memory.get('total_gb', 0):.2f} GB ({memory.get('usage_percent', 0):.1f}%)")
                
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
                
                auto_run = info.get('auto_run', {})
                if auto_run:
                    print(f"\n  🔍 AUTO-RUN INFORMATION:")
                    
                    startup_items = auto_run.get('startup_items', [])
                    print(f"  • Startup Items: {len(startup_items)}")
                    if startup_items:
                        for item in startup_items[:5]:
                            print(f"    - {item.get('name', 'Unknown')} ({item.get('location', 'Registry')})")
                        if len(startup_items) > 5:
                            print(f"    ... and {len(startup_items) - 5} more")
                    
                    services = auto_run.get('running_services', [])
                    print(f"  • Running Services: {len(services)}")
                    if services:
                        for service in services[:5]:
                            print(f"    - {service.get('name', 'Unknown')} ({service.get('status', 'N/A')})")
                        if len(services) > 5:
                            print(f"    ... and {len(services) - 5} more")
                    
                    tasks = auto_run.get('scheduled_tasks', [])
                    print(f"  • Scheduled Tasks: {len(tasks)}")
                    if tasks:
                        for task in tasks[:3]:
                            print(f"    - {task.get('name', 'Unknown')} ({task.get('status', 'N/A')})")
                        if len(tasks) > 3:
                            print(f"    ... and {len(tasks) - 3} more")
                    
                    processes = auto_run.get('running_processes', [])
                    print(f"  • Running Processes: {len(processes)}")
                    if processes:
                        for proc in processes[:3]:
                            print(f"    - {proc.get('name', 'Unknown')} (PID: {proc.get('pid', 'N/A')})")
                        if len(processes) > 3:
                            print(f"    ... and {len(processes) - 3} more")
                else:
                    print(f"\n  🔍 Auto-run information not available (non-Windows system)")
                
                print()

def main():
    parser = argparse.ArgumentParser(description='Query multiple servers for storage and auto-run info')
    parser.add_argument('servers', nargs='*', help='Server addresses (IP:PORT or just IP)')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Default port (default: 5000)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Timeout in seconds (default: 10)')
    parser.add_argument('-w', '--workers', type=int, default=10, help='Max concurrent workers (default: 10)')
    parser.add_argument('-f', '--file', type=str, help='Read servers from file')
    parser.add_argument('-d', '--detailed', action='store_true', help='Detailed mode (slower, more data)')
    
    args = parser.parse_args()
    
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
    
    formatted_servers = []
    for server in servers:
        if ':' not in server:
            formatted_servers.append(f"{server}:{args.port}")
        else:
            formatted_servers.append(server)
    
    print(f"⏱️  Timeout set to {args.timeout} seconds")
    print(f"📊 Maximum concurrent workers: {args.workers}")
    
    # Detailed mode disables quick_mode
    client = EnhancedClient(
        timeout=args.timeout,
        max_workers=args.workers,
        quick_mode=(False if args.detailed else None)
    )
    results = client.query_multiple_parallel(formatted_servers)
    client.display_results(results)
    
    success = len([r for r in results if r['status'] == 'success'])
    errors = len([r for r in results if r['status'] == 'error'])
    print(f"\n📊 SUMMARY: {success} successful, {errors} failed out of {len(results)} total")

if __name__ == "__main__":
    main()