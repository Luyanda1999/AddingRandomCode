# enhanced_client_continuous.py - Optimized (GUI compatible)
import socket
import json
import time
import zlib
import argparse
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class EnhancedContinuousClient:
    def __init__(self, timeout=30, max_workers=5, quick_mode=None):
        self.timeout = timeout
        self.max_workers = max_workers
        self.running = True
        if quick_mode is None:
            self.quick_mode = timeout <= 15
        else:
            self.quick_mode = quick_mode
    
    def recv_all(self, sock):
        """Receive compressed data (4-byte header + zlib). Backward-compatible fallback."""
        sock.settimeout(self.timeout)
        
        try:
            header = b''
            while len(header) < 4:
                chunk = sock.recv(4 - len(header))
                if not chunk:
                    return b''
                header += chunk
            
            data_size = int.from_bytes(header, 'big')
            
            if data_size <= 0 or data_size > 100 * 1024 * 1024:
                data = header
                while True:
                    try:
                        chunk = sock.recv(8192)
                        if not chunk:
                            break
                        data += chunk
                        try:
                            json.loads(data.decode('utf-8'))
                            return data
                        except:
                            continue
                    except socket.timeout:
                        break
                return data
            
            compressed = b''
            while len(compressed) < data_size:
                chunk = sock.recv(min(8192, data_size - len(compressed)))
                if not chunk:
                    break
                compressed += chunk
            
            try:
                return zlib.decompress(compressed)
            except zlib.error:
                full = header + compressed
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
            client_socket.connect((host, port))
            
            # Send query params
            params = {
                'quick': self.quick_mode,
                'include_processes': not self.quick_mode,
                'include_services': not self.quick_mode,
                'include_startup': not self.quick_mode,
                'include_tasks': False,
                'limit': 20
            }
            try:
                client_socket.sendall((json.dumps(params) + '\n').encode('utf-8'))
            except:
                pass
            
            data = self.recv_all(client_socket)
            client_socket.close()
            
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
                return {
                    'server': server_string, 'host': host, 'port': port,
                    'status': 'error', 'error': f'Invalid JSON: {str(e)}',
                    'response_time': round(time.time() - start_time, 2)
                }
                
        except socket.timeout:
            return {
                'server': server_string, 'host': host, 'port': port,
                'status': 'error', 'error': 'Connection timeout',
                'response_time': round(time.time() - start_time, 2)
            }
        except ConnectionRefusedError:
            return {
                'server': server_string, 'host': host, 'port': port,
                'status': 'error', 'error': 'Connection refused',
                'response_time': round(time.time() - start_time, 2)
            }
        except Exception as e:
            return {
                'server': server_string, 'host': host, 'port': port,
                'status': 'error', 'error': str(e),
                'response_time': round(time.time() - start_time, 2)
            }
    
    def create_bar(self, percentage, width=20):
        """Create a visual bar"""
        filled = int(width * percentage / 100)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def save_results(self, results, log_dir='.'):
        """Save results to a timestamped log file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"{log_dir}/monitor_{timestamp}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("="*100 + "\n")
            f.write(f"📊 SYSTEM INFORMATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*100 + "\n\n")
            
            success_results = [r for r in results if r['status'] == 'success']
            error_results = [r for r in results if r['status'] == 'error']
            
            if error_results:
                f.write(f"❌ FAILED: {len(error_results)} servers\n")
                for r in error_results:
                    f.write(f"  • {r['server']}: {r.get('error', 'Unknown error')}\n")
                f.write("\n")
            
            if success_results:
                f.write(f"✅ SUCCESSFUL: {len(success_results)} servers\n\n")
                
                for idx, r in enumerate(success_results, 1):
                    info = r['data']
                    
                    f.write(f"{'='*100}\n")
                    f.write(f"🖥️  SERVER #{idx}: {r['server']} (Response: {r['response_time']}s)\n")
                    f.write(f"{'='*100}\n")
                    
                    if info.get('status') == 'error':
                        f.write(f"  ❌ Server returned error: {info.get('message', 'Unknown error')}\n\n")
                        continue
                    
                    f.write(f"  Device Name: {info.get('device_name', 'N/A')}\n")
                    f.write(f"  OS: {info.get('os', 'N/A')} {info.get('os_version', '')}\n")
                    
                    storage = info.get('storage', {})
                    devices = storage.get('devices', [])
                    
                    if devices:
                        f.write(f"\n  💾 STORAGE DRIVES ({len(devices)} found):\n")
                        f.write(f"  {'Drive':<12} {'Type':<12} {'Total GB':<12} {'Used GB':<12} {'Free GB':<12} {'Usage':<10}\n")
                        f.write(f"  {'-'*80}\n")
                        
                        for device in devices:
                            drive = device.get('drive', 'Unknown')
                            drive_type = device.get('type', 'Unknown')
                            total = device.get('total_gb', 0)
                            used = device.get('used_gb', 0)
                            free = device.get('free_gb', 0)
                            percent = device.get('usage_percent', 0)
                            bar = self.create_bar(percent, 20)
                            f.write(f"  {drive:<12} {drive_type:<12} {total:<12.2f} {used:<12.2f} {free:<12.2f} {percent:>5.1f}% {bar}\n")
                        
                        f.write(f"\n  📊 OVERALL STORAGE:\n")
                        f.write(f"  Total: {storage.get('total_gb', 0):.2f} GB\n")
                        f.write(f"  Used:  {storage.get('used_gb', 0):.2f} GB ({storage.get('usage_percent', 0):.1f}%)\n")
                        f.write(f"  Free:  {storage.get('free_gb', 0):.2f} GB\n")
                    
                    auto_run = info.get('auto_run', {})
                    if auto_run:
                        f.write(f"\n  🔍 AUTO-RUN INFORMATION:\n")
                        startup_items = auto_run.get('startup_items', [])
                        f.write(f"  • Startup Items: {len(startup_items)}\n")
                        services = auto_run.get('running_services', [])
                        f.write(f"  • Running Services: {len(services)}\n")
                        tasks = auto_run.get('scheduled_tasks', [])
                        f.write(f"  • Scheduled Tasks: {len(tasks)}\n")
                        processes = auto_run.get('running_processes', [])
                        f.write(f"  • Running Processes: {len(processes)}\n")
                    
                    f.write("\n")
        
        return log_file
    
    def run_continuous(self, servers, interval=300, log_dir='.'):
        """Run continuously in background"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting continuous monitoring...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Interval: {interval} seconds")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Log directory: {log_dir}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Press Ctrl+C to stop")
        print("="*70)
        
        formatted_servers = []
        for server in servers:
            if ':' not in server:
                formatted_servers.append(f"{server}:5000")
            else:
                formatted_servers.append(server)
        
        iteration = 0
        while self.running:
            try:
                iteration += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iteration #{iteration} starting...")
                
                results = []
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_server = {
                        executor.submit(self.query_single_server, server): server 
                        for server in formatted_servers
                    }
                    
                    for future in as_completed(future_to_server):
                        result = future.result()
                        results.append(result)
                        status = '✅' if result['status'] == 'success' else '❌'
                        print(f"  {status} {result['server']} ({result.get('response_time', 0):.2f}s)")
                
                log_file = self.save_results(results, log_dir)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Iteration #{iteration} completed. Log: {log_file}")
                
                success = len([r for r in results if r['status'] == 'success'])
                errors = len([r for r in results if r['status'] == 'error'])
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Summary: {success} successful, {errors} failed")
                
                if self.running:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting {interval} seconds until next check...")
                    for _ in range(interval):
                        if not self.running:
                            break
                        time.sleep(1)
                        
            except KeyboardInterrupt:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stopped by user")
                break
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
                if self.running:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting 60 seconds before retry...")
                    time.sleep(60)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Continuous monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='Continuous system monitoring client')
    parser.add_argument('servers', nargs='+', help='Server addresses (IP:PORT or just IP)')
    parser.add_argument('-i', '--interval', type=int, default=300, help='Check interval in seconds (default: 300)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Timeout in seconds (default: 10)')
    parser.add_argument('-w', '--workers', type=int, default=10, help='Max concurrent workers (default: 10)')
    parser.add_argument('-l', '--log-dir', type=str, default='.', help='Log directory (default: current)')
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
    else:
        servers = args.servers
    
    if not servers:
        print("❌ No servers specified")
        return
    
    if args.log_dir != '.':
        os.makedirs(args.log_dir, exist_ok=True)
    
    client = EnhancedContinuousClient(
        timeout=args.timeout,
        max_workers=args.workers,
        quick_mode=(False if args.detailed else None)
    )
    
    try:
        client.run_continuous(servers, interval=args.interval, log_dir=args.log_dir)
    except KeyboardInterrupt:
        print("\nStopping...")
        client.running = False

if __name__ == "__main__":
    main()