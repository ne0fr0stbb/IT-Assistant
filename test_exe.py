#!/usr/bin/env python3
"""
Test script to debug executable issues
"""
import sys
import traceback

def test_imports():
    """Test importing all required modules"""
    modules_to_test = [
        'sys', 'os', 'time', 'threading', 'queue', 'subprocess',
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui',
        'pyqtgraph', 'numpy', 'csv', 'webbrowser', 'ipaddress', 
        'socket', 'concurrent.futures', 'speedtest', 'psutil',
        'ping3', 'manuf', 'scapy'
    ]
    
    print("Testing module imports...")
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append((module, str(e)))
        except Exception as e:
            print(f"⚠ {module}: {e}")
            failed_imports.append((module, str(e)))
    
    if failed_imports:
        print(f"\n{len(failed_imports)} modules failed to import:")
        for module, error in failed_imports:
            print(f"  - {module}: {error}")
    else:
        print("\nAll modules imported successfully!")
    
    return len(failed_imports) == 0

def test_local_files():
    """Test that local files are accessible"""
    local_files = [
        'scanthread.py', 'utils.py', 'livemonitor.py', 
        'speedtest_dialog.py', 'NetworkScanner.py'
    ]
    
    print("\nTesting local file accessibility...")
    missing_files = []
    
    for file in local_files:
        try:
            with open(file, 'r') as f:
                print(f"✓ {file}")
        except FileNotFoundError:
            print(f"✗ {file}: File not found")
            missing_files.append(file)
        except Exception as e:
            print(f"⚠ {file}: {e}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n{len(missing_files)} files missing:")
        for file in missing_files:
            print(f"  - {file}")
    else:
        print("\nAll local files accessible!")
    
    return len(missing_files) == 0

def test_gui_creation():
    """Test creating a basic PyQt5 application"""
    try:
        print("\nTesting PyQt5 GUI creation...")
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        print("✓ QApplication created successfully")
        app.quit()
        return True
    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("NetworkMonitor Executable Debug Test")
    print("=" * 50)
    
    imports_ok = test_imports()
    files_ok = test_local_files()
    gui_ok = test_gui_creation()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Files:   {'✓ PASS' if files_ok else '✗ FAIL'}")
    print(f"GUI:     {'✓ PASS' if gui_ok else '✗ FAIL'}")
    
    if all([imports_ok, files_ok, gui_ok]):
        print("\n🎉 All tests passed! The executable should work.")
        
        # Try to import and run the main application
        try:
            print("\nTesting main application import...")
            import NetworkMonitorGUI
            print("✓ Main application imported successfully")
        except Exception as e:
            print(f"✗ Main application import failed: {e}")
            traceback.print_exc()
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
    input("Press Enter to continue...")
