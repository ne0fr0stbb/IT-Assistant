from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt5.QtCore import QThread, pyqtSignal
import speedtest

class SpeedTestThread(QThread):
    speedtest_results = pyqtSignal(dict)
    speedtest_error = pyqtSignal(str)

    def run(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            ping = st.results.ping
            self.speedtest_results.emit({
                'download': download_speed,
                'upload': upload_speed,
                'ping': ping
            })
        except speedtest.ConfigRetrievalError as e:
            self.speedtest_error.emit(f"Config retrieval error: {e}. Retrying...")
            try:
                st = speedtest.Speedtest()
                st.get_best_server()
                download_speed = st.download() / 1_000_000
                upload_speed = st.upload() / 1_000_000
                ping = st.results.ping
                self.speedtest_results.emit({
                    'download': download_speed,
                    'upload': upload_speed,
                    'ping': ping
                })
            except Exception as retry_error:
                self.speedtest_error.emit(f"Retry failed: {retry_error}")
        except speedtest.SpeedtestException as e:
            self.speedtest_error.emit(f"Speedtest error: {e}")
        except Exception as e:
            self.speedtest_error.emit(f"Unexpected error: {e}")

class SpeedTestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Internet Speed Test')
        self.resize(400, 300)
        layout = QVBoxLayout()

        self.info_label = QLabel('Running speed test...')
        self.info_label.setStyleSheet('font-size: 16px;')  # Increased font size
        layout.addWidget(self.info_label)

        self.results_label = QLabel('')
        self.results_label.setStyleSheet('font-size: 14px;')  # Increased font size
        layout.addWidget(self.results_label)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.setStyleSheet('font-size: 14px;')  # Increased font size
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)

        self.setLayout(layout)

        self.thread = SpeedTestThread()
        self.thread.speedtest_results.connect(self.display_results)
        self.thread.speedtest_error.connect(self.display_error)
        self.thread.start()

    def display_results(self, results):
        self.results_label.setText(f"Download Speed: {results['download']:.2f} Mbps\n"
                                   f"Upload Speed: {results['upload']:.2f} Mbps\n"
                                   f"Ping: {results['ping']:.2f} ms")
        self.info_label.setText('Speed test completed.')

    def display_error(self, error):
        self.results_label.setText(f"Error: {error}")
        self.info_label.setText('Speed test failed.')
