import os
from netmiko import ConnectHandler

key_path = os.path.expanduser("~/.ssh/id_rsa")

# พารามิเตอร์สำหรับ Cisco IOS รุ่นเก่าเพื่อปิด Strict Key Matching และเพิ่ม Compatibility
ssh_extra_args = {
    "disabled_algorithms": dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])
}

devices = {
    "S1": {
        "device_type": "cisco_ios",
        "host": "172.31.19.3",
        "username": "admin",
        "use_keys": True,
        "key_file": key_path,
        **ssh_extra_args
    },
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
    },
}

# --- 1. คอนฟิก S1 ---
config_S1 = [
    "vlan 101",
    " name Control-Data",
    "exit",
    "interface GigabitEthernet0/0",
    " switchport mode access",
    " switchport access vlan 99",
    " no shutdown",
    "exit",
    "interface GigabitEthernet0/1",
    " switchport mode access",
    " switchport access vlan 101",
    " no shutdown",
    "exit",
    "interface GigabitEthernet1/1",
    " switchport mode access",
    " switchport access vlan 101",
    " no shutdown",
    "exit",
    "ip access-list standard MGMT_ONLY",
    " permit 172.31.19.0 0.0.0.15",
    " permit 10.30.6.0 0.0.255.255",
    "exit",
    "line vty 0 4",
    " access-class MGMT_ONLY in",
    "exit"
]

# --- 2. คอนฟิก R1 (VRF control-data) ---
config_R1 = [
    "router ospf 1 vrf control-data",
    " router-id 1.1.1.1",
    " network 172.31.19.16 0.0.0.15 area 0",
    " network 172.31.19.32 0.0.0.15 area 0",
    "exit",
    "ip access-list standard MGMT_ONLY",
    " permit 172.31.19.0 0.0.0.15",
    " permit 10.30.6.0 0.0.255.255",
    "exit",
    "line vty 0 4",
    " access-class MGMT_ONLY in vrf-also",
    "exit"
]

# --- 3. คอนฟิก R2 (VRF control-data + PAT + Default Route) ---
config_R2 = [
    "router ospf 1 vrf control-data",
    " router-id 2.2.2.2",
    " network 172.31.19.32 0.0.0.15 area 0",
    " network 172.31.19.48 0.0.0.15 area 0",
    " default-information originate always",
    "exit",
    "ip route vrf control-data 0.0.0.0 0.0.0.0 GigabitEthernet0/3 dhcp",
    "interface GigabitEthernet0/3",
    " description NAT Connection",
    " ip address dhcp",
    " ip nat outside",
    " no shutdown",
    "exit",
    "interface GigabitEthernet0/2",
    " ip nat inside",
    "exit",
    "ip access-list standard NAT_ACL",
    " permit 172.31.19.0 0.0.0.255",
    "exit",
    "ip nat inside source list NAT_ACL interface GigabitEthernet0/3 vrf control-data overload",
    "ip access-list standard MGMT_ONLY",
    " permit 172.31.19.0 0.0.0.15",
    " permit 10.30.6.0 0.0.255.255",
    "exit",
    "line vty 0 4",
    " access-class MGMT_ONLY in vrf-also",
    "exit"
]

# รัน Netmiko
for name, dev in devices.items():
    print(f"Connecting and configuring {name}...")
    try:
        net_connect = ConnectHandler(**dev)
        if name == "S1":
            output = net_connect.send_config_set(config_S1)
        elif name == "R1":
            output = net_connect.send_config_set(config_R1)
        elif name == "R2":
            output = net_connect.send_config_set(config_R2)
            
        print(f"[{name}] Success!\n{output}\n")
        net_connect.disconnect()
    except Exception as e:
        print(f"[{name}] Failed: {e}\n")