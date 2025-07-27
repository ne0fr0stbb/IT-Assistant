#!/usr/bin/env python3
"""
Email Testing Utility for Network Monitor
Provides functionality to test and validate email configuration
"""

import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import threading
import time


class EmailTester:
    """Email configuration testing utility"""
    
    def __init__(self):
        self.test_in_progress = False
        self.test_results = []
        
    def test_email_configuration(self, email_config: Dict, recipients: List[str], callback=None) -> Dict:
        """
        Test email configuration with detailed validation
        
        Args:
            email_config: Email configuration dictionary
            recipients: List of recipient email addresses
            callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with test results
        """
        if self.test_in_progress:
            return {"success": False, "error": "Test already in progress"}
            
        self.test_in_progress = True
        self.test_results = []
        
        try:
            # Start test in separate thread to prevent UI blocking
            thread = threading.Thread(
                target=self._run_email_test,
                args=(email_config, recipients, callback)
            )
            thread.daemon = True
            thread.start()
            
            return {"success": True, "message": "Email test started"}
            
        except Exception as e:
            self.test_in_progress = False
            return {"success": False, "error": f"Failed to start test: {str(e)}"}
    
    def _run_email_test(self, email_config: Dict, recipients: List[str], callback=None):
        """Run the actual email test in a separate thread"""
        results = {
            "success": False,
            "tests": [],
            "overall_status": "Failed",
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        try:
            # Test 1: Validate configuration
            if callback:
                callback("Validating email configuration...")
            config_result = self._validate_configuration(email_config)
            results["tests"].append(config_result)
            
            if not config_result["success"]:
                results["overall_status"] = "Configuration Invalid"
                return self._finish_test(results, callback)
            
            # Test 2: DNS and connectivity
            if callback:
                callback("Testing DNS resolution and connectivity...")
            dns_result = self._test_dns_and_connectivity(email_config["smtp_server"], email_config["smtp_port"])
            results["tests"].append(dns_result)
            
            if not dns_result["success"]:
                results["overall_status"] = "Connection Failed"
                return self._finish_test(results, callback)
            
            # Test 3: SMTP connection
            if callback:
                callback("Establishing SMTP connection...")
            smtp_result = self._test_smtp_connection(email_config)
            results["tests"].append(smtp_result)
            
            if not smtp_result["success"]:
                results["overall_status"] = "SMTP Connection Failed"
                return self._finish_test(results, callback)
            
            # Test 4: Authentication
            if callback:
                callback("Testing SMTP authentication...")
            auth_result = self._test_smtp_authentication(email_config)
            results["tests"].append(auth_result)
            
            if not auth_result["success"]:
                results["overall_status"] = "Authentication Failed"
                return self._finish_test(results, callback)
            
            # Test 5: Send test email
            if callback:
                callback("Sending test email...")
            send_result = self._send_test_email(email_config, recipients)
            results["tests"].append(send_result)
            
            if send_result["success"]:
                results["success"] = True
                results["overall_status"] = "All Tests Passed"
            else:
                results["overall_status"] = "Send Failed"
            
        except Exception as e:
            results["tests"].append({
                "test_name": "Unexpected Error",
                "success": False,
                "error": str(e),
                "details": "An unexpected error occurred during testing"
            })
            results["overall_status"] = "Test Error"
        
        finally:
            self._finish_test(results, callback)
    
    def _finish_test(self, results: Dict, callback=None):
        """Finish the test and update results"""
        results["end_time"] = datetime.now().isoformat()
        self.test_results = results
        self.test_in_progress = False
        
        if callback:
            callback("Test completed", results)
    
    def _validate_configuration(self, config: Dict) -> Dict:
        """Validate email configuration parameters"""
        test_result = {
            "test_name": "Configuration Validation",
            "success": True,
            "details": [],
            "warnings": []
        }
        
        # Required fields
        required_fields = ["smtp_server", "smtp_port", "username", "password", "from_address"]
        missing_fields = []
        
        for field in required_fields:
            if not config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            test_result["success"] = False
            test_result["error"] = f"Missing required fields: {', '.join(missing_fields)}"
            return test_result
        
        # Validate SMTP server format
        smtp_server = config["smtp_server"]
        if not smtp_server or len(smtp_server) < 3:
            test_result["success"] = False
            test_result["error"] = "Invalid SMTP server address"
            return test_result
        
        # Validate port
        try:
            port = int(config["smtp_port"])
            if port < 1 or port > 65535:
                raise ValueError("Port out of range")
        except (ValueError, TypeError):
            test_result["success"] = False
            test_result["error"] = "Invalid SMTP port"
            return test_result
        
        # Validate email format
        from_address = config["from_address"]
        if "@" not in from_address or "." not in from_address:
            test_result["success"] = False
            test_result["error"] = "Invalid from_address email format"
            return test_result
        
        # Check for common security configurations
        common_ports = {
            25: "SMTP (unencrypted)",
            587: "SMTP with STARTTLS",
            465: "SMTP with SSL/TLS"
        }
        
        if port in common_ports:
            test_result["details"].append(f"Port {port}: {common_ports[port]}")
        
        # Warn about security settings
        if not config.get("use_tls") and port == 587:
            test_result["warnings"].append("TLS is recommended for port 587")
        
        if not config.get("use_ssl") and port == 465:
            test_result["warnings"].append("SSL is recommended for port 465")
        
        test_result["details"].append("All required configuration fields are present")
        return test_result
    
    def _test_dns_and_connectivity(self, smtp_server: str, smtp_port: int) -> Dict:
        """Test DNS resolution and basic connectivity"""
        test_result = {
            "test_name": "DNS and Connectivity",
            "success": False,
            "details": []
        }
        
        try:
            # Test DNS resolution
            import socket
            ip_address = socket.gethostbyname(smtp_server)
            test_result["details"].append(f"DNS resolved {smtp_server} to {ip_address}")
            
            # Test basic connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            result = sock.connect_ex((smtp_server, smtp_port))
            sock.close()
            
            if result == 0:
                test_result["success"] = True
                test_result["details"].append(f"Successfully connected to {smtp_server}:{smtp_port}")
            else:
                test_result["error"] = f"Cannot connect to {smtp_server}:{smtp_port}"
                test_result["details"].append(f"Connection failed with error code: {result}")
            
        except socket.gaierror as e:
            test_result["error"] = f"DNS resolution failed: {str(e)}"
        except Exception as e:
            test_result["error"] = f"Connectivity test failed: {str(e)}"
        
        return test_result
    
    def _test_smtp_connection(self, config: Dict) -> Dict:
        """Test SMTP connection and protocol support"""
        test_result = {
            "test_name": "SMTP Connection",
            "success": False,
            "details": []
        }
        
        smtp_server = None
        try:
            smtp_server = smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=30)
            test_result["details"].append(f"SMTP connection established")
            
            # Get server capabilities
            smtp_server.ehlo()
            
            # Check for STARTTLS support
            if smtp_server.has_extn('STARTTLS'):
                test_result["details"].append("Server supports STARTTLS")
                
                if config.get("use_tls", False):
                    smtp_server.starttls()
                    test_result["details"].append("STARTTLS enabled")
                    smtp_server.ehlo()  # Re-identify after STARTTLS
            
            # Check authentication methods
            if smtp_server.has_extn('AUTH'):
                auth_methods = smtp_server.esmtp_features.get('auth', '').split()
                test_result["details"].append(f"Supported auth methods: {', '.join(auth_methods)}")
            
            test_result["success"] = True
            
        except smtplib.SMTPServerDisconnected as e:
            test_result["error"] = f"SMTP server disconnected: {str(e)}"
        except smtplib.SMTPConnectError as e:
            test_result["error"] = f"SMTP connection error: {str(e)}"
        except Exception as e:
            test_result["error"] = f"SMTP connection failed: {str(e)}"
        
        finally:
            if smtp_server:
                try:
                    smtp_server.quit()
                except:
                    pass
        
        return test_result
    
    def _test_smtp_authentication(self, config: Dict) -> Dict:
        """Test SMTP authentication"""
        test_result = {
            "test_name": "SMTP Authentication",
            "success": False,
            "details": []
        }
        
        smtp_server = None
        try:
            smtp_server = smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=30)
            smtp_server.ehlo()
            
            # Enable TLS if configured
            if config.get("use_tls", False) and smtp_server.has_extn('STARTTLS'):
                smtp_server.starttls()
                smtp_server.ehlo()
            
            # Test authentication
            smtp_server.login(config["username"], config["password"])
            
            test_result["success"] = True
            test_result["details"].append("SMTP authentication successful")
            
        except smtplib.SMTPAuthenticationError as e:
            test_result["error"] = f"Authentication failed: {str(e)}"
            test_result["details"].append("Check username and password")
        except smtplib.SMTPException as e:
            test_result["error"] = f"SMTP error during authentication: {str(e)}"
        except Exception as e:
            test_result["error"] = f"Authentication test failed: {str(e)}"
        
        finally:
            if smtp_server:
                try:
                    smtp_server.quit()
                except:
                    pass
        
        return test_result
    
    def _send_test_email(self, config: Dict, recipients: List[str]) -> Dict:
        """Send a test email to validate full functionality"""
        test_result = {
            "test_name": "Send Test Email",
            "success": False,
            "details": []
        }
        
        if not recipients:
            test_result["error"] = "No recipients specified"
            return test_result
        
        smtp_server = None
        try:
            # Create test message
            msg = MIMEMultipart()
            msg["From"] = config["from_address"]
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = "Network Monitor - Email Configuration Test"
            
            # Create email body
            body = f"""
This is a test email from Network Monitor to verify email configuration.

Test Details:
- SMTP Server: {config['smtp_server']}:{config['smtp_port']}
- From: {config['from_address']}
- Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Recipients: {', '.join(recipients)}

If you receive this email, your email configuration is working correctly.

---
Network Monitor Email Test
"""
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            smtp_server = smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=30)
            smtp_server.ehlo()
            
            if config.get("use_tls", False) and smtp_server.has_extn('STARTTLS'):
                smtp_server.starttls()
                smtp_server.ehlo()
            
            smtp_server.login(config["username"], config["password"])
            
            text = msg.as_string()
            smtp_server.sendmail(config["from_address"], recipients, text)
            
            test_result["success"] = True
            test_result["details"].append(f"Test email sent to {len(recipients)} recipient(s)")
            test_result["details"].append(f"Recipients: {', '.join(recipients)}")
            
        except smtplib.SMTPRecipientsRefused as e:
            test_result["error"] = f"Recipients refused: {str(e)}"
        except smtplib.SMTPDataError as e:
            test_result["error"] = f"SMTP data error: {str(e)}"
        except smtplib.SMTPException as e:
            test_result["error"] = f"SMTP error: {str(e)}"
        except Exception as e:
            test_result["error"] = f"Failed to send test email: {str(e)}"
        
        finally:
            if smtp_server:
                try:
                    smtp_server.quit()
                except:
                    pass
        
        return test_result
    
    def get_test_results(self) -> Dict:
        """Get the results of the last test"""
        return self.test_results
    
    def is_test_in_progress(self) -> bool:
        """Check if a test is currently in progress"""
        return self.test_in_progress
    
    def cancel_test(self):
        """Cancel the current test (if possible)"""
        # Note: This is a basic implementation. In a production environment,
        # you might want to implement proper thread cancellation
        self.test_in_progress = False


# Global email tester instance
email_tester = EmailTester()
