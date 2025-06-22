#!/usr/bin/env python3

import asyncio
import argparse
from kasa import Discover
import sys
import os
import subprocess
from datetime import datetime

HOSTS_FILE = "/etc/hosts"
BLOCK_ENTRY = "127.0.0.1 twitter.com"

def flush_dns_cache():
    """Flush DNS cache on macOS"""
    try:
        subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True)
        subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True)
        print("DNS cache flushed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to flush DNS cache: {str(e)}", file=sys.stderr)

def block_hosts_entry():
    """Add BLOCK_ENTRY to hosts file and flush DNS cache"""
    try:
        # Read current hosts file
        with open(HOSTS_FILE, 'r') as f:
            lines = f.readlines()
        
        # Check if our entry already exists
        entry_exists = any(BLOCK_ENTRY in line for line in lines)
        
        if not entry_exists:
            # Add the blocking entry
            with open(HOSTS_FILE, 'a') as f:
                f.write(f"\n# Added by kasa_monitor.py at {datetime.now()}\n")
                f.write(f"{BLOCK_ENTRY}\n")
            print(f"Added {BLOCK_ENTRY} to hosts file")
            # Flush DNS cache after adding the entry
            flush_dns_cache()
        else:
            print(f"{BLOCK_ENTRY} already exists in hosts file")
            
    except PermissionError:
        print("Error: Permission denied. This script needs to be run with sudo to modify /etc/hosts", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error updating hosts file: {str(e)}", file=sys.stderr)
        sys.exit(1)

def unblock_hosts_entry():
    """Remove BLOCK_ENTRY from hosts file"""
    try:
        # Read current hosts file
        with open(HOSTS_FILE, 'r') as f:
            lines = f.readlines()
        
        # Check if our entry exists
        entry_exists = any(BLOCK_ENTRY in line for line in lines)
        
        if entry_exists:
            # Remove our entries
            new_lines = [line for line in lines if BLOCK_ENTRY not in line and "# Added by kasa_monitor.py" not in line]
            with open(HOSTS_FILE, 'w') as f:
                f.writelines(new_lines)
            print(f"Removed {BLOCK_ENTRY} from hosts file")
        else:
            print(f"{BLOCK_ENTRY} not found in hosts file")
            
    except PermissionError:
        print("Error: Permission denied. This script needs to be run with sudo to modify /etc/hosts", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error updating hosts file: {str(e)}", file=sys.stderr)
        sys.exit(1)

def update_hosts_file(should_block):
    """Update hosts file based on whether to block or unblock"""
    if should_block:
        block_hosts_entry()
    else:
        unblock_hosts_entry()

async def monitor_plug(ip_address, username, password):
    try:
        # Check if we have root privileges
        if os.geteuid() != 0:
            print("Warning: This script needs root privileges to modify /etc/hosts", file=sys.stderr)
            print("Please run with sudo", file=sys.stderr)
            sys.exit(1)
            
        # Discover the device
        device = await Discover.discover_single(ip_address)
        
        print(f"Connected to device at {ip_address}")
        print("Monitoring device state. Press Ctrl+C to exit.")
        
        # Initial state
        await device.update()
        last_state = device.is_on
        print(f"Initial state: {'ON' if last_state else 'OFF'}")
        
        # Set initial hosts file state
        update_hosts_file(last_state)
        
        # Continuous monitoring
        while True:
            await device.update()
            current_state = device.is_on
            
            # Only print and update hosts when state changes
            if current_state != last_state:
                print(f"Device is now: {'ON' if current_state else 'OFF'}")
                update_hosts_file(current_state)
                last_state = current_state
            
            # Wait for 1 second before next check
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Monitor Kasa Smart Plug state and manage hosts file")
    parser.add_argument("ip_address", help="IP address of the Kasa plug")
    parser.add_argument("username", help="Username for Kasa account")
    parser.add_argument("password", help="Password for Kasa account")
    
    args = parser.parse_args()
    
    # Run the async monitoring function
    asyncio.run(monitor_plug(args.ip_address, args.username, args.password))


if __name__ == "__main__":
    main()
