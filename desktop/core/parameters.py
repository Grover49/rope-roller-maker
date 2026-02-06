"""
Parameter definitions for Rope Roller Maker.

All slider parameters, their ranges, defaults, and fixed specifications
are defined here in one place. This is the single source of truth —
both the UI and the generation algorithms reference these values.
"""

from dataclasses import dataclass, field
from typing import Literal
import math


# ============================================================
# Fixed Specifications (not user-adjustable)
# ============================================================

CIRCUMFERENCE = 200.0          # mm — fixed for clay work
DIAMETER = CIRCUMFERENCE / math.pi  # ~63.66mm
RADIUS = DIAMETER / 2.0        # ~31.83mm
BACKGROUND_DEPTH = 1.0         # mm — recessed purl texture depth
STRAND_RADIUS = 1.4            # mm — internal calculation for strand size

# Mesh resolution
# Higher = more detail but slower generation
# These are the values proven to work in the web prototype
SPIRAL_ANGULAR_STEPS = 200
SPIRAL_AXIAL_STEPS = 150
TANGENT_ANGULAR_STEPS = 150
TANGENT_AXIAL_STEPS = 100


# ============================================================
# Slider Parameter Definitions
# ============================================================

@dataclass
class SliderParam:
    """Definition of a single slider parameter.

    Attributes:
        name: Internal name used in code
        label: Display label shown in UI
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default starting value
        step: Increment per slider tick
        unit: Display unit (mm, %, or empty string)
        description: Short tooltip/help text
    """
    name: str
    label: str
    min_val: float
    max_val: float
    default: float
    step: float
    unit: str
    description: str


# The 8 adjustable parameters, in UI display order
SLIDER_DEFINITIONS = [
    SliderParam(
        name="width",
        label="Roller Width",
        min_val=100, max_val=300, default=200, step=10,
        unit="mm",
        description="Axial length of the roller"
    ),
    SliderParam(
        name="rope_width",
        label="Rope Width",
        min_val=20, max_val=60, default=40, step=5,
        unit="mm",
        description="Thickness of each rope"
    ),
    SliderParam(
        name="rope_depth",
        label="Rope Depth",
        min_val=2, max_val=8, default=4, step=0.5,
        unit="mm",
        description="Relief height / impression depth"
    ),
    SliderParam(
        name="num_wraps",
        label="Number of Wraps",
        min_val=1, max_val=25, default=10, step=1,
        unit="",
        description="How many ropes wrap around the roller"
    ),
    SliderParam(
        name="twist_rate",
        label="Rope Twist Rate",
        min_val=2, max_val=16, default=6, step=1,
        unit="",
        description="How tightly the rope strands braid"
    ),
    SliderParam(
        name="num_strands",
        label="Number of Strands",
        min_val=2, max_val=5, default=3, step=1,
        unit="",
        description="Strands per rope"
    ),
    SliderParam(
        name="smoothing",
        label="Smoothing",
        min_val=0, max_val=100, default=50, step=10,
        unit="%",
        description="Blend between sharp edges and smooth curves"
    ),
    SliderParam(
        name="weave_density",
        label="Weave Density",
        min_val=0.3, max_val=1.0, default=0.65, step=0.05,
        unit="",
        description="Spacing between strand orbits"
    ),
]


# ============================================================
# Roller Parameters (runtime values)
# ============================================================

@dataclass
class RollerParams:
    """Current parameter values for roller generation.

    Create with defaults using RollerParams(), or pass specific values.
    The mode field selects between 'spiral' and 'tangent' patterns.
    """
    width: float = 200.0
    rope_width: float = 40.0
    rope_depth: float = 4.0
    num_wraps: int = 10
    twist_rate: int = 6
    num_strands: int = 3
    smoothing: float = 50.0      # 0-100, will be divided by 100 in algorithm
    weave_density: float = 0.65
    mode: Literal["spiral", "tangent"] = "spiral"

    @property
    def smoothing_fraction(self) -> float:
        """Smoothing as 0.0-1.0 fraction (for use in algorithm)."""
        return self.smoothing / 100.0

    @property
    def strand_orbit(self) -> float:
        """How far strands orbit from rope center."""
        return self.rope_depth * self.weave_density

    @property
    def pitch(self) -> float:
        """Axial distance between spiral wraps (spiral mode only)."""
        return self.width / self.num_wraps

    def to_filename(self) -> str:
        """Generate the standardized STL filename from current settings.

        Format: Roller_W{width}-RW{rope_width}-RD{rope_depth}-{mode}{wraps}
                -TW{twist}-ST{strands}-SM{smoothing}-WD{weave}.stl

        Example: Roller_W200-RW40-RD4-SN10-TW6-ST3-SM50-WD65.stl
        """
        mode_prefix = "TN" if self.mode == "tangent" else "SN"
        weave_int = round(self.weave_density * 100)
        smoothing_int = round(self.smoothing)
        # Rope depth as integer: multiply by 10 and drop trailing zero
        # 4.0 → "4", 4.5 → "45", 5.5 → "55" (operator reads as 4, 4.5, 5.5)
        rd = int(self.rope_depth * 10) if self.rope_depth != int(self.rope_depth) else int(self.rope_depth)

        return (
            f"Roller_W{int(self.width)}"
            f"-RW{int(self.rope_width)}"
            f"-RD{rd}"
            f"-{mode_prefix}{self.num_wraps}"
            f"-TW{self.twist_rate}"
            f"-ST{self.num_strands}"
            f"-SM{smoothing_int}"
            f"-WD{weave_int}"
            f".stl"
        )

    def to_header_string(self) -> str:
        """Generate the 80-byte STL header string.

        Format: Roller:W200-RW40-D4-N10-T6-S3-Spiral
        """
        mode_name = "Tangent" if self.mode == "tangent" else "Spiral"
        rd = int(self.rope_depth * 10) if self.rope_depth != int(self.rope_depth) else int(self.rope_depth)
        header = (
            f"Roller:W{int(self.width)}"
            f"-RW{int(self.rope_width)}"
            f"-D{rd}"
            f"-N{self.num_wraps}"
            f"-T{self.twist_rate}"
            f"-S{self.num_strands}"
            f"-{mode_name}"
        )
        return header
