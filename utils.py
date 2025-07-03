# This module provides utility functions for network operations.
# Contains helper functions used across the NetworkMonitor application.

import psutil
import socket

def get_default_gateway():
    """
    Find the default gateway IP address by examining network interfaces.
    Specifically looks for 192.168.x.x networks and returns the typical gateway (.1).

    Returns:
        str: Gateway IP address (e.g., "192.168.1.1") or None if not found
    """
    # Get all network interface addresses
    gateways = psutil.net_if_addrs()

    # Iterate through all network interfaces
    for interface, snics in gateways.items():
        for snic in snics:
            # Look for IPv4 addresses in the private 192.168.x.x range
            if snic.family == socket.AF_INET and '192.168.' in snic.address:
                # Extract network portion (e.g., "192.168.1") and append ".1" for gateway
                return snic.address.rsplit('.', 1)[0] + '.1'

    # Return None if no suitable gateway found
    return None
