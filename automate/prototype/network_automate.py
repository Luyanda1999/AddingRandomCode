#!/usr/bin/env python3
"""
Disk Space Checker
Checks available disk space and prints to terminal and CSV file
"""

import shutil
import csv
import datetime
import os
from pathlib import Path

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

def print_to_terminal(disk_info):
    """
    Print disk space information to terminal
    
    Args:
        disk_info (dict): Dictionary containing disk space information
    """
    if disk_info:
        print("\n" + "="*60)
        print(f"DISK SPACE CHECK - {disk_info['timestamp']}")
        print("="*60)
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
        print("="*60 + "\n")

def save_to_csv(disk_info, csv_filename='disk_space_report.csv'):
    """
    Save disk space information to CSV file
    
    Args:
        disk_info (dict): Dictionary containing disk space information
        csv_filename (str): Name of the CSV file
    """
    file_exists = os.path.isfile(csv_filename)
    
    try:
        with open(csv_filename, mode='a', newline='') as csv_file:
            fieldnames = ['timestamp', 'path', 'total_gb', 'used_gb', 'free_gb', 'percent_used']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write the data
            writer.writerow(disk_info)
            
        print(f"✅ Data successfully appended to {csv_filename}")
    except Exception as e:
        print(f"❌ Error writing to CSV: {e}")

def check_multiple_paths(paths):
    """
    Check disk space for multiple paths
    
    Args:
        paths (list): List of paths to check
    """
    all_results = []
    
    for path in paths:
        if os.path.exists(path):
            disk_info = get_disk_space(path)
            if disk_info:
                print_to_terminal(disk_info)
                save_to_csv(disk_info)
                all_results.append(disk_info)
        else:
            print(f"❌ Path does not exist: {path}")
    
    return all_results

def main():
    """Main function to run the disk space checker"""
    
    # Single path check (root directory)
    print("Checking disk space for root directory...")
    disk_info = get_disk_space('/')
    
    if disk_info:
        # Print to terminal
        print_to_terminal(disk_info)
        
        # Save to CSV
        save_to_csv(disk_info)
    else:
        print("Failed to get disk space information")
    
    # Optional: Check multiple paths (uncomment to use)
    # paths_to_check = ['/', '/home', '/var']
    # check_multiple_paths(paths_to_check)

if __name__ == "__main__":
    main()