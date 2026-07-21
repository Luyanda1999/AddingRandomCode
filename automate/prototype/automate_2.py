#!/usr/bin/env python3
"""
Enhanced Disk Space Checker for Multiple Drives (Windows/Linux/Mac)
"""

import shutil
import csv
import datetime
import os
import platform

def get_all_drives():
    """
    Get all available drives based on operating system
    
    Returns:
        list: List of drive paths
    """
    system = platform.system()
    drives = []
    
    if system == 'Windows':
        # Check all drive letters from C to Z
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                drives.append(drive_path)
    else:
        # Linux/Mac - check common mount points
        drives = ['/', '/home', '/var', '/tmp']
        # Filter only existing paths
        drives = [d for d in drives if os.path.exists(d)]
    
    return drives

def get_disk_space(path):
    """Get disk space information for a given path"""
    try:
        usage = shutil.disk_usage(path)
        
        # Convert to appropriate units
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        free_gb = usage.free / (1024**3)
        percent_used = (usage.used / usage.total) * 100
        
        return {
            'path': path,
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2),
            'percent_used': round(percent_used, 2),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'computer_name': platform.node()
        }
    except Exception as e:
        print(f"Error checking disk space for {path}: {e}")
        return None

def print_to_terminal(disk_info):
    """Print disk space information to terminal with formatting"""
    if disk_info:
        print(f"\n📀 Drive: {disk_info['path']}")
        print(f"   Total: {disk_info['total_gb']:>10,.2f} GB")
        print(f"   Used:  {disk_info['used_gb']:>10,.2f} GB")
        print(f"   Free:  {disk_info['free_gb']:>10,.2f} GB")
        print(f"   Usage: {disk_info['percent_used']:>9.1f}%", end=" ")
        
        # Visual indicator
        if disk_info['percent_used'] > 90:
            print("🔴 CRITICAL")
        elif disk_info['percent_used'] > 75:
            print("🟡 WARNING")
        else:
            print("🟢 OK")

def save_to_csv(all_results, csv_filename='disk_space_report.csv'):
    """Save all disk space information to CSV file"""
    try:
        file_exists = os.path.isfile(csv_filename)
        
        with open(csv_filename, mode='a', newline='') as csv_file:
            fieldnames = ['timestamp', 'computer_name', 'path', 'total_gb', 'used_gb', 'free_gb', 'percent_used']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            for result in all_results:
                writer.writerow(result)
        
        print(f"\n✅ Data successfully saved to {csv_filename}")
        return True
    except Exception as e:
        print(f"❌ Error writing to CSV: {e}")
        return False

def main():
    """Main function to check all drives"""
    print("\n" + "="*60)
    print(f"DISK SPACE CHECKER - {platform.node()}")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"OS: {platform.system()} {platform.release()}")
    print("="*60)
    
    # Get all drives
    drives = get_all_drives()
    print(f"\nChecking {len(drives)} drive(s): {', '.join(drives)}")
    
    # Check each drive
    results = []
    for drive in drives:
        disk_info = get_disk_space(drive)
        if disk_info:
            print_to_terminal(disk_info)
            results.append(disk_info)
    
    # Save to CSV
    if results:
        save_to_csv(results)
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        for result in results:
            status = "🔴" if result['percent_used'] > 90 else "🟡" if result['percent_used'] > 75 else "🟢"
            print(f"{status} {result['path']}: {result['percent_used']:.1f}% used ({result['free_gb']:.2f} GB free)")
    else:
        print("\n❌ No valid disk information retrieved")

if __name__ == "__main__":
    main()