#!/usr/bin/env python3
"""
Speed Test Module
Contains functionality for running Internet speed tests
"""

try:
    import speedtest as speedtest_module
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False


class SpeedTestRunner:
    """Speed test functionality"""
    
    def __init__(self, progress_callback=None, status_callback=None, result_callback=None, error_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.result_callback = result_callback
        self.error_callback = error_callback
        self.cancelled = False
    
    def cancel(self):
        self.cancelled = True
    
    def run_test(self):
        """Run speed test in thread"""
        if not SPEEDTEST_AVAILABLE:
            if self.error_callback:
                self.error_callback("speedtest-cli not available")
            return
        
        try:
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Initializing speed test...")
            if self.progress_callback:
                self.progress_callback(10)
            
            st = speedtest_module.Speedtest()
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Finding best server...")
            if self.progress_callback:
                self.progress_callback(20)
            
            st.get_best_server()
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Testing download speed...")
            if self.progress_callback:
                self.progress_callback(40)
            
            download_speed = st.download() / 1_000_000
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Testing upload speed...")
            if self.progress_callback:
                self.progress_callback(70)
            
            upload_speed = st.upload() / 1_000_000
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Finalizing results...")
            if self.progress_callback:
                self.progress_callback(90)
            
            ping = st.results.ping
            
            if not self.cancelled:
                if self.progress_callback:
                    self.progress_callback(100)
                if self.result_callback:
                    self.result_callback({
                        'download': download_speed,
                        'upload': upload_speed,
                        'ping': ping,
                        'server': st.results.server
                    })
                    
        except Exception as e:
            if not self.cancelled and self.error_callback:
                self.error_callback(str(e))
