"""
STL file generator for Rope Roller Maker.

Takes a 2D displacement map and converts it into a 3D triangle mesh
wrapped around a cylinder, then writes it as a binary STL file.

The process:
  1. Map each displacement value to a 3D point on the cylinder surface
  2. Connect adjacent points into triangles (2 per quad)
  3. Handle the wrap-around seam (last column connects to first)
  4. Calculate outward-facing normals for each triangle
  5. Write binary STL format with settings embedded in the header
"""

import struct
import numpy as np
import math
from pathlib import Path
from .parameters import RollerParams, RADIUS


def generate_stl(
    displacement: np.ndarray,
    params: RollerParams,
    output_path: str | Path | None = None,
) -> bytes:
    """Generate a binary STL file from a displacement map.

    Args:
        displacement: 2D array (axial_steps x angular_steps) of displacement
                      values in mm from the base radius.
        params: Roller parameters (used for dimensions and filename/header).
        output_path: If provided, write the STL file to this path.
                     If None, just return the bytes.

    Returns:
        The binary STL data as bytes.
    """
    axial_steps, angular_steps = displacement.shape

    # ---- Step 1: Generate 3D vertices ----
    # Each displacement value becomes a point on the cylinder surface
    vertices = _generate_vertices(displacement, params.width,
                                  axial_steps, angular_steps)

    # ---- Step 2: Generate triangle faces ----
    # Two triangles per quad cell, plus wrap-around seam
    faces = _generate_faces(axial_steps, angular_steps)

    # ---- Step 3: Write binary STL ----
    stl_data = _write_binary_stl(vertices, faces, params)

    # ---- Step 4: Save to file if path provided ----
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(stl_data)

    return stl_data


def _generate_vertices(
    displacement: np.ndarray,
    width: float,
    axial_steps: int,
    angular_steps: int,
) -> np.ndarray:
    """Convert displacement map to 3D vertices on a cylinder.

    Each point in the displacement grid maps to:
      x = r * cos(theta)
      y = r * sin(theta)
      z = axial position along roller length

    Where r = RADIUS - displacement (positive displacement = raised = smaller radius
    because the texture sticks inward toward center... wait, actually in the web version
    r = radius - displacement, and positive displacement means the surface extends
    outward from the base. The sign convention matches the web app exactly.)

    Args:
        displacement: 2D displacement array.
        width: Roller width in mm.
        axial_steps: Number of rows (Z positions).
        angular_steps: Number of columns (theta positions).

    Returns:
        Array of shape (axial_steps * angular_steps, 3) containing [x, y, z] vertices.
    """
    # Create coordinate arrays
    z_1d = np.linspace(0, width, axial_steps)
    theta_1d = np.linspace(0, 2.0 * math.pi, angular_steps, endpoint=False)

    # Build grids
    z_grid, theta_grid = np.meshgrid(z_1d, theta_1d, indexing='ij')

    # Calculate radius at each point
    r_grid = RADIUS - displacement

    # Convert to Cartesian coordinates
    x_grid = r_grid * np.cos(theta_grid)
    y_grid = r_grid * np.sin(theta_grid)

    # Flatten into vertex list: shape (num_vertices, 3)
    vertices = np.column_stack([
        x_grid.ravel(),
        y_grid.ravel(),
        z_grid.ravel(),
    ])

    return vertices


def _generate_faces(axial_steps: int, angular_steps: int) -> np.ndarray:
    """Generate triangle face indices connecting the vertex grid.

    Each cell in the grid becomes two triangles. The last column
    wraps around to connect with the first column (seam closure).

    Args:
        axial_steps: Number of rows.
        angular_steps: Number of columns.

    Returns:
        Array of shape (num_faces, 3) containing vertex indices.
    """
    faces = []

    for i in range(axial_steps - 1):
        for j in range(angular_steps - 1):
            # Regular quad → 2 triangles
            v1 = i * angular_steps + j
            v2 = i * angular_steps + (j + 1)
            v3 = (i + 1) * angular_steps + j
            v4 = (i + 1) * angular_steps + (j + 1)

            faces.append([v1, v2, v3])
            faces.append([v2, v4, v3])

        # Wrap-around: connect last column to first column
        j = angular_steps - 1
        v1 = i * angular_steps + j
        v2 = i * angular_steps + 0
        v3 = (i + 1) * angular_steps + j
        v4 = (i + 1) * angular_steps + 0

        faces.append([v1, v2, v3])
        faces.append([v2, v4, v3])

    return np.array(faces, dtype=np.int32)


def _calculate_normal(v1: np.ndarray, v2: np.ndarray, v3: np.ndarray) -> np.ndarray:
    """Calculate the outward-facing unit normal for a triangle.

    Uses the cross product of two edges to find the perpendicular direction.

    Args:
        v1, v2, v3: The three vertices of the triangle (each shape (3,)).

    Returns:
        Unit normal vector, shape (3,).
    """
    edge1 = v2 - v1
    edge2 = v3 - v1
    normal = np.cross(edge1, edge2)

    length = np.linalg.norm(normal)
    if length > 0:
        normal = normal / length

    return normal


def _write_binary_stl(
    vertices: np.ndarray,
    faces: np.ndarray,
    params: RollerParams,
) -> bytes:
    """Write vertices and faces as a binary STL file.

    Binary STL format:
      - 80 byte header (we embed settings info here)
      - 4 byte triangle count (uint32, little-endian)
      - For each triangle (50 bytes):
        - 12 bytes: normal vector (3 x float32)
        - 12 bytes: vertex 1 (3 x float32)
        - 12 bytes: vertex 2 (3 x float32)
        - 12 bytes: vertex 3 (3 x float32)
        - 2 bytes: attribute byte count (uint16, always 0)

    Args:
        vertices: Array of shape (N, 3) with vertex positions.
        faces: Array of shape (M, 3) with vertex indices per triangle.
        params: Roller parameters (for header string).

    Returns:
        Complete binary STL file as bytes.
    """
    num_triangles = len(faces)

    # Total size: 80 (header) + 4 (count) + 50 per triangle
    buffer_size = 84 + num_triangles * 50
    data = bytearray(buffer_size)

    # ---- Header (80 bytes) ----
    header_str = params.to_header_string()
    header_bytes = header_str.encode('ascii')[:80]  # Truncate if too long
    data[0:len(header_bytes)] = header_bytes
    # Remaining bytes stay as 0 (null padding)

    # ---- Triangle count ----
    struct.pack_into('<I', data, 80, num_triangles)

    # ---- Triangles ----
    offset = 84
    for face in faces:
        v1 = vertices[face[0]]
        v2 = vertices[face[1]]
        v3 = vertices[face[2]]

        normal = _calculate_normal(v1, v2, v3)

        # Pack: normal (3 floats) + 3 vertices (9 floats) + attribute (1 uint16)
        struct.pack_into('<3f', data, offset, *normal)
        offset += 12
        struct.pack_into('<3f', data, offset, *v1)
        offset += 12
        struct.pack_into('<3f', data, offset, *v2)
        offset += 12
        struct.pack_into('<3f', data, offset, *v3)
        offset += 12
        struct.pack_into('<H', data, offset, 0)
        offset += 2

    return bytes(data)
