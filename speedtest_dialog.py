from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QPushButton, QHBoxLayout, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import speedtest
import time

class SpeedTestThread(QThread):
    speedtest_results = pyqtSignal(dict)
    speedtest_error = pyqtSignal(str)
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._is_cancelled = False
        self._current_test = None

    def cancel(self):
        """Cancel the current speed test"""
        self._is_cancelled = True
        if self._current_test:
            try:
                # Try to interrupt the current test
                self._current_test = None
            except:
                pass

    def run(self):
        try:
            if self._is_cancelled:
                return
                
            self.status_update.emit("Initializing speed test...")
            self.progress_update.emit(10)
            
            # Create speedtest instance with timeout
            st = speedtest.Speedtest()
            self._current_test = st
            
            if self._is_cancelled:
                return
                
            self.status_update.emit("Finding best server...")
            self.progress_update.emit(20)
            
            # Get best server with timeout protection
            try:
                st.get_best_server()
            except Exception as e:
                if "timeout" in str(e).lower():
                    self.speedtest_error.emit("Connection timeout while finding server. Please check your internet connection.")
                    return
                raise
            
            if self._is_cancelled:
                return
                
            self.status_update.emit("Testing download speed...")
            self.progress_update.emit(40)
            
            # Download test with timeout
            try:
                download_speed = st.download() / 1_000_000  # Convert to Mbps
            except Exception as e:
                if "timeout" in str(e).lower():
                    self.speedtest_error.emit("Download test timed out. Please try again.")
                    return
                raise
            
            if self._is_cancelled:
                return
                
            self.status_update.emit("Testing upload speed...")
            self.progress_update.emit(70)
            
            # Upload test with timeout
            try:
                upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            except Exception as e:
                if "timeout" in str(e).lower():
                    self.speedtest_error.emit("Upload test timed out. Please try again.")
                    return
                raise
            
            if self._is_cancelled:
                return
                
            self.status_update.emit("Finalizing results...")
            self.progress_update.emit(90)
            
            ping = st.results.ping
            
            if not self._is_cancelled:
                self.progress_update.emit(100)
                self.speedtest_results.emit({
                    'download': download_speed,
                    'upload': upload_speed,
                    'ping': ping,
                    'server': st.results.server
                })
                
        except speedtest.ConfigRetrievalError as e:
            if self._is_cancelled:
                return
            self.speedtest_error.emit(f"Unable to retrieve speedtest configuration. This may be due to network issues or server unavailability. Please try again later.")
            
            # Retry once after a short delay
            self.status_update.emit("Retrying...")
            time.sleep(2)
            
            if self._is_cancelled:
                return
                
            try:
                st = speedtest.Speedtest()
                self._current_test = st
                st.get_best_server()
                
                if self._is_cancelled:
                    return
                    
                download_speed = st.download() / 1_000_000
                
                if self._is_cancelled:
                    return
                    
                upload_speed = st.upload() / 1_000_000
                ping = st.results.ping
                
                if not self._is_cancelled:
                    self.speedtest_results.emit({
                        'download': download_speed,
                        'upload': upload_speed,
                        'ping': ping,
                        'server': st.results.server
                    })
                    
            except Exception as retry_error:
                if not self._is_cancelled:
                    self.speedtest_error.emit(f"Retry failed: {str(retry_error)}")
                    
        except speedtest.SpeedtestException as e:
            if not self._is_cancelled:
                error_msg = str(e)
                if "HTTP Error" in error_msg:
                    self.speedtest_error.emit("Unable to connect to speedtest servers. Please check your internet connection and try again.")
                elif "timeout" in error_msg.lower():
                    self.speedtest_error.emit("Speed test timed out. Please try again with a more stable connection.")
                else:
                    self.speedtest_error.emit(f"Speed test service error: {error_msg}")
                    
        except ConnectionError:
            if not self._is_cancelled:
                self.speedtest_error.emit("No internet connection detected. Please check your network connection and try again.")
                
        except Exception as e:
            if not self._is_cancelled:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    self.speedtest_error.emit("Operation timed out. Please try again.")
                elif "connection" in error_msg.lower():
                    self.speedtest_error.emit("Connection error. Please check your internet connection.")
                else:
                    self.speedtest_error.emit(f"Unexpected error: {error_msg}")
        
        finally:
            self._current_test = None

class SpeedTestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Internet Speed Test')
        self.resize(450, 350)
        self.setModal(True)
        
        # Track test state
        self.test_completed = False
        self.test_cancelled = False
        
        layout = QVBoxLayout()

        # Status label
        self.info_label = QLabel('Initializing speed test...')
        self.info_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        layout.addWidget(self.info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet('QProgressBar { height: 20px; }')
        layout.addWidget(self.progress_bar)

        # Results label
        self.results_label = QLabel('')
        self.results_label.setStyleSheet('font-size: 14px; margin: 10px;')
        self.results_label.setWordWrap(True)
        layout.addWidget(self.results_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Cancel/Retry button
        self.action_button = QPushButton('Cancel')
        self.action_button.setStyleSheet('font-size: 14px; padding: 8px;')
        self.action_button.clicked.connect(self.handle_action_button)
        button_layout.addWidget(self.action_button)
        
        # Close button
        self.close_button = QPushButton('Close')
        self.close_button.setStyleSheet('font-size: 14px; padding: 8px;')
        self.close_button.clicked.connect(self.close)
        self.close_button.setEnabled(False)  # Disabled until test completes
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Initialize and start the speed test thread
        self.thread = SpeedTestThread()
        self.thread.speedtest_results.connect(self.display_results)
        self.thread.speedtest_error.connect(self.display_error)
        self.thread.status_update.connect(self.update_status)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.finished.connect(self.on_test_finished)
        
        # Start the test
        self.start_test()

    def start_test(self):
        """Start or restart the speed test"""
        self.test_completed = False
        self.test_cancelled = False
        self.action_button.setText('Cancel')
        self.close_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.results_label.setText('')
        self.info_label.setText('Initializing speed test...')
        
        # Start the thread
        if not self.thread.isRunning():
            self.thread.start()

    def handle_action_button(self):
        """Handle cancel/retry button clicks"""
        if self.test_completed:
            # Retry the test
            self.thread = SpeedTestThread()  # Create new thread
            self.thread.speedtest_results.connect(self.display_results)
            self.thread.speedtest_error.connect(self.display_error)
            self.thread.status_update.connect(self.update_status)
            self.thread.progress_update.connect(self.update_progress)
            self.thread.finished.connect(self.on_test_finished)
            self.start_test()
        else:
            # Cancel the test
            self.cancel_test()

    def cancel_test(self):
        """Cancel the running speed test"""
        self.test_cancelled = True
        self.thread.cancel()
        self.info_label.setText('Cancelling speed test...')
        self.action_button.setEnabled(False)
        
        # Force terminate if it doesn't stop gracefully
        QTimer.singleShot(3000, self.force_terminate)

    def force_terminate(self):
        """Force terminate the thread if it doesn't stop gracefully"""
        if self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait(1000)  # Wait up to 1 second
            self.on_test_finished()

    def update_status(self, status):
        """Update the status label"""
        if not self.test_cancelled:
            self.info_label.setText(status)

    def update_progress(self, value):
        """Update the progress bar"""
        if not self.test_cancelled:
            self.progress_bar.setValue(value)

    def display_results(self, results):
        """Display the speed test results"""
        if self.test_cancelled:
            return
            
        server_info = ""
        if 'server' in results and results['server']:
            server = results['server']
            server_info = f"\nServer: {server.get('sponsor', 'Unknown')} ({server.get('name', 'Unknown')})"
        
        self.results_label.setText(
            f"<b>Results:</b><br/>"
            f"Download Speed: <b>{results['download']:.2f} Mbps</b><br/>"
            f"Upload Speed: <b>{results['upload']:.2f} Mbps</b><br/>"
            f"Ping: <b>{results['ping']:.2f} ms</b>{server_info}"
        )
        self.info_label.setText('Speed test completed successfully!')
        self.progress_bar.setValue(100)

    def display_error(self, error):
        """Display error message"""
        if self.test_cancelled:
            self.results_label.setText('<b>Speed test was cancelled.</b>')
            self.info_label.setText('Test cancelled by user.')
        else:
            self.results_label.setText(f'<b>Error:</b><br/>{error}')
            self.info_label.setText('Speed test failed.')
        
        self.progress_bar.setValue(0)

    def on_test_finished(self):
        """Handle test completion (success or failure)"""
        self.test_completed = True
        
        if self.test_cancelled:
            self.action_button.setText('Retry')
        else:
            self.action_button.setText('Retry')
            
        self.action_button.setEnabled(True)
        self.close_button.setEnabled(True)

    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.thread.isRunning():
            self.thread.cancel()
            self.thread.terminate()
            self.thread.wait(2000)  # Wait up to 2 seconds
        event.accept()
