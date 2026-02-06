"""
Pattern generator for Rope Roller Maker.

Generates a 2D displacement map representing the rope texture
on the roller surface. This is the core algorithm — a direct port
of the proven JavaScript implementation with numpy optimization.

The displacement map is a 2D array where:
  - Rows = axial positions (along roller length, Z axis)
  - Columns = angular positions (around circumference, theta)
  - Values = displacement from base radius in mm
    - Positive = raised above surface (rope pattern)
    - Negative = recessed below surface (background purl texture)
"""

import numpy as np
import math
from .parameters import (
    RollerParams, CIRCUMFERENCE, RADIUS,
    BACKGROUND_DEPTH, STRAND_RADIUS,
    SPIRAL_ANGULAR_STEPS, SPIRAL_AXIAL_STEPS,
    TANGENT_ANGULAR_STEPS, TANGENT_AXIAL_STEPS,
)


def generate_displacement_map(params: RollerParams) -> np.ndarray:
    """Generate the full displacement map for the given parameters.

    This is the main entry point. It selects the appropriate algorithm
    based on the mode (spiral or tangent) and returns the displacement grid.

    Args:
        params: Current roller parameters.

    Returns:
        2D numpy array of shape (axial_steps, angular_steps) containing
        displacement values in mm.
    """
    if params.mode == "tangent":
        return _generate_tangent(params)
    else:
        return _generate_spiral(params)


def _generate_background(z_values: np.ndarray, theta_values: np.ndarray) -> np.ndarray:
    """Generate the background purl (knit) texture.

    Creates a subtle crosshatch pattern that fills the areas between ropes.
    This gives the roller a realistic knit background texture.

    The pattern is: -background_depth + 0.3 * sin(z * 2pi/2.5) * sin(theta * 50)

    Args:
        z_values: 2D array of axial positions (shape: axial x angular)
        theta_values: 2D array of angular positions (shape: axial x angular)

    Returns:
        2D array of background displacement values.
    """
    purl_x = np.sin(z_values * 2.0 * math.pi / 2.5)   # 2.5mm wavelength axially
    purl_y = np.sin(theta_values * 50.0)                # 50 waves around circumference
    return -BACKGROUND_DEPTH + 0.3 * purl_x * purl_y


def _generate_spiral(params: RollerParams) -> np.ndarray:
    """Generate displacement map for spiral (diagonal) mode.

    Ropes wrap diagonally around the roller like a barber pole.
    Each rope is made of twisted strands that create the braided look.

    This is a direct port of the JavaScript generateSTLFile() spiral logic.
    """
    angular_steps = SPIRAL_ANGULAR_STEPS
    axial_steps = SPIRAL_AXIAL_STEPS

    width = params.width
    rope_width = params.rope_width
    rope_depth = params.rope_depth
    num_wraps = params.num_wraps
    twist_rate = params.twist_rate
    num_strands = params.num_strands
    smoothing = params.smoothing_fraction
    strand_orbit = params.strand_orbit
    pitch = params.pitch

    # Pre-compute coordinate grids
    # z_vals[i] = axial position for row i
    # theta_vals[j] = angle for column j
    z_1d = np.linspace(0, width, axial_steps)
    theta_1d = np.linspace(0, 2.0 * math.pi, angular_steps, endpoint=False)
    z_grid, theta_grid = np.meshgrid(z_1d, theta_1d, indexing='ij')

    # Start with background texture
    displacement = _generate_background(z_grid, theta_grid)

    # Arc position along circumference for each angular step
    arc_pos = theta_1d * RADIUS  # shape: (angular_steps,)

    # Rope twist angle at each angular position
    rope_twist_angles = (arc_pos / CIRCUMFERENCE) * twist_rate * 2.0 * math.pi

    # Process each spiral wrap
    for spiral_start in range(num_wraps):
        # For each angular position, calculate where this spiral's
        # centerline crosses (its Z position)
        # Shape: (angular_steps,)
        z_spiral_centers = (
            (theta_1d / (2.0 * math.pi)) * pitch + spiral_start * pitch
        ) % width

        # Distance from each grid point to this spiral centerline
        # z_grid shape: (axial, angular), z_spiral_centers shape: (angular,)
        dz = z_grid - z_spiral_centers[np.newaxis, :]

        # Handle wrapping at roller edges
        dz = np.where(dz > width / 2, dz - width, dz)
        dz = np.where(dz < -width / 2, dz + width, dz)

        # Only process points close enough to this rope
        close_mask = np.abs(dz) < rope_width

        # Skip this wrap entirely if no points are close
        if not np.any(close_mask):
            continue

        # Calculate strand contributions
        # We need rope_twist_angle for each angular position
        # Broadcast to match grid: shape (1, angular_steps)
        twist_angles = rope_twist_angles[np.newaxis, :]

        # Accumulate strand heights and influences
        strand_heights_all = np.zeros((num_strands, axial_steps, angular_steps))
        strand_influences_all = np.zeros((num_strands, axial_steps, angular_steps))

        for s in range(num_strands):
            base_angle = s * (2.0 * math.pi / num_strands)
            strand_angle = base_angle + twist_angles

            # Strand offset from rope centerline
            strand_offset_z = strand_orbit * np.sin(strand_angle)
            strand_offset_radial = strand_orbit * np.cos(strand_angle)

            # Distance from point to this strand
            dz_to_strand = dz - strand_offset_z
            dist_to_strand = np.abs(dz_to_strand)

            # Gaussian influence falloff
            strand_influence = np.exp(
                -(dist_to_strand ** 2) / (STRAND_RADIUS * 0.8) ** 2
            )

            # Strand height contribution
            strand_height = (
                rope_depth + strand_offset_radial + STRAND_RADIUS * strand_influence
            )

            strand_heights_all[s] = strand_height
            strand_influences_all[s] = strand_influence

        # Blend strands based on smoothing parameter
        max_strand = np.max(strand_heights_all, axis=0)
        total_influence = np.sum(strand_influences_all, axis=0)
        weighted_sum = np.sum(
            strand_heights_all * strand_influences_all, axis=0
        )
        weighted_avg = weighted_sum / (total_influence + 0.001)

        blended_height = (1.0 - smoothing) * max_strand + smoothing * weighted_avg

        # Rope envelope — Gaussian falloff from rope center
        rope_envelope = np.exp(-(dz ** 2) / (rope_width / 3.0) ** 2)
        rope_base = rope_depth * rope_envelope
        contribution = np.maximum(blended_height * rope_envelope, rope_base)

        # Only apply where points are close to this rope
        displacement = np.where(
            close_mask,
            np.maximum(displacement, contribution),
            displacement
        )

    return displacement


def _generate_tangent(params: RollerParams) -> np.ndarray:
    """Generate displacement map for tangent (horizontal ring) mode.

    Ropes form discrete horizontal rings perpendicular to the roller axis.
    Uses the optimized pre-calculation approach from the web prototype:
    calculate one ring's pattern, then reuse it for all rings via lookup.

    This is a direct port of the JavaScript tangent mode logic.
    """
    angular_steps = TANGENT_ANGULAR_STEPS
    axial_steps = TANGENT_AXIAL_STEPS

    width = params.width
    rope_width = params.rope_width
    rope_depth = params.rope_depth
    num_wraps = params.num_wraps
    twist_rate = params.twist_rate
    num_strands = params.num_strands
    smoothing = params.smoothing_fraction
    strand_orbit = params.strand_orbit
    z_step = width / num_wraps

    # Pre-calculate one ring's pattern for all angular positions
    # at various distances from ring center (the lookup table approach)
    # Distance resolution: 0.5mm steps, matching the web version
    max_dist = rope_width * 2.0
    dist_steps = np.arange(0, max_dist + 0.5, 0.5)
    num_dist_steps = len(dist_steps)

    # For each angular position, calculate pattern at each distance
    theta_1d = np.linspace(0, 2.0 * math.pi, angular_steps, endpoint=False)
    arc_pos = theta_1d * RADIUS
    rope_twist_angles = (arc_pos / CIRCUMFERENCE) * twist_rate * 2.0 * math.pi

    # ring_pattern[j, d] = height at angular position j, distance index d
    ring_pattern = np.zeros((angular_steps, num_dist_steps))

    for j in range(angular_steps):
        twist_angle = rope_twist_angles[j]

        for d_idx, dist_to_ring in enumerate(dist_steps):
            if dist_to_ring >= rope_width:
                ring_pattern[j, d_idx] = 0.0
                continue

            strand_heights = []
            strand_influences = []

            for s in range(num_strands):
                base_angle = s * (2.0 * math.pi / num_strands)
                strand_angle = base_angle + twist_angle

                strand_offset_z = strand_orbit * math.sin(strand_angle)
                strand_offset_radial = strand_orbit * math.cos(strand_angle)

                dz_to_strand = dist_to_ring - abs(strand_offset_z)
                dist_to_strand = abs(dz_to_strand)

                strand_influence = math.exp(
                    -(dist_to_strand ** 2) / (STRAND_RADIUS * 0.8) ** 2
                )
                strand_height = (
                    rope_depth + strand_offset_radial
                    + STRAND_RADIUS * strand_influence
                )

                strand_heights.append(strand_height)
                strand_influences.append(strand_influence)

            # Blend strands
            max_strand = max(strand_heights)
            total_influence = sum(strand_influences)
            weighted_avg = (
                sum(h * inf for h, inf in zip(strand_heights, strand_influences))
                / (total_influence + 0.001)
            )
            blended_height = (1.0 - smoothing) * max_strand + smoothing * weighted_avg

            # Rope envelope
            rope_envelope = math.exp(
                -(dist_to_ring ** 2) / (rope_width / 3.0) ** 2
            )
            rope_base = rope_depth * rope_envelope
            contribution = max(blended_height * rope_envelope, rope_base)

            ring_pattern[j, d_idx] = contribution

    # Now apply the pre-calculated pattern to all grid points
    z_1d = np.linspace(0, width, axial_steps)
    theta_1d_grid = np.linspace(0, 2.0 * math.pi, angular_steps, endpoint=False)
    z_grid, theta_grid = np.meshgrid(z_1d, theta_1d_grid, indexing='ij')

    # Start with background
    displacement = _generate_background(z_grid, theta_grid)

    # For each ring, look up the pre-calculated pattern by distance
    for wrap_idx in range(num_wraps):
        wrap_z = (wrap_idx + 0.5) * z_step

        for i in range(axial_steps):
            z = z_1d[i]
            dist_to_ring = abs(z - wrap_z)

            if dist_to_ring >= max_dist:
                continue

            # Look up in pre-calculated pattern (0.5mm resolution)
            dist_key = round(dist_to_ring * 2.0)  # Convert to index
            if dist_key >= num_dist_steps:
                continue

            for j in range(angular_steps):
                height = ring_pattern[j, dist_key]
                if height > displacement[i, j]:
                    displacement[i, j] = height

    return displacement
