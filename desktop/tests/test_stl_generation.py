"""
Test script for STL generation.

Generates STL files with default parameters for both Spiral and Tangent
modes, then reports basic stats so we can verify the output is reasonable.

Run from the repo root:
    python desktop/tests/test_stl_generation.py
"""

import sys
import os
import time

# Add the desktop folder to Python's path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.parameters import RollerParams
from core.pattern_generator import generate_displacement_map
from core.stl_generator import generate_stl


def test_spiral_mode():
    """Generate a spiral mode STL with default parameters."""
    print("=" * 60)
    print("TEST: Spiral Mode (default parameters)")
    print("=" * 60)

    params = RollerParams(mode="spiral")
    print(f"  Parameters: {params}")
    print(f"  Filename will be: {params.to_filename()}")
    print()

    # Generate displacement map
    print("  Generating displacement map...")
    start = time.time()
    displacement = generate_displacement_map(params)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.2f} seconds")
    print(f"  Grid size: {displacement.shape[0]} x {displacement.shape[1]}")
    print(f"  Displacement range: {displacement.min():.3f} to {displacement.max():.3f} mm")
    print()

    # Generate STL
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, params.to_filename())

    print("  Generating STL file...")
    start = time.time()
    stl_data = generate_stl(displacement, params, output_path)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.2f} seconds")
    print(f"  File size: {len(stl_data):,} bytes ({len(stl_data) / 1024 / 1024:.1f} MB)")
    print(f"  Saved to: {output_path}")
    print()


def test_tangent_mode():
    """Generate a tangent mode STL with default parameters."""
    print("=" * 60)
    print("TEST: Tangent Mode (default parameters)")
    print("=" * 60)

    params = RollerParams(mode="tangent")
    print(f"  Parameters: {params}")
    print(f"  Filename will be: {params.to_filename()}")
    print()

    # Generate displacement map
    print("  Generating displacement map...")
    start = time.time()
    displacement = generate_displacement_map(params)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.2f} seconds")
    print(f"  Grid size: {displacement.shape[0]} x {displacement.shape[1]}")
    print(f"  Displacement range: {displacement.min():.3f} to {displacement.max():.3f} mm")
    print()

    # Generate STL
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, params.to_filename())

    print("  Generating STL file...")
    start = time.time()
    stl_data = generate_stl(displacement, params, output_path)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.2f} seconds")
    print(f"  File size: {len(stl_data):,} bytes ({len(stl_data) / 1024 / 1024:.1f} MB)")
    print(f"  Saved to: {output_path}")
    print()


if __name__ == "__main__":
    print()
    print("Rope Roller Maker - STL Generation Test")
    print()

    test_spiral_mode()
    test_tangent_mode()

    print("=" * 60)
    print("ALL TESTS COMPLETE")
    print("Open the .stl files in your slicer to visually verify!")
    print("=" * 60)
