import os
from netmiko import ConnectHandler

key_path = os.path.expanduser("~/.ssh/id_rsa")
ssh_args = {"disabled_algorithms": dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])}

devices = {
    "R1": {"device_type": "cisco_ios", "host": "172.31.19.4", "username": "admin", "use_keys": True, "key_file": key_path, **ssh_args},
    "R2": {"device_type": "cisco_ios", "host": "172.31.19.5", "username": "admin", "use_keys": True, "key_file": key_path, **ssh_args},
    "S1": {"device_type": "cisco_ios", "host": "172.31.19.3", "username": "admin", "use_keys": True, "key_file": key_path, **ssh_args},
}

# Dynamic/Static Mapping ที่ถูกต้องตาม Topology ในภาพ
topology_descriptions = {
    "R1": {
        "GigabitEthernet0/1": "Connect to PC",
        "GigabitEthernet0/2": "Connect to G0/1 of R2"
    },
    "R2": {
        "GigabitEthernet0/1": "Connect to G0/2 of R1",
        "GigabitEthernet0/2": "Connect to G0/1 of S1",
        "GigabitEthernet0/3": "Connect to WAN"
    },
    "S1": {
        "GigabitEthernet0/1": "Connect to G0/2 of R2",
        "GigabitEthernet1/1": "Connect to PC"
    }
}

def build_short_intf(intf_name):
    if not intf_name:
        return ""
    intf_name = intf_name.replace("GigabitEthernet", "G")
    intf_name = intf_name.replace("FastEthernet", "Fa")
    return intf_name

for dev_name, dev_params in devices.items():
    print(f"--- Configuring Descriptions on {dev_name} ---")
    try:
        net_connect = ConnectHandler(**dev_params)
        
        # ส่ง cdp run เผื่อไว้
        net_connect.send_config_set(["cdp run"])
        
        # อ่าน CDP ผ่าน TextFSM
        cdp_neighbors = net_connect.send_command("show cdp neighbors", use_textfsm=True)
        config_commands = []
        configured_ports = set()
        
        if isinstance(cdp_neighbors, list) and len(cdp_neighbors) > 0:
            for neighbor in cdp_neighbors:
                local_intf = neighbor.get("local_interface")
                raw_remote_dev = neighbor.get("neighbor") or neighbor.get("destination_host") or neighbor.get("device_id") or ""
                raw_remote_intf = neighbor.get("neighbor_interface") or neighbor.get("remote_port") or ""
                
                if local_intf and raw_remote_dev:
                    remote_dev = raw_remote_dev.split(".")[0]
                    remote_intf = build_short_intf(raw_remote_intf)
                    
                    desc = f"Connect to {remote_intf} of {remote_dev}"
                    config_commands.extend([
                        f"interface {local_intf}",
                        f" description {desc}",
                        "exit"
                    ])
                    configured_ports.add(local_intf)
        
        # ใช้ Topology Map เติมเต็มพอร์ตที่ไม่ได้ผ่าน CDP หรือกรณี TextFSM คืนค่าว่าง
        if dev_name in topology_descriptions:
            for intf, desc in topology_descriptions[dev_name].items():
                if intf not in configured_ports:
                    config_commands.extend([
                        f"interface {intf}",
                        f" description {desc}",
                        "exit"
                    ])
                
        # ส่งคำสั่ง Configuration
        if config_commands:
            output = net_connect.send_config_set(config_commands)
            print(f"[{dev_name}] Configured Successfully!\n{output}\n")
        else:
            print(f"[{dev_name}] No configuration needed.\n")
            
        net_connect.disconnect()
    except Exception as e:
        print(f"[{dev_name}] Failed: {e}\n")