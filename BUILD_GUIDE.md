# NetworkMonitor Build Guide

## Quick Start
To build the executable, simply run:
```batch
build.bat
```

Or manually:
```batch
cxfreeze --clean NetworkMonitor.py --target-dir dist
```

## Build Options

### 1. **Single File Executable (Current)**
- **File**: `NetworkMonitor.spec`
- **Size**: ~9MB
- **Speed**: Fast startup
- **Distribution**: Single .exe file

### 2. **Optimized Build (Smaller Size)**
If you want a smaller executable, modify the spec file:
```python
# In NetworkMonitor.spec, change:
upx=True,  # Keep compression
excludes=[
    'matplotlib',
    'numpy.testing', 
    'tkinter',
    'unittest',
    'pdb',
    'doctest',
    'difflib',
    'email',
    'html',
    'http',
    'urllib3',
    'xml',
]
```

### 3. **Debug Build**
For troubleshooting, use:
```python
# In NetworkMonitor.spec, change:
debug=True,
console=True,  # Shows console for debugging
```

## Build Requirements

### Essential Dependencies
```
customtkinter>=5.2
matplotlib>=3.5
pysnmp>=7.0
speedtest-cli>=2.1
manuf
ping3
cx_Freeze>=6.0
```

### Install All Dependencies
```batch
pip install -r requirements.txt
pip install cx_Freeze
```

## Build Process

1. **Clean Previous Builds**
   ```batch
   rmdir /s /q dist
   rmdir /s /q build
   ```

2. **Run Build**
   ```batch
   cxfreeze --clean NetworkMonitor.py --target-dir dist
   ```

3. **Test Executable**
   ```batch
   dist\NetworkMonitor.exe
   ```

## Troubleshooting

### Common Issues

**Missing Dependencies**
```
ERROR: Hidden import 'module' not found
```
**Solution**: Add to `hiddenimports` in the spec file

**Large File Size**
**Solution**: Add modules to `excludes` list

**Slow Startup**
**Solution**: Use `--onedir` instead of `--onefile`

**Runtime Errors**
**Solution**: Enable debug mode and check console output

### Performance Tips

1. **Exclude Unused Modules**: Add unnecessary modules to `excludes`
2. **Use UPX Compression**: Keep `upx=True` 
3. **Hidden Imports**: Only include necessary modules
4. **Optimize Python**: Use `python -O` for optimized bytecode

## Distribution

### What to Include
- `NetworkMonitor.exe` - Main executable
- `README.md` - User instructions
- Any additional data files (if needed)

### System Requirements
- Windows 7/8/10/11 (64-bit)
- No Python installation required
- ~50MB disk space
- Internet connection (for speed tests and network scanning)

### Installation
1. Download `NetworkMonitor.exe`
2. Run as Administrator (for network scanning features)
3. Windows may show security warning - click "More info" → "Run anyway"

## Build Variants

### Development Build
```batch
cxfreeze --debug --console NetworkMonitorGUI.py
```

### Production Build  
```batch
cxfreeze --clean --onefile --noconsole NetworkMonitor.py
```

### Portable Build
```batch
cxfreeze --clean --onedir NetworkMonitor.py
```

## File Structure After Build

```
NetworkMonitor/
├── dist/
│   └── NetworkMonitor.exe          # Final executable
├── build/                          # Temporary build files
├── NetworkMonitor.spec             # Build configuration
├── build.bat                       # Build script
└── BUILD_GUIDE.md                  # This guide
```

## Advanced Options

### Custom Icon
1. Get a `.ico` file
2. In `NetworkMonitor.spec`, change:
   ```python
   icon='path/to/icon.ico'
   ```

### Version Information
1. Create `version.txt`:
   ```
   VSVersionInfo(
     ffi=FixedFileInfo(
       filevers=(1,0,0,0),
       prodvers=(1,0,0,0),
       mask=0x3f,
       flags=0x0,
       OS=0x4,
       fileType=0x1,
       subtype=0x0,
       date=(0, 0)
     ),
     kids=[
       StringFileInfo([
         StringTable('040904B0', [
           StringStruct('CompanyName', 'Your Company'),
           StringStruct('FileDescription', 'Network Monitor'),
           StringStruct('FileVersion', '1.0.0.0'),
           StringStruct('ProductName', 'NetworkMonitor'),
           StringStruct('ProductVersion', '1.0.0.0')])
       ]), 
       VarFileInfo([VarStruct('Translation', [1033, 1200])])
     ]
   )
   ```

2. In spec file:
   ```python
   version_file='version.txt'
   ```

## Success Criteria

✅ Executable builds without errors
✅ File size under 15MB  
✅ Starts in under 3 seconds
✅ All GUI features work
✅ Network scanning works
✅ Speed test works
✅ No console window appears
✅ Works on clean Windows systems
