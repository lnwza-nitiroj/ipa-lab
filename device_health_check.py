import os
import re
from netmiko import ConnectHandler

# ตำแหน่ง SSH Private Key
key_path = os.path.expanduser("~/.ssh/id_rsa")

# ตั้งค่า SSH สำหรับ Cisco IOS
ssh_extra_args = {
    "disabled_algorithms": {
        "pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]
    }
}

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

def get_uptime(output):
    """Extract router uptime from show version output."""

    uptime_match = re.search(
        r"uptime is (.+)",
        output,
        re.IGNORECASE
    )

    if uptime_match:
        return uptime_match.group(1).strip()

    return "Unknown"


def check_interface_status(output):
    """Count UP/UP and DOWN/DOWN interfaces."""

    up_interfaces = []
    down_interfaces = []

    for line in output.splitlines():
        if (
            not line.strip()
            or line.startswith("Interface")
        ):
            continue

        columns = line.split()
        if len(columns) < 6:
            continue

        interface_name = columns[0]
        status = columns[-2].lower()
        protocol = columns[-1].lower()

        if status == "up" and protocol == "up":
            up_interfaces.append(interface_name)

        elif status == "down" and protocol == "down":
            down_interfaces.append(interface_name)

    return up_interfaces, down_interfaces


def get_health_status(up_count, down_count):
    """Determine the overall health status."""

    if up_count == 0:
        return "CRITICAL"

    if down_count > 0:
        return "WARNING"

    return "HEALTHY"


def check_device(name, device):
    print("=" * 55)
    print(f"Checking {name} ({device['host']})")
    print("=" * 55)

    try:
        connection = ConnectHandler(**device)
        show_version = connection.send_command(
            "show version"
        )

        uptime = get_uptime(show_version)
        show_interfaces = connection.send_command(
            "show ip interface brief"
        )

        up_interfaces, down_interfaces = (
            check_interface_status(show_interfaces)
        )

        up_count = len(up_interfaces)
        down_count = len(down_interfaces)

        health_status = get_health_status(
            up_count,
            down_count
        )

        print(f"Device: {name}")
        print(f"Uptime: {uptime}")
        print(f"UP/UP Interfaces: {up_count}")
        print(f"DOWN/DOWN Interfaces: {down_count}")
        print(f"Overall Status: {health_status}")

        print("\nActive Interfaces:")

        if up_interfaces:
            for interface in up_interfaces:
                print(f"  [UP] {interface}")
        else:
            print("  No active interfaces found.")

        print("\nInactive Interfaces:")

        if down_interfaces:
            for interface in down_interfaces:
                print(f"  [DOWN] {interface}")
        else:
            print("  No DOWN/DOWN interfaces found.")

        connection.disconnect()

        return {
            "name": name,
            "status": health_status,
            "up_count": up_count,
            "down_count": down_count
        }

    except Exception as error:

        print(
            f"Connection failed: {error}"
        )

        return {
            "name": name,
            "status": "UNREACHABLE",
            "up_count": 0,
            "down_count": 0
        }


def print_summary(results):
    """Display the health summary of all devices."""

    print("\n")
    print("=" * 55)
    print("NETWORK HEALTH SUMMARY")
    print("=" * 55)

    for result in results:

        print(
            f"{result['name']}: "
            f"{result['status']} | "
            f"UP: {result['up_count']} | "
            f"DOWN: {result['down_count']}"
        )

def main():
    results = []
    for name, device in routers.items():

        result = check_device(
            name,
            device
        )
        results.append(result)
    print_summary(results)

if __name__ == "__main__":
    main()