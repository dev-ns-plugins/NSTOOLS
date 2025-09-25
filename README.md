# NS TOOLS V2

A game automation application with auto-clicking, macro recording, and hotkey features.

## 🚀 How to Run

### Method 1: Portable Executable (Recommended)
1. Download the `dist` folder
2. Run `NSToolsV2.exe` - no Python installation required!

### Method 2: Batch File
1. Double-click `run_silent.bat`
2. The application will run automatically

### Method 3: Command Line
1. Open PowerShell in the project directory
2. Run: `py src\main.py`

## 📋 Prerequisites

### For Portable Version:
- Windows 10/11 (64-bit)
- No additional software required!

### For Source Code:
- Python 3.7+ installed
- Dependencies installed:
  - pyautogui
  - keyboard
  - pywin32

## 🎮 Features

### Main Controls
- **CTRL**: Holds Ctrl key continuously
- **LEFT**: Automatic left mouse button clicking
- **RIGHT**: Automatic right mouse button clicking
- **F1-F10**: Presses function keys automatically

### Recording System
- **REC**: Start/stop recording movements and clicks
- **PLAY**: Execute saved recording
- **SAVE**: Save recording to file
- **LOAD**: Load a saved recording
- **CLEAR**: Clear current recording

### Global Hotkeys
- **PAUSE**: Pause/resume all functions
- **INSERT**: Toggle CTRL hold
- **HOME**: Toggle left click
- **PAGE UP**: Toggle right click
- **F1-F10**: Toggle function keys
- **F11**: Toggle recording
- **F12**: Play recording
- **ALT+O**: Open settings
- **ALT+S** or **CTRL+ALT+S**: Stop everything

## ⚙️ Settings

Click the "=" button in the interface to open settings:

- **Timer Speeds**: Adjust click speeds (ms)
- **Options**: Failsafe, auto-save, always on top
- **Transparency**: Adjust window transparency
- **Recording System**: Recording and playback settings

## 📁 File Structure

```
NSTOOLS V2/
├── dist/
│   └── NSToolsV2.exe    # Portable executable
├── src/
│   └── main.py          # Source code
├── saves/               # Folder for saved recordings
├── settings.json        # Application settings
├── run_silent.bat       # Run script
├── build.bat           # Build script for portable version
├── nstools.spec        # PyInstaller configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🔧 Troubleshooting

### "Python not found"
- Use `py` command instead of `python`
- Or install Python from official website

### "Module not found"
- Run: `py -m pip install -r requirements.txt`

### App won't open
- Run as administrator
- Check if all dependencies are installed

### Portable version issues
- Make sure you're running on Windows 10/11 64-bit
- Try running as administrator
- Check Windows Defender isn't blocking the executable

## ⚠️ Warnings

- Use responsibly in games
- Some games may detect automation
- Always test in a safe environment first
- The application requires administrator privileges to work properly

## 📞 Support

Discord: https://dsc.gg/nsplugins

---
**NS TOOLS V2** - Developed for game automation
