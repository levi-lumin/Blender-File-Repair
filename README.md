# Blend_Repair

A tool to repair corrupted Blender (.blend) files that crash or freeze when opened. Supports Blender 3.x, 4.x, and 5.x files.

![Blender](https://img.shields.io/badge/Blender-3.x%20%7C%204.x%20%7C%205.x-orange)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## Quick Start

1. **Place** your corrupted `.blend` file in this folder
2. **Run** the repair script for your OS:
   - **Windows:** Double-click `repair.bat`
   - **Linux:** Run `./repair.sh`
   - **macOS:** Double-click `repair.command`
3. **Find** your repaired file: `yourfile_repaired.blend`

## Requirements

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Blender** installed (for advanced repair strategies)

The script will automatically install the `zstandard` module if needed.

## How It Works

The tool attempts multiple repair strategies in order:

| Strategy | Description | Fixes |
|----------|-------------|-------|
| **1. Decompression/Recompression** | Decompresses and recompresses the file data | Compression corruption, truncated archives |
| **2. Background Mode** | Opens file in Blender with factory settings and resaves | UI corruption, addon conflicts, preference issues |
| **3. Append Recovery** | Creates new file and appends all data blocks | Scene-level corruption, broken references |
| **4. Selective Recovery** | Recovers each data block individually with error handling | Partial corruption, specific broken data blocks |

## Command Line Usage

For advanced users, you can run the Python script directly:

```bash
# Basic usage
python repair_blend.py corrupted.blend

# Specify output file
python repair_blend.py corrupted.blend repaired.blend

# Specify Blender path
python repair_blend.py --blender /path/to/blender corrupted.blend
```

### Options

| Option | Description |
|--------|-------------|
| `input` | Path to corrupted .blend file (required) |
| `output` | Output path (default: `input_repaired.blend`) |
| `--blender`, `-b` | Path to Blender executable |

## Features

- ✅ **Automatic backup** - Creates `.backup` before any repair attempt
- ✅ **Multi-format support** - Handles both gzip (Blender 2.x) and zstd (Blender 3.0+) compression
- ✅ **Auto-detects Blender** - Searches common installation paths
- ✅ **Batch processing** - Repairs all `.blend` files in the folder
- ✅ **Cross-platform** - Works on Windows, Linux, and macOS
- ✅ **Orphan cleanup** - Purges broken references and unused data

## Troubleshooting

### "Python not found"
Install Python 3.8+ from [python.org](https://www.python.org/downloads/) and ensure it's in your PATH.

### "Blender not found"
The tool searches common Blender locations. If not found, specify the path manually:
```bash
python repair_blend.py --blender "/path/to/blender" file.blend
```

Common Blender locations:
- **Windows:** `C:\Program Files\Blender Foundation\Blender X.X\blender.exe`
- **Linux:** `/usr/bin/blender`, `~/blender/blender`, or extracted tarball location
- **macOS:** `/Applications/Blender.app/Contents/MacOS/Blender`

### "All repair strategies failed"
Try these additional options:
1. Check for auto-save files in:
   - **Windows:** `%APPDATA%\Blender Foundation\Blender\X.X\autosave\`
   - **Linux:** `~/.config/blender/X.X/autosave/`
   - **macOS:** `~/Library/Application Support/Blender/X.X/autosave/`
2. Look for `.blend1`, `.blend2` backup files in the same directory
3. Try opening the file in an older Blender version
4. If from cloud storage, check version history

### "zstandard module not installed"
The script tries to install this automatically. If it fails:
```bash
pip install zstandard
# or
python -m pip install zstandard --user
```

## How Blender Files Get Corrupted

Common causes of .blend file corruption:
- Blender crash during save
- Power loss while saving
- Disk errors or bad sectors
- Interrupted file transfers
- Cloud sync conflicts
- Running out of disk space during save

## License

MIT License - Feel free to use, modify, and distribute.

## Contributing

Pull requests welcome! Please test on corrupted files before submitting.
