#!/usr/bin/env python3
"""
Blender File Repair Tool
Repairs corrupted .blend files that crash or freeze Blender 4.x/5.x

Usage:
    python repair_blend.py <corrupted_file.blend> [output_file.blend]
    
Repair strategies attempted:
    1. Decompress/recompress (fixes compression corruption)
    2. Background mode with factory settings
    3. Append data to new file (bypasses scene corruption)
    4. Data block cleanup and recovery
"""

import argparse
import gzip
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# Try to import zstandard for Blender 3.0+ files
try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False


def find_blender() -> str | None:
    """Find Blender executable on the system."""
    # Common Blender locations
    possible_paths = [
        "blender",  # In PATH
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "/snap/bin/blender",
        "/opt/blender/blender",
        os.path.expanduser("~/blender/blender"),
        # Flatpak
        "/var/lib/flatpak/exports/bin/org.blender.Blender",
    ]
    
    # Check PATH first
    result = shutil.which("blender")
    if result:
        return result
    
    # Check common locations
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None


def get_compression_type(filepath: str) -> str | None:
    """Detect compression type of .blend file."""
    try:
        with open(filepath, 'rb') as f:
            magic = f.read(4)
            # Gzip: 1f 8b
            if magic[:2] == b'\x1f\x8b':
                return 'gzip'
            # Zstandard: 28 b5 2f fd (Blender 3.0+)
            if magic == b'\x28\xb5\x2f\xfd':
                return 'zstd'
            # Uncompressed: starts with "BLENDER"
            if magic[:4] == b'BLEN':
                return None
    except Exception:
        pass
    return 'unknown'


def is_blend_file(filepath: str) -> bool:
    """Check if file is a valid .blend file (compressed or uncompressed)."""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(12)
            # Uncompressed: starts with "BLENDER"
            if header[:7] == b'BLENDER':
                return True
            # Gzip compressed: starts with gzip magic bytes
            if header[:2] == b'\x1f\x8b':
                return True
            # Zstandard compressed (Blender 3.0+): 28 b5 2f fd
            if header[:4] == b'\x28\xb5\x2f\xfd':
                return True
    except Exception:
        pass
    return False


def is_compressed(filepath: str) -> bool:
    """Check if .blend file is compressed (gzip or zstd)."""
    compression = get_compression_type(filepath)
    return compression in ('gzip', 'zstd')


def get_blend_version(filepath: str) -> str | None:
    """Extract Blender version from .blend file header."""
    try:
        compression = get_compression_type(filepath)
        
        if compression == 'zstd':
            if not HAS_ZSTD:
                return None
            with open(filepath, 'rb') as f:
                dctx = zstd.ZstdDecompressor()
                # Read just enough to get the header
                reader = dctx.stream_reader(f)
                header = reader.read(12)
        elif compression == 'gzip':
            with gzip.open(filepath, 'rb') as f:
                header = f.read(12)
        else:
            with open(filepath, 'rb') as f:
                header = f.read(12)
        
        if header[:7] == b'BLENDER':
            # Version is at bytes 9-12 (e.g., "400" for 4.0, "500" for 5.0)
            version = header[9:12].decode('ascii')
            major = version[0]
            minor = version[1:3].lstrip('0') or '0'
            return f"{major}.{minor}"
    except Exception:
        pass
    return None


def decompress_blend(input_path: str, output_path: str, compression: str = None) -> bool:
    """Decompress a compressed .blend file (gzip or zstd)."""
    if compression is None:
        compression = get_compression_type(input_path)
    
    try:
        if compression == 'zstd':
            if not HAS_ZSTD:
                print("  [!] zstandard module not installed. Install with: pip install zstandard")
                return False
            with open(input_path, 'rb') as f_in:
                dctx = zstd.ZstdDecompressor()
                with open(output_path, 'wb') as f_out:
                    dctx.copy_stream(f_in, f_out)
        elif compression == 'gzip':
            with gzip.open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            print(f"  [!] Unknown compression type: {compression}")
            return False
        return True
    except Exception as e:
        print(f"  [!] Decompression failed: {e}")
        return False


def compress_blend(input_path: str, output_path: str, compression: str = 'zstd') -> bool:
    """Compress a .blend file (zstd for Blender 3.0+, gzip for older)."""
    try:
        if compression == 'zstd':
            if not HAS_ZSTD:
                print("  [!] zstandard module not installed, falling back to gzip")
                compression = 'gzip'
            else:
                with open(input_path, 'rb') as f_in:
                    cctx = zstd.ZstdCompressor(level=6)
                    with open(output_path, 'wb') as f_out:
                        cctx.copy_stream(f_in, f_out)
                return True
        
        if compression == 'gzip':
            with open(input_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb', compresslevel=6) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        
        return False
    except Exception as e:
        print(f"  [!] Compression failed: {e}")
        return False


def repair_compression(input_path: str, output_path: str) -> bool:
    """
    Strategy 1: Decompress and recompress the file.
    Fixes issues caused by compression corruption.
    """
    print("\n[Strategy 1] Attempting decompression/recompression repair...")
    
    compression = get_compression_type(input_path)
    print(f"  Detected compression: {compression or 'none'}")
    
    if compression == 'zstd' and not HAS_ZSTD:
        print("  [!] zstandard module required for this file.")
        print("  [!] Install with: pip install zstandard")
        return False
    
    if not compression or compression == 'unknown':
        print("  File is not compressed or unknown format, trying to compress it...")
        return compress_blend(input_path, output_path, 'zstd')
    
    with tempfile.NamedTemporaryFile(suffix='.blend', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        print("  Decompressing file...")
        if not decompress_blend(input_path, tmp_path, compression):
            return False
        
        # Verify decompressed file
        if not is_blend_file(tmp_path):
            print("  [!] Decompressed data is not valid")
            return False
        
        print("  Recompressing file...")
        if compress_blend(tmp_path, output_path, compression):
            print("  [✓] Compression repair successful")
            return True
        return False
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def run_blender_script(blender_path: str, script: str, timeout: int = 120) -> tuple[bool, str]:
    """Run a Python script in Blender's background mode."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_path = f.name
    
    try:
        result = subprocess.run(
            [blender_path, '--background', '--factory-startup', '--python', script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Blender process timed out"
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(script_path):
            os.unlink(script_path)


def repair_with_blender_open(blender_path: str, input_path: str, output_path: str) -> bool:
    """
    Strategy 2: Open file in background mode with factory settings and resave.
    """
    print("\n[Strategy 2] Attempting Blender background mode repair...")
    
    script = f'''
import bpy
import sys

input_file = r"{input_path}"
output_file = r"{output_path}"

try:
    # Try to open with recovery enabled
    bpy.ops.wm.open_mainfile(filepath=input_file, load_ui=False)
    
    # Purge orphan data
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    
    # Save repaired file
    bpy.ops.wm.save_as_mainfile(filepath=output_file, compress=True)
    print("REPAIR_SUCCESS")
except Exception as e:
    print(f"REPAIR_FAILED: {{e}}")
    sys.exit(1)
'''
    
    success, output = run_blender_script(blender_path, script, timeout=180)
    
    if success and "REPAIR_SUCCESS" in output:
        print("  [✓] Background mode repair successful")
        return True
    
    print(f"  [!] Background mode repair failed")
    return False


def repair_with_append(blender_path: str, input_path: str, output_path: str) -> bool:
    """
    Strategy 3: Create new file and append all data from corrupted file.
    This bypasses scene-level corruption.
    """
    print("\n[Strategy 3] Attempting append-based recovery...")
    
    script = f'''
import bpy
import sys
import os

input_file = r"{input_path}"
output_file = r"{output_path}"

# Start fresh
bpy.ops.wm.read_factory_settings(use_empty=True)

# Data types to attempt recovery
data_types = [
    'collections',
    'objects', 
    'meshes',
    'materials',
    'textures',
    'images',
    'armatures',
    'cameras',
    'lights',
    'curves',
    'fonts',
    'grease_pencils',
    'node_groups',
    'particles',
    'scenes',
    'worlds',
    'actions',
]

recovered_count = 0
failed_types = []

for data_type in data_types:
    try:
        # Get directory path for this data type
        directory = os.path.join(input_file, data_type.title().replace('_', ''))
        
        # Try to link/append all items of this type
        with bpy.data.libraries.load(input_file, link=False) as (data_from, data_to):
            source_data = getattr(data_from, data_type, [])
            if source_data:
                setattr(data_to, data_type, list(source_data))
                recovered_count += len(source_data)
                print(f"Recovered {{len(source_data)}} {{data_type}}")
    except Exception as e:
        failed_types.append(data_type)

if recovered_count > 0:
    # Create a scene if none exists
    if not bpy.data.scenes:
        bpy.ops.scene.new(type='NEW')
    
    # Link recovered objects to scene
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        if obj.name not in scene.collection.objects:
            try:
                scene.collection.objects.link(obj)
            except:
                pass
    
    # Save recovered data
    bpy.ops.wm.save_as_mainfile(filepath=output_file, compress=True)
    print(f"RECOVERY_SUCCESS: Recovered {{recovered_count}} data blocks")
    if failed_types:
        print(f"Failed types: {{', '.join(failed_types)}}")
else:
    print("RECOVERY_FAILED: No data could be recovered")
    sys.exit(1)
'''
    
    success, output = run_blender_script(blender_path, script, timeout=300)
    
    if success and "RECOVERY_SUCCESS" in output:
        print("  [✓] Append-based recovery successful")
        # Print recovery details
        for line in output.split('\n'):
            if 'Recovered' in line or 'RECOVERY_SUCCESS' in line:
                print(f"  {line}")
        return True
    
    print(f"  [!] Append-based recovery failed")
    return False


def repair_selective_recovery(blender_path: str, input_path: str, output_path: str) -> bool:
    """
    Strategy 4: Selective data block recovery with error handling per block.
    Most thorough but slowest approach.
    """
    print("\n[Strategy 4] Attempting selective data block recovery...")
    
    script = f'''
import bpy
import sys

input_file = r"{input_path}"
output_file = r"{output_path}"

# Start fresh
bpy.ops.wm.read_factory_settings(use_empty=True)

recovered = []
failed = []

# Get list of data blocks in the file
try:
    with bpy.data.libraries.load(input_file, link=False) as (data_from, data_to):
        # Collect all available data
        all_data = {{}}
        for attr in dir(data_from):
            if not attr.startswith('_'):
                try:
                    items = list(getattr(data_from, attr, []))
                    if items:
                        all_data[attr] = items
                except:
                    pass
        
        # Copy all data
        for attr, items in all_data.items():
            try:
                setattr(data_to, attr, items)
                recovered.extend([(attr, name) for name in items])
            except Exception as e:
                failed.append((attr, str(e)))

except Exception as e:
    print(f"RECOVERY_FAILED: Could not read file: {{e}}")
    sys.exit(1)

if recovered:
    # Setup scene
    if not bpy.data.scenes:
        bpy.ops.scene.new(type='NEW')
    
    scene = bpy.context.scene
    
    # Link objects to scene
    for obj in bpy.data.objects:
        try:
            if obj.name not in scene.collection.objects:
                scene.collection.objects.link(obj)
        except:
            pass
    
    # Purge broken references
    try:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except:
        pass
    
    # Save
    bpy.ops.wm.save_as_mainfile(filepath=output_file, compress=True)
    print(f"RECOVERY_SUCCESS: Recovered {{len(recovered)}} items")
else:
    print("RECOVERY_FAILED: No data recovered")
    sys.exit(1)
'''
    
    success, output = run_blender_script(blender_path, script, timeout=300)
    
    if success and "RECOVERY_SUCCESS" in output:
        print("  [✓] Selective recovery successful")
        for line in output.split('\n'):
            if 'RECOVERY_SUCCESS' in line:
                print(f"  {line}")
        return True
    
    print(f"  [!] Selective recovery failed")
    return False


def repair_blend_file(input_path: str, output_path: str | None = None, blender_path: str | None = None) -> bool:
    """
    Main repair function. Tries multiple strategies in order.
    """
    input_path = os.path.abspath(input_path)
    
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return False
    
    if not is_blend_file(input_path):
        print(f"Error: Not a valid .blend file: {input_path}")
        return False
    
    # Generate output path if not specified
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_repaired{ext}"
    output_path = os.path.abspath(output_path)
    
    # Create backup
    backup_path = input_path + ".backup"
    if not os.path.exists(backup_path):
        print(f"Creating backup: {backup_path}")
        shutil.copy2(input_path, backup_path)
    
    print(f"\n{'='*60}")
    print("Blender File Repair Tool")
    print(f"{'='*60}")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    
    version = get_blend_version(input_path)
    if version:
        print(f"Blender version: {version}")
    
    compression = get_compression_type(input_path)
    print(f"Compression: {compression or 'none'}")
    
    # Find Blender
    if blender_path is None:
        blender_path = find_blender()
    
    if blender_path:
        print(f"Blender executable: {blender_path}")
    else:
        print("Warning: Blender not found. Some repair strategies unavailable.")
    
    # Strategy 1: Compression repair (doesn't need Blender)
    if repair_compression(input_path, output_path):
        # Verify the repaired file works
        if blender_path:
            print("\nVerifying repaired file...")
            verify_script = f'''
import bpy
bpy.ops.wm.open_mainfile(filepath=r"{output_path}", load_ui=False)
print("VERIFY_SUCCESS")
'''
            success, output = run_blender_script(blender_path, verify_script, timeout=60)
            if "VERIFY_SUCCESS" in output:
                print(f"\n[✓] Repair successful! Saved to: {output_path}")
                return True
            else:
                print("  Verification failed, trying other strategies...")
        else:
            print(f"\n[✓] Compression repair complete (unverified): {output_path}")
            return True
    
    if not blender_path:
        print("\n[!] Cannot continue without Blender. Please install Blender and try again.")
        return False
    
    # Strategy 2: Background mode with factory settings
    if repair_with_blender_open(blender_path, input_path, output_path):
        print(f"\n[✓] Repair successful! Saved to: {output_path}")
        return True
    
    # Strategy 3: Append-based recovery
    if repair_with_append(blender_path, input_path, output_path):
        print(f"\n[✓] Repair successful! Saved to: {output_path}")
        return True
    
    # Strategy 4: Selective recovery
    if repair_selective_recovery(blender_path, input_path, output_path):
        print(f"\n[✓] Repair successful! Saved to: {output_path}")
        return True
    
    print(f"\n[✗] All repair strategies failed.")
    print("\nAdditional suggestions:")
    print("  1. Check if Blender auto-save files exist in ~/.config/blender/*/autosave/")
    print("  2. Look for .blend1, .blend2 backup files in the same directory")
    print("  3. Try opening the file in an older Blender version")
    print("  4. If the file is from cloud storage, check for version history")
    
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Repair corrupted Blender (.blend) files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s corrupted.blend
  %(prog)s corrupted.blend repaired.blend
  %(prog)s --blender /path/to/blender corrupted.blend

Repair strategies attempted (in order):
  1. Decompress/recompress (fixes compression corruption)
  2. Background mode with factory settings
  3. Append data to new file (bypasses scene corruption)  
  4. Selective data block recovery (most thorough)
"""
    )
    parser.add_argument("input", help="Path to corrupted .blend file")
    parser.add_argument("output", nargs="?", help="Output path (default: input_repaired.blend)")
    parser.add_argument("--blender", "-b", help="Path to Blender executable")
    
    args = parser.parse_args()
    
    success = repair_blend_file(args.input, args.output, args.blender)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
