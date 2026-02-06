"""
Compare STL files from desktop app vs web app.

Reads the binary STL data and compares:
- File sizes
- Triangle counts
- Header content
- Vertex position differences (if same triangle count)
"""

import struct
import os
import sys


def read_stl_info(filepath):
    """Read basic info from a binary STL file."""
    with open(filepath, 'rb') as f:
        data = f.read()

    # Header (80 bytes) - read as string, stop at first null
    header_bytes = data[0:80]
    header = header_bytes.split(b'\x00')[0].decode('ascii', errors='replace')

    # Triangle count
    tri_count = struct.unpack_from('<I', data, 80)[0]

    # Read all vertex positions
    vertices = []
    offset = 84
    for i in range(tri_count):
        # Skip normal (12 bytes), read 3 vertices (36 bytes), skip attribute (2 bytes)
        nx, ny, nz = struct.unpack_from('<3f', data, offset)
        v1 = struct.unpack_from('<3f', data, offset + 12)
        v2 = struct.unpack_from('<3f', data, offset + 24)
        v3 = struct.unpack_from('<3f', data, offset + 36)
        vertices.extend([v1, v2, v3])
        offset += 50

    return {
        'filepath': filepath,
        'filesize': len(data),
        'header': header,
        'tri_count': tri_count,
        'vertices': vertices,
    }


def compare_files(desktop_path, web_path, label):
    """Compare two STL files and report differences."""
    print(f"\n{'=' * 60}")
    print(f"COMPARING: {label}")
    print(f"{'=' * 60}")

    desktop = read_stl_info(desktop_path)
    web = read_stl_info(web_path)

    print(f"\n  Desktop: {os.path.basename(desktop_path)}")
    print(f"    Header:    '{desktop['header']}'")
    print(f"    File size: {desktop['filesize']:,} bytes")
    print(f"    Triangles: {desktop['tri_count']:,}")

    print(f"\n  Web App: {os.path.basename(web_path)}")
    print(f"    Header:    '{web['header']}'")
    print(f"    File size: {web['filesize']:,} bytes")
    print(f"    Triangles: {web['tri_count']:,}")

    # Compare sizes
    if desktop['filesize'] == web['filesize']:
        print(f"\n  File sizes: IDENTICAL")
    else:
        diff = desktop['filesize'] - web['filesize']
        print(f"\n  File sizes: DIFFERENT (desktop is {diff:+,} bytes)")

    # Compare triangle counts
    if desktop['tri_count'] == web['tri_count']:
        print(f"  Triangle counts: IDENTICAL ({desktop['tri_count']:,})")

        # Compare actual vertex positions
        max_diff = 0
        total_diff = 0
        num_verts = len(desktop['vertices'])

        for i in range(num_verts):
            dv = desktop['vertices'][i]
            wv = web['vertices'][i]
            for k in range(3):
                diff = abs(dv[k] - wv[k])
                max_diff = max(max_diff, diff)
                total_diff += diff

        avg_diff = total_diff / (num_verts * 3) if num_verts > 0 else 0
        print(f"  Vertex comparison ({num_verts:,} vertices):")
        print(f"    Max difference:     {max_diff:.6f} mm")
        print(f"    Average difference: {avg_diff:.6f} mm")

        if max_diff < 0.001:
            print(f"    Result: EFFECTIVELY IDENTICAL")
        elif max_diff < 0.1:
            print(f"    Result: VERY CLOSE (minor floating point differences)")
        else:
            print(f"    Result: SIGNIFICANT DIFFERENCES - needs investigation")
    else:
        print(f"  Triangle counts: DIFFERENT - cannot compare vertices directly")


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), '..', '..', 'test_output')
    web_dir = os.path.join(base, 'From Web App')

    # Spiral comparison
    compare_files(
        os.path.join(base, 'Roller_W200-RW40-RD4.0-SN10-TW6-ST3-SM50-WD65.stl'),
        os.path.join(web_dir, 'Roller_W200-RW40-RD4-SN10-TW6-ST3-SM50-WD65.stl'),
        "SPIRAL MODE"
    )

    # Tangent comparison
    compare_files(
        os.path.join(base, 'Roller_W200-RW40-RD4.0-TN10-TW6-ST3-SM50-WD65.stl'),
        os.path.join(web_dir, 'Roller_W200-RW40-RD4-TN10-TW6-ST3-SM50-WD65.stl'),
        "TANGENT MODE"
    )

    print(f"\n{'=' * 60}")
    print("COMPARISON COMPLETE")
    print(f"{'=' * 60}")
