import os
import pytest
from netmiko import ConnectHandler

key_path = os.path.expanduser("~/.ssh/id_rsa")
ssh_args = {"disabled_algorithms": dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])}

devices = {
    "R1": {
        "device_type": "cisco_ios",
        "host": "172.31.19.4",
        "username": "admin",
        "use_keys": True,
        "key_file": key_path,
        **ssh_args
    },
    "R2": {
        "device_type": "cisco_ios",
        "host": "172.31.19.5",
        "username": "admin",
        "use_keys": True,
        "key_file": key_path,
        **ssh_args
    },
    "S1": {
        "device_type": "cisco_ios",
        "host": "172.31.19.3",
        "username": "admin",
        "use_keys": True,
        "key_file": key_path,
        **ssh_args
    },
}

def get_interface_descriptions(device_params):
    net_connect = ConnectHandler(**device_params)
    parsed_output = net_connect.send_command("show interfaces", use_textfsm=True)
    net_connect.disconnect()
    
    descriptions = {}
    if isinstance(parsed_output, list):
        for intf in parsed_output:
            descriptions[intf["interface"]] = intf.get("description", "")
    return descriptions

def test_r1_descriptions():
    desc = get_interface_descriptions(devices["R1"])
    assert "Connect to PC" in desc.get("GigabitEthernet0/1", "")
    assert "Connect to G0/1 of R2" in desc.get("GigabitEthernet0/2", "")

def test_r2_descriptions():
    desc = get_interface_descriptions(devices["R2"])
    assert "Connect to G0/2 of R1" in desc.get("GigabitEthernet0/1", "")
    assert "Connect to G0/1 of S1" in desc.get("GigabitEthernet0/2", "")
    assert "Connect to WAN" in desc.get("GigabitEthernet0/3", "")

def test_s1_descriptions():
    desc = get_interface_descriptions(devices["S1"])
    assert "Connect to G0/2 of R2" in desc.get("GigabitEthernet0/1", "")
    assert "Connect to PC" in desc.get("GigabitEthernet1/1", "")