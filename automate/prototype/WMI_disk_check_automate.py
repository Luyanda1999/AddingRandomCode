#!/usr/bin/env python3
"""
Remote Disk Checker - No Agents Required
Uses WMI to query Windows machines remotely
"""

import wmi  # pip install wmi
import datetime
import csv
import socket

def check_remote_disk_wmi(computer_name, username=None, password=None):
    """
    Check disk space on remote Windows machine using WMI
    
    Args:
        computer_name: Remote computer name or IP
        username: Domain\Username (if needed)
        password: Password (if needed)
    """
    try:
        # Connect to remote machine
        if username and password:
            connection = wmi.WMI(computer=computer_name, 
                                 user=username, 
                                 password=password)
        else:
            # Uses current credentials (must have admin rights)
            connection = wmi.WMI(computer=computer_name)
        
        results = []
        for disk in connection.Win32_LogicalDisk(DriveType=3):  # Only fixed drives
            free_gb = round(disk.FreeSpace / (1024**3), 2)
            total_gb = round(disk.Size / (1024**3), 2)
            
            results.append({
                'computer': computer_name,
                'drive': disk.DeviceID,
                'total_gb': total_gb,
                'free_gb': free_gb,
                'used_percent': round(((total_gb - free_gb) / total_gb) * 100, 2),
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        return results
    except Exception as e:
        print(f"❌ Failed to connect to {computer_name}: {e}")
        return None

def check_multiple_machines(machines_list):
    """Check disk space on multiple remote machines"""
    all_results = []
    
    for machine in machines_list:
        print(f"🔍 Checking {machine}...")
        results = check_remote_disk_wmi(machine)
        if results:
            all_results.extend(results)
            # Display results
            for disk in results:
                status = "🔴" if disk['used_percent'] > 90 else "🟡" if disk['used_percent'] > 75 else "🟢"
                print(f"  {status} {disk['drive']}: {disk['used_percent']:.1f}% used ({disk['free_gb']} GB free)")
    
    return all_results

if __name__ == "__main__":
    # List of machines to check
    machines = [
        'PC-DESKTOP-01',
        '192.168.1.100',
        'SERVER-FILES'
    ]
    
    results = check_multiple_machines(machines)
    
    # Save to CSV
    if results:
        with open('remote_disk_report.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"✅ Saved data for {len(results)} drives")