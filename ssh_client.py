#!/usr/bin/env python3
"""
SSH Client Module
Contains functionality for SSH connections and terminal operations
"""

import socket
import threading
import platform
import subprocess

try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False


class SSHClient:
    """SSH client functionality"""

    def __init__(self):
        self.ssh_available = SSH_AVAILABLE

    def is_available(self):
        """Check if SSH functionality is available"""
        return self.ssh_available

    def create_connection(self, hostname, username, password, port=22, timeout=10):
        """Create SSH connection"""
        if not SSH_AVAILABLE:
            raise Exception("SSH support not available - paramiko not installed")

        try:
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect
            ssh_client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=timeout
            )

            return ssh_client

        except paramiko.AuthenticationException:
            raise Exception("Authentication failed - check username/password")
        except paramiko.SSHException as e:
            raise Exception(f"SSH connection error: {str(e)}")
        except socket.timeout:
            raise Exception("Connection timeout - device may not be reachable")
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")

    def execute_command(self, ssh_client, command, timeout=30):
        """Execute command on SSH connection"""
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)

            # Read output
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')

            return output, error

        except Exception as e:
            raise Exception(f"Command execution error: {str(e)}")

    def close_connection(self, ssh_client):
        """Close SSH connection"""
        try:
            if ssh_client:
                ssh_client.close()
        except Exception:
            pass

    def open_external_ssh(self, ip, username="root"):
        """Try to open external SSH client"""
        try:
            if platform.system().lower() == 'windows':
                # Try to use Windows SSH client
                subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', f'ssh {username}@{ip}'],
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Mac/Linux
                subprocess.Popen(['ssh', f'{username}@{ip}'])

            return True
        except Exception as e:
            raise Exception(f"Could not launch external SSH client: {e}")

    def get_installation_message(self):
        """Get SSH installation instructions"""
        os_name = platform.system().lower()
        
        if os_name == "windows":
            return """SSH SUPPORT NOT AVAILABLE

To use SSH functionality, you need to install the 'paramiko' library.

INSTALLATION INSTRUCTIONS:

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)

2. Install paramiko using pip:
   pip install paramiko

3. Alternative installation methods:
   • Using conda: conda install paramiko
   • Using pip3: pip3 install paramiko

4. Restart the application after installation

ALTERNATIVE SSH OPTIONS:

• Use built-in SSH client:
  - Windows: ssh username@{ip}
  - Mac/Linux: ssh username@{ip}

• Use dedicated SSH clients:
  - PuTTY (Windows)
  - Terminal (Mac/Linux)
  - MobaXterm (Windows)

After installing paramiko, you'll be able to SSH directly from this application."""
        
        elif os_name == "darwin":  # macOS
            return """SSH SUPPORT NOT AVAILABLE

To use SSH functionality, you need to install the 'paramiko' library.

INSTALLATION INSTRUCTIONS FOR macOS:

1. Using Homebrew (Recommended):
   brew install python3
   pip3 install paramiko

2. Using MacPorts:
   sudo port install py-paramiko

3. Using pip directly:
   pip install paramiko

4. Restart the application after installation.

After installation, you'll be able to SSH directly from this application."""
        
        else:  # Linux and others
            return """SSH SUPPORT NOT AVAILABLE

To use SSH functionality, you need to install the 'paramiko' library.

INSTALLATION INSTRUCTIONS FOR LINUX:

• Ubuntu/Debian:
  sudo apt update
  sudo apt install python3-paramiko
  or: pip install paramiko

• CentOS/RHEL/Fedora:
  sudo yum install python3-paramiko     (or: sudo dnf install python3-paramiko)
  or: pip install paramiko

• Arch Linux:
  sudo pacman -S python-paramiko
  or: pip install paramiko

After installation, you'll be able to SSH directly from this application."""
