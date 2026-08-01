import os
import paramiko
import time

key_file = os.path.expanduser("~/.ssh/id_rsa")

key = paramiko.RSAKey.from_private_key_file(key_file)

# รายการอุปกรณ์ Management IP (Group Y=19)
devices = [
    "172.31.19.1", # R0
    "172.31.19.2", # S0
    "172.31.19.3", # S1
    "172.31.19.4", # R1
    "172.31.19.5", # R2
]

username = "admin"

for ip in devices:
    print(f"Connecting to {ip} via SSH Public Key...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # เชื่อมต่อโดยใช้ Public/Private Key (no password)
        client.connect(
            hostname=ip,
            username=username,
            pkey=key,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )
        
        # ส่งคำสั่งทดสอบ
        stdin, stdout, stderr = client.exec_command("show version | include uptime")
        output = stdout.read().decode()
        print(f"[{ip}] Success:\n{output.strip()}\n")
        
        client.close()
    except Exception as e:
        print(f"[{ip}] Failed: {e}\n")