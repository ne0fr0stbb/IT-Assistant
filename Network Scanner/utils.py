import psutil
import socket

def get_default_gateway():
    gateways = psutil.net_if_addrs()
    for interface, snics in gateways.items():
        for snic in snics:
            if snic.family == socket.AF_INET and '192.168.' in snic.address:
                return snic.address.rsplit('.', 1)[0] + '.1'
    return None

