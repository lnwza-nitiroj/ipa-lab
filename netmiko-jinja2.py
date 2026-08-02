import os
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

key_path = os.path.expanduser("~/.ssh/id_rsa")

# พารามิเตอร์สำหรับ Cisco IOS
ssh_extra_args = {
    "disabled_algorithms": dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])
}

# ---------------------------------------------------------
# Data Structure: ข้อมูลของแต่ละอุปกรณ์สำหรับส่งให้ Jinja2
# ---------------------------------------------------------
devices_data = {
    "S1": {
        "connection": {
            "device_type": "cisco_ios",
            "host": "172.31.19.3",
            "username": "admin",
            "use_keys": True,
            "key_file": key_path,
            **ssh_extra_args
        },
        "config_data": {
            "vlans": [
                {"id": 101, "name": "Control-Data"}
            ],
            "interfaces": [
                {"name": "GigabitEthernet0/0", "mode": "access", "access_vlan": 99},
                {"name": "GigabitEthernet0/1", "mode": "access", "access_vlan": 101},
                {"name": "GigabitEthernet1/1", "mode": "access", "access_vlan": 101}
            ],
            "acls": [
                {
                    "name": "MGMT_ONLY",
                    "rules": [
                        {"action": "permit", "source": "172.31.19.0", "wildcard": "0.0.0.15"},
                        {"action": "permit", "source": "10.30.6.0", "wildcard": "0.0.255.255"}
                    ]
                }
            ],
            "vty": {
                "access_list": "MGMT_ONLY",
                "vrf_also": False
            }
        }
    },
    "R1": {
        "connection": {
            "device_type": "cisco_ios",
            "host": "172.31.19.4",
            "username": "admin",
            "use_keys": True,
            "key_file": key_path,
            **ssh_extra_args
        },
        "config_data": {
            "ospf": {
                "process_id": 1,
                "vrf": "control-data",
                "router_id": "1.1.1.1",
                "networks": [
                    {"ip": "172.31.19.16", "wildcard": "0.0.0.15", "area": 0},
                    {"ip": "172.31.19.32", "wildcard": "0.0.0.15", "area": 0}
                ]
            },
            "acls": [
                {
                    "name": "MGMT_ONLY",
                    "rules": [
                        {"action": "permit", "source": "172.31.19.0", "wildcard": "0.0.0.15"},
                        {"action": "permit", "source": "10.30.6.0", "wildcard": "0.0.255.255"}
                    ]
                }
            ],
            "vty": {
                "access_list": "MGMT_ONLY",
                "vrf_also": True
            }
        }
    },
    "R2": {
        "connection": {
            "device_type": "cisco_ios",
            "host": "172.31.19.5",
            "username": "admin",
            "use_keys": True,
            "key_file": key_path,
            **ssh_extra_args
        },
        "config_data": {
            "ospf": {
                "process_id": 1,
                "vrf": "control-data",
                "router_id": "2.2.2.2",
                "networks": [
                    {"ip": "172.31.19.32", "wildcard": "0.0.0.15", "area": 0},
                    {"ip": "172.31.19.48", "wildcard": "0.0.0.15", "area": 0}
                ],
                "default_originate": True
            },
            "static_routes": [
                {"vrf": "control-data", "prefix": "0.0.0.0", "mask": "0.0.0.0", "next_hop": "GigabitEthernet0/3 dhcp"}
            ],
            "interfaces": [
                {"name": "GigabitEthernet0/2", "nat": "inside"},
                {"name": "GigabitEthernet0/3", "description": "NAT Connection", "ip_address": "dhcp", "nat": "outside"}
            ],
            "acls": [
                {
                    "name": "NAT_ACL",
                    "rules": [
                        {"action": "permit", "source": "172.31.19.0", "wildcard": "0.0.0.255"}
                    ]
                },
                {
                    "name": "MGMT_ONLY",
                    "rules": [
                        {"action": "permit", "source": "172.31.19.0", "wildcard": "0.0.0.15"},
                        {"action": "permit", "source": "10.30.6.0", "wildcard": "0.0.255.255"}
                    ]
                }
            ],
            "nat_rule": {
                "acl_name": "NAT_ACL",
                "interface": "GigabitEthernet0/3",
                "vrf": "control-data"
            },
            "vty": {
                "access_list": "MGMT_ONLY",
                "vrf_also": True
            }
        }
    }
}

# ---------------------------------------------------------
# Setup Jinja2 Environment
# ---------------------------------------------------------
env = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True)
template = env.get_template("template.j2")

# ---------------------------------------------------------
# Execution Loop: Render Jinja2 & Send via Netmiko
# ---------------------------------------------------------
for name, dev in devices_data.items():
    print(f"--- Processing {name} ---")
    
    # Render Jinja2 Template ออกมาเป็นคำสั่ง Configuration List
    rendered_config = template.render(dev["config_data"])
    config_commands = [line.strip() for line in rendered_config.splitlines() if line.strip()]
    
    print(f"Connecting to {name}...")
    try:
        net_connect = ConnectHandler(**dev["connection"])
        output = net_connect.send_config_set(config_commands)
        
        print(f"[{name}] Configuration Successful!\n{output}\n")
        net_connect.disconnect()
    except Exception as e:
        print(f"[{name}] Failed: {e}\n")