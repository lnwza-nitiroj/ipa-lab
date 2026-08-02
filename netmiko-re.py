import os
import re
from netmiko import ConnectHandler

key_path = os.path.expanduser("~/.ssh/id_rsa")

# พารามิเตอร์สำหรับ Cisco IOS
ssh_extra_args = {
    "disabled_algorithms": dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])
}

# รายชื่ออุปกรณ์ R1 และ R2 ตามโจทย์
routers = {
    "R1": {
        "device_type": "cisco_ios",
        "host": "172.31.19.4",
        "username": "admin",
        "use_keys": True,
        "key_file": key_path,
        **ssh_extra_args
    },
    "R2": {
        "device_type": "cisco_ios",
        "host": "172.31.19.5",
        "username": "admin",
        "use_keys": True,
        "key_file": key_path,
        **ssh_extra_args
    }
}

for name, dev in routers.items():
    print(f"=" * 50)
    print(f" Connecting to {name} ({dev['host']})...")
    print(f"=" * 50)
    
    try:
        net_connect = ConnectHandler(**dev)
        
        # 1. ดึงข้อมูล show version และหา Uptime ด้วย Regex
        show_ver_output = net_connect.send_command("show version")
        uptime_match = re.search(r"uptime is (.+)", show_ver_output)
        
        if uptime_match:
            uptime = uptime_match.group(1).strip()
        else:
            uptime = "Unknown"
            
        print(f"⏱️  Router Uptime: {uptime}\n")
        
        # 2. ดึงข้อมูล show ip interface brief และหา Active Interfaces ด้วย Regex
        show_ip_int_output = net_connect.send_command("show ip interface brief")
        
        # Regex แมตช์เฉพาะบรรทัดที่ Interface สถานะเป็น up และ Protocol เป็น up
        active_intf_pattern = r"^(\S+)\s+\S+\s+YES\s+\S+\s+up\s+up"
        active_interfaces = re.findall(active_intf_pattern, show_ip_int_output, re.MULTILINE)
        
        print("🟢 Active Interfaces (Status: UP / Protocol: UP):")
        if active_interfaces:
            for intf in active_interfaces:
                print(f"   - {intf}")
        else:
            print("   No active interfaces found.")
            
        print("\n")
        net_connect.disconnect()
        
    except Exception as e:
        print(f"❌ [{name}] Connection failed: {e}\n")