#!/usr/bin/env python3
"""
Remote Disk Checker - Shows Asterisks When Typing Password
"""

import subprocess
import csv
import datetime
import sys
import time
import os
import platform
import msvcrt  # Windows-specific for keypress handling

def get_password_with_asterisks(prompt="Enter password: "):
    """
    Get password input with asterisks showing for each character typed.
    Works on Windows using msvcrt.
    """
    print(prompt, end='', flush=True)
    password = []
    
    while True:
        # Get a single character without echoing
        char = msvcrt.getch()
        
        # Check if it's a special key (like arrow keys)
        if char == b'\xe0':  # Special key prefix
            msvcrt.getch()  # Consume the next byte
            continue
            
        # Enter key pressed (carriage return or line feed)
        if char in (b'\r', b'\n'):
            print()  # New line after password
            break
            
        # Backspace key
        if char == b'\x08':
            if password:
                password.pop()
                # Erase last asterisk from display
                print('\b \b', end='', flush=True)
            continue
            
        # Any other character (regular key)
        if 32 <= ord(char) <= 126:  # Printable characters only
            password.append(char.decode('utf-8'))
            print('*', end='', flush=True)
    
    return ''.join(password)

def get_admin_credentials():
    """
    Prompt user for administrator credentials with asterisk password.
    Returns (username, password) tuple.
    """
    print("\n" + "="*70)
    print("🔐 ADMIN CREDENTIALS REQUIRED")
    print("="*70)
    print("To access remote computers, you need administrator credentials.")
    print("These can be:")
    print("  - A domain admin account: DOMAIN\\username")
    print("  - A local admin account: COMPUTERNAME\\Administrator")
    print("  - A workgroup admin account: Administrator")
    print("="*70 + "\n")
    
    # Get username (no asterisks needed for username)
    username = input("Enter admin username: ").strip()
    
    # Get password with asterisks
    password = get_password_with_asterisks("Enter admin password: ")
    
    print("\n✅ Credentials received. Testing connection...\n")
    
    return username, password

def get_remote_disk_wmic(computer, username, password):
    """
    Query disk space using WMIC with provided credentials.
    Returns list of dicts or None on failure.
    """
    try:
        # Build WMIC command with credentials
        cmd = [
            'wmic',
            '/node:' + computer,
            '/user:' + username,
            '/password:' + password,
            'path', 'Win32_LogicalDisk',
            'where', 'DriveType=3',
            'get', 'DeviceID,Size,FreeSpace',
            '/format:csv'
        ]
        
        # Execute command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        
        # Check for errors
        if result.returncode != 0:
            error = result.stderr.strip()
            
            if "Access is denied" in error:
                print(f"❌ Access denied on {computer}")
                print("   - Check if the account is in the Administrators group")
                print("   - Verify the password is correct")
                print("   - Try using COMPUTERNAME\\Administrator format")
            elif "RPC server" in error:
                print(f"❌ RPC unavailable on {computer}")
                print("   - Check firewall (WMI rule should be enabled)")
                print("   - Verify the computer is online")
            elif "Invalid parameter" in error:
                print(f"❌ Invalid parameter on {computer}")
                print("   - Check username format (use DOMAIN\\user or COMPUTERNAME\\user)")
            else:
                print(f"❌ Error on {computer}: {error}")
            return None
        
        # Parse CSV output
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            print(f"⚠️  No data returned from {computer}")
            return None
        
        results = []
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) >= 3:
                device = parts[0].strip()
                size_str = parts[1].strip()
                free_str = parts[2].strip()
                
                if not size_str or not free_str or size_str == '0':
                    continue
                
                try:
                    total_gb = round(int(size_str) / (1024**3), 2)
                    free_gb = round(int(free_str) / (1024**3), 2)
                    used_gb = round(total_gb - free_gb, 2)
                    percent = round((used_gb / total_gb) * 100, 2) if total_gb > 0 else 0
                    
                    results.append({
                        'computer': computer,
                        'drive': device,
                        'total_gb': total_gb,
                        'free_gb': free_gb,
                        'used_gb': used_gb,
                        'percent_used': percent,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                except ValueError:
                    continue
        
        return results if results else None
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout connecting to {computer}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error on {computer}: {e}")
        return None

def test_connection(computer, username, password):
    """
    Test if we can connect to the remote computer with given credentials.
    Returns True if successful, False otherwise.
    """
    try:
        # Simple test - just get computer name
        cmd = [
            'wmic',
            '/node:' + computer,
            '/user:' + username,
            '/password:' + password,
            'computersystem',
            'get', 'name',
            '/format:csv'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and "Access" not in result.stderr
        
    except:
        return False

def save_to_csv(results, filename=None):
    """Save results to CSV file with timestamp."""
    if not results:
        return None
    
    if not filename:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"disk_report_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        return filename
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return None

def display_results(results):
    """Display results in a formatted table."""
    if not results:
        print("\n❌ No data to display")
        return
    
    print("\n" + "="*70)
    print("📊 DISK SPACE SUMMARY")
    print("="*70)
    
    # Group by computer
    computers = {}
    for r in results:
        comp = r['computer']
        if comp not in computers:
            computers[comp] = []
        computers[comp].append(r)
    
    for comp, drives in computers.items():
        print(f"\n🖥️  {comp}")
        print("-" * 50)
        for d in drives:
            # Status indicator
            if d['percent_used'] > 90:
                status = "🔴 CRITICAL"
            elif d['percent_used'] > 75:
                status = "🟡 WARNING"
            else:
                status = "🟢 OK"
            
            # Progress bar (visual)
            bar_length = 30
            filled = int(bar_length * d['percent_used'] / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"  {d['drive']}  [{bar}] {d['percent_used']:.1f}%")
            print(f"      Total: {d['total_gb']:>8,.2f} GB")
            print(f"      Used:  {d['used_gb']:>8,.2f} GB")
            print(f"      Free:  {d['free_gb']:>8,.2f} GB")
            print(f"      Status: {status}")
            print()

def main():
    """Main function with credential request."""
    
    # Check if running on Windows
    if platform.system() != 'Windows':
        print("❌ This script requires Windows to use WMIC")
        sys.exit(1)
    
    print("="*70)
    print("💾 REMOTE DISK SPACE MONITOR")
    print("="*70)
    print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Computer: {platform.node()}")
    print("="*70)
    
    # ============================================================
    # EDIT THIS SECTION - Add your computers here
    # ============================================================
    computers = [
        '10.0.1.224',        # ← Replace with your target IP
        'NFRDPFS',
        # Add more computers:
        # '192.168.1.100',
        # 'SRV-FILES',
        # 'PC-ACCOUNTING',
    ]
    # ============================================================
    
    # Check if any computers are specified
    if not computers:
        print("❌ No computers specified. Edit the 'computers' list.")
        sys.exit(1)
    
    print(f"\n📋 Computers to check: {len(computers)}")
    for comp in computers:
        print(f"   • {comp}")
    
    # Get admin credentials with asterisks
    username, password = get_admin_credentials()
    
    # Test connection to first computer
    print(f"🔍 Testing connection to {computers[0]}...")
    if test_connection(computers[0], username, password):
        print("✅ Connection successful!")
    else:
        print("⚠️  Could not connect to first computer.")
        retry = input("\nContinue anyway? (y/n): ").strip().lower()
        if retry != 'y':
            print("❌ Exiting...")
            sys.exit(1)
    
    # Collect data from all computers
    all_results = []
    failed_computers = []
    
    print("\n" + "="*70)
    print("📡 COLLECTING DATA...")
    print("="*70)
    
    for comp in computers:
        print(f"\n🔍 Checking {comp}...")
        data = get_remote_disk_wmic(comp, username, password)
        
        if data:
            all_results.extend(data)
            for d in data:
                status = "🔴" if d['percent_used'] > 90 else "🟡" if d['percent_used'] > 75 else "🟢"
                print(f"  {status} {d['drive']}: {d['percent_used']:.1f}% used ({d['free_gb']} GB free)")
        else:
            failed_computers.append(comp)
            print(f"  ❌ Failed to get data from {comp}")
        
        time.sleep(0.5)  # Be gentle to network
    
    # Display summary
    print("\n" + "="*70)
    print("📊 RESULTS SUMMARY")
    print("="*70)
    
    if all_results:
        # Display formatted results
        display_results(all_results)
        
        # Save to CSV
        csv_file = save_to_csv(all_results)
        if csv_file:
            print(f"\n✅ Report saved to: {csv_file}")
        
        # Show which computers failed
        if failed_computers:
            print(f"\n⚠️  Failed to connect to: {', '.join(failed_computers)}")
    else:
        print("\n❌ No data collected from any computer!")
        print("\nTroubleshooting tips:")
        print("  1. Verify the remote computers are online")
        print("  2. Check firewall (WMI rule must be enabled)")
        print("  3. Confirm the account has admin privileges")
        print("  4. Try using COMPUTERNAME\\Administrator format")
    
    print("\n" + "="*70)
    print("✅ Done")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)