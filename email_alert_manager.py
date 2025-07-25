#!/usr/bin/env python3
"""
Email Alert Manager for Network Monitor
Handles threshold-based email alerts with cooldown periods and batching
"""

import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, deque
from typing import Dict, List, Optional
import math

from settings import settings_manager


class EmailAlertManager:
    """Manages email alerts with cooldown, batching, and consecutive failure tracking"""
    
    def __init__(self):
        self.device_failure_counts = defaultdict(int)
        self.last_alert_times = defaultdict(lambda: datetime.min)
        self.alert_queue = deque()
        self.batch_timer = None
        self.lock = threading.Lock()
        
    def check_and_send_alert(self, ip: str, latency: float, status: str, device_info: dict = None):
        """
        Check if alert conditions are met and send email if necessary
        
        Args:
            ip: Device IP address
            latency: Current latency in milliseconds
            status: Device status ('up' or 'down')
            device_info: Optional device information (hostname, manufacturer, etc.)
        """
        alert_settings = settings_manager.settings.alerts
        
        # Check if email notifications are enabled
        if not alert_settings.email_notifications:
            print(f"[DEBUG] Email notifications disabled, skipping alert for {ip}")
            return
            
        # Check if we have recipients configured
        if not alert_settings.email_recipient_list:
            print(f"[DEBUG] No email recipients configured, skipping alert for {ip}")
            return
            
        # Check if email configuration is complete
        if not self._is_email_config_complete(alert_settings):
            print(f"[DEBUG] Email configuration incomplete, skipping alert for {ip}")
            return
            
        with self.lock:
            current_time = datetime.now()
            
            # Check if we're in cooldown period for this device
            if self._is_in_cooldown(ip, current_time):
                print(f"[DEBUG] Cooldown active for {ip}, skipping alert")
                return
                
            # Determine if threshold is exceeded
            threshold_exceeded = self._check_thresholds(ip, latency, status, alert_settings)
            
            if threshold_exceeded:
                # Check consecutive failures requirement
                if self._check_consecutive_failures(ip, status, alert_settings):
                    alert_data = {
                        'ip': ip,
                        'latency': latency,
                        'status': status,
                        'timestamp': current_time,
                        'device_info': device_info or {}
                    }
                    
                    if alert_settings.email_batch_alerts:
                        self._queue_alert(alert_data)
                    else:
                        self._send_immediate_alert(alert_data)
                        
                    # Update last alert time
                    self.last_alert_times[ip] = current_time
            else:
                # Reset failure count if device is working normally
                if status == 'up' and not math.isnan(latency) and latency <= alert_settings.email_threshold_ms:
                    self.device_failure_counts[ip] = 0
    
    def _is_email_config_complete(self, alert_settings) -> bool:
        """Check if email configuration is complete"""
        required_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_address']
        return all(getattr(alert_settings, field, None) for field in required_fields)

    def _is_in_cooldown(self, ip: str, current_time: datetime) -> bool:
        """Check if device is in cooldown period"""
        alert_settings = settings_manager.settings.alerts
        cooldown_minutes = alert_settings.email_cooldown_minutes
        
        last_alert = self.last_alert_times[ip]
        cooldown_period = timedelta(minutes=cooldown_minutes)
        
        return current_time - last_alert < cooldown_period
    
    def _check_thresholds(self, ip: str, latency: float, status: str, alert_settings) -> bool:
        """Check if alert thresholds are exceeded"""
        # Check if device is down
        if status == 'down':
            return alert_settings.alert_types.get('device_down', True)
        
        # Check latency threshold
        if not math.isnan(latency) and latency > alert_settings.email_threshold_ms:
            return alert_settings.alert_types.get('high_latency', True)
            
        return False
    
    def _check_consecutive_failures(self, ip: str, status: str, alert_settings) -> bool:
        """Check consecutive failures requirement"""
        consecutive_failures_required = alert_settings.email_consecutive_failures
        
        # Track failures for both down and high latency conditions
        if status == 'down':
            self.device_failure_counts[ip] += 1
            print(f"[DEBUG] Device {ip} down count: {self.device_failure_counts[ip]}/{consecutive_failures_required}")
            return self.device_failure_counts[ip] >= consecutive_failures_required
        else:
            # For 'up' status, increment counter since threshold was already verified
            # in check_and_send_alert before calling this method
            self.device_failure_counts[ip] += 1
            print(f"[DEBUG] Device {ip} high latency count: {self.device_failure_counts[ip]}/{consecutive_failures_required}")
            return self.device_failure_counts[ip] >= consecutive_failures_required
    
    def _queue_alert(self, alert_data: dict):
        """Queue alert for batch processing"""
        self.alert_queue.append(alert_data)
        
        # Start batch timer if not already running
        if self.batch_timer is None:
            alert_settings = settings_manager.settings.alerts
            batch_interval = alert_settings.email_batch_interval_minutes * 60  # Convert to seconds
            
            self.batch_timer = threading.Timer(batch_interval, self._process_batch_alerts)
            self.batch_timer.start()
    
    def _process_batch_alerts(self):
        """Process queued alerts as a batch"""
        with self.lock:
            if not self.alert_queue:
                self.batch_timer = None
                return
                
            # Group alerts by device
            device_alerts = defaultdict(list)
            while self.alert_queue:
                alert = self.alert_queue.popleft()
                device_alerts[alert['ip']].append(alert)
            
            # Send batch email
            self._send_batch_alert(device_alerts)
            
            # Reset batch timer
            self.batch_timer = None
    
    def _send_immediate_alert(self, alert_data: dict):
        """Send immediate individual alert"""
        threading.Thread(target=self._send_alert_email, args=(alert_data,), daemon=True).start()
    
    def _send_batch_alert(self, device_alerts: Dict[str, List[dict]]):
        """Send batch alert email"""
        threading.Thread(target=self._send_batch_email, args=(device_alerts,), daemon=True).start()
    
    def _send_alert_email(self, alert_data: dict):
        print(f"[DEBUG] _send_alert_email thread started for {alert_data.get('ip')}")
        try:
            alert_settings = settings_manager.settings.alerts
            recipients = alert_settings.email_recipient_list
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = alert_settings.from_address
            msg['To'] = ', '.join(recipients)
            
            # Determine alert type
            if alert_data['status'] == 'down':
                alert_type = 'Device Down'
            else:
                alert_type = 'High Latency'
            
            msg['Subject'] = alert_settings.email_subject_template.format(alert_type=alert_type)
            
            # Create email body
            body = self._create_alert_body(alert_data, alert_type)
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            self._send_email(msg, alert_settings, recipients)

        except Exception as e:
            print(f"Failed to send alert email: {str(e)}")
    
    def _send_batch_email(self, device_alerts: Dict[str, List[dict]]):
        """Send batch alert email"""
        try:
            alert_settings = settings_manager.settings.alerts
            recipients = alert_settings.email_recipient_list
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = alert_settings.from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = alert_settings.email_subject_template.format(alert_type='Batch Alert')
            
            # Create batch email body
            body = self._create_batch_body(device_alerts)
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            self._send_email(msg, alert_settings, recipients)

        except Exception as e:
            print(f"Failed to send batch alert email: {str(e)}")
    
    def _create_alert_body(self, alert_data: dict, alert_type: str) -> str:
        """Create individual alert email body"""
        device_info = alert_data.get('device_info', {})
        timestamp = alert_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        body = f"""
Network Monitor Alert - {alert_type}

Device Information:
- IP Address: {alert_data['ip']}
- Hostname: {device_info.get('hostname', 'Unknown')}
- Manufacturer: {device_info.get('manufacturer', 'Unknown')}
- Status: {alert_data['status']}
- Latency: {alert_data['latency']:.2f}ms
- Alert Time: {timestamp}

Alert Details:
"""
        
        if alert_data['status'] == 'down':
            body += "- Device is not responding to ping requests\n"
        else:
            alert_settings = settings_manager.settings.alerts
            body += f"- Latency ({alert_data['latency']:.2f}ms) exceeds threshold ({alert_settings.email_threshold_ms}ms)\n"
        
        body += f"""
Configuration:
- Email Threshold: {settings_manager.settings.alerts.email_threshold_ms}ms
- Consecutive Failures Required: {settings_manager.settings.alerts.email_consecutive_failures}
- Cooldown Period: {settings_manager.settings.alerts.email_cooldown_minutes} minutes

This alert was generated by Network Monitor.
"""
        
        return body
    
    def _create_batch_body(self, device_alerts: Dict[str, List[dict]]) -> str:
        """Create batch alert email body"""
        alert_settings = settings_manager.settings.alerts
        batch_interval = alert_settings.email_batch_interval_minutes
        
        body = f"""
Network Monitor - Batch Alert Report

This batch contains alerts collected over the last {batch_interval} minutes.

Alert Summary:
"""
        
        total_alerts = 0
        for ip, alerts in device_alerts.items():
            total_alerts += len(alerts)
            latest_alert = max(alerts, key=lambda x: x['timestamp'])
            device_info = latest_alert.get('device_info', {})
            
            body += f"""
Device: {ip} ({device_info.get('hostname', 'Unknown')})
- Manufacturer: {device_info.get('manufacturer', 'Unknown')}
- Alert Count: {len(alerts)}
- Latest Status: {latest_alert['status']}
- Latest Latency: {latest_alert['latency']:.2f}ms
- Last Alert: {latest_alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        body += f"""
Total Alerts: {total_alerts}
Batch Interval: {batch_interval} minutes

Configuration:
- Email Threshold: {alert_settings.email_threshold_ms}ms
- Consecutive Failures Required: {alert_settings.email_consecutive_failures}
- Cooldown Period: {alert_settings.email_cooldown_minutes} minutes

This batch alert was generated by Network Monitor.
"""
        
        return body
    
    def _send_email(self, msg: MIMEMultipart, alert_settings, recipients: List[str]):
        print(f"[DEBUG] _send_email called for recipients: {recipients}")
        smtp_server = None
        try:
            # Create SMTP connection
            smtp_server = smtplib.SMTP(alert_settings.smtp_server, alert_settings.smtp_port, timeout=30)
            smtp_server.ehlo()
            
            # Enable TLS if configured
            if alert_settings.smtp_tls:
                smtp_server.starttls()
                smtp_server.ehlo()
            
            # Login
            smtp_server.login(alert_settings.smtp_username, alert_settings.smtp_password)

            # Send email
            text = msg.as_string()
            smtp_server.sendmail(alert_settings.from_address, recipients, text)

            print(f"Alert email sent to {len(recipients)} recipients")
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            raise
        finally:
            if smtp_server:
                try:
                    smtp_server.quit()
                except:
                    pass
    
    def send_test_report(self):
        """Send periodic monitoring report"""
        alert_settings = settings_manager.settings.alerts
        
        if not alert_settings.email_send_reports:
            return
            
        if not alert_settings.email_recipient_list:
            return
            
        if not self._is_email_config_complete(alert_settings):
            return
            
        # Create report (this would be expanded to include monitoring statistics)
        threading.Thread(target=self._send_report_email, daemon=True).start()
    
    def _send_report_email(self):
        """Send monitoring report email"""
        try:
            alert_settings = settings_manager.settings.alerts
            recipients = alert_settings.email_recipient_list
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = alert_settings.from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = alert_settings.email_subject_template.format(alert_type='Monitoring Report')
            
            # Create report body
            body = self._create_report_body()
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            self._send_email(msg, alert_settings, recipients)

        except Exception as e:
            print(f"Failed to send report email: {str(e)}")
    
    def _create_report_body(self) -> str:
        """Create monitoring report email body"""
        current_time = datetime.now()
        report_interval = settings_manager.settings.alerts.email_report_interval_hours
        
        body = f"""
Network Monitor - Monitoring Report

Report Generated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Report Interval: {report_interval} hours

Alert Summary:
- Total devices monitored: {len(self.device_failure_counts)}
- Devices with recent failures: {sum(1 for count in self.device_failure_counts.values() if count > 0)}
- Recent alerts sent: {len(self.last_alert_times)}

Configuration:
- Email Threshold: {settings_manager.settings.alerts.email_threshold_ms}ms
- Consecutive Failures Required: {settings_manager.settings.alerts.email_consecutive_failures}
- Cooldown Period: {settings_manager.settings.alerts.email_cooldown_minutes} minutes
- Batch Alerts: {'Enabled' if settings_manager.settings.alerts.email_batch_alerts else 'Disabled'}

This report was generated automatically by Network Monitor.
"""
        
        return body
    
    def cleanup(self):
        """Clean up resources"""
        with self.lock:
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None
            
            self.alert_queue.clear()
            self.device_failure_counts.clear()
            self.last_alert_times.clear()


# Global email alert manager instance
email_alert_manager = EmailAlertManager()
