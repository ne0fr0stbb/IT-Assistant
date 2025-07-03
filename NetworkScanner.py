# This module provides network scanning functionality using Scapy's ARP scanning.
# It discovers active devices on a network and retrieves basic information about them.
from scapy.layers.l2 import ARP, Ether, srp
import socket
import psutil
import logging
import time

# Configure logging to display informational messages with timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_default_gateway():
    """
    Find the default gateway IP address by examining network interfaces.
    Returns the gateway IP for 192.168.x.x networks, or None if not found.
    """
    gateways = psutil.net_if_addrs()
    for interface, snics in gateways.items():
        for snic in snics:
            # Look for IPv4 addresses in the 192.168.x.x range
            if snic.family == socket.AF_INET and '192.168.' in snic.address:
                # Extract network portion and append .1 for typical gateway
                return snic.address.rsplit('.', 1)[0] + '.1'
    return None


def scan_network(ip_range):
    """
    Perform ARP scan on the specified IP range to discover active devices.

    Args:
        ip_range: IP range in CIDR notation (e.g., "192.168.1.0/24")

    Returns:
        List of dictionaries containing device information (ip, mac, response_time)
    """
    # Create ARP request packet for broadcast discovery
    arp = ARP(pdst=ip_range)  # ARP request for destination network
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Ethernet broadcast frame
    packet = ether / arp  # Combine Ethernet and ARP layers

    # Send the packet and receive responses
    logging.info("Sending ARP requests...")
    start_time = time.time()
    result = srp(packet, timeout=4, verbose=0)[0]  # Send/receive with 4s timeout
    end_time = time.time()

    # Extract active IPs, MAC addresses, and calculate response time
    devices = []
    for _, received in result:
        ip = received.psrc  # Source IP from ARP reply
        mac = received.hwsrc  # Source MAC from ARP reply
        response_time = end_time - start_time  # Total scan time
        devices.append({'ip': ip, 'mac': mac, 'response_time': response_time})

    # Log scan results
    if devices:
        logging.info(f"Found {len(devices)} devices.")
    else:
        logging.info("No devices found.")

    return devices


if __name__ == "__main__":
    # Main execution block for standalone script usage
    default_gateway = get_default_gateway()
    if not default_gateway:
        logging.error("Could not determine the default gateway.")
    else:
        ip_range = f"{default_gateway}/23"  # /23 subnet (512 addresses)
        logging.info(f"Scanning network: {ip_range}")
        active_devices = scan_network(ip_range)
        if active_devices:
            logging.info("Active devices found:")
            for device in active_devices:
                logging.info(
                    f"IP: {device['ip']}, MAC: {device['mac']}, Response Time: {device['response_time']:.2f} seconds")
        else:
            logging.info("No active devices found.")