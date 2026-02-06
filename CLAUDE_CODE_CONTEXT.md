# Rope Roller Maker - Claude Code Development Context

## QUICK START FOR CLAUDE CODE

**Read this entire document before making any changes.** This project is transitioning from a working web prototype to a cross-platform desktop application. The human developer has basic coding knowledge - explain decisions, ask before major changes, and prioritize code quality and reliability over speed.

---

## PROJECT SUMMARY

### What This Is
A desktop application for designing and generating custom 3D-printable texture rollers for clay, pottery, and crafts. Users adjust parameters via sliders, see a live preview, and export STL files for 3D printing.

### Target Users
- Clay and pottery artists
- Crafters who want custom texture tools
- Eventually: commercial product for sale

### Current State
- **Working web prototype:** `rope_roller_maker_standalone.html` (fully functional)
- **Proven patterns:** Spiral mode (diagonal) and Tangent mode (horizontal rings)
- **Tested:** 3 physical rollers printed and successfully tested on clay
- **Next phase:** Cross-platform desktop app with Python/PyQt

---

## WHAT WE'RE BUILDING

### Desktop Application Requirements

**Must Have:**
1. Cross-platform: Windows, Mac, Linux
2. All current functionality from web app (Spiral + Tangent modes)
3. Live preview of pattern
4. STL export with embedded settings in filename and header
5. Fast, reliable STL generation (no browser limitations)
6. Professional UI suitable for commercial release

**New Feature - Image to Texture:**
- User provides an image (PNG, JPG)
- App converts image to grayscale heightmap
- Generates 3D relief texture on roller surface
- This is the major new feature for the desktop version

**Dropped Features:**
- Parallel mode (vertical stripes) - abandoned, do not implement

### Technology Stack Decision

**Recommended:** Python + PyQt6 (or PyQt5)
- Cross-platform with single codebase
- Native look and feel
- Good 3D/graphics libraries available
- PyInstaller for executable packaging
- Human has no Python GUI experience - will need guidance

**Alternative considered:** Electron - rejected (too heavy, essentially a browser)

**For STL Generation:**
- numpy for mesh calculations
- numpy-stl or trimesh for STL file writing
- Consider OpenGL or vispy for 3D preview (optional enhancement)

---

## CURRENT PARAMETERS (8 Adjustable Sliders)

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| Roller Width | 100-300mm | 200mm | Axial length of roller |
| Rope Width | 20-60mm | 40mm | Thickness of each rope |
| Rope Depth | 2-8mm | 4mm | Relief height/impression depth |
| Number of Wraps | 1-25 | 10 | Density of pattern |
| Rope Twist Rate | 2-16 | 6 | How tightly rope strands braid |
| Number of Strands | 2-5 | 3 | Strands per rope |
| Smoothing | 0-100% | 50% | Blend between sharp and smooth |
| Weave Density | 0.3-1.0 | 0.65 | Spacing between strand orbits |

### Fixed Specifications
- **Circumference:** 200mm (fixed, determines roller size for clay work)
- **Diameter:** 63.66mm (derived: 200/π)
- **Radius:** 31.83mm
- **Background depth:** 1mm recessed purl texture
- **Strand radius:** 1.4mm (internal calculation)

---

## STL GENERATION ALGORITHM - COMPLETE SPECIFICATION

This is the core intellectual property. The algorithm generates a displacement map on a cylindrical surface, then converts to triangle mesh.

### Overview
```
1. Create 2D grid (axial_steps × angular_steps)
2. For each grid point, calculate displacement from base radius
3. Displacement = background texture + rope pattern
4. Convert displacement map to 3D vertices on cylinder
5. Generate triangle faces connecting vertices
6. Calculate normals for each face
7. Write binary STL format
```

### Coordinate System
- **Z axis:** Along roller length (0 to width)
- **Theta:** Angle around circumference (0 to 2π)
- **R:** Radius from center (base radius minus displacement)
- **X, Y:** Cartesian coordinates (R×cos(θ), R×sin(θ))

### Background Texture (Purl Pattern)
```python
purl_x = sin(z * 2π / 2.5)  # 2.5mm wavelength axially
purl_y = sin(theta * 50)     # 50 waves around circumference
displacement = -background_depth + 0.3 * purl_x * purl_y
# background_depth = 1.0mm
```

### Spiral Mode Algorithm
```python
pitch = width / spiral_wraps

for each point (z, theta):
    arc_position = theta * radius  # Position along circumference
    
    for each spiral_start in range(spiral_wraps):
        # Calculate where spiral centerline crosses this theta
        z_spiral_center = ((theta / 2π) * pitch + spiral_start * pitch) % width
        
        # Distance to spiral centerline (with wrapping)
        dz = z - z_spiral_center
        if dz > width/2: dz -= width
        if dz < -width/2: dz += width
        
        if abs(dz) < rope_width:
            # Calculate rope twist at this position
            rope_twist_angle = (arc_position / circumference) * twist_rate * 2π
            
            strand_heights = []
            strand_influences = []
            
            for each strand s in range(num_strands):
                # Each strand orbits the rope centerline
                base_angle = s * (2π / num_strands)
                strand_angle = base_angle + rope_twist_angle
                
                # Strand position offset from rope center
                strand_offset_z = (rope_depth * weave_density) * sin(strand_angle)
                strand_offset_radial = (rope_depth * weave_density) * cos(strand_angle)
                
                # Distance from current point to this strand
                dz_to_strand = dz - strand_offset_z
                dist_to_strand = abs(dz_to_strand)
                
                # Gaussian influence falloff
                strand_influence = exp(-(dist_to_strand²) / (strand_radius * 0.8)²)
                strand_height = rope_depth + strand_offset_radial + strand_radius * strand_influence
                
                strand_heights.append(strand_height)
                strand_influences.append(strand_influence)
            
            # Blend strands based on smoothing parameter
            max_strand = max(strand_heights)
            total_influence = sum(strand_influences)
            weighted_avg = sum(h * i for h, i in zip(strand_heights, strand_influences)) / (total_influence + 0.001)
            
            blended_height = (1 - smoothing) * max_strand + smoothing * weighted_avg
            
            # Apply rope envelope (Gaussian falloff from rope center)
            rope_envelope = exp(-(dz²) / (rope_width/3)²)
            rope_base = rope_depth * rope_envelope
            contribution = max(blended_height * rope_envelope, rope_base)
            
            displacement = max(displacement, contribution)
```

### Tangent Mode Algorithm
Similar to spiral, but ropes are discrete horizontal rings at fixed Z positions:
```python
z_step = width / num_wraps

for wrap_idx in range(num_wraps):
    wrap_z = (wrap_idx + 0.5) * z_step  # Center of this ring
    dist_to_ring = abs(z - wrap_z)
    
    # Same strand calculation as spiral mode
    # But no diagonal pitch - rings are perpendicular to axis
```

**Tangent Mode Optimization:**
Pre-calculate one ring's pattern for all angular positions, then reuse for each ring (lookup by distance). This was implemented to improve performance.

### Mesh Generation
```python
# Resolution
angular_steps = 200  # (150 for tangent mode - performance tradeoff)
axial_steps = 150    # (100 for tangent mode)

# Generate vertices
vertices = []
for i in range(axial_steps):
    z = (i / (axial_steps - 1)) * width
    for j in range(angular_steps):
        theta = (j / angular_steps) * 2π
        r = radius - displacement[i][j]
        x = r * cos(theta)
        y = r * sin(theta)
        vertices.append([x, y, z])

# Generate faces (2 triangles per quad, plus wrap-around seam)
faces = []
for i in range(axial_steps - 1):
    for j in range(angular_steps - 1):
        v1 = i * angular_steps + j
        v2 = i * angular_steps + (j + 1)
        v3 = (i + 1) * angular_steps + j
        v4 = (i + 1) * angular_steps + (j + 1)
        
        faces.append([v1, v2, v3])
        faces.append([v2, v4, v3])
    
    # Wrap around (connect last column to first)
    j = angular_steps - 1
    v1 = i * angular_steps + j
    v2 = i * angular_steps + 0
    v3 = (i + 1) * angular_steps + j
    v4 = (i + 1) * angular_steps + 0
    faces.append([v1, v2, v3])
    faces.append([v2, v4, v3])
```

### Binary STL Format
```
Bytes 0-79:    Header (80 bytes) - embed settings string
Bytes 80-83:   Triangle count (uint32, little-endian)
For each triangle (50 bytes each):
    Bytes 0-11:  Normal vector (3 × float32)
    Bytes 12-23: Vertex 1 (3 × float32)
    Bytes 24-35: Vertex 2 (3 × float32)
    Bytes 36-47: Vertex 3 (3 × float32)
    Bytes 48-49: Attribute byte count (uint16, usually 0)
```

### Normal Calculation
```python
edge1 = v2 - v1
edge2 = v3 - v1
normal = cross(edge1, edge2)
normal = normalize(normal)  # Unit length
```

---

## FILE NAMING CONVENTION

**Format:** `Roller_W{width}-RW{rope_width}-RD{rope_depth}-{mode}{wraps}-TW{twist}-ST{strands}-SM{smoothing}-WD{weave}.stl`

**Example:** `Roller_W200-RW40-RD4-SN10-TW6-ST3-SM50-WD65.stl`

**Legend:**
- W = Width (mm)
- RW = Rope Width (mm)
- RD = Rope Depth (mm)
- SN = Spiral Number of wraps / TN = Tangent Number
- TW = Twist rate
- ST = Strands
- SM = Smoothing (%)
- WD = Weave Density (×100)

**STL Header (80 bytes):**
```
Roller:W200-RW40-D4-N10-T6-S3-Spiral
```
Padded with nulls to 80 bytes.

---

## DEVELOPMENT HISTORY - WHAT WAS TRIED

### Successful Approaches
1. **Single-file web app** - Easy distribution, worked well for prototype
2. **Smart filename with settings** - Users love being able to identify settings from filename
3. **Smoothing parameter** - Blending max height with weighted average gives best visual results
4. **Gaussian falloff** - For strand influence and rope envelope, creates natural-looking braids
5. **Pre-calculated patterns** - For tangent mode, calculate once and lookup (improved performance)

### Failed Approaches - DO NOT REPEAT

1. **High wrap count to simulate tangent mode**
   - Tried using 50-100 spiral wraps
   - Ropes overlapped and became too thin
   - Had to implement true tangent mode separately

2. **Low mesh resolution for speed**
   - Reduced to 100×75 for faster generation
   - Caused missing pattern areas and poor quality
   - Reverted to 150×100 minimum for tangent, 200×150 for spiral

3. **Web Worker for background processing**
   - Attempted to move STL generation to background thread
   - Broke entire app - scope issues, undefined functions
   - Too complex to debug, abandoned approach
   - **Desktop app won't have this limitation** - can use proper threading

4. **Incremental code edits via string replacement**
   - Caused duplicate code, syntax errors, missing brackets
   - Solution: Always make complete function replacements, keep backups

### Performance Notes
- Spiral mode: Instant generation (< 1 second)
- Tangent mode: 20-30 seconds in browser, user had to click "Wait" multiple times
- **Desktop app should be much faster** - Python with numpy is more efficient than browser JS

---

## IMAGE TO TEXTURE - NEW FEATURE SPECIFICATION

This is the major new feature for the desktop version.

### Concept
- User loads an image (PNG, JPG, etc.)
- Image is converted to grayscale
- Grayscale values map to displacement (white = high, black = low)
- Creates embossed/debossed relief on roller surface
- When rolled on clay, transfers the image as a texture

### Implementation Approach
```python
1. Load image with PIL/Pillow
2. Convert to grayscale
3. Resize to match mesh resolution (angular_steps × axial_steps)
4. Normalize values to displacement range (0 to max_depth)
5. Optionally: Apply Gaussian blur for smoother relief
6. Optionally: Invert (emboss vs deboss)
7. Optionally: Tile/repeat image across roller surface
8. Use as displacement map instead of rope algorithm
```

### Parameters for Image Mode
- **Image file:** File picker
- **Max depth:** 1-10mm (how deep the relief goes)
- **Invert:** Checkbox (swap raised/recessed)
- **Blur/Smooth:** 0-100% (soften harsh edges)
- **Tile X:** 1-10 (repeat image horizontally)
- **Tile Y:** 1-10 (repeat image around circumference)
- **Brightness/Contrast:** Adjust before conversion

### Edge Cases to Handle
- Non-square images (stretch vs crop vs letterbox)
- Very small images (upscale with interpolation)
- Very large images (downsample efficiently)
- Transparent PNGs (treat alpha as white? black? user choice?)

---

## PROJECT FILE STRUCTURE

### Current Files (Web Prototype)
```
rope_roller_project/
├── rope_roller_maker_standalone.html  # Main web app (reference implementation)
├── manifest.json                       # PWA config (not needed for desktop)
├── service-worker.js                   # PWA offline (not needed for desktop)
├── icon192.png                         # App icon
├── icon512.png                         # App icon (larger)
├── README_PWA.md                       # Web deployment docs
├── PROJECT_CONTEXT.md                  # Original context doc
└── CLAUDE_CODE_CONTEXT.md              # This file
```

### Proposed Desktop Structure
```
rope_roller_project/
├── web/                                # Archive web version
│   └── (move all web files here)
├── desktop/                            # New desktop app
│   ├── main.py                         # Entry point
│   ├── ui/
│   │   ├── main_window.py              # Main window layout
│   │   ├── controls_panel.py           # Parameter sliders
│   │   ├── preview_panel.py            # Pattern preview
│   │   └── resources/                  # Icons, styles
│   ├── core/
│   │   ├── pattern_generator.py        # Displacement map calculation
│   │   ├── stl_generator.py            # Mesh and STL export
│   │   ├── image_processor.py          # Image to heightmap (new feature)
│   │   └── parameters.py               # Parameter definitions and defaults
│   ├── tests/
│   │   └── test_stl_generation.py      # Unit tests
│   ├── requirements.txt                # Python dependencies
│   └── build/
│       ├── build_windows.py            # PyInstaller config for Windows
│       ├── build_mac.py                # PyInstaller config for Mac
│       └── build_linux.py              # PyInstaller config for Linux
├── assets/
│   ├── icons/                          # App icons various sizes
│   └── sample_images/                  # Test images for image-to-texture
├── CLAUDE_CODE_CONTEXT.md              # This file (keep at root)
└── README.md                           # Project overview
```

---

## QUALITY STANDARDS

### Code Quality Expectations
- **Readable:** Clear variable names, comments explaining "why"
- **Modular:** Separate concerns (UI, generation, file I/O)
- **Tested:** Unit tests for core algorithms
- **Documented:** Docstrings on all functions
- **Type hints:** Use Python type hints for clarity

### STL Quality Expectations
- **Watertight meshes:** No holes or non-manifold edges
- **Correct normals:** All pointing outward
- **Efficient:** Reasonable file sizes (current: 1-12 MB)
- **Accurate:** Patterns match preview exactly

### UI/UX Expectations
- **Responsive:** Preview updates as sliders move (or on release)
- **Informative:** Show generation progress for slow operations
- **Professional:** Suitable for commercial release
- **Accessible:** Keyboard navigation, reasonable contrast

---

## KNOWN ISSUES TO ADDRESS

1. **Tangent mode performance** - Was slow in browser, should be fast in Python/numpy
2. **No Undo/Redo** - Consider adding for parameter changes
3. **No Presets** - Users might want to save/load parameter combinations
4. **No 3D Preview** - Currently 2D canvas, consider adding 3D viewer (nice to have)
5. **Roller ends are open** - STL is just the textured surface, no end caps (might need for some printers)

---

## DEVELOPER NOTES

### Human's Technical Level
- Basic coding knowledge
- Comfortable with Git/GitHub Desktop
- No Python GUI experience
- Has 3D printer, uses AnycubicSlicer
- Understands the domain (clay, pottery, textures)

### Communication Style Needed
- Explain decisions before implementing
- Ask for confirmation on major architectural choices
- Provide context for why something is done a certain way
- Be patient with questions
- Offer to explain any code in detail

### Workflow Preferences
- Confirm actions before starting tasks
- Keep backups before major changes
- Quality over speed
- Rock-solid reliability is priority

---

## GETTING STARTED - FIRST STEPS

### Recommended Initial Tasks

1. **Set up project structure**
   - Create desktop/ folder and subfolders
   - Initialize requirements.txt with dependencies
   - Create basic main.py entry point

2. **Port STL generation first**
   - Translate JavaScript algorithm to Python
   - Use numpy for performance
   - Verify output matches web version exactly

3. **Build minimal UI**
   - Single window with sliders
   - Generate button
   - Save STL button
   - No preview yet - just verify generation works

4. **Add preview**
   - 2D preview first (like web version)
   - Can enhance to 3D later

5. **Add image-to-texture mode**
   - New feature, implement after core is solid

6. **Build executables**
   - PyInstaller for each platform
   - Test on actual machines (not just dev environment)

---

## LICENSE AND PERMISSIONS

This project is being developed for eventual commercial release. Claude Code has full permission to:
- Modify any code
- Refactor for better architecture
- Optimize algorithms
- Improve code quality
- Suggest better approaches
- Rewrite sections entirely if beneficial

The goal is **production-quality code** suitable for commercial distribution.

---

## CONTACT AND CONTEXT

This document was prepared by Claude (Projects) to hand off to Claude Code. The human developer is based in Amarillo, Texas, US. They have been developing this project over multiple sessions and have a clear vision of the end product.

**Primary goals:**
1. Professional desktop app
2. Rock-solid reliability
3. Impressive, detailed 3D relief generation
4. Cross-platform distribution
5. Eventually: commercial release

**When in doubt:** Ask the human. They prefer confirmation before major changes.

---

*Document version: 1.0*
*Created: February 2025*
*For use with: Claude Code CLI*
