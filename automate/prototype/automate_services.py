#!/usr/bin/env python3
"""
System Information Checker
Checks disk space and running services on the local machine
"""

import shutil
import datetime
import os
import subprocess
import platform
import psutil

def get_disk_space(path='/'):
    """
    Get disk space information for a given path
    
    Args:
        path (str): Path to check disk space for (default: root '/')
    
    Returns:
        dict: Dictionary containing disk space information
    """
    try:
        # Get disk usage statistics
        usage = shutil.disk_usage(path)
        
        # Convert bytes to GB for readability
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        free_gb = usage.free / (1024**3)
        
        # Calculate percentage used
        percent_used = (usage.used / usage.total) * 100
        
        return {
            'path': path,
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2),
            'percent_used': round(percent_used, 2),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Error checking disk space for {path}: {e}")
        return None

def get_running_services():
    """
    Get a list of all running services on the local machine
    
    Returns:
        list: List of dictionaries containing service information
    """
    services = []
    system = platform.system()
    
    try:
        if system == 'Linux':
            # Using systemctl for systemd-based Linux
            try:
                result = subprocess.run(
                    ['systemctl', 'list-units', '--type=service', '--state=running', '--no-pager'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip() and not line.startswith('●'):
                        parts = line.split()
                        if len(parts) >= 4:
                            services.append({
                                'name': parts[0],
                                'status': 'running',
                                'description': ' '.join(parts[4:]) if len(parts) > 4 else ''
                            })
            except subprocess.CalledProcessError:
                # Fallback to ps command if systemctl fails
                result = subprocess.run(
                    ['ps', 'aux', '--no-headers'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(None, 10)
                        if len(parts) >= 11:
                            services.append({
                                'name': parts[10] if parts[10] else parts[0],
                                'status': 'running',
                                'description': f"PID: {parts[1]}, CPU: {parts[2]}%, MEM: {parts[3]}%"
                            })
        
        elif system == 'Windows':
            # Using PowerShell for Windows
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object Name, DisplayName, Status'],
                capture_output=True,
                text=True,
                check=True
            )
            lines = result.stdout.strip().split('\n')
            for line in lines[3:]:  # Skip header and separator
                if line.strip():
                    parts = line.split(None, 2)
                    if len(parts) >= 2:
                        services.append({
                            'name': parts[0],
                            'status': 'running',
                            'description': parts[1] if len(parts) > 1 else ''
                        })
        
        elif system == 'Darwin':  # macOS
            result = subprocess.run(
                ['ps', 'aux', '--no-headers'],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        services.append({
                            'name': parts[10] if parts[10] else parts[0],
                            'status': 'running',
                            'description': f"PID: {parts[1]}, CPU: {parts[2]}%, MEM: {parts[3]}%"
                        })
        
        # Also get services using psutil for cross-platform compatibility
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                services.append({
                    'name': pinfo['name'],
                    'status': 'running',
                    'description': f"PID: {pinfo['pid']}, CPU: {pinfo['cpu_percent']:.1f}%, MEM: {pinfo['memory_percent']:.1f}%"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    except Exception as e:
        print(f"Error getting services: {e}")
    
    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_services = []
    for service in services:
        key = service['name']
        if key not in seen:
            seen.add(key)
            unique_services.append(service)
    
    return unique_services[:50]  # Limit to first 50 services for readability

def print_to_terminal(disk_info, services):
    """
    Print disk space information and services to terminal
    
    Args:
        disk_info (dict): Dictionary containing disk space information
        services (list): List of running services
    """
    # Print disk information
    if disk_info:
        print("\n" + "="*70)
        print(f"SYSTEM INFORMATION - {disk_info['timestamp']}")
        print("="*70)
        print("\n📊 DISK SPACE:")
        print("-"*70)
        print(f"Path: {disk_info['path']}")
        print(f"Total Space: {disk_info['total_gb']} GB")
        print(f"Used Space: {disk_info['used_gb']} GB")
        print(f"Free Space: {disk_info['free_gb']} GB")
        print(f"Usage: {disk_info['percent_used']}%")
        
        # Add visual bar for usage
        bar_length = 50
        filled_length = int(bar_length * disk_info['percent_used'] / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"Status: [{bar}] {disk_info['percent_used']}%")
        
        # Warning if disk is almost full
        if disk_info['percent_used'] > 90:
            print("⚠️  WARNING: Disk usage is above 90%!")
        elif disk_info['percent_used'] > 75:
            print("⚠️  Notice: Disk usage is above 75%")
    
    # Print services information
    print("\n🔧 RUNNING SERVICES:")
    print("-"*70)
    if services:
        print(f"Total running services: {len(services)}")
        print("-"*70)
        for i, service in enumerate(services[:20], 1):  # Show first 20
            print(f"{i:2}. {service['name']}")
            if service['description']:
                print(f"    └─ {service['description']}")
        if len(services) > 20:
            print(f"\n... and {len(services) - 20} more services")
    else:
        print("No services found or unable to retrieve services")
    
    print("\n" + "="*70 + "\n")

def main():
    """Main function to run the system information checker"""
    
    print("🔍 Collecting system information...")
    
    # Get disk space
    disk_info = get_disk_space('/')
    
    # Get running services (requires psutil package)
    try:
        import psutil
        services = get_running_services()
    except ImportError:
        print("⚠️  psutil not installed. Installing...")
        os.system('pip install psutil')
        import psutil
        services = get_running_services()
    
    # Print everything to terminal
    print_to_terminal(disk_info, services)

if __name__ == "__main__":
    main()