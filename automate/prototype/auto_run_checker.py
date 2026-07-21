import os
import subprocess
import winreg
import sys
import re
from datetime import datetime

class AutoRunChecker:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "startup_items": [],
            "running_services": [],
            "scheduled_tasks": [],
            "running_processes": []
        }
    
    def get_startup_items(self):
        """Check programs that run at startup from registry and startup folder"""
        startup_locations = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
        ]
        
        for hive, path in startup_locations:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        # Skip binary data for StartupApproved keys
                        if isinstance(value, bytes):
                            value = "<binary data>"
                        self.results["startup_items"].append({
                            "name": name,
                            "path": str(value),
                            "location": path,
                            "hive": "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
                        })
                        i += 1
                    except WindowsError:
                        break
                winreg.CloseKey(key)
            except FileNotFoundError:
                pass
            except Exception as e:
                pass
        
        # Check startup folders
        startup_folders = [
            os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup'),
            os.path.join(os.getenv('PROGRAMDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup'),
            os.path.join(os.getenv('ALLUSERSPROFILE'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        ]
        
        for folder in startup_folders:
            if folder and os.path.exists(folder):
                try:
                    for file in os.listdir(folder):
                        if file.lower().endswith(('.exe', '.lnk', '.bat', '.cmd', '.vbs', '.ps1')):
                            self.results["startup_items"].append({
                                "name": file,
                                "path": os.path.join(folder, file),
                                "location": "Startup Folder",
                                "hive": "N/A"
                            })
                except:
                    pass
    
    def get_services(self, status_filter='RUNNING'):
        """Get Windows services using sc command"""
        try:
            # Get all services
            result = subprocess.run(['sc', 'query', 'state=all'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            lines = result.stdout.split('\n')
            current_service = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('SERVICE_NAME:'):
                    if current_service and 'name' in current_service:
                        self._add_service(current_service, status_filter)
                    name = line.split(':', 1)[1].strip()
                    current_service = {'name': name}
                elif ':' in line and current_service:
                    key, value = line.split(':', 1)
                    current_service[key.strip()] = value.strip()
            
            if current_service and 'name' in current_service:
                self._add_service(current_service, status_filter)
                
        except Exception as e:
            pass
    
    def _add_service(self, service, status_filter):
        """Helper to add service if it matches filter"""
        status = service.get('STATE', '')
        # Extract status from "4 RUNNING" format
        status_parts = status.split()
        status_text = ' '.join(status_parts[1:]) if len(status_parts) > 1 else status
        
        if status_filter is None or status_filter.upper() in status_text.upper():
            self.results["running_services"].append({
                "name": service.get('name', 'Unknown'),
                "status": status_text,
                "type": service.get('TYPE', 'Unknown'),
                "win32_exit_code": service.get('WIN32_EXIT_CODE', 'Unknown'),
                "service_type": service.get('SERVICE_TYPE', 'Unknown')
            })
    
    def get_scheduled_tasks(self):
        """Get scheduled tasks using schtasks command"""
        try:
            # Use CSV format for easier parsing
            result = subprocess.run(['schtasks', '/query', '/fo', 'csv', '/v'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                # Parse CSV (handle quoted fields)
                headers = self._parse_csv_line(lines[0].strip())
                
                for i in range(1, len(lines)):
                    if lines[i].strip():
                        values = self._parse_csv_line(lines[i].strip())
                        if len(values) >= len(headers):
                            task_info = dict(zip(headers, values))
                            
                            # Only include enabled/ready tasks
                            status = task_info.get('Status', '').strip('"')
                            if status in ['Ready', 'Running']:
                                self.results["scheduled_tasks"].append({
                                    "name": task_info.get('TaskName', 'Unknown').strip('"'),
                                    "status": status,
                                    "schedule": task_info.get('Schedule', 'N/A').strip('"'),
                                    "last_run": task_info.get('Last Run Time', 'N/A').strip('"'),
                                    "next_run": task_info.get('Next Run Time', 'N/A').strip('"'),
                                    "task_path": task_info.get('Task To Run', 'N/A').strip('"')
                                })
        except Exception as e:
            pass
    
    def _parse_csv_line(self, line):
        """Simple CSV parser for quoted fields"""
        result = []
        current = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                result.append(current.strip())
                current = ""
            else:
                current += char
        
        if current:
            result.append(current.strip())
        
        return result
    
    def get_running_processes(self):
        """Get running processes using tasklist command"""
        try:
            result = subprocess.run(['tasklist', '/v', '/fo', 'csv'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                headers = self._parse_csv_line(lines[0].strip())
                
                for i in range(1, len(lines)):
                    if lines[i].strip():
                        values = self._parse_csv_line(lines[i].strip())
                        if len(values) >= len(headers):
                            proc_info = dict(zip(headers, values))
                            
                            # Filter out system idle processes
                            name = proc_info.get('Image Name', '').strip('"')
                            if name and name.lower() not in ['', 'system idle process']:
                                self.results["running_processes"].append({
                                    "pid": proc_info.get('PID', 'Unknown').strip('"'),
                                    "name": name,
                                    "session": proc_info.get('Session Name', 'N/A').strip('"'),
                                    "session_id": proc_info.get('Session#', 'N/A').strip('"'),
                                    "memory_usage": proc_info.get('Mem Usage', 'N/A').strip('"'),
                                    "status": proc_info.get('Status', 'Unknown').strip('"'),
                                    "user": proc_info.get('User Name', 'N/A').strip('"')
                                })
        except Exception as e:
            pass
    
    def get_wmi_services_alternative(self):
        """Alternative method using wmic if available"""
        try:
            result = subprocess.run(['wmic', 'service', 'where', 'state="running"', 
                                    'get', 'name,displayname,pathname,startmode'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            lines = result.stdout.split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        self.results["running_services"].append({
                            "name": parts[0] if len(parts) > 0 else 'Unknown',
                            "display_name": ' '.join(parts[1:]) if len(parts) > 1 else 'N/A',
                            "status": "RUNNING",
                            "type": "WMI"
                        })
        except:
            pass
    
    def check_suspicious_items(self):
        """Flag potentially suspicious auto-running items"""
        suspicious = []
        suspicious_keywords = ['temp', 'tmp', 'download', 'installer', 'uninstall', 
                               'crypto', 'miner', 'remote', 'helper', 'toolbar',
                               'update', 'updater', 'adobe', 'java', 'flash']
        
        suspicious_extensions = ['.scr', '.vbs', '.js', '.jse', '.ps1']
        
        for item in self.results["startup_items"]:
            path_lower = item['path'].lower()
            name_lower = item['name'].lower()
            
            # Check for suspicious keywords or extensions
            if any(keyword in path_lower or keyword in name_lower for keyword in suspicious_keywords):
                suspicious.append(item)
            elif any(item['name'].lower().endswith(ext) for ext in suspicious_extensions):
                suspicious.append(item)
            elif '.exe' in name_lower and 'temp' in path_lower:
                suspicious.append(item)
        
        return suspicious
    
    def generate_report(self, output_file=None):
        """Generate a detailed report"""
        report = "=" * 80 + "\n"
        report += "AUTO-RUN ANALYSIS REPORT\n"
        report += f"Generated: {self.results['timestamp']}\n"
        report += "=" * 80 + "\n\n"
        
        # Startup Items
        report += f"📁 STARTUP ITEMS ({len(self.results['startup_items'])})\n"
        report += "-" * 80 + "\n"
        if self.results['startup_items']:
            for item in self.results['startup_items']:
                report += f"  • {item['name']}\n"
                report += f"    Path: {item['path']}\n"
                report += f"    Location: {item.get('location', 'Registry')}\n"
                report += f"    Hive: {item.get('hive', 'N/A')}\n\n"
        else:
            report += "  No startup items found.\n\n"
        
        # Running Services
        report += f"\n⚙️  RUNNING SERVICES ({len(self.results['running_services'])})\n"
        report += "-" * 80 + "\n"
        if self.results['running_services']:
            for service in self.results['running_services']:
                report += f"  • {service['name']}\n"
                report += f"    Status: {service['status']}\n"
                report += f"    Type: {service.get('type', 'N/A')}\n\n"
        else:
            report += "  No running services found.\n\n"
        
        # Scheduled Tasks
        report += f"\n📅 SCHEDULED TASKS ({len(self.results['scheduled_tasks'])})\n"
        report += "-" * 80 + "\n"
        if self.results['scheduled_tasks']:
            for task in self.results['scheduled_tasks']:
                report += f"  • {task['name']}\n"
                report += f"    Status: {task.get('status', 'N/A')}\n"
                report += f"    Schedule: {task.get('schedule', 'N/A')}\n"
                report += f"    Last Run: {task.get('last_run', 'N/A')}\n\n"
        else:
            report += "  No scheduled tasks found.\n\n"
        
        # Running Processes (first 50 to keep report manageable)
        report += f"\n🔄 RUNNING PROCESSES ({len(self.results['running_processes'])} total - showing first 50)\n"
        report += "-" * 80 + "\n"
        process_count = 0
        for proc in self.results['running_processes'][:50]:
            report += f"  • {proc['name']} (PID: {proc['pid']})\n"
            report += f"    User: {proc.get('user', 'N/A')}\n"
            report += f"    Memory: {proc.get('memory_usage', 'N/A')}\n\n"
            process_count += 1
        
        if len(self.results['running_processes']) > 50:
            report += f"  ... and {len(self.results['running_processes']) - 50} more processes.\n\n"
        
        # Suspicious Items
        suspicious = self.check_suspicious_items()
        if suspicious:
            report += "\n⚠️  POTENTIALLY SUSPICIOUS ITEMS ⚠️\n"
            report += "-" * 80 + "\n"
            for item in suspicious:
                report += f"  • {item['name']}\n"
                report += f"    Path: {item['path']}\n"
                report += f"    Location: {item.get('location', 'Registry')}\n\n"
        else:
            report += "\n✅ No suspicious items detected.\n"
        
        report += "=" * 80 + "\n"
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"📄 Report saved to: {output_file}")
            except:
                print(f"⚠️  Could not save report to {output_file}")
        
        return report
    
    def save_json(self, output_file):
        """Save results as JSON using only built-in json module"""
        try:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"📄 JSON data saved to: {output_file}")
        except:
            # Fallback to simple text format if json not available
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(str(self.results))
                print(f"📄 Data saved (text format) to: {output_file}")
            except:
                pass

def main():
    print("🔍 Scanning for auto-running items...\n")
    print("⏳ This may take a few moments...\n")
    
    checker = AutoRunChecker()
    
    print("📁 Checking startup items...")
    checker.get_startup_items()
    
    print("⚙️  Checking running services...")
    checker.get_services(status_filter='RUNNING')
    
    print("📅 Checking scheduled tasks...")
    checker.get_scheduled_tasks()
    
    print("🔄 Checking running processes...")
    checker.get_running_processes()
    
    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"auto_run_report_{timestamp}.txt"
    json_file = f"auto_run_report_{timestamp}.json"
    
    report = checker.generate_report(report_file)
    checker.save_json(json_file)
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"  • Startup items: {len(checker.results['startup_items'])}")
    print(f"  • Running services: {len(checker.results['running_services'])}")
    print(f"  • Scheduled tasks: {len(checker.results['scheduled_tasks'])}")
    print(f"  • Running processes: {len(checker.results['running_processes'])}")
    
    suspicious = checker.check_suspicious_items()
    if suspicious:
        print(f"\n⚠️  Found {len(suspicious)} potentially suspicious items - check report for details")
    else:
        print("\n✅ No suspicious items detected")
    
    print(f"\n📄 Full report saved to: {report_file}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please run this script as Administrator for best results")
        
    input("\nPress Enter to exit...")