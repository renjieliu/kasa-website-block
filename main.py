#!/usr/bin/env python3

import asyncio
import argparse
import os
import sys
import subprocess
from kasa import Discover
from datetime import datetime

HOSTS_FILE_PATH = "/etc/hosts"
HOSTS_DELIMITER = "### LAPTOP-BRICK ###"
BLOCKLIST_FILE_PATH = "blocklist"

def _flush_dns_cache():
    try:
        subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True)
        subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error blocking sites: {e}", file=sys.stderr)


def _read_blocklist() -> list[str]:
    with open(BLOCKLIST_FILE_PATH, "r") as f:
        lines = f.readlines()
   
    lines = [line.strip() for line in lines]
    return lines


def _update_hosts_file(should_block: bool, blocklist: list[str]):
    try:
        with open(HOSTS_FILE_PATH, "r") as f:
            # Write contents of hostfile unrelated to blocklist
            lines = f.readlines()
            new_lines = []
            for line in lines:
                if line == HOSTS_DELIMITER or HOSTS_DELIMITER in line:
                    break
                new_lines.append(line.rstrip())
        
        with open(HOSTS_FILE_PATH, 'w') as f:
            # Block URLs in blocklist if needed     
            if should_block:
                print(f"Blocking {len(blocklist)} sites...")
                new_lines.extend([HOSTS_DELIMITER] + blocklist + [HOSTS_DELIMITER])
                            
            # Update hosts file and flush DNS cache to make hosts changes take effect
            f.write('\n'.join(new_lines))
            _flush_dns_cache()

    except Exception as e:
        print(f"Error reading hosts file: {e}", file=sys.stderr)


async def monitor_plug(ip_address):
    device = await Discover.discover_single(ip_address)
    print(f"Connected to device at {ip_address}")
    print("Monitoring device state. Press Ctrl+C to exit.")
    
    # Read blocklist 
    blocklist = _read_blocklist()
    print("Will block these URLs when plug is on: " + '\n'.join(blocklist) + "\n")
    
    # Initial state
    await device.update()
    last_state = device.is_on
    print(f"Initial state: {'ON' if last_state else 'OFF'}")
    _update_hosts_file(last_state, blocklist)
    
    # Continuously monitor
    while True:
        await device.update()
        current_state = device.is_on
        
        # Only print and update hosts when state changes
        if current_state != last_state:
            print(f"Device is now: {'ON' if current_state else 'OFF'}")
            _update_hosts_file(current_state, blocklist)
            last_state = current_state
       
        # Wait before polling again 
        await asyncio.sleep(1)


def main():
    if os.geteuid() != 0:
        print("Warning: This script needs root privileges to modify /etc/hosts", file=sys.stderr)
        print("Please run with sudo", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Monitor Kasa Smart Plug state and manage hosts file")
    parser.add_argument("ip_address", help="IP address of the Kasa plug")
    args = parser.parse_args()
   
    # Run the async monitoring function
    asyncio.run(monitor_plug(args.ip_address))
 
if __name__ == "__main__":
    main()