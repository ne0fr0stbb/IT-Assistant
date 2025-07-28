#!/usr/bin/env python3
"""
Nmap Module
Contains functionality for running Nmap scans
"""

import subprocess
import platform


class NmapRunner:
    """Nmap scanning functionality"""

    def run_nmap(self, ip, args):
        """Run nmap scan"""
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(
                    ['nmap'] + args + [ip],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    ['nmap'] + args + [ip],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            return result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            return "Nmap scan timed out"
        except FileNotFoundError:
            return "Nmap not found"
        except Exception as e:
            return f"Error running nmap: {e}"

